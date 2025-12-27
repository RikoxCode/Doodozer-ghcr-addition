import argparse
import asyncio
import logging
from urllib.parse import urlparse

from doodoo.core.downloader import Doodozer
from doodoo.utils.helper import setup_logger

def is_valid_url(url: str) -> bool:
    """Validate whether a string is a valid URL.

    This method checks if the given string contains valid URL components, 
    such as scheme and netloc.

    Args:
        url (str): URL string to validate.

    Returns:
        bool: True if URL is valid, False if invalid.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def main():
    """Main function to run the Doodozer CLI.

    This function sets up command line arguments, validates URLs (one or more separated by commas),
    initializes the logger, and starts the video download process from DoodStream.

    Returns:
        None: This function does not return a value.

    Raises:
        SystemExit: If no valid URLs are provided or a fatal error occurs.

    Example:
        Run from command line:
        $ python main.py https://d-s.io/e/xxxxxxxxxx
        $ python main.py https://d-s.io/e/xxxxxxxxxx -o video.mp4 -v
        $ python main.py "https://d-s.io/e/xxxxxxxxxx,https://d-s.io/e/yyyyyyyyyy" -o videos/
    """
    parser = argparse.ArgumentParser(
        description="Doodozer CLI - Video Downloader Tool for DoodStream.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Usage examples:\n"
               "  python main.py https://d-s.io/e/xxxxxxxxxx\n"
               "  python main.py https://d-s.io/e/xxxxxxxxxx -o my_video.mp4 -v\n"
               "  python main.py \"https://d-s.io/e/xxxxxxxxxx,https://d-s.io/e/yyyyyyyyyy\" -o videos/"
    )

    parser.add_argument("url", metavar="URL", type=str, help="DoodStream video URL to download. Can use multiple URLs separated by commas (example: url1,url2).")
    parser.add_argument("-o", "--output", dest="output_path", type=str, default=None, help="Filename or path to save the video. If not provided, filename will be created automatically.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode for more detailed log output.")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar during download.")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)

    urls = [url.strip() for url in args.url.split(",")]
    
    valid_urls = []
    for url in urls:
        if not is_valid_url(url) or ("/e/" not in url and "/d/" not in url):
            logging.warning(f"Invalid URL and will be ignored: {url}")
        else:
            valid_urls.append(url)
    
    if not valid_urls:
        logging.error("No valid DoodStream URLs. Make sure URLs are from DoodStream.")
        return
    
    logging.info(f"Downloading {len(valid_urls)} video(s)...")

    try:
        if len(valid_urls) > 1 and args.output_path and not args.output_path.endswith("/") and not args.output_path.endswith("\\"):
            import os
            output_dir = args.output_path
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
                logging.info(f"Creating directory: {output_dir}")
                args.output_path = output_dir
            else:
                args.output_path = output_dir

        for i, url in enumerate(valid_urls, 1):
            logging.info(f"Processing video {i}/{len(valid_urls)}: {url}")
            
            if len(valid_urls) > 1:
                if args.output_path and os.path.isdir(args.output_path):
                    current_output_path = args.output_path
                elif args.output_path:
                    current_output_path = os.path.dirname(args.output_path) or "."
                else:
                    current_output_path = "."
            else:
                current_output_path = args.output_path
            
            downloader = Doodozer(
                url=url,
                output_path=current_output_path,
                show_progress=not args.no_progress
            )
            await downloader.download()
            
            logging.info(f"Finished downloading video {i}/{len(valid_urls)}")
            
        logging.info("All videos successfully downloaded!")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    except asyncio.CancelledError:
        logging.info("Program stopped by asyncio")

if __name__ == "__main__":
    asyncio.run(main())