import logging
import os
from typing import Optional

import aiohttp
import aiofiles
from tqdm.asyncio import tqdm

from doodoo.api.doodstream import DoodStreamAPI

class Doodozer:
    """Main class for orchestrating the DoodStream video download process.

    This class provides a complete interface for downloading videos from DoodStream,
    from obtaining the download URL to saving the file with a progress bar.

    Attributes:
        url (str): DoodStream video URL to download.
        output_path (Optional[str]): Output file path. If None, filename will be created automatically.
        show_progress (bool): Display progress bar if True.
        logger (logging.Logger): Logger for logging download activities.
    """

    def __init__(self, url: str, output_path: Optional[str] = None, show_progress: bool = True):
        """Initialize the Doodozer Downloader instance.

        Args:
            url (str): DoodStream video URL to download.
            output_path (Optional[str]): Output file path. If None, filename will be created
                automatically based on video title. If it's a directory, file will be saved
                inside that directory with an automatic name.
            show_progress (bool): Display progress bar if True. Default is True.

        Raises:
            ValueError: If the provided URL is invalid or empty.
        """
        self.url = url
        self.output_path = output_path
        self.show_progress = show_progress
        self.logger = logging.getLogger(__name__)
    
    async def download(self) -> None:
        """Start the entire DoodStream video download process.

        This method orchestrates the entire download process, including:
        1. Retrieving video information (direct download URL and title)
        2. Determining the output file path
        3. Downloading the file with progress bar (if enabled)
        4. Saving the file to the specified location

        Returns:
            None: This method is asynchronous and does not return a value.

        Raises:
            aiohttp.ClientError: If a network error occurs while accessing DoodStream.
            Exception: Other errors that may occur during the download process.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            api = DoodStreamAPI(session)

            result = await api.get_download_url(self.url)
            if not result:
                self.logger.error("Failed to retrieve video information. Process stopped.")
                return
            
            direct_url, title = result

            if self.output_path:
                if os.path.isdir(self.output_path):
                    filename = f"{title}.mp4"
                    final_path = os.path.join(self.output_path, filename)
                else:
                    final_path = self.output_path
            else:
                filename = f"{title}.mp4"
                final_path = filename
            
            self.logger.info(f"Video will be saved to: {os.path.abspath(final_path)}")

            await self._download_file(session, direct_url, final_path)

    async def _download_file(self, session: aiohttp.ClientSession, url: str, path: str) -> None:
        """Download file from URL and save it to the given path with progress bar.

        This method downloads the file asynchronously using HTTP streaming and displays
        a progress bar if show_progress is enabled. Files are downloaded in chunks
        to reduce memory usage.

        Args:
            session (aiohttp.ClientSession): HTTP session for making requests.
            url (str): URL of the file to download.
            path (str): Full path where the file will be saved.

        Returns:
            None: This method is asynchronous and does not return a value.

        Raises:
            aiohttp.ClientError: If a network error occurs during download.
            OSError: If an error occurs while writing the file to disk.
            Exception: Other errors that may occur during the download process.

        Note:
            If an error occurs during download, the partially downloaded file
            will be deleted to prevent corrupt files from remaining on disk.
        """
        try:
            async with session.get(url, timeout=None) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("Content-Length", 0))

                self.logger.info("Starting download process...")

                progress_bar = None
                if self.show_progress:
                    progress_bar = tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=os.path.basename(path)
                    )
                
                async with aiofiles.open(path, "wb") as f:
                    chunk_size = 1024 * 1024  # 1 MB chunks for better throughput
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        if progress_bar:
                            progress_bar.update(len(chunk))
                
                if progress_bar:
                    progress_bar.close()

                self.logger.info(f"\nDownload complete! Video successfully saved.")
        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to download file: {e}")
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            self.logger.error(f"Error occurred while saving file: {e}")
            if os.path.exists(path):
                os.remove(path)