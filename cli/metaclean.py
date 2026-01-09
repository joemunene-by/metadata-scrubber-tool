import os
import sys
import argparse
from PIL import Image

def scrub_image(file_path, output_path=None):
    """
    Strips EXIF data from an image by re-saving it.
    """
    try:
        img = Image.open(file_path)
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)
        
        if not output_path:
            filename, ext = os.path.splitext(file_path)
            output_path = f"{filename}_cleaned{ext}"
            
        image_without_exif.save(output_path)
        print(f"  [✓] Successfully cleaned: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"  [✗] Failed to clean {os.path.basename(file_path)}: {str(e)}")
        return False

def banner():
    print("""
    \033[95m ███╗   ███╗███████╗████████╗ █████╗  ██████╗██╗     ███████╗ █████╗ ███╗   ██╗
    \033[95m ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║     ██╔════╝██╔══██╗████╗  ██║
    \033[95m ██╔████╔██║█████╗     ██║   ███████║██║     ██║     █████╗  ███████║██╔██╗ ██║
    \033[95m ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║██║     ██║     ██╔══╝  ██╔══██║██║╚██╗██║
    \033[95m ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║╚██████╗███████╗███████╗██║  ██║██║ ╚████║
    \033[95m ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝\033[0m
                                  \033[90mProfessional Metadata Sanitizer\033[0m
    """)

def main():
    banner()
    parser = argparse.ArgumentParser(description="Clean metadata from image files.")
    parser.add_argument("-f", "--file", help="Path to a single file to clean")
    parser.add_argument("-d", "--dir", help="Path to a directory to clean all images in")
    parser.add_argument("-o", "--output", help="Output path (for single file mode)")
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.print_help()
        sys.exit(1)
        
    if args.file:
        scrub_image(args.file, args.output)
        
    if args.dir:
        print(f"Cleaning all images in: {args.dir}")
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        for filename in os.listdir(args.dir):
            if filename.lower().endswith(valid_extensions):
                scrub_image(os.path.join(args.dir, filename))

if __name__ == "__main__":
    main()
