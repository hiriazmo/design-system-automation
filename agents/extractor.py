"""
Agent 1: Token Extractor
Design System Extractor v2

Persona: Meticulous Design Archaeologist

Responsibilities:
- Crawl pages at specified viewport
- Extract computed styles from all elements
- Parse CSS files for variables and rules
- Extract colors from SVGs
- Collect colors, typography, spacing, radius, shadows
- Track frequency and context for each token
"""

import asyncio
import re
from typing import Optional, Callable
from datetime import datetime
from collections import defaultdict

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from core.token_schema import (
    Viewport,
    ExtractedTokens,
    ColorToken,
    TypographyToken,
    SpacingToken,
    RadiusToken,
    ShadowToken,
    FontFamily,
    TokenSource,
    Confidence,
)
from core.color_utils import (
    normalize_hex,
    parse_color,
    get_contrast_with_white,
    get_contrast_with_black,
    check_wcag_compliance,
)
from config.settings import get_settings


class TokenExtractor:
    """
    Extracts design tokens from web pages.
    
    This is the second part of Agent 1's job — after pages are confirmed,
    we crawl and extract all CSS values.
    
    Enhanced with:
    - CSS file parsing for variables and rules
    - SVG color extraction
    - Inline style extraction
    """
    
    def __init__(self, viewport: Viewport = Viewport.DESKTOP):
        self.settings = get_settings()
        self.viewport = viewport
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Token collection
        self.colors: dict[str, ColorToken] = {}
        self.typography: dict[str, TypographyToken] = {}
        self.spacing: dict[str, SpacingToken] = {}
        self.radius: dict[str, RadiusToken] = {}
        self.shadows: dict[str, ShadowToken] = {}

        # Foreground-background pairs extracted from actual DOM elements
        self.fg_bg_pairs: list[dict] = []

        # CSS Variables collection
        self.css_variables: dict[str, str] = {}

        # Font tracking
        self.font_families: dict[str, FontFamily] = {}

        # Statistics
        self.total_elements = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
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
        
        # Set viewport based on extraction mode
        if self.viewport == Viewport.DESKTOP:
            width = self.settings.viewport.desktop_width
            height = self.settings.viewport.desktop_height
        else:
            width = self.settings.viewport.mobile_width
            height = self.settings.viewport.mobile_height
        
        self.context = await self.browser.new_context(
            viewport={"width": width, "height": height},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
    
    async def _close_browser(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def _scroll_page(self, page: Page):
        """Scroll page to load lazy content."""
        await page.evaluate("""
            async () => {
                const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                const height = document.body.scrollHeight;
                const step = window.innerHeight;
                
                for (let y = 0; y < height; y += step) {
                    window.scrollTo(0, y);
                    await delay(100);
                }
                
                // Scroll back to top
                window.scrollTo(0, 0);
            }
        """)
        
        # Wait for network idle after scrolling
        await page.wait_for_load_state("networkidle", timeout=self.settings.browser.network_idle_timeout)
    
    async def _extract_styles_from_page(self, page: Page) -> dict:
        """
        Extract computed styles from all elements on the page.
        
        This is the core extraction logic — we get getComputedStyle for every element.
        """
        styles_data = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const results = {
                    colors: [],
                    typography: [],
                    spacing: [],
                    radius: [],
                    shadows: [],
                    elements_count: elements.length,
                    loaded_fonts: [],
                };

                // v3: Collect actually loaded font names via document.fonts API
                // This gives us the REAL font names, not generic fallbacks
                const genericFamilies = new Set([
                    'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy',
                    'system-ui', 'ui-serif', 'ui-sans-serif', 'ui-monospace', 'ui-rounded',
                    'math', 'emoji', 'fangsong',
                ]);
                try {
                    document.fonts.forEach(function(font) {
                        const name = font.family.replace(/['"]/g, '').trim();
                        if (name && !genericFamilies.has(name.toLowerCase())) {
                            results.loaded_fonts.push(name);
                        }
                    });
                } catch(e) {}
                // Deduplicate
                results.loaded_fonts = [...new Set(results.loaded_fonts)];

                const colorProperties = [
                    'color', 'background-color', 'border-color',
                    'border-top-color', 'border-right-color',
                    'border-bottom-color', 'border-left-color',
                    'outline-color', 'text-decoration-color',
                ];

                const spacingProperties = [
                    'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
                    'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
                    'gap', 'row-gap', 'column-gap',
                ];

                elements.forEach(el => {
                    const tag = el.tagName.toLowerCase();
                    const styles = window.getComputedStyle(el);

                    // Skip invisible elements
                    if (styles.display === 'none' || styles.visibility === 'hidden') {
                        return;
                    }

                    // --- COLORS ---
                    colorProperties.forEach(prop => {
                        const value = styles.getPropertyValue(prop);
                        if (value && value !== 'rgba(0, 0, 0, 0)' && value !== 'transparent') {
                            results.colors.push({
                                value: value,
                                property: prop,
                                element: tag,
                                context: prop.includes('background') ? 'background' :
                                        prop.includes('border') ? 'border' : 'text',
                            });
                        }
                    });

                    // --- TYPOGRAPHY ---
                    // v3: Get full font-family stack (not just computed generic)
                    const fontFamily = styles.getPropertyValue('font-family');
                    const fontSize = styles.getPropertyValue('font-size');
                    const fontWeight = styles.getPropertyValue('font-weight');
                    const lineHeight = styles.getPropertyValue('line-height');
                    const letterSpacing = styles.getPropertyValue('letter-spacing');
                    
                    if (fontSize && fontFamily) {
                        results.typography.push({
                            fontFamily: fontFamily,
                            fontSize: fontSize,
                            fontWeight: fontWeight,
                            lineHeight: lineHeight,
                            letterSpacing: letterSpacing,
                            element: tag,
                        });
                    }
                    
                    // --- SPACING ---
                    spacingProperties.forEach(prop => {
                        const value = styles.getPropertyValue(prop);
                        if (value && value !== '0px' && value !== 'auto' && value !== 'normal') {
                            const px = parseFloat(value);
                            if (!isNaN(px) && px > 0 && px < 500) {
                                results.spacing.push({
                                    value: value,
                                    valuePx: Math.round(px),
                                    property: prop,
                                    context: prop.includes('margin') ? 'margin' : 
                                            prop.includes('padding') ? 'padding' : 'gap',
                                });
                            }
                        }
                    });
                    
                    // --- BORDER RADIUS ---
                    const radiusProps = [
                        'border-radius', 'border-top-left-radius', 
                        'border-top-right-radius', 'border-bottom-left-radius',
                        'border-bottom-right-radius',
                    ];
                    
                    radiusProps.forEach(prop => {
                        const value = styles.getPropertyValue(prop);
                        if (value && value !== '0px') {
                            results.radius.push({
                                value: value,
                                element: tag,
                            });
                        }
                    });
                    
                    // --- BOX SHADOW ---
                    const shadow = styles.getPropertyValue('box-shadow');
                    if (shadow && shadow !== 'none') {
                        results.shadows.push({
                            value: shadow,
                            element: tag,
                        });
                    }
                });
                
                return results;
            }
        """)
        
        return styles_data

    async def _extract_fg_bg_pairs(self, page: Page) -> list[dict]:
        """
        Extract actual foreground-background color pairs from visible DOM elements.

        For each visible element that has a non-transparent text color, walk up the
        ancestor chain to find the effective background color.  This gives us real
        foreground/background pairs so we can do accurate WCAG AA checks instead of
        only comparing every color against white/black.
        """
        pairs = await page.evaluate("""
            () => {
                const pairs = [];
                const seen = new Set();

                function rgbToHex(rgb) {
                    if (!rgb || rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') return null;
                    const match = rgb.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                    if (!match) return null;
                    const r = parseInt(match[1]);
                    const g = parseInt(match[2]);
                    const b = parseInt(match[3]);
                    return '#' + [r, g, b].map(c => c.toString(16).padStart(2, '0')).join('');
                }

                function getEffectiveBackground(el) {
                    let current = el;
                    while (current && current !== document.documentElement) {
                        const bg = window.getComputedStyle(current).backgroundColor;
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                            return rgbToHex(bg);
                        }
                        current = current.parentElement;
                    }
                    return '#ffffff';  // default page background
                }

                const elements = document.querySelectorAll('*');
                elements.forEach(el => {
                    const styles = window.getComputedStyle(el);
                    if (styles.display === 'none' || styles.visibility === 'hidden') return;

                    const fg = rgbToHex(styles.color);
                    if (!fg) return;

                    const bg = getEffectiveBackground(el);
                    if (!bg) return;

                    const key = fg + '|' + bg;
                    if (seen.has(key)) return;
                    seen.add(key);

                    pairs.push({
                        foreground: fg,
                        background: bg,
                        element: el.tagName.toLowerCase(),
                    });
                });

                return pairs;
            }
        """)
        return pairs or []

    async def _extract_css_variables(self, page: Page) -> dict:
        """
        Extract CSS custom properties (variables) from :root and stylesheets.
        
        This catches colors defined as:
        - :root { --primary-color: #3860be; }
        - :root { --brand-cyan: #00c4cc; }
        """
        css_vars = await page.evaluate("""
            () => {
                const variables = {};
                
                // 1. Get CSS variables from :root computed styles
                const rootStyles = getComputedStyle(document.documentElement);
                const rootCss = document.documentElement.style.cssText;
                
                // 2. Parse all stylesheets for CSS variables
                for (const sheet of document.styleSheets) {
                    try {
                        const rules = sheet.cssRules || sheet.rules;
                        for (const rule of rules) {
                            if (rule.style) {
                                for (let i = 0; i < rule.style.length; i++) {
                                    const prop = rule.style[i];
                                    if (prop.startsWith('--')) {
                                        const value = rule.style.getPropertyValue(prop).trim();
                                        if (value) {
                                            variables[prop] = value;
                                        }
                                    }
                                }
                            }
                            // Also check @media rules
                            if (rule.cssRules) {
                                for (const innerRule of rule.cssRules) {
                                    if (innerRule.style) {
                                        for (let i = 0; i < innerRule.style.length; i++) {
                                            const prop = innerRule.style[i];
                                            if (prop.startsWith('--')) {
                                                const value = innerRule.style.getPropertyValue(prop).trim();
                                                if (value) {
                                                    variables[prop] = value;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        // CORS may block access to external stylesheets
                        console.log('Could not access stylesheet:', e);
                    }
                }
                
                // 3. Get computed CSS variable values from :root
                const computedVars = {};
                for (const prop of Object.keys(variables)) {
                    const computed = rootStyles.getPropertyValue(prop).trim();
                    if (computed) {
                        computedVars[prop] = computed;
                    }
                }
                
                return { raw: variables, computed: computedVars };
            }
        """)
        
        return css_vars
    
    async def _extract_svg_colors(self, page: Page) -> list[dict]:
        """
        Extract colors from SVG elements (fill, stroke).
        
        This catches colors in:
        - <svg fill="#00c4cc">
        - <path stroke="#3860be">
        - <circle fill="rgb(188, 212, 50)">
        """
        svg_colors = await page.evaluate("""
            () => {
                const colors = [];
                
                // Find all SVG elements
                const svgs = document.querySelectorAll('svg, svg *');
                
                svgs.forEach(el => {
                    // Check fill attribute
                    const fill = el.getAttribute('fill');
                    if (fill && fill !== 'none' && fill !== 'currentColor' && !fill.startsWith('url(')) {
                        colors.push({
                            value: fill,
                            property: 'svg-fill',
                            element: el.tagName.toLowerCase(),
                            context: 'svg',
                        });
                    }
                    
                    // Check stroke attribute
                    const stroke = el.getAttribute('stroke');
                    if (stroke && stroke !== 'none' && stroke !== 'currentColor' && !stroke.startsWith('url(')) {
                        colors.push({
                            value: stroke,
                            property: 'svg-stroke',
                            element: el.tagName.toLowerCase(),
                            context: 'svg',
                        });
                    }
                    
                    // Check computed styles for SVG elements
                    const styles = getComputedStyle(el);
                    const computedFill = styles.fill;
                    const computedStroke = styles.stroke;
                    
                    if (computedFill && computedFill !== 'none' && !computedFill.startsWith('url(')) {
                        colors.push({
                            value: computedFill,
                            property: 'svg-fill-computed',
                            element: el.tagName.toLowerCase(),
                            context: 'svg',
                        });
                    }
                    
                    if (computedStroke && computedStroke !== 'none' && !computedStroke.startsWith('url(')) {
                        colors.push({
                            value: computedStroke,
                            property: 'svg-stroke-computed',
                            element: el.tagName.toLowerCase(),
                            context: 'svg',
                        });
                    }
                });
                
                return colors;
            }
        """)
        
        return svg_colors
    
    async def _extract_inline_styles(self, page: Page) -> dict:
        """
        Extract colors from inline style attributes.
        
        This catches colors in:
        - <div style="background-color: #bcd432;">
        - <span style="color: rgb(0, 196, 204);">
        """
        inline_data = await page.evaluate("""
            () => {
                const colors = [];
                const colorRegex = /#[0-9a-fA-F]{3,8}|rgb\\([^)]+\\)|rgba\\([^)]+\\)|hsl\\([^)]+\\)|hsla\\([^)]+\\)/gi;
                
                // Find all elements with inline styles
                const elements = document.querySelectorAll('[style]');
                
                elements.forEach(el => {
                    const styleAttr = el.getAttribute('style');
                    if (styleAttr) {
                        const matches = styleAttr.match(colorRegex);
                        if (matches) {
                            matches.forEach(color => {
                                colors.push({
                                    value: color,
                                    property: 'inline-style',
                                    element: el.tagName.toLowerCase(),
                                    context: 'inline',
                                });
                            });
                        }
                    }
                });
                
                return colors;
            }
        """)
        
        return inline_data
    
    async def _extract_stylesheet_colors(self, page: Page) -> list[dict]:
        """
        Parse CSS stylesheets for color values.
        
        This catches colors defined in CSS rules that may not be
        currently applied to visible elements.
        
        Also fetches external stylesheets that may be CORS-blocked.
        """
        css_colors = await page.evaluate("""
            () => {
                const colors = [];
                const colorRegex = /#[0-9a-fA-F]{3,8}|rgb\\([^)]+\\)|rgba\\([^)]+\\)|hsl\\([^)]+\\)|hsla\\([^)]+\\)/gi;
                
                // Color-related CSS properties
                const colorProps = [
                    'color', 'background-color', 'background', 'border-color',
                    'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color',
                    'outline-color', 'box-shadow', 'text-shadow', 'fill', 'stroke',
                    'caret-color', 'column-rule-color', 'text-decoration-color',
                ];
                
                // Parse all stylesheets
                for (const sheet of document.styleSheets) {
                    try {
                        const rules = sheet.cssRules || sheet.rules;
                        for (const rule of rules) {
                            if (rule.style) {
                                colorProps.forEach(prop => {
                                    const value = rule.style.getPropertyValue(prop);
                                    if (value) {
                                        const matches = value.match(colorRegex);
                                        if (matches) {
                                            matches.forEach(color => {
                                                colors.push({
                                                    value: color,
                                                    property: prop,
                                                    element: 'css-rule',
                                                    context: 'stylesheet',
                                                    selector: rule.selectorText || '',
                                                });
                                            });
                                        }
                                    }
                                });
                            }
                        }
                    } catch (e) {
                        // CORS may block access to external stylesheets
                    }
                }
                
                return colors;
            }
        """)
        
        return css_colors
    
    async def _fetch_external_css_colors(self, page: Page) -> list[dict]:
        """
        Fetch and parse external CSS files directly to bypass CORS.
        
        This catches colors in external stylesheets that are blocked by CORS.
        """
        colors = []
        
        try:
            # Get all stylesheet URLs
            css_urls = await page.evaluate("""
                () => {
                    const urls = [];
                    const links = document.querySelectorAll('link[rel="stylesheet"]');
                    links.forEach(link => {
                        if (link.href) {
                            urls.push(link.href);
                        }
                    });
                    return urls;
                }
            """)
            
            # Color regex pattern
            color_regex = re.compile(r'#[0-9a-fA-F]{3,8}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|hsla\([^)]+\)', re.IGNORECASE)
            
            # Fetch each CSS file
            for css_url in css_urls[:10]:  # Limit to 10 files
                try:
                    response = await page.request.get(css_url, timeout=5000)
                    if response.ok:
                        css_text = await response.text()
                        
                        # Find all color values in CSS text
                        matches = color_regex.findall(css_text)
                        for match in matches:
                            colors.append({
                                "value": match,
                                "property": "external-css",
                                "element": "css-file",
                                "context": "external-stylesheet",
                            })
                except Exception as e:
                    # Skip if fetch fails
                    pass
            
        except Exception as e:
            self.warnings.append(f"External CSS fetch failed: {str(e)}")
        
        return colors
    
    async def _extract_all_page_colors(self, page: Page) -> list[dict]:
        """
        Extract ALL color values from the page source and styles.
        
        This is a brute-force approach that scans the entire page HTML
        and all style blocks for any color values.
        """
        colors = await page.evaluate("""
            () => {
                const colors = [];
                const colorRegex = /#[0-9a-fA-F]{3,8}|rgb\\([^)]+\\)|rgba\\([^)]+\\)|hsl\\([^)]+\\)|hsla\\([^)]+\\)/gi;
                
                // 1. Scan all <style> tags
                const styleTags = document.querySelectorAll('style');
                styleTags.forEach(style => {
                    const matches = style.textContent.match(colorRegex);
                    if (matches) {
                        matches.forEach(color => {
                            colors.push({
                                value: color,
                                property: 'style-tag',
                                element: 'style',
                                context: 'style-block',
                            });
                        });
                    }
                });
                
                // 2. Scan data attributes that might contain colors
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    // Check data attributes
                    for (const attr of el.attributes) {
                        if (attr.name.startsWith('data-') || attr.name === 'style') {
                            const matches = attr.value.match(colorRegex);
                            if (matches) {
                                matches.forEach(color => {
                                    colors.push({
                                        value: color,
                                        property: attr.name,
                                        element: el.tagName.toLowerCase(),
                                        context: 'attribute',
                                    });
                                });
                            }
                        }
                    }
                    
                    // Check for color in class names (some frameworks use color classes)
                    const classList = el.className;
                    if (typeof classList === 'string') {
                        const colorMatches = classList.match(colorRegex);
                        if (colorMatches) {
                            colorMatches.forEach(color => {
                                colors.push({
                                    value: color,
                                    property: 'class',
                                    element: el.tagName.toLowerCase(),
                                    context: 'class-name',
                                });
                            });
                        }
                    }
                });
                
                // 3. Look for colors in script tags (config objects)
                const scriptTags = document.querySelectorAll('script');
                scriptTags.forEach(script => {
                    if (script.textContent && !script.src) {
                        const matches = script.textContent.match(colorRegex);
                        if (matches) {
                            matches.forEach(color => {
                                colors.push({
                                    value: color,
                                    property: 'script',
                                    element: 'script',
                                    context: 'javascript',
                                });
                            });
                        }
                    }
                });
                
                return colors;
            }
        """)
        
        return colors
    
    def _process_css_variables(self, css_vars: dict):
        """Process CSS variables and extract color tokens from them."""
        computed = css_vars.get("computed", {})
        raw = css_vars.get("raw", {})
        
        # Store CSS variables
        self.css_variables = {**raw, **computed}
        
        # Extract colors from CSS variables
        color_regex = re.compile(r'#[0-9a-fA-F]{3,8}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|hsla\([^)]+\)', re.IGNORECASE)
        
        for var_name, value in computed.items():
            if color_regex.match(value.strip()):
                # This is a color variable
                color_data = {
                    "value": value.strip(),
                    "property": var_name,
                    "element": ":root",
                    "context": "css-variable",
                }
                
                hex_value = self._process_color(color_data)
                if hex_value and hex_value not in self.colors:
                    contrast_white = get_contrast_with_white(hex_value)
                    contrast_black = get_contrast_with_black(hex_value)
                    compliance = check_wcag_compliance(hex_value, "#ffffff")
                    
                    self.colors[hex_value] = ColorToken(
                        value=hex_value,
                        frequency=1,
                        contexts=["css-variable"],
                        elements=[":root"],
                        css_properties=[var_name],
                        contrast_white=round(contrast_white, 2),
                        contrast_black=round(contrast_black, 2),
                        wcag_aa_large_text=compliance["aa_large_text"],
                        wcag_aa_small_text=compliance["aa_normal_text"],
                        source=TokenSource.DETECTED,  # CSS variable is still "detected"
                        confidence=Confidence.HIGH,
                    )
                elif hex_value and hex_value in self.colors:
                    # Update existing token
                    token = self.colors[hex_value]
                    token.frequency += 1
                    if "css-variable" not in token.contexts:
                        token.contexts.append("css-variable")
                    if var_name not in token.css_properties:
                        token.css_properties.append(var_name)

    def _process_color(self, color_data: dict) -> Optional[str]:
        """Process and normalize a color value."""
        value = color_data.get("value", "")
        
        # Parse and normalize
        parsed = parse_color(value)
        if not parsed:
            return None
        
        return parsed.hex
    
    def _aggregate_colors(self, raw_colors: list[dict]):
        """Aggregate color data from extraction."""
        for color_data in raw_colors:
            hex_value = self._process_color(color_data)
            if not hex_value:
                continue
            
            if hex_value not in self.colors:
                # Calculate contrast ratios
                contrast_white = get_contrast_with_white(hex_value)
                contrast_black = get_contrast_with_black(hex_value)
                compliance = check_wcag_compliance(hex_value, "#ffffff")
                
                self.colors[hex_value] = ColorToken(
                    value=hex_value,
                    frequency=0,
                    contexts=[],
                    elements=[],
                    css_properties=[],
                    contrast_white=round(contrast_white, 2),
                    contrast_black=round(contrast_black, 2),
                    wcag_aa_large_text=compliance["aa_large_text"],
                    wcag_aa_small_text=compliance["aa_normal_text"],
                )
            
            # Update frequency and context
            token = self.colors[hex_value]
            token.frequency += 1
            
            context = color_data.get("context", "")
            if context and context not in token.contexts:
                token.contexts.append(context)
            
            element = color_data.get("element", "")
            if element and element not in token.elements:
                token.elements.append(element)
            
            prop = color_data.get("property", "")
            if prop and prop not in token.css_properties:
                token.css_properties.append(prop)
    
    # Generic CSS font families that are NOT real font names
    _GENERIC_FAMILIES = {
        'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy',
        'system-ui', 'ui-serif', 'ui-sans-serif', 'ui-monospace', 'ui-rounded',
        '-apple-system', 'blinkmacsystemfont', 'segoe ui',
        'math', 'emoji', 'fangsong',
    }

    def _resolve_font_family(self, font_family_str: str, loaded_fonts: list) -> str:
        """Resolve a font-family CSS value to the actual font name.

        v3: If the first item in the stack is a generic family (sans-serif, etc.),
        check the loaded_fonts list from document.fonts API to find the real name.
        """
        parts = [p.strip().strip('"\'') for p in font_family_str.split(",")]
        first = parts[0] if parts else ""

        # If first item is already a real font name, use it
        if first.lower() not in self._GENERIC_FAMILIES:
            return first

        # First item is generic — check loaded_fonts for a match
        # Prefer the most-loaded font (first in the list, which is order of discovery)
        if loaded_fonts:
            return loaded_fonts[0]

        # Last resort: check if any non-generic name exists deeper in the stack
        for p in parts[1:]:
            if p.lower() not in self._GENERIC_FAMILIES:
                return p

        return first  # Fallback to the generic name

    def _aggregate_typography(self, raw_typography: list[dict], loaded_fonts: list = None):
        """Aggregate typography data from extraction.

        v3: uses loaded_fonts from document.fonts API to resolve generic fallbacks.
        """
        loaded_fonts = loaded_fonts or []

        for typo_data in raw_typography:
            # Create unique key
            font_family = typo_data.get("fontFamily", "")
            font_size = typo_data.get("fontSize", "")
            font_weight = typo_data.get("fontWeight", "400")
            line_height = typo_data.get("lineHeight", "normal")

            key = f"{font_size}|{font_weight}|{font_family[:50]}"

            if key not in self.typography:
                # Parse font size to px
                font_size_px = None
                if font_size.endswith("px"):
                    try:
                        font_size_px = float(font_size.replace("px", ""))
                    except ValueError:
                        pass

                # Parse line height
                line_height_computed = None
                if line_height and line_height != "normal":
                    if line_height.endswith("px") and font_size_px:
                        try:
                            lh_px = float(line_height.replace("px", ""))
                            line_height_computed = round(lh_px / font_size_px, 2)
                        except ValueError:
                            pass
                    else:
                        try:
                            line_height_computed = float(line_height)
                        except ValueError:
                            pass

                # v3: Resolve generic font families using loaded_fonts
                resolved_family = self._resolve_font_family(font_family, loaded_fonts)

                self.typography[key] = TypographyToken(
                    font_family=resolved_family,
                    font_size=font_size,
                    font_size_px=font_size_px,
                    font_weight=int(font_weight) if font_weight.isdigit() else 400,
                    line_height=line_height,
                    line_height_computed=line_height_computed,
                    letter_spacing=typo_data.get("letterSpacing"),
                    frequency=0,
                    elements=[],
                )
            
            # Update
            token = self.typography[key]
            token.frequency += 1
            
            element = typo_data.get("element", "")
            if element and element not in token.elements:
                token.elements.append(element)
            
            # Track font families
            primary_font = token.font_family
            if primary_font not in self.font_families:
                self.font_families[primary_font] = FontFamily(
                    name=primary_font,
                    fallbacks=[f.strip().strip('"\'') for f in font_family.split(",")[1:]],
                    frequency=0,
                )
            self.font_families[primary_font].frequency += 1
    
    def _aggregate_spacing(self, raw_spacing: list[dict]):
        """Aggregate spacing data from extraction."""
        for space_data in raw_spacing:
            value = space_data.get("value", "")
            value_px = space_data.get("valuePx", 0)
            
            key = str(value_px)
            
            if key not in self.spacing:
                self.spacing[key] = SpacingToken(
                    value=f"{value_px}px",
                    value_px=value_px,
                    frequency=0,
                    contexts=[],
                    properties=[],
                    fits_base_4=value_px % 4 == 0,
                    fits_base_8=value_px % 8 == 0,
                )
            
            token = self.spacing[key]
            token.frequency += 1
            
            context = space_data.get("context", "")
            if context and context not in token.contexts:
                token.contexts.append(context)
            
            prop = space_data.get("property", "")
            if prop and prop not in token.properties:
                token.properties.append(prop)
    
    def _aggregate_radius(self, raw_radius: list[dict]):
        """Aggregate border radius data."""
        for radius_data in raw_radius:
            value = radius_data.get("value", "")
            
            # Normalize to simple format
            # "8px 8px 8px 8px" -> "8px"
            parts = value.split()
            if len(set(parts)) == 1:
                value = parts[0]
            
            if value not in self.radius:
                value_px = None
                if value.endswith("px"):
                    try:
                        value_px = int(float(value.replace("px", "")))
                    except ValueError:
                        pass
                
                self.radius[value] = RadiusToken(
                    value=value,
                    value_px=value_px,
                    frequency=0,
                    elements=[],
                    fits_base_4=value_px % 4 == 0 if value_px else False,
                    fits_base_8=value_px % 8 == 0 if value_px else False,
                )
            
            token = self.radius[value]
            token.frequency += 1
            
            element = radius_data.get("element", "")
            if element and element not in token.elements:
                token.elements.append(element)
    
    def _aggregate_shadows(self, raw_shadows: list[dict]):
        """Aggregate box shadow data."""
        for shadow_data in raw_shadows:
            value = shadow_data.get("value", "")
            
            if value not in self.shadows:
                self.shadows[value] = ShadowToken(
                    value=value,
                    frequency=0,
                    elements=[],
                )
            
            token = self.shadows[value]
            token.frequency += 1
            
            element = shadow_data.get("element", "")
            if element and element not in token.elements:
                token.elements.append(element)
    
    def _calculate_confidence(self, frequency: int) -> Confidence:
        """Calculate confidence level based on frequency."""
        if frequency >= 10:
            return Confidence.HIGH
        elif frequency >= 3:
            return Confidence.MEDIUM
        return Confidence.LOW
    
    def _detect_spacing_base(self) -> Optional[int]:
        """Detect the base spacing unit (4 or 8)."""
        fits_4 = sum(1 for s in self.spacing.values() if s.fits_base_4)
        fits_8 = sum(1 for s in self.spacing.values() if s.fits_base_8)
        
        total = len(self.spacing)
        if total == 0:
            return None
        
        # If 80%+ values fit base 8, use 8
        if fits_8 / total >= 0.8:
            return 8
        # If 80%+ values fit base 4, use 4
        elif fits_4 / total >= 0.8:
            return 4
        
        return None
    
    async def extract(
        self,
        pages: list[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> ExtractedTokens:
        """
        Extract tokens from a list of pages.
        
        Enhanced extraction includes:
        - DOM computed styles
        - CSS variables from :root
        - SVG fill/stroke colors
        - Inline style colors
        - Stylesheet color rules
        
        Args:
            pages: List of URLs to crawl
            progress_callback: Optional callback for progress updates
        
        Returns:
            ExtractedTokens with all discovered tokens
        """
        start_time = datetime.now()
        pages_crawled = []
        
        async with self:
            for i, url in enumerate(pages):
                try:
                    page = await self.context.new_page()
                    
                    # Navigate with fallback strategy
                    try:
                        await page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=60000  # 60 seconds
                        )
                        # Wait for JS to render
                        await page.wait_for_timeout(2000)
                    except Exception as nav_error:
                        # Fallback to load event
                        try:
                            await page.goto(
                                url,
                                wait_until="load",
                                timeout=60000
                            )
                            await page.wait_for_timeout(3000)
                        except Exception:
                            self.warnings.append(f"Slow load for {url}, extracting partial content")
                    
                    # Scroll to load lazy content
                    await self._scroll_page(page)
                    
                    # =========================================================
                    # ENHANCED EXTRACTION: Multiple sources
                    # =========================================================
                    
                    # Track counts before extraction for this page
                    colors_before = len(self.colors)
                    typo_before = len(self.typography)
                    spacing_before = len(self.spacing)
                    radius_before = len(self.radius)
                    shadows_before = len(self.shadows)
                    
                    # 1. Extract DOM computed styles (original method)
                    styles = await self._extract_styles_from_page(page)
                    dom_colors = len(styles.get("colors", []))
                    self._aggregate_colors(styles.get("colors", []))
                    # v3: pass loaded_fonts so we can resolve generic fallbacks
                    self._aggregate_typography(
                        styles.get("typography", []),
                        loaded_fonts=styles.get("loaded_fonts", []),
                    )
                    self._aggregate_spacing(styles.get("spacing", []))
                    self._aggregate_radius(styles.get("radius", []))
                    self._aggregate_shadows(styles.get("shadows", []))
                    
                    # 2. Extract CSS variables (--primary-color, etc.)
                    css_var_count = 0
                    try:
                        css_vars = await self._extract_css_variables(page)
                        css_var_count = len(css_vars.get("computed", {}))
                        self._process_css_variables(css_vars)
                    except Exception as e:
                        self.warnings.append(f"CSS variables extraction failed: {str(e)}")
                    
                    # 3. Extract SVG colors (fill, stroke)
                    svg_color_count = 0
                    try:
                        svg_colors = await self._extract_svg_colors(page)
                        svg_color_count = len(svg_colors)
                        self._aggregate_colors(svg_colors)
                    except Exception as e:
                        self.warnings.append(f"SVG color extraction failed: {str(e)}")
                    
                    # 4. Extract inline style colors
                    inline_color_count = 0
                    try:
                        inline_colors = await self._extract_inline_styles(page)
                        inline_color_count = len(inline_colors)
                        self._aggregate_colors(inline_colors)
                    except Exception as e:
                        self.warnings.append(f"Inline style extraction failed: {str(e)}")
                    
                    # 5. Extract stylesheet colors (CSS rules)
                    stylesheet_color_count = 0
                    try:
                        stylesheet_colors = await self._extract_stylesheet_colors(page)
                        stylesheet_color_count = len(stylesheet_colors)
                        self._aggregate_colors(stylesheet_colors)
                    except Exception as e:
                        self.warnings.append(f"Stylesheet color extraction failed: {str(e)}")
                    
                    # 6. Fetch external CSS files (bypass CORS)
                    external_css_count = 0
                    try:
                        external_colors = await self._fetch_external_css_colors(page)
                        external_css_count = len(external_colors)
                        self._aggregate_colors(external_colors)
                    except Exception as e:
                        self.warnings.append(f"External CSS fetch failed: {str(e)}")
                    
                    # 7. Brute-force scan all page content for colors
                    page_scan_count = 0
                    try:
                        page_colors = await self._extract_all_page_colors(page)
                        page_scan_count = len(page_colors)
                        self._aggregate_colors(page_colors)
                    except Exception as e:
                        self.warnings.append(f"Page scan failed: {str(e)}")

                    # 8. Extract foreground-background color pairs for real AA checks
                    try:
                        fg_bg = await self._extract_fg_bg_pairs(page)
                        self.fg_bg_pairs.extend(fg_bg)
                    except Exception as e:
                        self.warnings.append(f"FG/BG pair extraction failed: {str(e)}")

                    # =========================================================
                    # Log extraction results for this page
                    # =========================================================
                    colors_new = len(self.colors) - colors_before
                    typo_new = len(self.typography) - typo_before
                    spacing_new = len(self.spacing) - spacing_before
                    radius_new = len(self.radius) - radius_before
                    shadows_new = len(self.shadows) - shadows_before
                    
                    # Store extraction stats for logging
                    self._last_extraction_stats = {
                        "url": url,
                        "dom_colors": dom_colors,
                        "css_variables": css_var_count,
                        "svg_colors": svg_color_count,
                        "inline_colors": inline_color_count,
                        "stylesheet_colors": stylesheet_color_count,
                        "external_css_colors": external_css_count,
                        "page_scan_colors": page_scan_count,
                        "new_colors": colors_new,
                        "new_typography": typo_new,
                        "new_spacing": spacing_new,
                        "new_radius": radius_new,
                        "new_shadows": shadows_new,
                    }
                    
                    # =========================================================
                    
                    self.total_elements += styles.get("elements_count", 0)
                    pages_crawled.append(url)
                    
                    await page.close()
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback((i + 1) / len(pages))
                    
                    # Rate limiting
                    await asyncio.sleep(self.settings.crawl.crawl_delay_ms / 1000)
                    
                except Exception as e:
                    self.errors.append(f"Error extracting {url}: {str(e)}")
        
        # Calculate confidence for all tokens
        for token in self.colors.values():
            token.confidence = self._calculate_confidence(token.frequency)
        for token in self.typography.values():
            token.confidence = self._calculate_confidence(token.frequency)
        for token in self.spacing.values():
            token.confidence = self._calculate_confidence(token.frequency)
        
        # Detect spacing base
        spacing_base = self._detect_spacing_base()
        
        # Mark outliers in spacing
        if spacing_base:
            for token in self.spacing.values():
                if spacing_base == 8 and not token.fits_base_8:
                    token.is_outlier = True
                elif spacing_base == 4 and not token.fits_base_4:
                    token.is_outlier = True
        
        # Determine primary font
        if self.font_families:
            primary_font = max(self.font_families.values(), key=lambda f: f.frequency)
            primary_font.usage = "primary"
        
        # Build result
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return ExtractedTokens(
            viewport=self.viewport,
            source_url=pages[0] if pages else "",
            pages_crawled=pages_crawled,
            colors=list(self.colors.values()),
            typography=list(self.typography.values()),
            spacing=list(self.spacing.values()),
            radius=list(self.radius.values()),
            shadows=list(self.shadows.values()),
            font_families=list(self.font_families.values()),
            spacing_base=spacing_base,
            extraction_timestamp=start_time,
            extraction_duration_ms=duration_ms,
            total_elements_analyzed=self.total_elements,
            unique_colors=len(self.colors),
            unique_font_sizes=len(set(t.font_size for t in self.typography.values())),
            unique_spacing_values=len(self.spacing),
            errors=self.errors,
            warnings=self.warnings,
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def extract_from_pages(
    pages: list[str],
    viewport: Viewport = Viewport.DESKTOP
) -> ExtractedTokens:
    """Convenience function to extract tokens from pages."""
    extractor = TokenExtractor(viewport=viewport)
    return await extractor.extract(pages)


async def extract_both_viewports(pages: list[str]) -> tuple[ExtractedTokens, ExtractedTokens]:
    """Extract tokens from both desktop and mobile viewports."""
    desktop_extractor = TokenExtractor(viewport=Viewport.DESKTOP)
    mobile_extractor = TokenExtractor(viewport=Viewport.MOBILE)
    
    desktop_result = await desktop_extractor.extract(pages)
    mobile_result = await mobile_extractor.extract(pages)
    
    return desktop_result, mobile_result
