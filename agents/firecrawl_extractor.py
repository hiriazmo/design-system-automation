"""
Agent 1B: Firecrawl CSS Extractor
Design System Extractor v2

Persona: CSS Deep Diver

Responsibilities:
- Fetch and parse all CSS files from a website
- Extract colors from CSS rules, variables, and values
- Bypass CORS restrictions by fetching CSS directly
- Complement Playwright extraction with deeper CSS analysis
"""

import re
import asyncio
from typing import Optional, Callable
from datetime import datetime

# Firecrawl for web scraping
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

from core.color_utils import (
    parse_color,
    get_contrast_with_white,
    get_contrast_with_black,
)


class FirecrawlExtractor:
    """
    Extracts colors from CSS files using Firecrawl.
    
    This complements the Playwright extraction by:
    1. Fetching all linked CSS files
    2. Parsing inline <style> blocks
    3. Extracting CSS variables
    4. Finding all color values in CSS rules
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl extractor.
        
        Args:
            api_key: Firecrawl API key (optional for free tier)
        """
        self.api_key = api_key
        self.colors: dict[str, dict] = {}
        self.css_variables: dict[str, str] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats = {
            "css_files_parsed": 0,
            "style_blocks_parsed": 0,
            "colors_found": 0,
            "css_variables_found": 0,
        }
        
        # Color regex pattern
        self.color_regex = re.compile(
            r'#[0-9a-fA-F]{3,8}|'
            r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)|'
            r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)|'
            r'hsl\(\s*\d+\s*,\s*[\d.]+%?\s*,\s*[\d.]+%?\s*\)|'
            r'hsla\(\s*\d+\s*,\s*[\d.]+%?\s*,\s*[\d.]+%?\s*,\s*[\d.]+\s*\)',
            re.IGNORECASE
        )
        
        # CSS variable pattern
        self.css_var_regex = re.compile(
            r'--[\w-]+\s*:\s*([^;]+)',
            re.IGNORECASE
        )
    
    def _extract_colors_from_css(self, css_text: str, source: str = "css") -> list[dict]:
        """Extract all color values from CSS text."""
        colors = []
        
        # Find all color values
        matches = self.color_regex.findall(css_text)
        for match in matches:
            colors.append({
                "value": match.strip(),
                "source": source,
                "context": "firecrawl-css",
            })
        
        return colors
    
    def _extract_css_variables(self, css_text: str) -> dict[str, str]:
        """Extract CSS variables from CSS text."""
        variables = {}
        
        matches = self.css_var_regex.findall(css_text)
        for match in matches:
            # Get variable name and value
            var_match = re.search(r'(--[\w-]+)\s*:\s*([^;]+)', css_text)
            if var_match:
                var_name = var_match.group(1)
                var_value = var_match.group(2).strip()
                variables[var_name] = var_value
        
        # More precise extraction
        for match in re.finditer(r'(--[\w-]+)\s*:\s*([^;]+);', css_text):
            var_name = match.group(1)
            var_value = match.group(2).strip()
            variables[var_name] = var_value
        
        return variables
    
    def _process_color(self, color_value: str) -> Optional[str]:
        """Process and normalize a color value to hex."""
        parsed = parse_color(color_value)
        if parsed:
            return parsed.hex
        return None
    
    def _aggregate_color(self, color_data: dict):
        """Aggregate a color into the collection."""
        hex_value = self._process_color(color_data.get("value", ""))
        if not hex_value:
            return
        
        if hex_value not in self.colors:
            contrast_white = get_contrast_with_white(hex_value)
            contrast_black = get_contrast_with_black(hex_value)
            
            self.colors[hex_value] = {
                "value": hex_value,
                "frequency": 0,
                "contexts": [],
                "sources": [],
                "contrast_white": round(contrast_white, 2),
                "contrast_black": round(contrast_black, 2),
            }
        
        # Update frequency and context
        self.colors[hex_value]["frequency"] += 1
        
        context = color_data.get("context", "")
        if context and context not in self.colors[hex_value]["contexts"]:
            self.colors[hex_value]["contexts"].append(context)
        
        source = color_data.get("source", "")
        if source and source not in self.colors[hex_value]["sources"]:
            self.colors[hex_value]["sources"].append(source)
    
    async def extract_with_firecrawl(
        self,
        url: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> dict:
        """
        Extract colors using Firecrawl API.
        
        Args:
            url: Website URL to analyze
            log_callback: Optional callback for logging progress
        
        Returns:
            Dict with extracted colors and stats
        """
        
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        if not FIRECRAWL_AVAILABLE:
            log("⚠️ Firecrawl not available, skipping...")
            return {"colors": {}, "css_variables": {}, "stats": self.stats}
        
        log("")
        log("=" * 60)
        log("🔥 FIRECRAWL CSS EXTRACTION")
        log("=" * 60)
        log("")
        
        try:
            # Initialize Firecrawl
            if self.api_key:
                app = FirecrawlApp(api_key=self.api_key)
            else:
                # Try without API key (limited functionality)
                log("   ⚠️ No Firecrawl API key - using fallback method")
                return await self._fallback_css_extraction(url, log_callback)
            
            log(f"   🌐 Scraping: {url}")
            
            # Scrape the page
            result = app.scrape_url(
                url,
                params={
                    'formats': ['html'],
                    'includeTags': ['style', 'link'],
                }
            )
            
            if not result:
                log("   ❌ Firecrawl returned no results")
                return {"colors": {}, "css_variables": {}, "stats": self.stats}
            
            html_content = result.get('html', '') or result.get('content', '')
            
            log(f"   ✅ Page scraped ({len(html_content)} chars)")
            
            # Extract <style> blocks
            log("   📝 Parsing <style> blocks...")
            style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL | re.IGNORECASE)
            
            for i, block in enumerate(style_blocks):
                colors = self._extract_colors_from_css(block, f"style-block-{i}")
                for color in colors:
                    self._aggregate_color(color)
                
                variables = self._extract_css_variables(block)
                self.css_variables.update(variables)
                self.stats["style_blocks_parsed"] += 1
            
            log(f"      Found {len(style_blocks)} style blocks")
            
            # Extract CSS file URLs
            log("   🔗 Finding linked CSS files...")
            css_urls = re.findall(r'href=["\']([^"\']*\.css[^"\']*)["\']', html_content, re.IGNORECASE)
            
            log(f"      Found {len(css_urls)} CSS files")
            
            # Fetch and parse each CSS file
            for css_url in css_urls[:15]:  # Limit to 15 files
                try:
                    # Make URL absolute
                    if css_url.startswith('//'):
                        css_url = 'https:' + css_url
                    elif css_url.startswith('/'):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        css_url = f"{parsed.scheme}://{parsed.netloc}{css_url}"
                    elif not css_url.startswith('http'):
                        from urllib.parse import urljoin
                        css_url = urljoin(url, css_url)
                    
                    log(f"   📄 Fetching: {css_url[:60]}...")
                    
                    # Fetch CSS file
                    css_result = app.scrape_url(css_url, params={'formats': ['rawHtml']})
                    css_content = css_result.get('rawHtml', '') or css_result.get('content', '')
                    
                    if css_content:
                        colors = self._extract_colors_from_css(css_content, css_url.split('/')[-1])
                        for color in colors:
                            self._aggregate_color(color)
                        
                        variables = self._extract_css_variables(css_content)
                        self.css_variables.update(variables)
                        self.stats["css_files_parsed"] += 1
                        
                        log(f"      ✅ Parsed ({len(colors)} colors)")
                    
                except Exception as e:
                    log(f"      ⚠️ Failed: {str(e)[:50]}")
                    self.warnings.append(f"Failed to fetch {css_url}: {str(e)}")
            
            # Process CSS variables that contain colors
            log("   🎨 Processing CSS variables...")
            for var_name, var_value in self.css_variables.items():
                if self.color_regex.match(var_value.strip()):
                    self._aggregate_color({
                        "value": var_value.strip(),
                        "source": f"css-var:{var_name}",
                        "context": "css-variable",
                    })
                    self.stats["css_variables_found"] += 1
            
            self.stats["colors_found"] = len(self.colors)
            
            # Log summary
            log("")
            log("📊 FIRECRAWL RESULTS:")
            log(f"   CSS files parsed:    {self.stats['css_files_parsed']}")
            log(f"   Style blocks parsed: {self.stats['style_blocks_parsed']}")
            log(f"   CSS variables found: {self.stats['css_variables_found']}")
            log(f"   Unique colors found: {self.stats['colors_found']}")
            log("")
            
            # Show top colors found
            if self.colors:
                sorted_colors = sorted(self.colors.items(), key=lambda x: -x[1]['frequency'])[:10]
                log("   🎨 Top colors found:")
                for hex_val, data in sorted_colors:
                    log(f"      {hex_val} (used {data['frequency']}x)")
            
            return {
                "colors": self.colors,
                "css_variables": self.css_variables,
                "stats": self.stats,
            }
            
        except Exception as e:
            log(f"   ❌ Firecrawl error: {str(e)}")
            self.errors.append(f"Firecrawl error: {str(e)}")
            return await self._fallback_css_extraction(url, log_callback)
    
    async def _fallback_css_extraction(
        self,
        url: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> dict:
        """
        Fallback CSS extraction using httpx (no Firecrawl API key needed).
        """
        
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        log("")
        log("🔄 Using fallback CSS extraction (httpx)...")
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch main page
                log(f"   🌐 Fetching: {url}")
                response = await client.get(url)
                html_content = response.text
                
                log(f"   ✅ Page fetched ({len(html_content)} chars)")
                
                # Extract <style> blocks
                log("   📝 Parsing <style> blocks...")
                style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL | re.IGNORECASE)
                
                for i, block in enumerate(style_blocks):
                    colors = self._extract_colors_from_css(block, f"style-block-{i}")
                    for color in colors:
                        self._aggregate_color(color)
                    
                    variables = self._extract_css_variables(block)
                    self.css_variables.update(variables)
                    self.stats["style_blocks_parsed"] += 1
                
                log(f"      Found {len(style_blocks)} style blocks")
                
                # Extract CSS file URLs
                log("   🔗 Finding linked CSS files...")
                css_urls = re.findall(r'href=["\']([^"\']*\.css[^"\']*)["\']', html_content, re.IGNORECASE)
                
                log(f"      Found {len(css_urls)} CSS files")
                
                # Fetch and parse each CSS file
                for css_url in css_urls[:15]:
                    try:
                        # Make URL absolute
                        if css_url.startswith('//'):
                            css_url = 'https:' + css_url
                        elif css_url.startswith('/'):
                            from urllib.parse import urlparse
                            parsed = urlparse(url)
                            css_url = f"{parsed.scheme}://{parsed.netloc}{css_url}"
                        elif not css_url.startswith('http'):
                            from urllib.parse import urljoin
                            css_url = urljoin(url, css_url)
                        
                        log(f"   📄 Fetching: {css_url[:60]}...")
                        
                        css_response = await client.get(css_url)
                        css_content = css_response.text
                        
                        if css_content:
                            colors = self._extract_colors_from_css(css_content, css_url.split('/')[-1])
                            for color in colors:
                                self._aggregate_color(color)
                            
                            variables = self._extract_css_variables(css_content)
                            self.css_variables.update(variables)
                            self.stats["css_files_parsed"] += 1
                            
                            log(f"      ✅ Parsed ({len(colors)} colors)")
                        
                    except Exception as e:
                        log(f"      ⚠️ Failed: {str(e)[:50]}")
                        self.warnings.append(f"Failed to fetch {css_url}: {str(e)}")
                
                # Process CSS variables
                log("   🎨 Processing CSS variables...")
                for var_name, var_value in self.css_variables.items():
                    if self.color_regex.match(var_value.strip()):
                        self._aggregate_color({
                            "value": var_value.strip(),
                            "source": f"css-var:{var_name}",
                            "context": "css-variable",
                        })
                        self.stats["css_variables_found"] += 1
                
                self.stats["colors_found"] = len(self.colors)
                
                # Log summary
                log("")
                log("📊 FALLBACK EXTRACTION RESULTS:")
                log(f"   CSS files parsed:    {self.stats['css_files_parsed']}")
                log(f"   Style blocks parsed: {self.stats['style_blocks_parsed']}")
                log(f"   CSS variables found: {self.stats['css_variables_found']}")
                log(f"   Unique colors found: {self.stats['colors_found']}")
                log("")
                
                # Show top colors
                if self.colors:
                    sorted_colors = sorted(self.colors.items(), key=lambda x: -x[1]['frequency'])[:10]
                    log("   🎨 Top colors found:")
                    for hex_val, data in sorted_colors:
                        log(f"      {hex_val} (used {data['frequency']}x)")
                
                return {
                    "colors": self.colors,
                    "css_variables": self.css_variables,
                    "stats": self.stats,
                }
                
        except Exception as e:
            log(f"   ❌ Fallback extraction failed: {str(e)}")
            self.errors.append(f"Fallback extraction failed: {str(e)}")
            return {"colors": {}, "css_variables": {}, "stats": self.stats}


async def extract_css_colors(
    url: str,
    api_key: Optional[str] = None,
    log_callback: Optional[Callable[[str], None]] = None
) -> dict:
    """
    Convenience function to extract CSS colors.
    
    Args:
        url: Website URL
        api_key: Optional Firecrawl API key
        log_callback: Optional logging callback
    
    Returns:
        Dict with colors, css_variables, and stats
    """
    extractor = FirecrawlExtractor(api_key=api_key)
    return await extractor.extract_with_firecrawl(url, log_callback)
