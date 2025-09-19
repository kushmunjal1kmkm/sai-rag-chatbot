import asyncio
import aiohttp
import time
import hashlib
import json
import re
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

from bs4 import BeautifulSoup
from .config_manager import ConfigManager

@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    scraped_at: str
    content_hash: str

class WebScraper:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config()
        self.session = None
        self.scraped_urls: Set[str] = set()
        self.cache_dir = Path(self.config.cache_path) / "web_content"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'SAI-RAG-Bot/1.0 (Educational Purpose)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_cache_path(self, url: str) -> Path:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"
    
    def _is_content_cached(self, url: str) -> bool:
        cache_path = self._get_cache_path(url)
        return cache_path.exists()
    
    def _load_cached_content(self, url: str) -> Optional[ScrapedContent]:
        if not self.config.enable_caching:
            return None
        
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return ScrapedContent(**data)
            except Exception as e:
                self.logger.warning(f"Failed to load cached content for {url}: {e}")
        return None
    
    def _save_to_cache(self, content: ScrapedContent):
        if not self.config.enable_caching:
            return
        
        cache_path = self._get_cache_path(content.url)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': content.url,
                    'title': content.title,
                    'content': content.content,
                    'metadata': content.metadata,
                    'scraped_at': content.scraped_at,
                    'content_hash': content.content_hash
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to cache content for {content.url}: {e}")
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _calculate_content_relevance(self, content: str, title: str = "") -> float:
        """Calculate relevance score for sports-related content"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Sports-specific keywords with weights
        sports_keywords = {
            'high_priority': ['sports authority of india', 'sai', 'athlete', 'training', 'coaching', 
                            'olympic', 'commonwealth', 'national games', 'talent identification',
                            'sports science', 'fitness assessment', 'khelo india', 'tops'],
            'medium_priority': ['sports', 'fitness', 'exercise', 'physical', 'performance',
                              'competition', 'tournament', 'championship', 'medal', 'academy'],
            'low_priority': ['health', 'nutrition', 'wellness', 'youth', 'development', 
                           'infrastructure', 'facility', 'equipment', 'program', 'scheme']
        }
        
        score = 0.0
        word_count = len(content.split())
        
        # Score based on keyword frequency
        for priority, keywords in sports_keywords.items():
            weight = 3.0 if priority == 'high_priority' else 2.0 if priority == 'medium_priority' else 1.0
            
            for keyword in keywords:
                # Count occurrences in content
                content_count = content_lower.count(keyword)
                title_count = title_lower.count(keyword) * 2  # Title keywords get double weight
                
                score += (content_count + title_count) * weight
        
        # Normalize by content length
        if word_count > 0:
            score = score / (word_count / 100)  # Per 100 words
        
        # Bonus for sports-specific phrases
        bonus_phrases = [
            'sports development', 'athlete development', 'sports training',
            'national coach', 'sports facility', 'fitness standards',
            'talent scouting', 'sports policy', 'annual report'
        ]
        
        for phrase in bonus_phrases:
            if phrase in content_lower:
                score += 5.0
        
        return min(score, 100.0)  # Cap at 100
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'extracted_at': datetime.now().isoformat()
        }
        
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('name') == 'description':
                metadata['description'] = tag.get('content', '')
            elif tag.get('name') == 'keywords':
                metadata['keywords'] = tag.get('content', '')
            elif tag.get('property') == 'og:title':
                metadata['og_title'] = tag.get('content', '')
        
        return metadata
    
    def _extract_hyperlinks(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract relevant hyperlinks with enhanced discovery"""
        links = []
        
        # Get all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip unwanted links
            if any(skip in href for skip in ['#', 'javascript:', 'mailto:', 'tel:', '.pdf', '.doc', '.jpg', '.png']):
                continue
            
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Only include relevant domains
            if parsed.netloc and any(domain in parsed.netloc for domain in [
                'sportsauthorityofindia.nic.in',
                'kheloindia.gov.in', 
                'fitindia.gov.in',
                'yas.nic.in',  # Youth Affairs and Sports
                'sportstechnology.gov.in'
            ]):
                # Priority links (more likely to have valuable content)
                link_text = link.get_text().lower()
                priority_keywords = [
                    'about', 'scheme', 'program', 'training', 'facility', 'athlete',
                    'sport', 'fitness', 'talent', 'development', 'policy', 'guideline',
                    'annual report', 'document', 'circular', 'notification', 'news',
                    'achievement', 'infrastructure', 'centre', 'academy', 'course'
                ]
                
                # Check if link contains priority keywords
                is_priority = any(keyword in link_text or keyword in href.lower() for keyword in priority_keywords)
                
                links.append({
                    'url': full_url,
                    'text': link.get_text().strip()[:100],
                    'priority': is_priority
                })
        
        # Sort by priority and return unique URLs
        links.sort(key=lambda x: x['priority'], reverse=True)
        return list(set([link['url'] for link in links]))
    
    async def _scrape_single_url(self, url: str) -> Optional[ScrapedContent]:
        if url in self.scraped_urls:
            return None
        
        cached_content = self._load_cached_content(url)
        if cached_content:
            self.logger.info(f"Using cached content for: {url}")
            self.scraped_urls.add(url)
            return cached_content
        
        try:
            await asyncio.sleep(self.config.request_delay)
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                title = soup.title.string.strip() if soup.title else urlparse(url).path
                content = self._extract_text_content(soup)
                metadata = self._extract_metadata(soup, url)
                
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                scraped_content = ScrapedContent(
                    url=url,
                    title=title,
                    content=content,
                    metadata=metadata,
                    scraped_at=datetime.now().isoformat(),
                    content_hash=content_hash
                )
                
                self._save_to_cache(scraped_content)
                self.scraped_urls.add(url)
                
                self.logger.info(f"Scraped: {url} (Content length: {len(content)})")
                return scraped_content
                
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def _scrape_with_hyperlinks(self, start_urls: List[str], max_depth: int = 3) -> List[ScrapedContent]:
        """Enhanced deep scraping with better hyperlink following"""
        all_content = []
        urls_to_process = [(url, 0) for url in start_urls]
        processed_urls = set()
        urls_by_depth = {0: [], 1: [], 2: [], 3: []}
        
        self.logger.info(f"Starting deep scan with max depth: {max_depth}")
        
        while urls_to_process:
            # Process URLs in batches by depth (breadth-first approach)
            current_depth = min(depth for _, depth in urls_to_process)
            current_batch = [(url, depth) for url, depth in urls_to_process if depth == current_depth][:15]
            
            # Remove processed batch from queue
            urls_to_process = [(url, depth) for url, depth in urls_to_process if depth != current_depth or (url, depth) not in current_batch]
            
            self.logger.info(f"Processing {len(current_batch)} URLs at depth {current_depth}")
            
            # Scrape current batch
            tasks = []
            for url, depth in current_batch:
                if url not in processed_urls and depth <= max_depth:
                    tasks.append(self._scrape_single_url(url))
                    processed_urls.add(url)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and extract new links
                for result, (url, depth) in zip(results, current_batch):
                    if isinstance(result, ScrapedContent):
                        all_content.append(result)
                        urls_by_depth[depth].append(url)
                        
                        # Extract hyperlinks for next depth level
                        if depth < max_depth:
                            try:
                                async with self.session.get(url) as response:
                                    if response.status == 200:
                                        html = await response.text()
                                        soup = BeautifulSoup(html, 'html.parser')
                                        hyperlinks = self._extract_hyperlinks(soup, url)
                                        
                                        # Limit new links per page based on depth
                                        max_links = max(15 - depth * 3, 5)
                                        for link in hyperlinks[:max_links]:
                                            if link not in processed_urls:
                                                urls_to_process.append((link, depth + 1))
                                        
                                        self.logger.info(f"Found {len(hyperlinks[:max_links])} new links from {url}")
                                        
                            except Exception as e:
                                self.logger.warning(f"Failed to extract hyperlinks from {url}: {e}")
        
        # Log scanning summary
        total_by_depth = {depth: len(urls) for depth, urls in urls_by_depth.items() if urls}
        self.logger.info(f"Deep scan complete. URLs by depth: {total_by_depth}")
        
        return all_content
    
    async def scrape_urls_from_file(self, url_file_path: str) -> List[ScrapedContent]:
        if not Path(url_file_path).exists():
            self.logger.error(f"URL file not found: {url_file_path}")
            return []
        
        with open(url_file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        self.logger.info(f"Starting to scrape {len(urls)} URLs with deep hyperlink following...")
        
        scraped_content = await self._scrape_with_hyperlinks(urls, max_depth=3)
        
        self.logger.info(f"Completed scraping. Total content pieces: {len(scraped_content)}")
        return scraped_content
    
    def convert_to_documents(self, scraped_contents: List[ScrapedContent]) -> List[Dict[str, Any]]:
        documents = []
        
        for content in scraped_contents:
            if len(content.content.strip()) < 100:  # Skip very short content
                continue
            
            # Calculate relevance score
            relevance_score = self._calculate_content_relevance(content.content, content.title)
            
            # Only include content with reasonable relevance (threshold: 5.0)
            if relevance_score >= 5.0:
                doc = {
                    'text': content.content,
                    'title': content.title,
                    'source': content.url,
                    'category': 'web_content',
                    'metadata': {
                        **content.metadata,
                        'content_hash': content.content_hash,
                        'scraped_at': content.scraped_at,
                        'relevance_score': relevance_score
                    }
                }
                documents.append(doc)
            else:
                self.logger.debug(f"Filtered out low relevance content: {content.title} (score: {relevance_score})")
        
        # Sort by relevance score (highest first)
        documents.sort(key=lambda x: x['metadata']['relevance_score'], reverse=True)
        
        self.logger.info(f"Filtered {len(documents)} relevant documents from {len(scraped_contents)} scraped pages")
        return documents

async def main():
    config_manager = ConfigManager()
    
    async with WebScraper(config_manager) as scraper:
        scraped_content = await scraper.scrape_urls_from_file("./data/urls.txt")
        documents = scraper.convert_to_documents(scraped_content)
        
        print(f"Scraped {len(documents)} documents")
        for doc in documents[:3]:
            print(f"Title: {doc['title'][:100]}...")
            print(f"Content length: {len(doc['text'])}")
            print("---")

if __name__ == "__main__":
    asyncio.run(main())