"""
Agent 1: Website Crawler
Design System Extractor v2

Persona: Meticulous Design Archaeologist

Responsibilities:
- Auto-discover pages from base URL
- Classify page types (homepage, listing, detail, etc.)
- Prepare page list for user confirmation
"""

import asyncio
import re
from urllib.parse import urljoin, urlparse
from typing import Optional, Callable
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from core.token_schema import DiscoveredPage, PageType, Viewport
from config.settings import get_settings


class PageDiscoverer:
    """
    Discovers pages from a website for design system extraction.
    
    This is the first part of Agent 1's job — finding pages before
    the human confirms which ones to crawl.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.visited_urls: set[str] = set()
        self.discovered_pages: list[DiscoveredPage] = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_browser()
    
    async def _init_browser(self):
        """Initialize Playwright browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.settings.browser.headless
        )
        self.context = await self.browser.new_context(
            viewport={
                "width": self.settings.viewport.desktop_width,
                "height": self.settings.viewport.desktop_height,
            },
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
    
    async def _close_browser(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    def _normalize_url(self, url: str, base_url: str) -> Optional[str]:
        """Normalize and validate URL."""
        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        
        # Only allow same domain
        if parsed.netloc != base_parsed.netloc:
            return None
        
        # Remove fragments and normalize
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Remove trailing slash for consistency
        if normalized.endswith('/') and len(normalized) > len(f"{parsed.scheme}://{parsed.netloc}/"):
            normalized = normalized.rstrip('/')
        
        return normalized
    
    def _classify_page_type(self, url: str, title: str = "") -> PageType:
        """
        Classify page type based on URL patterns and title.
        
        This is a heuristic — not perfect, but good enough for discovery.
        """
        url_lower = url.lower()
        title_lower = title.lower() if title else ""
        
        # Check URL patterns
        patterns = {
            PageType.HOMEPAGE: [r'/$', r'/home$', r'/index'],
            PageType.LISTING: [r'/products', r'/catalog', r'/list', r'/category', r'/collection', r'/search'],
            PageType.DETAIL: [r'/product/', r'/item/', r'/detail/', r'/p/', r'/[a-z-]+/\d+'],
            PageType.FORM: [r'/contact', r'/form', r'/apply', r'/submit', r'/register'],
            PageType.AUTH: [r'/login', r'/signin', r'/signup', r'/auth', r'/account'],
            PageType.CHECKOUT: [r'/cart', r'/checkout', r'/basket', r'/payment'],
            PageType.MARKETING: [r'/landing', r'/promo', r'/campaign', r'/offer'],
            PageType.ABOUT: [r'/about', r'/team', r'/company', r'/story'],
            PageType.CONTACT: [r'/contact', r'/support', r'/help'],
        }
        
        for page_type, url_patterns in patterns.items():
            for pattern in url_patterns:
                if re.search(pattern, url_lower):
                    return page_type
        
        # Check title patterns
        title_patterns = {
            PageType.HOMEPAGE: ['home', 'welcome'],
            PageType.LISTING: ['products', 'catalog', 'collection', 'browse'],
            PageType.DETAIL: ['product', 'item'],
            PageType.AUTH: ['login', 'sign in', 'sign up', 'register'],
            PageType.ABOUT: ['about', 'our story', 'team'],
            PageType.CONTACT: ['contact', 'get in touch', 'support'],
        }
        
        for page_type, keywords in title_patterns.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return page_type
        
        return PageType.OTHER
    
    async def _extract_links(self, page: Page, base_url: str) -> list[str]:
        """Extract all internal links from a page."""
        links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(a => a.href).filter(href => 
                    href && 
                    !href.startsWith('javascript:') && 
                    !href.startsWith('mailto:') &&
                    !href.startsWith('tel:') &&
                    !href.includes('#')
                );
            }
        """)
        
        # Normalize and filter
        valid_links = []
        for link in links:
            normalized = self._normalize_url(link, base_url)
            if normalized and normalized not in self.visited_urls:
                valid_links.append(normalized)
        
        return list(set(valid_links))
    
    async def _get_page_title(self, page: Page) -> str:
        """Get page title."""
        try:
            return await page.title()
        except Exception:
            return ""
    
    async def discover(
        self,
        base_url: str,
        max_pages: int = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> list[DiscoveredPage]:
        """
        Discover pages from a website.
        
        Args:
            base_url: The starting URL
            max_pages: Maximum pages to discover (default from settings)
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of discovered pages
        """
        max_pages = max_pages or self.settings.crawl.max_pages
        
        async with self:
            # Start with homepage
            normalized_base = self._normalize_url(base_url, base_url)
            if not normalized_base:
                raise ValueError(f"Invalid base URL: {base_url}")
            
            queue = [normalized_base]
            self.visited_urls = set()
            self.discovered_pages = []
            
            while queue and len(self.discovered_pages) < max_pages:
                current_url = queue.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                self.visited_urls.add(current_url)
                
                try:
                    page = await self.context.new_page()
                    
                    # Navigate to page with more lenient settings
                    # Use 'domcontentloaded' instead of 'networkidle' for faster/more reliable loading
                    try:
                        await page.goto(
                            current_url,
                            wait_until="domcontentloaded",
                            timeout=60000  # 60 seconds
                        )
                        # Wait a bit more for JS to render
                        await page.wait_for_timeout(2000)
                    except Exception as nav_error:
                        # Try with 'load' event as fallback
                        try:
                            await page.goto(
                                current_url,
                                wait_until="load",
                                timeout=60000
                            )
                            await page.wait_for_timeout(3000)
                        except Exception:
                            # Last resort - just try to get whatever loaded
                            pass
                    
                    # Get page info
                    title = await self._get_page_title(page)
                    page_type = self._classify_page_type(current_url, title)
                    depth = len(urlparse(current_url).path.split('/')) - 1
                    
                    # Create discovered page
                    discovered = DiscoveredPage(
                        url=current_url,
                        title=title,
                        page_type=page_type,
                        depth=depth,
                        selected=True,
                    )
                    self.discovered_pages.append(discovered)
                    
                    # Extract links for further crawling
                    new_links = await self._extract_links(page, base_url)
                    
                    # Prioritize certain page types
                    priority_patterns = ['/product', '/listing', '/category', '/about', '/contact']
                    priority_links = [l for l in new_links if any(p in l.lower() for p in priority_patterns)]
                    other_links = [l for l in new_links if l not in priority_links]
                    
                    # Add to queue (priority first)
                    for link in priority_links + other_links:
                        if link not in self.visited_urls and link not in queue:
                            queue.append(link)
                    
                    await page.close()
                    
                    # Progress callback
                    if progress_callback:
                        progress = len(self.discovered_pages) / max_pages
                        progress_callback(min(progress, 1.0))
                    
                    # Rate limiting
                    await asyncio.sleep(self.settings.crawl.crawl_delay_ms / 1000)
                    
                except Exception as e:
                    # Log error but continue
                    discovered = DiscoveredPage(
                        url=current_url,
                        title="",
                        page_type=PageType.OTHER,
                        depth=0,
                        selected=False,
                        error=str(e),
                    )
                    self.discovered_pages.append(discovered)
            
            return self.discovered_pages
    
    def get_pages_by_type(self) -> dict[PageType, list[DiscoveredPage]]:
        """Group discovered pages by type."""
        grouped: dict[PageType, list[DiscoveredPage]] = {}
        for page in self.discovered_pages:
            if page.page_type not in grouped:
                grouped[page.page_type] = []
            grouped[page.page_type].append(page)
        return grouped
    
    def get_suggested_pages(self, min_pages: int = None) -> list[DiscoveredPage]:
        """
        Get suggested pages for extraction.
        
        Ensures diversity of page types and prioritizes key templates.
        """
        min_pages = min_pages or self.settings.crawl.min_pages
        
        # Priority order for page types
        priority_types = [
            PageType.HOMEPAGE,
            PageType.LISTING,
            PageType.DETAIL,
            PageType.FORM,
            PageType.MARKETING,
            PageType.AUTH,
            PageType.ABOUT,
            PageType.CONTACT,
            PageType.OTHER,
        ]
        
        selected = []
        grouped = self.get_pages_by_type()
        
        # First pass: get at least one of each priority type
        for page_type in priority_types:
            if page_type in grouped and grouped[page_type]:
                # Take the first (usually shallowest) page of this type
                page = sorted(grouped[page_type], key=lambda p: p.depth)[0]
                if page not in selected:
                    selected.append(page)
        
        # Second pass: fill up to min_pages with remaining pages
        remaining = [p for p in self.discovered_pages if p not in selected and not p.error]
        remaining.sort(key=lambda p: p.depth)
        
        while len(selected) < min_pages and remaining:
            selected.append(remaining.pop(0))
        
        # Mark as selected
        for page in selected:
            page.selected = True
        
        return selected


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def discover_pages(base_url: str, max_pages: int = 20) -> list[DiscoveredPage]:
    """Convenience function to discover pages."""
    discoverer = PageDiscoverer()
    return await discoverer.discover(base_url, max_pages)


async def quick_discover(base_url: str) -> dict:
    """Quick discovery returning summary dict."""
    pages = await discover_pages(base_url)
    
    return {
        "total_found": len(pages),
        "by_type": {
            pt.value: len([p for p in pages if p.page_type == pt])
            for pt in PageType
        },
        "pages": [
            {
                "url": p.url,
                "title": p.title,
                "type": p.page_type.value,
                "selected": p.selected,
            }
            for p in pages
        ],
    }
