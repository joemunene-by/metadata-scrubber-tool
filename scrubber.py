#!/usr/bin/env python3
"""
scrubber.py - Metadata Scrubber Tool

A command-line utility for stripping metadata from images and PDFs.
Supports EXIF removal from JPEG/PNG/TIFF and metadata cleaning from PDF files.

Usage:
    python3 scrubber.py --input photo.jpg --inspect
    python3 scrubber.py --input ./photos/ --recursive --backup
    python3 scrubber.py --input document.pdf --dry-run --verbose
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

try:
    from PIL import Image, ExifTags
except ImportError:
    print("[!] Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("[!] PyPDF2 is required. Install with: pip install PyPDF2")
    sys.exit(1)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # Graceful fallback if colorama is not installed
    class _Dummy:
        def __getattr__(self, _):
            return ""
    Fore = _Dummy()
    Style = _Dummy()


SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
SUPPORTED_PDF_EXT = {".pdf"}
SUPPORTED_EXT = SUPPORTED_IMAGE_EXT | SUPPORTED_PDF_EXT

BANNER = rf"""
{Fore.CYAN}  __  __      _          ___              _     _
 |  \/  |___ | |_ __ _  / __| __ _ _ _  _| |__ | |__  ___ _ _
 | |\/| / -_)|  _/ _` | \__ \/ _| '_| || | '_ \| '_ \/ -_) '_|
 |_|  |_\___| \__\__,_| |___/\__|_|  \_,_|_.__/|_.__/\___|_|
{Style.RESET_ALL}
{Fore.WHITE} Metadata Scrubber Tool — Strip. Clean. Protect.{Style.RESET_ALL}
"""


class ImageScrubber:
    """Handles metadata inspection and removal for image files."""

    EXIF_TAG_NAMES = {v: k for k, v in ExifTags.TAGS.items()}

    @staticmethod
    def get_metadata(filepath: str) -> dict:
        """Extract EXIF metadata from an image file."""
        metadata = {}
        try:
            img = Image.open(filepath)
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, f"Unknown-{tag_id}")
                    # Sanitize binary data for display
                    if isinstance(value, bytes):
                        value = f"<binary data, {len(value)} bytes>"
                    metadata[tag_name] = value
            img_info = img.info
            for key in ("dpi", "icc_profile", "exif", "xmp"):
                if key in img_info:
                    if key == "icc_profile":
                        metadata[f"info.{key}"] = f"<binary data, {len(img_info[key])} bytes>"
                    elif key == "exif":
                        metadata[f"info.{key}"] = f"<binary data, {len(img_info[key])} bytes>"
                    else:
                        metadata[f"info.{key}"] = img_info[key]
            img.close()
        except Exception as e:
            metadata["_error"] = str(e)
        return metadata

    @staticmethod
    def strip_metadata(filepath: str, output_path: str) -> dict:
        """
        Remove all metadata from an image by re-encoding pixel data.
        Returns a dict with status information.
        """
        result = {"success": False, "fields_removed": 0, "error": None}
        try:
            original_meta = ImageScrubber.get_metadata(filepath)
            result["fields_removed"] = len(
                {k for k in original_meta if not k.startswith("_")}
            )

            img = Image.open(filepath)
            # Create a clean copy with only pixel data
            clean = Image.new(img.mode, img.size)
            clean.putdata(list(img.getdata()))

            # Preserve format-specific settings
            fmt = img.format or Path(filepath).suffix.lstrip(".").upper()
            if fmt in ("JPG",):
                fmt = "JPEG"

            save_kwargs = {}
            if fmt == "JPEG":
                save_kwargs["quality"] = 95
                save_kwargs["subsampling"] = 0
            elif fmt == "PNG":
                save_kwargs["compress_level"] = 6

            clean.save(output_path, format=fmt, **save_kwargs)
            img.close()
            clean.close()

            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result


class PDFScrubber:
    """Handles metadata inspection and removal for PDF files."""

    METADATA_KEYS = [
        "/Title", "/Author", "/Subject", "/Keywords",
        "/Creator", "/Producer", "/CreationDate", "/ModDate",
        "/Trapped",
    ]

    @staticmethod
    def get_metadata(filepath: str) -> dict:
        """Extract document metadata from a PDF."""
        metadata = {}
        try:
            reader = PdfReader(filepath)
            info = reader.metadata
            if info:
                for key in PDFScrubber.METADATA_KEYS:
                    val = info.get(key)
                    if val:
                        metadata[key.lstrip("/")] = str(val)
            metadata["_pages"] = len(reader.pages)
        except Exception as e:
            metadata["_error"] = str(e)
        return metadata

    @staticmethod
    def strip_metadata(filepath: str, output_path: str) -> dict:
        """
        Remove all document-level metadata from a PDF.
        Returns a dict with status information.
        """
        result = {"success": False, "fields_removed": 0, "error": None}
        try:
            original_meta = PDFScrubber.get_metadata(filepath)
            result["fields_removed"] = len(
                {k for k in original_meta if not k.startswith("_")}
            )

            reader = PdfReader(filepath)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Write with empty metadata
            writer.add_metadata({
                "/Title": "",
                "/Author": "",
                "/Subject": "",
                "/Keywords": "",
                "/Creator": "",
                "/Producer": "",
            })

            with open(output_path, "wb") as f:
                writer.write(f)

            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result


class MetadataScrubber:
    """Main controller for the metadata scrubbing pipeline."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.files_processed = 0
        self.files_failed = 0
        self.total_fields_removed = 0

    def log(self, msg: str, level: str = "info"):
        """Print a formatted log message."""
        prefix_map = {
            "info":    f"{Fore.CYAN}[*]{Style.RESET_ALL}",
            "success": f"{Fore.GREEN}[+]{Style.RESET_ALL}",
            "warn":    f"{Fore.YELLOW}[!]{Style.RESET_ALL}",
            "error":   f"{Fore.RED}[-]{Style.RESET_ALL}",
            "verbose": f"{Fore.WHITE}[>]{Style.RESET_ALL}",
        }
        prefix = prefix_map.get(level, "[*]")
        print(f" {prefix} {msg}")

    def collect_files(self) -> list:
        """Gather all target files from the input path."""
        input_path = Path(self.args.input).resolve()
        files = []

        if input_path.is_file():
            if input_path.suffix.lower() in SUPPORTED_EXT:
                files.append(input_path)
            else:
                self.log(f"Unsupported format: {input_path.suffix}", "warn")
        elif input_path.is_dir():
            pattern = "**/*" if self.args.recursive else "*"
            for p in input_path.glob(pattern):
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXT:
                    files.append(p)
        else:
            self.log(f"Path not found: {input_path}", "error")

        return sorted(files)

    def resolve_output(self, filepath: Path) -> Path:
        """Determine the output path for a processed file."""
        if self.args.output:
            out_dir = Path(self.args.output).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            # Preserve relative structure for batch processing
            try:
                rel = filepath.relative_to(Path(self.args.input).resolve())
            except ValueError:
                rel = filepath.name
            dest = out_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            return dest
        return filepath

    def backup_file(self, filepath: Path):
        """Create a backup copy of the original file."""
        backup_path = filepath.with_suffix(filepath.suffix + ".bak")
        counter = 1
        while backup_path.exists():
            backup_path = filepath.with_suffix(f"{filepath.suffix}.bak{counter}")
            counter += 1
        shutil.copy2(filepath, backup_path)
        if self.args.verbose:
            self.log(f"Backup saved: {backup_path}", "verbose")

    def inspect_file(self, filepath: Path):
        """Display metadata for a single file."""
        ext = filepath.suffix.lower()
        print(f"\n {Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f" {Fore.WHITE}{Style.BRIGHT}{filepath.name}{Style.RESET_ALL}")
        print(f" {Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"   Path: {filepath}")
        print(f"   Size: {filepath.stat().st_size:,} bytes")
        print(f"   Type: {ext.upper().lstrip('.')}")
        print()

        if ext in SUPPORTED_IMAGE_EXT:
            meta = ImageScrubber.get_metadata(str(filepath))
        elif ext in SUPPORTED_PDF_EXT:
            meta = PDFScrubber.get_metadata(str(filepath))
        else:
            self.log("Unsupported format for inspection.", "warn")
            return

        visible = {k: v for k, v in meta.items() if not k.startswith("_")}
        if not visible:
            self.log("No metadata found.", "info")
        else:
            self.log(f"{len(visible)} metadata field(s) detected:", "info")
            print()
            for key, value in visible.items():
                val_str = str(value)
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                print(f"   {Fore.YELLOW}{key:<30}{Style.RESET_ALL} {val_str}")
        print()

    def scrub_file(self, filepath: Path):
        """Strip metadata from a single file."""
        ext = filepath.suffix.lower()
        output_path = self.resolve_output(filepath)
        is_inplace = (output_path == filepath)

        if self.args.dry_run:
            if ext in SUPPORTED_IMAGE_EXT:
                meta = ImageScrubber.get_metadata(str(filepath))
            else:
                meta = PDFScrubber.get_metadata(str(filepath))
            count = len({k for k in meta if not k.startswith("_")})
            self.log(
                f"[DRY RUN] {filepath.name} -- {count} field(s) would be removed",
                "info",
            )
            return

        if self.args.backup and is_inplace:
            self.backup_file(filepath)

        # For in-place writes, use a temp file
        if is_inplace:
            tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        else:
            tmp_path = output_path

        if ext in SUPPORTED_IMAGE_EXT:
            result = ImageScrubber.strip_metadata(str(filepath), str(tmp_path))
        elif ext in SUPPORTED_PDF_EXT:
            result = PDFScrubber.strip_metadata(str(filepath), str(tmp_path))
        else:
            self.log(f"Skipping unsupported file: {filepath.name}", "warn")
            return

        if result["success"]:
            if is_inplace:
                shutil.move(str(tmp_path), str(filepath))
            self.files_processed += 1
            self.total_fields_removed += result["fields_removed"]
            self.log(
                f"Scrubbed: {filepath.name} ({result['fields_removed']} fields removed)",
                "success",
            )
        else:
            if is_inplace and tmp_path.exists():
                tmp_path.unlink()
            self.files_failed += 1
            self.log(f"Failed: {filepath.name} -- {result['error']}", "error")

    def run(self):
        """Execute the scrubbing pipeline."""
        print(BANNER)

        files = self.collect_files()
        if not files:
            self.log("No supported files found at the specified path.", "warn")
            sys.exit(1)

        self.log(f"Found {len(files)} file(s) to process.\n", "info")

        start = time.time()

        if self.args.inspect:
            for f in files:
                self.inspect_file(f)
        else:
            for f in files:
                self.scrub_file(f)

        elapsed = time.time() - start

        # Summary
        print(f"\n {Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
        if self.args.inspect:
            self.log(f"Inspected {len(files)} file(s) in {elapsed:.2f}s", "info")
        elif self.args.dry_run:
            self.log(f"Dry run complete. {len(files)} file(s) analyzed in {elapsed:.2f}s", "info")
        else:
            self.log(f"Processed: {self.files_processed}  |  Failed: {self.files_failed}  |  Fields removed: {self.total_fields_removed}", "success")
            self.log(f"Elapsed: {elapsed:.2f}s", "info")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrubber",
        description="Strip metadata from images and PDF files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scrubber.py --input photo.jpg --inspect\n"
            "  python3 scrubber.py --input ./photos/ --recursive --backup\n"
            "  python3 scrubber.py --input doc.pdf --output ./clean/ --verbose\n"
            "  python3 scrubber.py --input ./files/ --dry-run --recursive\n"
        ),
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to a file or directory to process.",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory for cleaned files. If omitted, files are modified in place.",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Display metadata without modifying files.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create .bak copies of originals before scrubbing.",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan directories for supported files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be removed without making changes.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    scrubber = MetadataScrubber(args)
    scrubber.run()


if __name__ == "__main__":
    main()
