import logging
import re
import random
import time
from typing import Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

class DoodStreamAPI:
    """Class for interacting with DoodStream API.

    This class provides methods to access and process videos from the
    DoodStream platform, including obtaining direct download URLs and video titles.

    Attributes:
        session (aiohttp.ClientSession): HTTP session for making requests.
        logger (logging.Logger): Logger for logging class activities.
    """

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize DoodStreamAPI instance.

        Args:
            session (aiohttp.ClientSession): HTTP session used to make
                requests to DoodStream API.

        Raises:
            ValueError: If the provided session is not an instance of aiohttp.ClientSession.
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    async def get_download_url(self, url: str) -> Optional[Tuple[str, str]]:
        """Get direct download URL and video title from DoodStream page.

        This method processes the DoodStream embed page to extract the direct
        download URL and video title that can be used to download the video.

        Args:
            url (str): DoodStream video URL (example: https://dood.la/e/xxxxxxxx).
                       URL must be in valid embed format.

        Returns:
            Optional[Tuple[str, str]]: Tuple containing (direct_download_url, title) if successful,
                                     or None if URL processing fails.

        Raises:
            aiohttp.ClientError: If an error occurs while making HTTP request.
            Exception: Other general errors that occur while processing the page.

        Example:
            >>> api = DoodStreamAPI(session)
            >>> download_url, title = await api.get_download_url("https://dood.la/e/xxxxxxxx")
            >>> if download_url:
            ...     print(f"Title: {title}")
            ...     print(f"Download URL: {download_url}")
        """
        self.logger.info(f"Processing URL: {url}")

        embed_url = url.replace('/d/', '/e/')

        try:
            self.session.headers.update({"Referer": embed_url})

            async with self.session.get(embed_url) as response:
                response.raise_for_status()
                html_content = await response.text()
            
            pass_md5_match = re.search(r'/pass_md5/([^"\']+)', html_content)
            if not pass_md5_match:
                self.logger.error("Cannot find 'pass_md5' on embed page.")
                return None
            
            pass_md5_path = pass_md5_match.group(1)
            domain = urlparse(embed_url).netloc
            pass_md5_url = f"https://{domain}/pass_md5/{pass_md5_path}"
            self.logger.debug(f"pass_md5 URL found: {pass_md5_url}")

            async with self.session.get(pass_md5_url) as md5_response:
                md5_response.raise_for_status()
                media_url_base = await md5_response.text()

            token = pass_md5_path.split('/')[-1]
            random_chars = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=10))

            final_url = f"{media_url_base}{random_chars}?token={token}&expiry={int(time.time())}"

            soup = BeautifulSoup(html_content, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.text.strip() if title_tag else token

            title = re.sub(r'[\\/*?:"<>|]', "", title)

            self.logger.info(f"Direct download link successfully created for '{title}'")
            return final_url, title
        except aiohttp.ClientError as e:
            self.logger.error(f"Request error while accessing DoodStream: {e}")
        except Exception as e:
            self.logger.error(f"Error occurred while processing DoodStream URL: {e}", exc_info=True)

        return None