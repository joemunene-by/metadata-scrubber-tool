# Metadata Scrubber Tool

A command-line utility for stripping metadata from images and PDF files. Built for privacy-conscious professionals who need reliable, local-only metadata sanitization without sending files to third-party services.

All processing happens locally. Nothing leaves your machine.

## Features

- Strip EXIF data from JPEG, PNG, and TIFF images (GPS coordinates, device info, timestamps, thumbnails)
- Remove document metadata from PDFs (author, creator, producer, creation/modification dates)
- Inspect mode to view embedded metadata without modifying files
- Batch processing across entire directories
- Recursive directory scanning
- Automatic backup of originals before scrubbing
- Dry-run mode to preview changes before committing
- Verbose output showing exactly what was removed
- Clean re-encoding of images to eliminate hidden metadata layers

## Installation

```bash
git clone https://github.com/joemunene-by/metadata-scrubber-tool.git
cd metadata-scrubber-tool
pip install -r requirements.txt
```

Requires Python 3.8 or later.

## Usage

### Inspect metadata on a single file

```bash
python3 scrubber.py --input photo.jpg --inspect
```

### Strip metadata from a single image

```bash
python3 scrubber.py --input photo.jpg
```

### Strip metadata from a PDF

```bash
python3 scrubber.py --input document.pdf
```

### Batch process a directory with backups

```bash
python3 scrubber.py --input ./photos/ --recursive --backup
```

### Output cleaned files to a separate directory

```bash
python3 scrubber.py --input ./photos/ --output ./clean/ --recursive
```

### Preview what would be removed (dry run)

```bash
python3 scrubber.py --input ./files/ --dry-run --recursive --verbose
```

## Supported Formats

| Format | Extensions         | Metadata Removed                          |
|--------|--------------------|-------------------------------------------|
| JPEG   | .jpg, .jpeg        | EXIF, GPS, ICC profile, XMP, thumbnails   |
| PNG    | .png               | Text chunks, ICC profile, EXIF            |
| TIFF   | .tiff, .tif        | EXIF, GPS, ICC profile                    |
| PDF    | .pdf               | Author, creator, producer, dates, subject |

## Command Reference

| Flag            | Description                                      |
|-----------------|--------------------------------------------------|
| `-i, --input`   | Path to file or directory (required)             |
| `-o, --output`  | Output directory for cleaned files               |
| `--inspect`     | View metadata without modifying files            |
| `--backup`      | Create .bak copies before scrubbing              |
| `-r, --recursive` | Scan directories recursively                   |
| `--dry-run`     | Preview removals without writing changes         |
| `-v, --verbose` | Show detailed processing output                  |

## How It Works

For images, the tool opens the file, extracts raw pixel data, and writes it to a new file without any metadata. This is more thorough than simply deleting EXIF tags -- it ensures no hidden metadata survives in ancillary chunks or application markers.

For PDFs, the tool reads all pages and writes them to a new document with zeroed-out document information fields.

## Disclaimer

This tool is provided for legitimate privacy and security purposes. Use it responsibly and in compliance with applicable laws. The authors are not responsible for misuse.

## License

MIT License. See [LICENSE](LICENSE) for details.
