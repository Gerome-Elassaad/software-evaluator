import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.settings import use_config

from product_evaluator.config import settings
from product_evaluator.utils.logger import log_info, log_error, log_debug, log_execution_time


class WebExtractor:
    """Service for extracting content from web pages."""
    
    def __init__(self):
        """Initialize the web extractor."""
        # Configure trafilatura for best content extraction
        self.traf_config = use_config()
        self.traf_config.set("DEFAULT", "extraction_timeout", "30")
        self.traf_config.set("DEFAULT", "min_extracted_size", "500")
        
        # User agent to mimic a browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
    
    @log_execution_time
    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary containing the extracted content
        """
        if not url:
            return {"error": "No URL provided", "content": "", "metadata": {}}
        
        # Validate URL
        if not self._is_valid_url(url):
            return {"error": "Invalid URL format", "content": "", "metadata": {}}
        
        try:
            # Use requests to get the web page
            response = await asyncio.to_thread(
                requests.get, url, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            
            # Get the HTML content
            html_content = response.text
            
            # Extract main content using trafilatura
            extracted_text = await asyncio.to_thread(
                trafilatura.extract, html_content, config=self.traf_config, 
                include_comments=False, include_tables=True, output_format="text"
            )
            
            # If trafilatura fails, fallback to BS4
            if not extracted_text or len(extracted_text) < 500:
                log_info(f"Trafilatura extraction failed for {url}, using BeautifulSoup fallback")
                extracted_text = await self._extract_with_bs4(html_content)
            
            # Extract metadata
            metadata = await self._extract_metadata(html_content, url)
            
            # If all extraction methods fail
            if not extracted_text or len(extracted_text) < 100:
                log_error(f"Content extraction failed for {url}")
                return {
                    "error": "Failed to extract meaningful content from the URL",
                    "content": "",
                    "metadata": metadata,
                }
            
            return {
                "content": extracted_text,
                "metadata": metadata,
                "error": None,
            }
            
        except requests.exceptions.RequestException as e:
            log_error(f"Request error for {url}: {str(e)}")
            return {
                "error": f"Failed to fetch URL: {str(e)}",
                "content": "",
                "metadata": {},
            }
        except Exception as e:
            log_error(f"Content extraction error for {url}: {str(e)}")
            return {
                "error": f"Content extraction error: {str(e)}",
                "content": "",
                "metadata": {},
            }
    
    async def _extract_with_bs4(self, html_content: str) -> str:
        """
        Extract text content using BeautifulSoup as a fallback.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Extracted text
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Extract text and clean it
            text = soup.get_text(separator="\n")
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            log_error(f"BeautifulSoup extraction error: {str(e)}")
            return ""
    
    async def _extract_metadata(self, html_content: str, url: str) -> Dict[str, str]:
        """
        Extract metadata from HTML content.
        
        Args:
            html_content: HTML content as string
            url: Original URL
            
        Returns:
            Dictionary of metadata
        """
        metadata = {"url": url}
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                metadata["title"] = title_tag.get_text().strip()
            
            # Extract description
            description_tag = soup.find("meta", attrs={"name": "description"})
            if description_tag:
                metadata["description"] = description_tag.get("content", "").strip()
            
            # Extract product information if available
            # Price
            price_selectors = [
                "span.price", ".price", ".product-price", 
                "span[itemprop='price']", "*[itemprop='price']"
            ]
            for selector in price_selectors:
                price_tag = soup.select_one(selector)
                if price_tag:
                    price_text = price_tag.get_text().strip()
                    # Clean price text
                    price_text = re.sub(r'[^\d.,]', '', price_text)
                    if price_text:
                        metadata["price"] = price_text
                        break
            
            # Product name
            product_name_selectors = [
                "h1.product-title", "h1.product-name", "h1[itemprop='name']",
                "*[itemprop='name']", "h1.entry-title"
            ]
            for selector in product_name_selectors:
                name_tag = soup.select_one(selector)
                if name_tag:
                    metadata["product_name"] = name_tag.get_text().strip()
                    break
            
            # Features section
            features_section = None
            features_selectors = [
                "div.features", "section.features", "div.product-features",
                "ul.features", "div#features", "section#features"
            ]
            for selector in features_selectors:
                section = soup.select_one(selector)
                if section:
                    features_section = section
                    break
            
            if features_section:
                features_list = features_section.find_all("li")
                if features_list:
                    features = [item.get_text().strip() for item in features_list]
                    metadata["features"] = "\n".join(features)
            
            return metadata
            
        except Exception as e:
            log_error(f"Metadata extraction error: {str(e)}")
            return metadata
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


# Singleton instance
extractor = WebExtractor()


# Convenience function for module-level usage
async def extract_content_from_url(url: str) -> Dict[str, Any]:
    """
    Extract content from a URL.
    
    Args:
        url: URL to extract content from
        
    Returns:
        Dictionary containing the extracted content
    """
    global extractor
    return await extractor.extract_from_url(url)