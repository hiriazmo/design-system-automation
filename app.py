"""
Design System Automation — Main Application
==============================================

Flow:
1. User enters URL
2. Agent 1 discovers pages → User confirms
3. Agent 1 extracts tokens (Desktop + Mobile)
4. Agent 2 normalizes tokens
5. Stage 1 UI: User reviews tokens (accept/reject, Desktop↔Mobile toggle)
6. Agent 3 proposes upgrades
7. Stage 2 UI: User selects options with live preview
8. Agent 4 generates JSON
9. Stage 3 UI: User exports
"""

import os
import asyncio
import json
import gradio as gr
from datetime import datetime
from typing import Optional

# Get HF token from environment
HF_TOKEN_FROM_ENV = os.getenv("HF_TOKEN", "")

# =============================================================================
# GLOBAL STATE
# =============================================================================

class AppState:
    """Global application state."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.discovered_pages = []
        self.base_url = ""
        self.desktop_raw = None  # ExtractedTokens
        self.mobile_raw = None   # ExtractedTokens
        self.desktop_normalized = None  # NormalizedTokens
        self.mobile_normalized = None   # NormalizedTokens
        self.upgrade_recommendations = None  # UpgradeRecommendations
        self.selected_upgrades = {}  # User selections
        self.color_classification = None  # ClassificationResult from rule-based classifier
        self.logs = []
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 500:
            self.logs.pop(0)
    
    def get_logs(self) -> str:
        return "\n".join(self.logs)

state = AppState()


# =============================================================================
# MESSAGE HELPERS
# =============================================================================

def success_message(title: str, details: str, next_step: str) -> str:
    """Generate a formatted success message with next-step guidance."""
    return f"## ✅ {title}\n\n{details}\n\n**Next step:** {next_step}"


def error_message(title: str, details: str, how_to_fix: str) -> str:
    """Generate a formatted error message with fix guidance."""
    return f"## ❌ {title}\n\n{details}\n\n**How to fix:** {how_to_fix}"


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def get_crawler():
    import agents.crawler
    return agents.crawler

def get_extractor():
    import agents.extractor
    return agents.extractor

def get_normalizer():
    import agents.normalizer
    return agents.normalizer

def get_advisor():
    import agents.advisor
    return agents.advisor

def get_schema():
    import core.token_schema
    return core.token_schema


# =============================================================================
# PHASE 1: DISCOVER PAGES
# =============================================================================

async def discover_pages(url: str, progress=gr.Progress()):
    """Discover pages from URL."""
    state.reset()
    
    if not url or not url.startswith(("http://", "https://")):
        return error_message("Invalid URL",
                             "The URL must start with `https://` or `http://`.",
                             "Enter a full URL like `https://example.com` and try again."), "", None
    
    state.log(f"🚀 Starting discovery for: {url}")
    progress(0.1, desc="🔍 Discovering pages...")
    
    try:
        crawler = get_crawler()
        discoverer = crawler.PageDiscoverer()
        
        pages = await discoverer.discover(url)
        
        state.discovered_pages = pages
        state.base_url = url
        
        state.log(f"✅ Found {len(pages)} pages")
        
        # Format for display
        pages_data = []
        for page in pages:
            pages_data.append([
                True,  # Selected by default
                page.url,
                page.title if page.title else "(No title)",
                page.page_type.value,
                "✓" if not page.error else f"⚠ {page.error}"
            ])
        
        progress(1.0, desc="✅ Discovery complete!")
        
        status = success_message(
            f"Found {len(pages)} Pages",
            f"The crawler discovered **{len(pages)} pages** on `{url}`. Review the table below — "
            "use the **Select** checkboxes to choose which pages to scan for design tokens.",
            "Click **'Extract Tokens (Desktop + Mobile)'** to begin extraction."
        )

        return status, state.get_logs(), pages_data
        
    except Exception as e:
        import traceback
        state.log(f"❌ Error: {str(e)}")
        error_detail = str(e).lower()
        if "timeout" in error_detail:
            hint = "The website took too long to respond. Try again, or check if the site is accessible in your browser."
        elif "dns" in error_detail or "name resolution" in error_detail:
            hint = "Could not find this website. Please check the URL for typos."
        elif "ssl" in error_detail or "certificate" in error_detail:
            hint = "SSL/certificate error. Try using `http://` instead of `https://`, or check if the site has a valid certificate."
        else:
            hint = "Check that the URL is correct and the site is publicly accessible. Review the log above for details."
        return error_message("Discovery Failed", str(e)[:200], hint), state.get_logs(), None


# =============================================================================
# PHASE 2: EXTRACT TOKENS
# =============================================================================

async def extract_tokens(pages_data, progress=gr.Progress()):
    """Extract tokens from selected pages (both viewports)."""
    
    state.log(f"📥 Received pages_data type: {type(pages_data)}")
    
    if pages_data is None:
        return (error_message("No Pages Discovered",
                              "No pages have been discovered yet.",
                              "Go to **Step 1** above, enter a URL, and click **'Discover Pages'** first."),
                state.get_logs(), None, None)
    
    # Get selected URLs - handle pandas DataFrame
    selected_urls = []
    
    try:
        # Check if it's a pandas DataFrame
        if hasattr(pages_data, 'iterrows'):
            state.log(f"📥 DataFrame with {len(pages_data)} rows, columns: {list(pages_data.columns)}")
            
            for idx, row in pages_data.iterrows():
                # Get values by column name or position
                try:
                    # Try column names first
                    is_selected = row.get('Select', row.iloc[0] if len(row) > 0 else False)
                    url = row.get('URL', row.iloc[1] if len(row) > 1 else '')
                except (KeyError, IndexError, TypeError):
                    # Fallback to positional
                    is_selected = row.iloc[0] if len(row) > 0 else False
                    url = row.iloc[1] if len(row) > 1 else ''
                
                if is_selected and url:
                    selected_urls.append(url)
        
        # If it's a dict (Gradio sometimes sends this)
        elif isinstance(pages_data, dict):
            state.log(f"📥 Dict with keys: {list(pages_data.keys())}")
            data = pages_data.get('data', [])
            for row in data:
                if isinstance(row, (list, tuple)) and len(row) >= 2 and row[0]:
                    selected_urls.append(row[1])
        
        # If it's a list
        elif isinstance(pages_data, (list, tuple)):
            state.log(f"📥 List with {len(pages_data)} items")
            for row in pages_data:
                if isinstance(row, (list, tuple)) and len(row) >= 2 and row[0]:
                    selected_urls.append(row[1])
                    
    except Exception as e:
        state.log(f"❌ Error parsing pages_data: {str(e)}")
        import traceback
        state.log(traceback.format_exc())
    
    state.log(f"📋 Found {len(selected_urls)} selected URLs")
    
    # If still no URLs, try using stored discovered pages
    if not selected_urls and state.discovered_pages:
        state.log("⚠️ No URLs from table, using all discovered pages")
        selected_urls = [p.url for p in state.discovered_pages if not p.error][:10]
    
    if not selected_urls:
        return (error_message("No Pages Selected",
                              "No pages are selected for extraction.",
                              "Go back to the pages table above and check the **Select** boxes for the pages you want to extract, then click this button again."),
                state.get_logs(), None, None)
    
    # Limit to 10 pages for performance
    selected_urls = selected_urls[:10]
    
    state.log(f"📋 Extracting from {len(selected_urls)} pages:")
    for url in selected_urls[:3]:
        state.log(f"   • {url}")
    if len(selected_urls) > 3:
        state.log(f"   ... and {len(selected_urls) - 3} more")
    
    progress(0.05, desc="🚀 Starting extraction...")
    
    try:
        schema = get_schema()
        extractor_mod = get_extractor()
        normalizer_mod = get_normalizer()
        
        # === DESKTOP EXTRACTION ===
        state.log("")
        state.log("=" * 60)
        state.log("🖥️ DESKTOP EXTRACTION (1440px)")
        state.log("=" * 60)
        state.log("")
        state.log("📡 Enhanced extraction from 7 sources:")
        state.log("   1. DOM computed styles (getComputedStyle)")
        state.log("   2. CSS variables (:root { --color: })")
        state.log("   3. SVG colors (fill, stroke)")
        state.log("   4. Inline styles (style='color:')")
        state.log("   5. Stylesheet rules (CSS files)")
        state.log("   6. External CSS files (fetch & parse)")
        state.log("   7. Page content scan (brute-force)")
        state.log("")
        
        progress(0.1, desc="🖥️ Extracting desktop tokens...")
        
        desktop_extractor = extractor_mod.TokenExtractor(viewport=schema.Viewport.DESKTOP)
        
        def desktop_progress(p):
            progress(0.1 + (p * 0.35), desc=f"🖥️ Desktop... {int(p*100)}%")
        
        state.desktop_raw = await desktop_extractor.extract(selected_urls, progress_callback=desktop_progress)
        
        # Log extraction details
        state.log("📊 EXTRACTION RESULTS:")
        state.log(f"   Colors:     {len(state.desktop_raw.colors)} unique")
        state.log(f"   Typography: {len(state.desktop_raw.typography)} styles")
        state.log(f"   Spacing:    {len(state.desktop_raw.spacing)} values")
        state.log(f"   Radius:     {len(state.desktop_raw.radius)} values")
        state.log(f"   Shadows:    {len(state.desktop_raw.shadows)} values")
        
        # Store foreground-background pairs for real AA checking in Stage 2
        if hasattr(desktop_extractor, 'fg_bg_pairs') and desktop_extractor.fg_bg_pairs:
            state.fg_bg_pairs = desktop_extractor.fg_bg_pairs
            state.log(f"   FG/BG Pairs: {len(state.fg_bg_pairs)} unique pairs for AA checking")
        else:
            state.fg_bg_pairs = []

        # Log CSS variables if found
        if hasattr(desktop_extractor, 'css_variables') and desktop_extractor.css_variables:
            state.log("")
            state.log(f"🎨 CSS Variables found: {len(desktop_extractor.css_variables)}")
            for var_name, var_value in list(desktop_extractor.css_variables.items())[:5]:
                state.log(f"   {var_name}: {var_value}")
            if len(desktop_extractor.css_variables) > 5:
                state.log(f"   ... and {len(desktop_extractor.css_variables) - 5} more")
        
        # Log warnings if any
        if desktop_extractor.warnings:
            state.log("")
            state.log("⚠️ Warnings:")
            for w in desktop_extractor.warnings[:3]:
                state.log(f"   {w}")
        
        # Normalize desktop
        state.log("")
        state.log("🔄 Normalizing (deduping, naming)...")
        state.desktop_normalized = normalizer_mod.normalize_tokens(state.desktop_raw)
        state.log(f"   ✅ Normalized: {len(state.desktop_normalized.colors)} colors, {len(state.desktop_normalized.typography)} typography, {len(state.desktop_normalized.spacing)} spacing")
        
        # === MOBILE EXTRACTION ===
        state.log("")
        state.log("=" * 60)
        state.log("📱 MOBILE EXTRACTION (375px)")
        state.log("=" * 60)
        state.log("")
        
        progress(0.5, desc="📱 Extracting mobile tokens...")
        
        mobile_extractor = extractor_mod.TokenExtractor(viewport=schema.Viewport.MOBILE)
        
        def mobile_progress(p):
            progress(0.5 + (p * 0.35), desc=f"📱 Mobile... {int(p*100)}%")
        
        state.mobile_raw = await mobile_extractor.extract(selected_urls, progress_callback=mobile_progress)
        
        # Log extraction details
        state.log("📊 EXTRACTION RESULTS:")
        state.log(f"   Colors:     {len(state.mobile_raw.colors)} unique")
        state.log(f"   Typography: {len(state.mobile_raw.typography)} styles")
        state.log(f"   Spacing:    {len(state.mobile_raw.spacing)} values")
        state.log(f"   Radius:     {len(state.mobile_raw.radius)} values")
        state.log(f"   Shadows:    {len(state.mobile_raw.shadows)} values")
        
        # Normalize mobile
        state.log("")
        state.log("🔄 Normalizing...")
        state.mobile_normalized = normalizer_mod.normalize_tokens(state.mobile_raw)
        state.log(f"   ✅ Normalized: {len(state.mobile_normalized.colors)} colors, {len(state.mobile_normalized.typography)} typography, {len(state.mobile_normalized.spacing)} spacing")
        
        # === FIRECRAWL CSS EXTRACTION (Agent 1B) ===
        progress(0.88, desc="🔥 Firecrawl CSS analysis...")
        
        try:
            from agents.firecrawl_extractor import extract_css_colors
            
            # Get base URL for Firecrawl
            base_url = selected_urls[0] if selected_urls else state.base_url
            
            # Extract CSS colors using Firecrawl
            firecrawl_result = await extract_css_colors(
                url=base_url,
                api_key=None,  # Will use fallback method
                log_callback=state.log
            )
            
            # Merge Firecrawl colors into desktop normalized
            firecrawl_colors = firecrawl_result.get("colors", {})
            
            if firecrawl_colors:
                state.log("")
                state.log("🔀 Merging Firecrawl colors with Playwright extraction...")
                
                # Count new colors
                new_colors_count = 0
                
                for hex_val, color_data in firecrawl_colors.items():
                    # Check if this color already exists
                    existing = False
                    for name, existing_color in state.desktop_normalized.colors.items():
                        if existing_color.value.lower() == hex_val.lower():
                            existing = True
                            # Update frequency
                            existing_color.frequency += color_data.get("frequency", 1)
                            if "firecrawl" not in existing_color.contexts:
                                existing_color.contexts.append("firecrawl")
                            break
                    
                    if not existing:
                        # Add new color from Firecrawl
                        from core.token_schema import ColorToken, TokenSource, Confidence
                        
                        new_token = ColorToken(
                            value=hex_val,
                            frequency=color_data.get("frequency", 1),
                            contexts=["firecrawl"] + color_data.get("contexts", []),
                            elements=["css-file"],
                            css_properties=color_data.get("sources", []),
                            contrast_white=color_data.get("contrast_white", 0),
                            contrast_black=color_data.get("contrast_black", 0),
                            source=TokenSource.DETECTED,
                            confidence=Confidence.MEDIUM,
                        )
                        
                        # Generate name based on color characteristics (not garbage like firecrawl.34)
                        # This will be a fallback; semantic analysis may override later
                        new_token.suggested_name = None  # Let consolidation generate proper name

                        state.desktop_normalized.colors[hex_val] = new_token
                        new_colors_count += 1
                
                state.log(f"   ✅ Added {new_colors_count} new colors from Firecrawl")
                state.log(f"   📊 Total colors now: {len(state.desktop_normalized.colors)}")
        
        except Exception as e:
            state.log(f"   ⚠️ Firecrawl extraction skipped: {str(e)}")
        
        # === SEMANTIC COLOR ANALYSIS (Agent 1C) ===
        progress(0.92, desc="🧠 Semantic color analysis...")
        
        semantic_result = {}
        semantic_preview_html = ""
        
        try:
            from agents.semantic_analyzer import SemanticColorAnalyzer, generate_semantic_preview_html
            
            # Create analyzer (using rule-based for now, can add LLM later)
            semantic_analyzer = SemanticColorAnalyzer(llm_provider=None)
            
            # Run analysis
            semantic_result = semantic_analyzer.analyze_sync(
                colors=state.desktop_normalized.colors,
                log_callback=state.log
            )
            
            # Store in state for Stage 2
            state.semantic_analysis = semantic_result
            
            # Generate preview HTML
            semantic_preview_html = generate_semantic_preview_html(semantic_result)
            
        except Exception as e:
            state.log(f"   ⚠️ Semantic analysis skipped: {str(e)}")
            import traceback
            state.log(traceback.format_exc())
        
        progress(0.95, desc="📊 Preparing results...")
        
        # Format results for Stage 1 UI
        desktop_data = format_tokens_for_display(state.desktop_normalized)
        mobile_data = format_tokens_for_display(state.mobile_normalized)
        
        # Generate visual previews - AS-IS for Stage 1 (no ramps, no enhancements)
        state.log("")
        state.log("🎨 Generating AS-IS visual previews...")
        
        from core.preview_generator import (
            generate_typography_preview_html,
            generate_colors_asis_preview_html,
            generate_spacing_asis_preview_html,
            generate_radius_asis_preview_html,
            generate_shadows_asis_preview_html,
        )
        
        # Get detected font
        fonts = get_detected_fonts()
        primary_font = fonts.get("primary", "Open Sans")
        
        # Convert typography tokens to dict format for preview
        typo_dict = {}
        for name, t in state.desktop_normalized.typography.items():
            typo_dict[name] = {
                "font_size": t.font_size,
                "font_weight": t.font_weight,
                "line_height": t.line_height or "1.5",
                "letter_spacing": "0",
            }
        
        # Convert color tokens to dict format for preview (with full metadata)
        color_dict = {}
        for name, c in state.desktop_normalized.colors.items():
            color_dict[name] = {
                "value": c.value,
                "frequency": c.frequency,
                "contexts": c.contexts[:3] if c.contexts else [],
                "elements": c.elements[:3] if c.elements else [],
                "css_properties": c.css_properties[:3] if c.css_properties else [],
                "contrast_white": c.contrast_white,
                "contrast_black": getattr(c, 'contrast_black', 0),
            }
        
        # Convert spacing tokens to dict format
        spacing_dict = {}
        for name, s in state.desktop_normalized.spacing.items():
            spacing_dict[name] = {
                "value": s.value,
                "value_px": s.value_px,
            }
        
        # Convert radius tokens to dict format
        radius_dict = {}
        for name, r in state.desktop_normalized.radius.items():
            radius_dict[name] = {"value": r.value}
        
        # Convert shadow tokens to dict format
        shadow_dict = {}
        for name, s in state.desktop_normalized.shadows.items():
            shadow_dict[name] = {"value": s.value}
        
        # Generate AS-IS previews (Stage 1 - raw extracted values)
        typography_preview_html = generate_typography_preview_html(
            typography_tokens=typo_dict,
            font_family=primary_font,
            sample_text="The quick brown fox jumps over the lazy dog",
        )
        
        # AS-IS color preview (no ramps)
        colors_asis_preview_html = generate_colors_asis_preview_html(
            color_tokens=color_dict,
        )
        
        # AS-IS spacing preview
        spacing_asis_preview_html = generate_spacing_asis_preview_html(
            spacing_tokens=spacing_dict,
        )
        
        # AS-IS radius preview
        radius_asis_preview_html = generate_radius_asis_preview_html(
            radius_tokens=radius_dict,
        )
        
        # AS-IS shadows preview
        shadows_asis_preview_html = generate_shadows_asis_preview_html(
            shadow_tokens=shadow_dict,
        )
        
        state.log("   ✅ Typography preview generated")
        state.log("   ✅ Colors AS-IS preview generated (no ramps)")
        state.log("   ✅ Semantic color analysis preview generated")
        state.log("   ✅ Spacing AS-IS preview generated")
        state.log("   ✅ Radius AS-IS preview generated")
        state.log("   ✅ Shadows AS-IS preview generated")
        
        # Get semantic summary for status
        brand_count = len(semantic_result.get("brand", {}))
        text_count = len(semantic_result.get("text", {}))
        bg_count = len(semantic_result.get("background", {}))
        
        state.log("")
        state.log("=" * 50)
        state.log("✅ EXTRACTION COMPLETE!")
        state.log(f"   Enhanced extraction captured:")
        state.log(f"   • {len(state.desktop_normalized.colors)} colors (DOM + CSS vars + SVG + inline)")
        state.log(f"   • {len(state.desktop_normalized.typography)} typography styles")
        state.log(f"   • {len(state.desktop_normalized.spacing)} spacing values")
        state.log(f"   • {len(state.desktop_normalized.radius)} radius values")
        state.log(f"   • {len(state.desktop_normalized.shadows)} shadow values")
        state.log(f"   Semantic Analysis:")
        state.log(f"   • {brand_count} brand colors identified")
        state.log(f"   • {text_count} text colors identified")
        state.log(f"   • {bg_count} background colors identified")
        state.log("=" * 50)
        
        progress(1.0, desc="✅ Complete!")
        
        status = f"""## ✅ Extraction Complete!

| Viewport | Colors | Typography | Spacing | Radius | Shadows |
|----------|--------|------------|---------|--------|---------|
| Desktop | {len(state.desktop_normalized.colors)} | {len(state.desktop_normalized.typography)} | {len(state.desktop_normalized.spacing)} | {len(state.desktop_normalized.radius)} | {len(state.desktop_normalized.shadows)} |
| Mobile | {len(state.mobile_normalized.colors)} | {len(state.mobile_normalized.typography)} | {len(state.mobile_normalized.spacing)} | {len(state.mobile_normalized.radius)} | {len(state.mobile_normalized.shadows)} |

**Primary Font:** {primary_font}

**Semantic Analysis:** {brand_count} brand, {text_count} text, {bg_count} background colors

**Enhanced Extraction:** DOM + CSS Variables + SVG + Inline + Stylesheets + Firecrawl

**Next:** Review the tokens below. Accept or reject, then proceed to Stage 2.
"""
        
        # Return all AS-IS previews including semantic
        return (
            status, 
            state.get_logs(), 
            desktop_data, 
            mobile_data, 
            typography_preview_html, 
            colors_asis_preview_html,
            semantic_preview_html,
            spacing_asis_preview_html,
            radius_asis_preview_html,
            shadows_asis_preview_html,
        )
        
    except Exception as e:
        import traceback
        state.log(f"❌ Error: {str(e)}")
        state.log(traceback.format_exc())
        error_detail = str(e).lower()
        if "timeout" in error_detail or "navigation" in error_detail:
            hint = "The page took too long to load. Try selecting fewer pages, or check if the site requires authentication."
        elif "no tokens" in error_detail or "empty" in error_detail:
            hint = "No design tokens could be extracted. The site may use unusual CSS patterns. Try a different page selection."
        else:
            hint = "Check the log above for details. Try selecting fewer pages or a different set of pages."
        return (error_message("Extraction Failed", str(e)[:200], hint),
                state.get_logs(), None, None, "", "", "", "", "", "")


def format_tokens_for_display(normalized) -> dict:
    """Format normalized tokens for Gradio display."""
    if normalized is None:
        return {"colors": [], "typography": [], "spacing": []}
    
    # Colors are now a dict
    colors = []
    color_items = list(normalized.colors.values()) if isinstance(normalized.colors, dict) else normalized.colors
    for c in sorted(color_items, key=lambda x: -x.frequency)[:50]:
        colors.append([
            True,  # Accept checkbox
            c.value,
            c.suggested_name or "",
            c.frequency,
            c.confidence.value if c.confidence else "medium",
            f"{c.contrast_white:.1f}:1" if c.contrast_white else "N/A",
            "✓" if c.wcag_aa_small_text else "✗",
            ", ".join(c.contexts[:2]) if c.contexts else "",
        ])
    
    # Typography
    typography = []
    typo_items = list(normalized.typography.values()) if isinstance(normalized.typography, dict) else normalized.typography
    for t in sorted(typo_items, key=lambda x: -x.frequency)[:30]:
        typography.append([
            True,  # Accept checkbox
            t.font_family,
            t.font_size,
            str(t.font_weight),
            t.line_height or "",
            t.suggested_name or "",
            t.frequency,
            t.confidence.value if t.confidence else "medium",
        ])
    
    # Spacing
    spacing = []
    spacing_items = list(normalized.spacing.values()) if isinstance(normalized.spacing, dict) else normalized.spacing
    for s in sorted(spacing_items, key=lambda x: x.value_px)[:20]:
        spacing.append([
            True,  # Accept checkbox
            s.value,
            f"{s.value_px}px",
            s.suggested_name or "",
            s.frequency,
            "✓" if s.fits_base_8 else "",
            s.confidence.value if s.confidence else "medium",
        ])
    
    # Radius
    radius = []
    radius_items = list(normalized.radius.values()) if isinstance(normalized.radius, dict) else normalized.radius
    for r in sorted(radius_items, key=lambda x: -x.frequency)[:20]:
        radius.append([
            True,  # Accept checkbox
            r.value,
            r.frequency,
            ", ".join(r.elements[:3]) if r.elements else "",
        ])

    return {
        "colors": colors,
        "typography": typography,
        "spacing": spacing,
        "radius": radius,
    }


def switch_viewport(viewport: str):
    """Switch between desktop and mobile view."""
    if viewport == "Desktop (1440px)":
        data = format_tokens_for_display(state.desktop_normalized)
    else:
        data = format_tokens_for_display(state.mobile_normalized)

    return data["colors"], data["typography"], data["spacing"], data["radius"]


# Legacy run_stage2_analysis() removed in v3 — use run_stage2_analysis_v2()


def normalized_to_dict(normalized) -> dict:
    """Convert NormalizedTokens to dict for workflow.

    v3: Includes full context (elements, contexts, role_hint, blur_px, etc.)
    so agents can reason about WHY each token is used.
    """
    if not normalized:
        return {}

    result = {
        "colors": {},
        "typography": {},
        "spacing": {},
        "radius": {},
        "shadows": {},
    }

    # Colors — include contexts, elements, role_hint for AURORA
    for name, c in normalized.colors.items():
        result["colors"][name] = {
            "value": c.value,
            "frequency": c.frequency,
            "suggested_name": c.suggested_name,
            "contrast_white": c.contrast_white,
            "contrast_black": c.contrast_black,
            "contexts": getattr(c, 'contexts', []),
            "elements": getattr(c, 'elements', []),
            "role_hint": getattr(c, 'role_hint', None),
        }

    # Typography — include elements for hierarchy analysis
    for name, t in normalized.typography.items():
        result["typography"][name] = {
            "font_family": t.font_family,
            "font_size": t.font_size,
            "font_weight": t.font_weight,
            "line_height": t.line_height,
            "frequency": t.frequency,
            "elements": getattr(t, 'elements', []),
        }

    # Spacing — include contexts and grid-alignment flags
    for name, s in normalized.spacing.items():
        result["spacing"][name] = {
            "value": s.value,
            "value_px": s.value_px,
            "frequency": s.frequency,
            "contexts": getattr(s, 'contexts', []),
            "fits_base_4": getattr(s, 'fits_base_4', False),
            "fits_base_8": getattr(s, 'fits_base_8', False),
        }

    # Radius — include grid-alignment flags and elements
    for name, r in normalized.radius.items():
        result["radius"][name] = {
            "value": r.value,
            "value_px": getattr(r, 'value_px', None),
            "frequency": r.frequency,
            "elements": getattr(r, 'elements', []),
            "fits_base_4": getattr(r, 'fits_base_4', False),
            "fits_base_8": getattr(r, 'fits_base_8', False),
        }

    # Shadows — include parsed components for elevation analysis
    for name, s in normalized.shadows.items():
        result["shadows"][name] = {
            "value": s.value,
            "frequency": s.frequency,
            "blur_px": getattr(s, 'blur_px', None),
            "y_offset_px": getattr(s, 'y_offset_px', None),
            "elements": getattr(s, 'elements', []),
        }
    
    return result


# =============================================================================
# STAGE 2: NEW ARCHITECTURE (Rule Engine + Benchmark Research + LLM Agents)
# =============================================================================

async def run_stage2_analysis_v2(
    selected_benchmarks: list[str] = None,
    progress=gr.Progress()
):
    """
    Run Stage 2 analysis with new architecture:
    - Layer 1: Rule Engine (FREE)
    - Layer 2: Benchmark Research (Firecrawl + Cache)
    - Layer 3: LLM Agents (Brand ID, Benchmark Advisor, Best Practices)
    - Layer 4: HEAD Synthesizer
    
    Includes comprehensive error handling for graceful degradation.
    """
    
    # Validate Stage 1 completion
    if not state.desktop_normalized or not state.mobile_normalized:
        return create_stage2_error_response(
            error_message("Stage 1 Not Complete",
                          "No extracted tokens found. Stage 1 extraction must be completed before running analysis.",
                          "Go back to **Step 1**, enter a URL, discover pages, and extract tokens first.")
        )
    
    # Default benchmarks if none selected
    if not selected_benchmarks or len(selected_benchmarks) == 0:
        selected_benchmarks = [
            "material_design_3",
            "shopify_polaris", 
            "atlassian_design",
        ]
    
    state.log("")
    state.log("═" * 60)
    state.log("🚀 STAGE 2: MULTI-AGENT ANALYSIS")
    state.log("═" * 60)
    state.log(f"   Started: {datetime.now().strftime('%H:%M:%S')}")
    state.log(f"   Benchmarks: {', '.join(selected_benchmarks)}")
    state.log("")
    
    # Import dataclasses early so fallbacks always work
    try:
        from agents.llm_agents import (
            BrandIdentification,
            BenchmarkAdvice,
            BestPracticesResult,
        )
    except ImportError:
        # Minimal v3-compatible fallback dataclasses
        from dataclasses import dataclass, field
        @dataclass
        class BrandIdentification:
            brand_primary: dict = field(default_factory=dict)
            brand_secondary: dict = field(default_factory=dict)
            brand_accent: dict = field(default_factory=dict)
            palette_strategy: str = ""
            cohesion_score: int = 5
            cohesion_notes: str = ""
            naming_map: dict = field(default_factory=dict)
            semantic_names: dict = field(default_factory=dict)
            self_evaluation: dict = field(default_factory=dict)
            reasoning_trace: list = field(default_factory=list)
            validation_passed: bool = False
            retry_count: int = 0
            typography_notes: str = ""
            spacing_notes: str = ""
            radius_notes: str = ""
            shadow_notes: str = ""
            def to_dict(self):
                return {k: getattr(self, k) for k in ['brand_primary', 'brand_secondary', 'brand_accent', 'palette_strategy', 'cohesion_score', 'naming_map', 'self_evaluation']}

        @dataclass
        class BenchmarkAdvice:
            recommended_benchmark: str = ""
            recommended_benchmark_name: str = ""
            reasoning: str = ""
            alignment_changes: list = field(default_factory=list)
            pros_of_alignment: list = field(default_factory=list)
            cons_of_alignment: list = field(default_factory=list)
            alternative_benchmarks: list = field(default_factory=list)
            self_evaluation: dict = field(default_factory=dict)
            reasoning_trace: list = field(default_factory=list)
            typography_comparison: dict = field(default_factory=dict)
            spacing_comparison: dict = field(default_factory=dict)
            color_comparison: dict = field(default_factory=dict)
            radius_comparison: dict = field(default_factory=dict)
            shadow_comparison: dict = field(default_factory=dict)
            def to_dict(self):
                return {k: getattr(self, k) for k in ['recommended_benchmark', 'recommended_benchmark_name', 'reasoning', 'alignment_changes']}

        @dataclass
        class BestPracticesResult:
            overall_score: int = 50
            checks: dict = field(default_factory=dict)
            priority_fixes: list = field(default_factory=list)
            passing_practices: list = field(default_factory=list)
            failing_practices: list = field(default_factory=list)
            self_evaluation: dict = field(default_factory=dict)
            reasoning_trace: list = field(default_factory=list)
            validation_passed: bool = False
            color_assessment: dict = field(default_factory=dict)
            typography_assessment: dict = field(default_factory=dict)
            spacing_assessment: dict = field(default_factory=dict)
            radius_assessment: dict = field(default_factory=dict)
            shadow_assessment: dict = field(default_factory=dict)
            def to_dict(self):
                return {k: getattr(self, k) for k in ['overall_score', 'checks', 'priority_fixes', 'passing_practices', 'failing_practices']}

    # Initialize results with defaults (for graceful degradation)
    rule_results = None
    benchmark_comparisons = []
    brand_result = None
    benchmark_advice = None
    best_practices = None
    final_synthesis = None
    
    progress(0.05, desc="⚙️ Running Rule Engine...")
    
    try:
        # =================================================================
        # LAYER 1: RULE ENGINE (FREE) - Critical, must succeed
        # =================================================================
        try:
            from core.rule_engine import run_rule_engine
            
            # Convert tokens to dict
            desktop_dict = normalized_to_dict(state.desktop_normalized)
            mobile_dict = normalized_to_dict(state.mobile_normalized)
            
            # Validate we have data
            if not desktop_dict.get("colors") and not desktop_dict.get("typography"):
                raise ValueError("No tokens extracted from Stage 1")
            
            # Run rule engine
            rule_results = run_rule_engine(
                typography_tokens=desktop_dict.get("typography", {}),
                color_tokens=desktop_dict.get("colors", {}),
                spacing_tokens=desktop_dict.get("spacing", {}),
                radius_tokens=desktop_dict.get("radius", {}),
                shadow_tokens=desktop_dict.get("shadows", {}),
                log_callback=state.log,
                fg_bg_pairs=getattr(state, 'fg_bg_pairs', None),
            )
            
            state.rule_engine_results = rule_results
            state.log("")
            state.log("   ✅ Rule Engine: SUCCESS")
            
        except Exception as e:
            state.log(f"   ❌ Rule Engine FAILED: {str(e)[:100]}")
            state.log("   └─ Cannot proceed without rule engine results")
            import traceback
            state.log(traceback.format_exc()[:500])
            return create_stage2_error_response(
                error_message("Rule Engine Failed",
                              f"The rule engine could not analyze your tokens: {str(e)[:150]}",
                              "This usually means the extracted tokens are incomplete. Try re-running Stage 1 extraction with different pages selected.")
            )
        
        progress(0.20, desc="🔬 Researching benchmarks...")
        
        # =================================================================
        # LAYER 2: BENCHMARK RESEARCH - Can use fallback
        # =================================================================
        try:
            from agents.benchmark_researcher import BenchmarkResearcher, FALLBACK_BENCHMARKS, BenchmarkData
            
            # Try to get Firecrawl client (optional)
            firecrawl_client = None
            try:
                from agents.firecrawl_extractor import get_firecrawl_client
                firecrawl_client = get_firecrawl_client()
                state.log("   ├─ Firecrawl client: Available")
            except Exception as fc_err:
                state.log(f"   ├─ Firecrawl client: Not available ({str(fc_err)[:30]})")
                state.log("   │  └─ Will use cached/fallback data")
            
            # Get HF client for LLM extraction (optional)
            hf_client = None
            try:
                from core.hf_inference import get_inference_client
                hf_client = get_inference_client()
                state.log("   ├─ HF client: Available")
            except Exception as hf_err:
                state.log(f"   ├─ HF client: Not available ({str(hf_err)[:30]})")
            
            researcher = BenchmarkResearcher(
                firecrawl_client=firecrawl_client,
                hf_client=hf_client,
            )
            
            # Research selected benchmarks (with fallback)
            try:
                benchmarks = await researcher.research_selected_benchmarks(
                    selected_keys=selected_benchmarks,
                    log_callback=state.log,
                )
            except Exception as research_err:
                state.log(f"   ⚠️ Research failed, using fallback: {str(research_err)[:50]}")
                # Use fallback data
                benchmarks = []
                for key in selected_benchmarks:
                    if key in FALLBACK_BENCHMARKS:
                        data = FALLBACK_BENCHMARKS[key]
                        benchmarks.append(BenchmarkData(
                            key=key,
                            name=key.replace("_", " ").title(),
                            short_name=key.split("_")[0].title(),
                            vendor="",
                            icon="📦",
                            typography=data.get("typography", {}),
                            spacing=data.get("spacing", {}),
                            colors=data.get("colors", {}),
                            radius=data.get("radius", {}),
                            shadows=data.get("shadows", {}),
                            fetched_at=datetime.now().isoformat(),
                            confidence="fallback",
                            best_for=[],
                        ))
            
            # Compare to benchmarks
            if benchmarks and rule_results:
                # Count user's radius tiers and shadow levels for comparison
                _user_radius_tiers = len(desktop_dict.get("radius", {}))
                _user_shadow_levels = len(desktop_dict.get("shadows", {}))
                _user_color_count = len(desktop_dict.get("colors", {}))

                benchmark_comparisons = researcher.compare_to_benchmarks(
                    your_ratio=rule_results.typography.detected_ratio,
                    your_base_size=int(rule_results.typography.base_size) if rule_results.typography.sizes_px else 16,
                    your_spacing_grid=rule_results.spacing.detected_base,
                    benchmarks=benchmarks,
                    log_callback=state.log,
                    your_color_count=_user_color_count,
                    your_radius_tiers=_user_radius_tiers,
                    your_shadow_levels=_user_shadow_levels,
                )
                state.benchmark_comparisons = benchmark_comparisons
                state.log("")
                state.log(f"   ✅ Benchmark Research: SUCCESS ({len(benchmarks)} systems)")
            else:
                state.log("   ⚠️ No benchmarks available for comparison")
            
        except Exception as e:
            state.log(f"   ⚠️ Benchmark Research FAILED: {str(e)[:100]}")
            state.log("   └─ Continuing without benchmark comparison...")
            benchmark_comparisons = []
        
        progress(0.40, desc="🤖 Running LLM Agents in parallel...")

        # =================================================================
        # LAYER 3: LLM AGENTS — v3: ALL token types, ReAct reasoning
        # =================================================================
        try:
            from agents.llm_agents import (
                BrandIdentifierAgent,
                BenchmarkAdvisorAgent,
                BestPracticesValidatorAgent,
                BrandIdentification,
                BenchmarkAdvice,
                BestPracticesResult,
            )

            state.log("")
            state.log("=" * 60)
            state.log("LAYER 3: LLM AGENTS (ReAct + Parallel)")
            state.log("=" * 60)
            state.log("   Each agent researches ALL token types:")
            state.log("   Colors + Typography + Spacing + Radius + Shadows")
            state.log("")

            # Check if HF client is available
            if not hf_client:
                try:
                    from core.hf_inference import get_inference_client
                    hf_client = get_inference_client()
                except Exception:
                    state.log("   HF client not available - skipping LLM agents")
                    hf_client = None

            if hf_client:
                # Initialize agents
                brand_agent = BrandIdentifierAgent(hf_client)
                benchmark_agent = BenchmarkAdvisorAgent(hf_client)
                best_practices_agent = BestPracticesValidatorAgent(hf_client)

                # Full token dict with all context
                desktop_dict = normalized_to_dict(state.desktop_normalized)

                # Prepare shared data for agents
                typo = rule_results.typography
                spacing = rule_results.spacing
                sizes_str = ", ".join([f"{s}px" for s in typo.sizes_px[:10]]) if typo.sizes_px else "N/A"
                sp_vals = ", ".join([f"{v}px" for v in spacing.current_values[:10]]) if spacing.current_values else "N/A"
                color_count = rule_results.color_stats.unique_count
                brand_info_str = ""

                # Radius/shadow formatted strings for ATLAS
                from agents.llm_agents import _fmt_radius, _fmt_shadows
                radius_str = _fmt_radius(desktop_dict.get("radius", {}))
                shadow_str = _fmt_shadows(desktop_dict.get("shadows", {}))

                # ─── AURORA: ALL token types ───
                async def _run_aurora():
                    try:
                        return await brand_agent.analyze(
                            color_tokens=desktop_dict.get("colors", {}),
                            typography_tokens=desktop_dict.get("typography", {}),
                            spacing_tokens=desktop_dict.get("spacing", {}),
                            radius_tokens=desktop_dict.get("radius", {}),
                            shadow_tokens=desktop_dict.get("shadows", {}),
                            log_callback=state.log,
                        )
                    except Exception as e:
                        state.log(f"   AURORA failed: {str(e)[:120]}")
                        return BrandIdentification()

                # ─── ATLAS: ALL token types ───
                async def _run_atlas():
                    if not benchmark_comparisons:
                        state.log("   ATLAS skipped (no benchmarks)")
                        return BenchmarkAdvice()
                    try:
                        return await benchmark_agent.analyze(
                            user_ratio=typo.detected_ratio,
                            user_base=int(typo.base_size) if typo.sizes_px else 16,
                            user_spacing=spacing.detected_base,
                            benchmark_comparisons=benchmark_comparisons,
                            color_count=color_count,
                            brand_info=brand_info_str,
                            user_sizes=sizes_str,
                            spacing_values=sp_vals,
                            radius_data=radius_str,
                            shadow_data=shadow_str,
                            log_callback=state.log,
                        )
                    except Exception as e:
                        state.log(f"   ATLAS failed: {str(e)[:120]}")
                        return BenchmarkAdvice()

                # ─── SENTINEL: ALL token types ───
                async def _run_sentinel():
                    try:
                        return await best_practices_agent.analyze(
                            rule_engine_results=rule_results,
                            radius_tokens=desktop_dict.get("radius", {}),
                            shadow_tokens=desktop_dict.get("shadows", {}),
                            log_callback=state.log,
                        )
                    except Exception as e:
                        state.log(f"   SENTINEL failed: {str(e)[:120]}")
                        return BestPracticesResult(overall_score=rule_results.consistency_score)

                # Execute AURORA + ATLAS + SENTINEL in parallel
                import asyncio
                state.log("   Running 3 agents in parallel: AURORA | ATLAS | SENTINEL")
                state.log("")
                brand_result, benchmark_advice, best_practices = await asyncio.gather(
                    _run_aurora(),
                    _run_atlas(),
                    _run_sentinel(),
                )
            else:
                # No HF client - use defaults
                state.log("   Using default values (no LLM)")
                brand_result = BrandIdentification()
                benchmark_advice = BenchmarkAdvice()
                best_practices = BestPracticesResult(overall_score=rule_results.consistency_score)

        except Exception as e:
            state.log(f"   LLM Agents FAILED: {str(e)[:100]}")
            brand_result = BrandIdentification() if not brand_result else brand_result
            benchmark_advice = BenchmarkAdvice() if not benchmark_advice else benchmark_advice
            best_practices = BestPracticesResult(overall_score=rule_results.consistency_score if rule_results else 50)

        progress(0.70, desc="Synthesizing results...")

        # =================================================================
        # LAYER 4: NEXUS — Tree of Thought synthesis
        # =================================================================
        try:
            from agents.llm_agents import HeadSynthesizerAgent, HeadSynthesis, post_validate_stage2

            if hf_client and brand_result and benchmark_advice and best_practices:
                head_agent = HeadSynthesizerAgent(hf_client)

                try:
                    final_synthesis = await head_agent.synthesize(
                        rule_engine_results=rule_results,
                        benchmark_comparisons=benchmark_comparisons,
                        brand_identification=brand_result,
                        benchmark_advice=benchmark_advice,
                        best_practices=best_practices,
                        log_callback=state.log,
                    )
                except Exception as e:
                    state.log(f"   NEXUS failed: {str(e)[:120]}")
                    import traceback
                    state.log(f"   {traceback.format_exc()[:200]}")
                    final_synthesis = None

                # ─── POST-VALIDATION (deterministic) ───
                if final_synthesis:
                    try:
                        pv_issues = post_validate_stage2(
                            aurora=brand_result,
                            sentinel=best_practices,
                            nexus=final_synthesis,
                            rule_engine=rule_results,
                        )
                        if pv_issues:
                            state.log("")
                            state.log(f"   POST-VALIDATION: {len(pv_issues)} issues found")
                            for issue in pv_issues[:10]:
                                state.log(f"      ├─ {issue}")
                            if len(pv_issues) > 10:
                                state.log(f"      └─ ... and {len(pv_issues) - 10} more")
                        else:
                            state.log("   POST-VALIDATION: All checks passed ✅")
                    except Exception as pv_err:
                        state.log(f"   POST-VALIDATION error: {str(pv_err)}")

            # Create fallback synthesis if needed
            if not final_synthesis:
                state.log("   Creating fallback synthesis...")
                final_synthesis = create_fallback_synthesis(
                    rule_results, benchmark_comparisons, brand_result, best_practices
                )

            state.final_synthesis = final_synthesis
            state.brand_result = brand_result  # Preserve AURORA naming_map for export

            # ─── AGENT EVALUATION SUMMARY ───
            state.log("")
            state.log("=" * 60)
            state.log("AGENT EVALUATION SUMMARY")
            state.log("=" * 60)

            def _eval_line(name, emoji, result_obj):
                se = getattr(result_obj, 'self_evaluation', None) or {}
                if isinstance(se, dict) and se:
                    conf = se.get('confidence', '?')
                    dq = se.get('data_quality', '?')
                    flags = se.get('flags', [])
                    flag_str = f", flags={flags}" if flags else ""
                    return f"   {emoji} {name}: confidence={conf}/10, data={dq}{flag_str}"
                return f"   {emoji} {name}: no self-evaluation returned"

            if brand_result:
                named = len(brand_result.naming_map) if brand_result.naming_map else 0
                valid = "PASSED" if brand_result.validation_passed else "FALLBACK"
                state.log(_eval_line("AURORA  (Brand ID)", "", brand_result) + f", named={named}, critic={valid}")
            if benchmark_advice:
                state.log(_eval_line("ATLAS   (Benchmark)", "", benchmark_advice))
            if best_practices:
                bp_score = getattr(best_practices, 'overall_score', '?')
                valid = "PASSED" if best_practices.validation_passed else "FIXED"
                state.log(_eval_line("SENTINEL (Practices)", "", best_practices) + f", score={bp_score}/100, critic={valid}")
            if final_synthesis:
                synth_overall = final_synthesis.scores.get('overall', '?') if final_synthesis.scores else '?'
                chosen = final_synthesis.chosen_perspective or "?"
                state.log(_eval_line("NEXUS   (Synthesis)", "", final_synthesis) + f", overall={synth_overall}/100, perspective={chosen}")

            state.log("=" * 60)
            state.log("")

        except Exception as e:
            state.log(f"   Synthesis FAILED: {str(e)[:100]}")
            final_synthesis = create_fallback_synthesis(
                rule_results, benchmark_comparisons, brand_result, best_practices
            )
            state.final_synthesis = final_synthesis

        progress(0.85, desc="📊 Formatting results...")
        
        # =================================================================
        # FORMAT OUTPUTS FOR UI
        # =================================================================
        
        try:
            # Build status markdown
            status_md = format_stage2_status_v2(
                rule_results=rule_results,
                final_synthesis=final_synthesis,
                best_practices=best_practices,
            )
            
            # Build benchmark comparison HTML
            benchmark_md = format_benchmark_comparison_v2(
                benchmark_comparisons=benchmark_comparisons,
                benchmark_advice=benchmark_advice,
            )
            
            # Build scores dashboard HTML
            scores_html = format_scores_dashboard_v2(
                rule_results=rule_results,
                final_synthesis=final_synthesis,
                best_practices=best_practices,
            )
            
            # Build priority actions HTML
            actions_html = format_priority_actions_v2(
                rule_results=rule_results,
                final_synthesis=final_synthesis,
                best_practices=best_practices,
            )
            
            # Build color recommendations table
            color_recs_table = format_color_recommendations_table_v2(
                rule_results=rule_results,
                brand_result=brand_result,
                final_synthesis=final_synthesis,
            )
            
            # Get fonts and typography data
            fonts = get_detected_fonts()
            base_size = get_base_font_size()

            typography_desktop_data = format_typography_comparison_viewport(
                state.desktop_normalized, base_size, "desktop"
            )
            typography_mobile_data = format_typography_comparison_viewport(
                state.mobile_normalized, base_size, "mobile"
            )

            # Generate spacing comparison table from rule_results
            spacing_data = []
            if rule_results and rule_results.spacing:
                sp = rule_results.spacing
                current_vals = sp.current_values or []
                suggested_8 = [i * 8 for i in range(1, 11)]
                suggested_4 = [i * 4 for i in range(1, 11)]
                for i in range(min(10, max(len(current_vals), 10))):
                    cur = f"{current_vals[i]}px" if i < len(current_vals) else "—"
                    g8 = f"{suggested_8[i]}px" if i < len(suggested_8) else "—"
                    g4 = f"{suggested_4[i]}px" if i < len(suggested_4) else "—"
                    spacing_data.append([cur, g8, g4])

            # Generate base colors, color ramps, radius, shadows markdown
            base_colors_md = format_base_colors()
            color_ramps_md = ""  # Visual ramps are in color_ramps_preview_html
            try:
                from core.preview_generator import generate_color_ramp
                colors = list(state.desktop_normalized.colors.values())
                colors.sort(key=lambda c: -c.frequency)
                ramp_lines = ["### 🌈 Color Ramps (Top Colors)", ""]
                for c in colors[:6]:
                    ramp = generate_color_ramp(c.value)
                    if ramp:
                        shades_str = " → ".join(f"`{s['hex']}`" for s in ramp[::2])  # every other shade
                        ramp_lines.append(f"**{c.value}** ({c.frequency}x): {shades_str}")
                        ramp_lines.append("")
                color_ramps_md = "\n".join(ramp_lines)
            except Exception:
                color_ramps_md = "*Color ramps shown in visual preview above*"

            radius_md = format_radius_with_tokens()
            shadows_md = format_shadows_with_tokens()
            
            # Generate visual previews
            typography_preview_html = ""
            color_ramps_preview_html = ""
            llm_recs_html = ""

            try:
                from core.preview_generator import (
                    generate_typography_preview_html,
                    generate_semantic_color_ramps_html,
                    generate_color_ramps_preview_html,
                )

                primary_font = fonts.get("primary", "Open Sans")
                desktop_typo_dict = {
                    name: {
                        "font_size": t.font_size,
                        "font_weight": t.font_weight,
                        "line_height": t.line_height,
                    }
                    for name, t in state.desktop_normalized.typography.items()
                }
                typography_preview_html = generate_typography_preview_html(desktop_typo_dict, primary_font)

                # Generate color ramps preview (semantic groups)
                semantic_analysis = getattr(state, 'semantic_analysis', {})
                desktop_dict_for_colors = normalized_to_dict(state.desktop_normalized)

                if semantic_analysis:
                    color_ramps_preview_html = generate_semantic_color_ramps_html(
                        semantic_analysis=semantic_analysis,
                        color_tokens=desktop_dict_for_colors.get("colors", {}),
                    )
                else:
                    color_ramps_preview_html = generate_color_ramps_preview_html(
                        color_tokens=desktop_dict_for_colors.get("colors", {}),
                    )

                state.log("   ✅ Color ramps preview generated")

            except Exception as preview_err:
                state.log(f"   ⚠️ Preview generation failed: {str(preview_err)[:80]}")
                typography_preview_html = typography_preview_html or "<div class='placeholder-msg'>Preview unavailable</div>"
                color_ramps_preview_html = "<div class='placeholder-msg'>Color ramps preview unavailable</div>"

            # Generate LLM recommendations HTML
            try:
                # Build recs dict in the format expected by the HTML formatter
                synth_recs = {}
                if final_synthesis:
                    # Convert list of color recs to dict keyed by role
                    # HeadSynthesis uses: {role, current, suggested, reason, accept}
                    # Formatter expects: {current, suggested, action, rationale}
                    color_recs_dict = {}
                    for rec in (final_synthesis.color_recommendations or []):
                        if isinstance(rec, dict) and rec.get("role"):
                            current_val = rec.get("current", "?")
                            suggested_val = rec.get("suggested", current_val)
                            accept = rec.get("accept", True)
                            reason = rec.get("reason", "")
                            # Determine action: if suggested differs from current, it's a change
                            if suggested_val and suggested_val != current_val and not accept:
                                action = "change"
                            elif suggested_val and suggested_val != current_val:
                                action = "change"
                            else:
                                action = "keep"
                            color_recs_dict[rec["role"]] = {
                                "current": current_val,
                                "suggested": suggested_val,
                                "action": action,
                                "rationale": reason,
                            }
                    synth_recs["color_recommendations"] = color_recs_dict

                    # Add AA fixes from rule engine
                    # Formatter expects: {color, role, issue, fix, current_contrast, fixed_contrast}
                    aa_fixes = []
                    if rule_results and rule_results.accessibility:
                        for a in rule_results.accessibility:
                            if not a.passes_aa_normal:
                                best_contrast = a.contrast_on_white if a.best_text_color == "#FFFFFF" else a.contrast_on_black
                                aa_fixes.append({
                                    "color": a.hex_color,
                                    "role": a.name or "unknown",
                                    "issue": f"Fails AA normal ({best_contrast:.1f}:1 < 4.5:1)",
                                    "fix": a.suggested_fix or a.hex_color,
                                    "current_contrast": f"{best_contrast:.1f}",
                                    "fixed_contrast": f"{a.suggested_fix_contrast:.1f}" if a.suggested_fix_contrast else "—",
                                })
                    synth_recs["accessibility_fixes"] = aa_fixes

                llm_recs_html = format_llm_color_recommendations_html(
                    final_recs=synth_recs,
                    semantic_analysis=getattr(state, 'semantic_analysis', {}),
                )
            except Exception as recs_err:
                state.log(f"   ⚠️ LLM recs HTML failed: {str(recs_err)[:120]}")
                import traceback
                state.log(f"   └─ {traceback.format_exc()[:200]}")
                llm_recs_html = "<div class='placeholder-msg'>LLM recommendations unavailable</div>"

            # Store upgrade_recommendations for Apply Upgrades button
            aa_failures_list = []
            if rule_results and rule_results.accessibility:
                aa_failures_list = [
                    a.to_dict() for a in rule_results.accessibility
                    if not a.passes_aa_normal
                ]
            state.upgrade_recommendations = {
                "color_recommendations": (final_synthesis.color_recommendations if final_synthesis else []),
                "accessibility_fixes": aa_failures_list,
                "scores": (final_synthesis.scores if final_synthesis else {}),
                "top_3_actions": (final_synthesis.top_3_actions if final_synthesis else []),
            }

        except Exception as format_err:
            state.log(f"   ⚠️ Formatting failed: {str(format_err)[:100]}")
            import traceback
            state.log(traceback.format_exc()[:500])
            # Return minimal results (must match 18 outputs)
            return (
                f"⚠️ Analysis completed with formatting errors: {str(format_err)[:50]}",
                state.get_logs(),
                "",  # benchmark_html
                "<div class='placeholder-msg'>Scores unavailable</div>",
                "<div class='placeholder-msg'>Actions unavailable</div>",
                [],
                None,
                None,
                "<div class='placeholder-msg'>Typography preview unavailable</div>",
                "<div class='placeholder-msg'>Color ramps preview unavailable</div>",
                "<div class='placeholder-msg'>LLM recommendations unavailable</div>",
                [],  # spacing_data
                "*Formatting error - base colors unavailable*",  # base_colors_md
                "*Formatting error - color ramps unavailable*",  # color_ramps_md
                "*Formatting error - radius tokens unavailable*",  # radius_md
                "*Formatting error - shadow tokens unavailable*",  # shadows_md
                "⚠️ Color preview unavailable due to formatting errors.",  # auto_color_preview
                "",  # asis_tobe_html
            )
        
        # Auto-generate color classification preview
        auto_color_preview = ""
        try:
            auto_color_preview = preview_color_classification("semantic")
            state.log("   ✅ Color classification preview auto-generated (semantic convention)")
        except Exception as cp_err:
            state.log(f"   ⚠️ Auto color preview failed: {str(cp_err)}")
            auto_color_preview = "⚠️ Color preview unavailable — click 'Preview Color Names' button to generate."

        # Build As-Is → To-Be transformation summary
        asis_tobe_html = ""
        try:
            cards = []
            # Type Scale
            detected_ratio = f"{rule_results.typography.detected_ratio:.2f}" if rule_results else "?"
            rec_ratio = "1.25"
            rec_name = "Major Third"
            if final_synthesis and final_synthesis.type_scale_recommendation:
                rec_ratio = str(final_synthesis.type_scale_recommendation.get("recommended_ratio", "1.25"))
                rec_name = final_synthesis.type_scale_recommendation.get("name", "Major Third")
            cards.append(_render_as_is_to_be(
                "Type Scale", detected_ratio,
                f"{rule_results.typography.scale_name if rule_results else '?'} • Variance: {rule_results.typography.variance:.2f}" if rule_results else "",
                rec_ratio, rec_name, icon="📐"
            ))
            # Spacing
            detected_base = f"{rule_results.spacing.detected_base}px" if rule_results else "?"
            alignment = f"{rule_results.spacing.alignment_percentage:.0f}% aligned" if rule_results else ""
            cards.append(_render_as_is_to_be(
                "Spacing Grid", detected_base, alignment,
                "8px", "Industry standard (Material, Tailwind)", icon="📏"
            ))
            # Colors
            color_count = str(rule_results.color_stats.unique_count) if rule_results else "?"
            aa_fails = rule_results.aa_failures if rule_results else 0
            cards.append(_render_as_is_to_be(
                "Colors", f"{color_count} unique",
                f"{aa_fails} fail AA compliance" if aa_fails else "All pass AA",
                f"~15 semantic" if int(color_count) > 20 else color_count,
                "0 AA failures" if aa_fails else "All pass ✓", icon="🎨"
            ))
            # Shadows
            shadow_count = 0
            if state.desktop_normalized:
                shadow_count = len(getattr(state.desktop_normalized, 'shadows', {}))
            tobe_shadow_count = max(shadow_count, 5) if shadow_count > 0 else 0  # Always 5 levels (interpolated)
            cards.append(_render_as_is_to_be(
                "Shadows", f"{shadow_count} extracted",
                "Elevation tokens" if shadow_count > 0 else "No shadows found",
                f"{tobe_shadow_count} levels",
                "xs → sm → md → lg → xl" + (f" (interpolated from {shadow_count})" if shadow_count < 5 else ""),
                icon="🌫️"
            ))
            asis_tobe_html = "".join(cards)
        except Exception:
            asis_tobe_html = ""

        progress(0.95, desc="✅ Complete!")

        # Final log summary
        state.log("")
        state.log("═" * 60)
        state.log("📊 FINAL RESULTS")
        state.log("═" * 60)
        state.log("")
        overall_score = final_synthesis.scores.get('overall', rule_results.consistency_score) if final_synthesis else rule_results.consistency_score
        state.log(f"   🎯 OVERALL SCORE: {overall_score}/100")
        if final_synthesis and final_synthesis.scores:
            state.log(f"   ├─ Accessibility:  {final_synthesis.scores.get('accessibility', '?')}/100")
            state.log(f"   ├─ Consistency:    {final_synthesis.scores.get('consistency', '?')}/100")
            state.log(f"   └─ Organization:   {final_synthesis.scores.get('organization', '?')}/100")
        state.log("")
        if benchmark_comparisons:
            state.log(f"   🏆 Closest Benchmark: {benchmark_comparisons[0].benchmark.name if benchmark_comparisons else 'N/A'}")
        state.log("")
        state.log("   🎯 TOP 3 ACTIONS:")
        if final_synthesis and final_synthesis.top_3_actions:
            for i, action in enumerate(final_synthesis.top_3_actions[:3]):
                impact = action.get('impact', 'medium')
                icon = "🔴" if impact == "high" else "🟡" if impact == "medium" else "🟢"
                state.log(f"   │  {i+1}. {icon} {action.get('action', 'N/A')}")
        else:
            state.log(f"   │  1. 🔴 Fix {rule_results.aa_failures} AA compliance failures")
        state.log("")
        state.log("═" * 60)
        state.log(f"   💰 TOTAL COST: ~$0.003")
        state.log(f"   ⏱️  COMPLETED: {datetime.now().strftime('%H:%M:%S')}")
        state.log("═" * 60)

        return (
            status_md,
            state.get_logs(),
            benchmark_md,
            scores_html,
            actions_html,
            color_recs_table,
            typography_desktop_data,
            typography_mobile_data,
            typography_preview_html,
            color_ramps_preview_html,
            llm_recs_html,
            spacing_data,
            base_colors_md,
            color_ramps_md,
            radius_md,
            shadows_md,
            auto_color_preview,
            asis_tobe_html,
        )

    except Exception as e:
        import traceback
        state.log(f"❌ Critical Error: {str(e)}")
        state.log(traceback.format_exc())
        error_detail = str(e).lower()
        if "token" in error_detail or "auth" in error_detail or "401" in error_detail:
            hint = "Your HuggingFace token may be invalid or expired. Go to **Configuration** above and re-enter your token."
        elif "rate" in error_detail or "429" in error_detail:
            hint = "Rate limit reached. Wait a few minutes and try again."
        else:
            hint = "Check the analysis log above for details. Try running the analysis again."
        return create_stage2_error_response(
            error_message("Analysis Failed", str(e)[:200], hint)
        )


def create_fallback_synthesis(rule_results, benchmark_comparisons, brand_result, best_practices):
    """Create a fallback synthesis when LLM synthesis fails.

    v3: includes radius_recommendation, shadow_recommendation, perspective fields.
    """
    try:
        from agents.llm_agents import HeadSynthesis
    except ImportError:
        from dataclasses import dataclass, field
        @dataclass
        class HeadSynthesis:
            executive_summary: str = ""
            scores: dict = field(default_factory=dict)
            benchmark_fit: dict = field(default_factory=dict)
            brand_analysis: dict = field(default_factory=dict)
            top_3_actions: list = field(default_factory=list)
            color_recommendations: list = field(default_factory=list)
            type_scale_recommendation: dict = field(default_factory=dict)
            spacing_recommendation: dict = field(default_factory=dict)
            radius_recommendation: dict = field(default_factory=dict)
            shadow_recommendation: dict = field(default_factory=dict)
            self_evaluation: dict = field(default_factory=dict)
            perspective_a: dict = field(default_factory=dict)
            perspective_b: dict = field(default_factory=dict)
            chosen_perspective: str = ""
            choice_reasoning: str = ""
            reasoning_trace: list = field(default_factory=list)
            def to_dict(self):
                return {k: getattr(self, k) for k in [
                    'executive_summary', 'scores', 'benchmark_fit', 'brand_analysis',
                    'top_3_actions', 'color_recommendations', 'type_scale_recommendation',
                    'spacing_recommendation', 'radius_recommendation', 'shadow_recommendation',
                    'self_evaluation', 'chosen_perspective', 'choice_reasoning',
                ]}

    # Calculate scores from rule engine
    overall = rule_results.consistency_score if rule_results else 50
    accessibility = max(0, 100 - (rule_results.aa_failures * 10)) if rule_results else 50

    # Build actions from rule engine
    actions = []
    if rule_results and rule_results.aa_failures > 0:
        actions.append({
            "action": f"Fix {rule_results.aa_failures} colors failing AA compliance",
            "impact": "high",
            "token_type": "color",
        })
    if rule_results and not rule_results.typography.is_consistent:
        actions.append({
            "action": f"Align type scale to {rule_results.typography.recommendation} ({rule_results.typography.recommendation_name})",
            "impact": "medium",
            "token_type": "typography",
        })
    if rule_results and rule_results.color_stats.unique_count > 30:
        actions.append({
            "action": f"Consolidate {rule_results.color_stats.unique_count} colors to ~15 semantic colors",
            "impact": "medium",
            "token_type": "color",
        })

    return HeadSynthesis(
        executive_summary=f"Your design system scores {overall}/100. Analysis completed with fallback synthesis.",
        scores={
            "overall": overall,
            "accessibility": accessibility,
            "consistency": overall,
            "organization": 50,
        },
        benchmark_fit={
            "closest": benchmark_comparisons[0].benchmark.name if benchmark_comparisons else "Unknown",
            "similarity": f"{benchmark_comparisons[0].overall_match_pct:.0f}%" if benchmark_comparisons else "N/A",
        },
        brand_analysis={
            "primary": brand_result.brand_primary.get("color", "Unknown") if brand_result else "Unknown",
            "cohesion": brand_result.cohesion_score if brand_result else 5,
        },
        top_3_actions=actions[:3],
        color_recommendations=[],
        type_scale_recommendation={
            "current_ratio": rule_results.typography.detected_ratio if rule_results else 1.0,
            "recommended_ratio": rule_results.typography.recommendation if rule_results else 1.25,
        },
        spacing_recommendation={
            "current": f"{rule_results.spacing.detected_base}px" if rule_results else "Unknown",
            "recommended": f"{rule_results.spacing.recommendation}px" if rule_results else "8px",
        },
        radius_recommendation={},
        shadow_recommendation={},
    )


def create_stage2_error_response(error_msg: str):
    """Create error response tuple for Stage 2 (must match 18 outputs)."""
    return (
        error_msg,
        state.get_logs(),
        "",  # benchmark_html
        f"<div class='placeholder-msg'>{error_msg}</div>",  # scores_html
        "",  # actions_html
        [],  # color_recs_table
        None,  # typography_desktop
        None,  # typography_mobile
        "",  # typography_preview
        "",  # color_ramps_preview
        "",  # llm_recs_html
        [],  # spacing_data
        "*Run analysis to see base colors*",  # base_colors_md
        "*Run analysis to see color ramps*",  # color_ramps_md
        "*Run analysis to see radius tokens*",  # radius_md
        "*Run analysis to see shadow tokens*",  # shadows_md
        "",  # auto_color_preview
        "",  # asis_tobe_html
    )


def format_stage2_status_v2(rule_results, final_synthesis, best_practices) -> str:
    """Format Stage 2 status with new architecture results."""
    
    lines = []
    lines.append("## ✅ Analysis Complete!")
    lines.append("")
    
    # Overall Score
    overall = final_synthesis.scores.get('overall', rule_results.consistency_score)
    lines.append(f"### 🎯 Overall Score: {overall}/100")
    lines.append("")
    
    # Executive Summary
    if final_synthesis.executive_summary:
        lines.append(f"*{final_synthesis.executive_summary}*")
        lines.append("")
    
    # Quick Stats
    lines.append("### 📊 Quick Stats")
    lines.append(f"- **AA Failures:** {rule_results.aa_failures}")
    lines.append(f"- **Type Scale:** {rule_results.typography.detected_ratio:.3f} ({rule_results.typography.scale_name})")
    lines.append(f"- **Spacing Grid:** {rule_results.spacing.detected_base}px ({rule_results.spacing.alignment_percentage:.0f}% aligned)")
    lines.append(f"- **Unique Colors:** {rule_results.color_stats.unique_count}")
    lines.append("")
    
    # Cost
    lines.append("### 💰 Cost")
    lines.append("**Total:** ~$0.003 (Rule Engine: $0 + LLM: ~$0.003)")
    lines.append("")

    # Next step guidance
    lines.append("---")
    lines.append("**Next:** Review the analysis results below. Accept or reject color recommendations, "
                 "choose your type scale and spacing grid, then click **'Apply Selected Upgrades'** at the bottom.")

    return "\n".join(lines)


def format_benchmark_comparison_v2(benchmark_comparisons, benchmark_advice) -> str:
    """Format benchmark comparison as visual HTML cards with progress bars."""
    return _render_benchmark_cards(benchmark_comparisons, benchmark_advice)


def format_scores_dashboard_v2(rule_results, final_synthesis, best_practices) -> str:
    """Format scores dashboard HTML."""
    
    overall = final_synthesis.scores.get('overall', rule_results.consistency_score)
    accessibility = final_synthesis.scores.get('accessibility', 100 - (rule_results.aa_failures * 5))
    consistency = final_synthesis.scores.get('consistency', rule_results.consistency_score)
    organization = final_synthesis.scores.get('organization', 50)
    
    def score_color(score):
        if score >= 80:
            return "#10b981"  # Green
        elif score >= 60:
            return "#f59e0b"  # Yellow
        else:
            return "#ef4444"  # Red
    
    html = f"""
    <style>
        .scores-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
        .score-card {{ border-radius: 12px; padding: 20px; text-align: center; }}
        .score-card-secondary {{ background: #f8fafc; border: 1px solid #e2e8f0; }}
        .score-card .score-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
        .dark .score-card-secondary {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .score-card .score-label {{ color: #94a3b8 !important; }}
    </style>
    <div class="scores-grid">
        <div class="score-card" style="background: linear-gradient(135deg, {score_color(overall)}22 0%, {score_color(overall)}11 100%);
                    border: 2px solid {score_color(overall)};">
            <div style="font-size: 32px; font-weight: 700; color: {score_color(overall)};">{overall}</div>
            <div class="score-label">OVERALL</div>
        </div>
        <div class="score-card score-card-secondary">
            <div style="font-size: 24px; font-weight: 600; color: {score_color(accessibility)};">{accessibility}</div>
            <div class="score-label">Accessibility</div>
        </div>
        <div class="score-card score-card-secondary">
            <div style="font-size: 24px; font-weight: 600; color: {score_color(consistency)};">{consistency}</div>
            <div class="score-label">Consistency</div>
        </div>
        <div class="score-card score-card-secondary">
            <div style="font-size: 24px; font-weight: 600; color: {score_color(organization)};">{organization}</div>
            <div class="score-label">Organization</div>
        </div>
    </div>
    """
    
    return html


def format_priority_actions_v2(rule_results, final_synthesis, best_practices) -> str:
    """Format priority actions HTML."""
    
    actions = final_synthesis.top_3_actions if final_synthesis.top_3_actions else []
    
    # If no synthesis actions, build from rule engine
    if not actions and best_practices and best_practices.priority_fixes:
        actions = best_practices.priority_fixes
    
    if not actions:
        # Default actions from rule engine
        actions = []
        if rule_results.aa_failures > 0:
            actions.append({
                "action": f"Fix {rule_results.aa_failures} colors failing AA compliance",
                "impact": "high",
                "effort": "30 min",
            })
        if not rule_results.typography.is_consistent:
            actions.append({
                "action": f"Align type scale to {rule_results.typography.recommendation} ({rule_results.typography.recommendation_name})",
                "impact": "medium", 
                "effort": "1 hour",
            })
        if rule_results.color_stats.unique_count > 30:
            actions.append({
                "action": f"Consolidate {rule_results.color_stats.unique_count} colors to ~15 semantic colors",
                "impact": "medium",
                "effort": "2 hours",
            })
    
    html_items = []
    for i, action in enumerate(actions[:3]):
        impact = action.get('impact', 'medium')
        border_color = "#ef4444" if impact == "high" else "#f59e0b" if impact == "medium" else "#10b981"
        impact_bg = "#fee2e2" if impact == "high" else "#fef3c7" if impact == "medium" else "#dcfce7"
        impact_text = "#991b1b" if impact == "high" else "#92400e" if impact == "medium" else "#166534"
        icon = "🔴" if impact == "high" else "🟡" if impact == "medium" else "🟢"
        
        html_items.append(f"""
        <div class="priority-action-card" style="border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="priority-action-title">
                        {icon} {action.get('action', 'N/A')}
                    </div>
                    <div class="priority-action-detail">
                        {action.get('details', '')}
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span style="background: {impact_bg}; color: {impact_text}; padding: 4px 8px;
                                 border-radius: 12px; font-size: 11px; font-weight: 600;">
                        {impact.upper()}
                    </span>
                    <span class="priority-effort-badge">
                        {action.get('effort', '?')}
                    </span>
                </div>
            </div>
        </div>
        """)
    
    return f"""
    <style>
        .priority-actions-wrap {{ margin: 20px 0; }}
        .priority-actions-wrap h3 {{ margin-bottom: 16px; color: #1e293b; }}
        .priority-action-card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
        .priority-action-title {{ font-weight: 600; color: #1e293b; margin-bottom: 4px; }}
        .priority-action-detail {{ font-size: 13px; color: #64748b; }}
        .priority-effort-badge {{ background: #f1f5f9; color: #475569; padding: 4px 8px; border-radius: 12px; font-size: 11px; }}
        .dark .priority-actions-wrap h3 {{ color: #f1f5f9 !important; }}
        .dark .priority-action-card {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .priority-action-title {{ color: #f1f5f9 !important; }}
        .dark .priority-action-detail {{ color: #94a3b8 !important; }}
        .dark .priority-effort-badge {{ background: #334155 !important; color: #cbd5e1 !important; }}
    </style>
    <div class="priority-actions-wrap">
        <h3>🎯 Priority Actions</h3>
        {''.join(html_items)}
    </div>
    """


def format_color_recommendations_table_v2(rule_results, brand_result, final_synthesis) -> list:
    """Format color recommendations as table data."""
    
    rows = []
    
    # Add AA failures with fixes
    for a in rule_results.accessibility:
        if not a.passes_aa_normal and a.suggested_fix:
            role = "brand.primary" if brand_result and brand_result.brand_primary.get("color") == a.hex_color else a.name
            rows.append([
                True,  # Accept checkbox
                role,
                a.hex_color,
                f"Fails AA ({a.contrast_on_white:.1f}:1)",
                a.suggested_fix,
                f"{a.suggested_fix_contrast:.1f}:1",
            ])
    
    # Add recommendations from synthesis
    if final_synthesis and final_synthesis.color_recommendations:
        for rec in final_synthesis.color_recommendations:
            if rec.get("current") != rec.get("suggested"):
                # Check if not already in rows
                if not any(r[2] == rec.get("current") for r in rows):
                    rows.append([
                        rec.get("accept", True),
                        rec.get("role", "unknown"),
                        rec.get("current", ""),
                        rec.get("reason", ""),
                        rec.get("suggested", ""),
                        "",
                    ])
    
    return rows


def build_analysis_status(final_recs: dict, cost_tracking: dict, errors: list) -> str:
    """Build status markdown from analysis results."""
    
    lines = ["## 🧠 Multi-Agent Analysis Complete!"]
    lines.append("")
    
    # Cost summary
    if cost_tracking:
        total_cost = cost_tracking.get("total_cost", 0)
        lines.append(f"### 💰 Cost Summary")
        lines.append(f"**Total estimated cost:** ${total_cost:.4f}")
        lines.append(f"*(Free tier: $0.10/mo | Pro: $2.00/mo)*")
        lines.append("")
    
    # Final recommendations
    if final_recs and "final_recommendations" in final_recs:
        recs = final_recs["final_recommendations"]
        lines.append("### 📋 Recommendations")
        
        if recs.get("type_scale"):
            lines.append(f"**Type Scale:** {recs['type_scale']}")
            if recs.get("type_scale_rationale"):
                lines.append(f"  *{recs['type_scale_rationale'][:100]}*")
        
        if recs.get("spacing_base"):
            lines.append(f"**Spacing:** {recs['spacing_base']}")
        
        lines.append("")
    
    # Summary
    if final_recs.get("summary"):
        lines.append("### 📝 Summary")
        lines.append(final_recs["summary"])
        lines.append("")
    
    # Confidence
    if final_recs.get("overall_confidence"):
        lines.append(f"**Confidence:** {final_recs['overall_confidence']}%")
    
    # Errors
    if errors:
        lines.append("")
        lines.append("### ⚠️ Warnings")
        for err in errors[:3]:
            lines.append(f"- {err[:100]}")
    
    return "\n".join(lines)


def format_multi_agent_comparison(llm1: dict, llm2: dict, final: dict) -> str:
    """Format comparison from multi-agent analysis."""
    
    lines = ["### 📊 Multi-Agent Analysis Comparison"]
    lines.append("")
    
    # Agreements
    if final.get("agreements"):
        lines.append("#### ✅ Agreements (High Confidence)")
        for a in final["agreements"][:5]:
            topic = a.get("topic", "?")
            finding = a.get("finding", "?")[:80]
            lines.append(f"- **{topic}**: {finding}")
        lines.append("")
    
    # Disagreements and resolutions
    if final.get("disagreements"):
        lines.append("#### 🔄 Resolved Disagreements")
        for d in final["disagreements"][:3]:
            topic = d.get("topic", "?")
            resolution = d.get("resolution", "?")[:100]
            lines.append(f"- **{topic}**: {resolution}")
        lines.append("")
    
    # Score comparison
    lines.append("#### 📈 Score Comparison")
    lines.append("")
    lines.append("| Category | LLM 1 (Qwen) | LLM 2 (Llama) |")
    lines.append("|----------|--------------|---------------|")
    
    categories = ["typography", "colors", "accessibility", "spacing"]
    for cat in categories:
        llm1_score = llm1.get(cat, {}).get("score", "?") if isinstance(llm1.get(cat), dict) else "?"
        llm2_score = llm2.get(cat, {}).get("score", "?") if isinstance(llm2.get(cat), dict) else "?"
        lines.append(f"| {cat.title()} | {llm1_score}/10 | {llm2_score}/10 |")
    
    return "\n".join(lines)


def format_spacing_comparison_from_rules(rule_calculations: dict) -> list:
    """Format spacing comparison from rule engine."""
    if not rule_calculations:
        return []
    
    spacing_options = rule_calculations.get("spacing_options", {})
    
    data = []
    for i in range(10):
        current = f"{(i+1) * 4}px" if i < 5 else f"{(i+1) * 8}px"
        grid_8 = spacing_options.get("8px", [])
        grid_4 = spacing_options.get("4px", [])
        
        val_8 = f"{grid_8[i+1]}px" if i+1 < len(grid_8) else "—"
        val_4 = f"{grid_4[i+1]}px" if i+1 < len(grid_4) else "—"
        
        data.append([current, val_8, val_4])
    
    return data


def format_color_ramps_from_rules(rule_calculations: dict) -> str:
    """Format color ramps from rule engine."""
    if not rule_calculations:
        return "*No color ramps generated*"
    
    ramps = rule_calculations.get("color_ramps", {})
    if not ramps:
        return "*No color ramps generated*"
    
    lines = ["### 🌈 Generated Color Ramps"]
    lines.append("")
    
    for name, ramp in list(ramps.items())[:6]:
        lines.append(f"**{name}**")
        if isinstance(ramp, list) and len(ramp) >= 10:
            lines.append("| 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|")
            row = "| " + " | ".join([f"`{ramp[i]}`" for i in range(10)]) + " |"
            lines.append(row)
        lines.append("")
    
    return "\n".join(lines)


def get_detected_fonts() -> dict:
    """Get detected font information."""
    if not state.desktop_normalized:
        return {"primary": "Unknown", "weights": []}
    
    fonts = {}
    weights = set()
    
    for t in state.desktop_normalized.typography.values():
        family = t.font_family
        weight = t.font_weight
        
        if family not in fonts:
            fonts[family] = 0
        fonts[family] += t.frequency
        
        if weight:
            try:
                weights.add(int(weight))
            except (ValueError, TypeError):
                pass
    
    primary = max(fonts.items(), key=lambda x: x[1])[0] if fonts else "Unknown"
    
    return {
        "primary": primary,
        "weights": sorted(weights) if weights else [400],
        "all_fonts": fonts,
    }


def get_base_font_size() -> int:
    """Detect base font size from typography."""
    if not state.desktop_normalized:
        return 16
    
    # Find most common size in body range (14-18px)
    sizes = {}
    for t in state.desktop_normalized.typography.values():
        size_str = str(t.font_size).replace('px', '').replace('rem', '').replace('em', '')
        try:
            size = float(size_str)
            if 14 <= size <= 18:
                sizes[size] = sizes.get(size, 0) + t.frequency
        except (ValueError, TypeError):
            pass
    
    if sizes:
        return int(max(sizes.items(), key=lambda x: x[1])[0])
    return 16


def format_brand_comparison(recommendations) -> str:
    """Format brand comparison as markdown table."""
    if not recommendations.brand_analysis:
        return "*Brand analysis not available*"
    
    lines = [
        "### 📊 Design System Comparison (5 Top Brands)",
        "",
        "| Brand | Type Ratio | Base Size | Spacing | Notes |",
        "|-------|------------|-----------|---------|-------|",
    ]
    
    for brand in recommendations.brand_analysis[:5]:
        name = brand.get("brand", "Unknown")
        ratio = brand.get("ratio", "?")
        base = brand.get("base", "?")
        spacing = brand.get("spacing", "?")
        notes = brand.get("notes", "")[:50] + ("..." if len(brand.get("notes", "")) > 50 else "")
        lines.append(f"| {name} | {ratio} | {base}px | {spacing} | {notes} |")
    
    return "\n".join(lines)


def format_font_families_display(fonts: dict) -> str:
    """Format detected font families for display."""
    lines = []
    
    primary = fonts.get("primary", "Unknown")
    weights = fonts.get("weights", [400])
    all_fonts = fonts.get("all_fonts", {})
    
    lines.append(f"### Primary Font: **{primary}**")
    lines.append("")
    lines.append(f"**Weights detected:** {', '.join(map(str, weights))}")
    lines.append("")
    
    if all_fonts and len(all_fonts) > 1:
        lines.append("### All Fonts Detected")
        lines.append("")
        lines.append("| Font Family | Usage Count |")
        lines.append("|-------------|-------------|")
        
        sorted_fonts = sorted(all_fonts.items(), key=lambda x: -x[1])
        for font, count in sorted_fonts[:5]:
            lines.append(f"| {font} | {count:,} |")
    
    lines.append("")
    lines.append("*Note: This analysis focuses on English typography only.*")
    
    return "\n".join(lines)


def format_llm_color_recommendations_html(final_recs: dict, semantic_analysis: dict) -> str:
    """Generate HTML showing LLM color recommendations with before/after comparison."""
    
    if not final_recs:
        return '''
        <div class="placeholder-msg" style="text-align: center;">
            <p>No LLM recommendations available yet. Run analysis first.</p>
        </div>
        '''
    
    color_recs = final_recs.get("color_recommendations", {})
    aa_fixes = final_recs.get("accessibility_fixes", [])
    
    if not color_recs and not aa_fixes:
        return '''
        <div class="llm-no-recs" style="padding: 20px; border-radius: 8px; border: 1px solid #28a745; background: #d4edda;">
            <p style="margin: 0; color: #155724;">✅ No color changes recommended. Your colors look good!</p>
        </div>
        <style>
            .dark .llm-no-recs { background: #14532d !important; border-color: #22c55e !important; }
            .dark .llm-no-recs p { color: #86efac !important; }
        </style>
        '''
    
    # Build recommendations HTML
    recs_html = ""
    
    # Process color recommendations
    for role, rec in color_recs.items():
        if not isinstance(rec, dict):
            continue
        if role in ["generate_ramps_for", "changes_made"]:
            continue
            
        current = rec.get("current", "?")
        suggested = rec.get("suggested", current)
        action = rec.get("action", "keep")
        rationale = rec.get("rationale", "")
        
        if action == "keep" or suggested == current:
            # No change needed
            recs_html += f'''
            <div class="llm-rec-row keep">
                <div class="rec-color-box" style="background: {current};"></div>
                <div class="rec-details">
                    <span class="rec-role">{role}</span>
                    <span class="rec-current">{current}</span>
                    <span class="rec-action keep">✓ Keep</span>
                </div>
            </div>
            '''
        else:
            # Change suggested
            recs_html += f'''
            <div class="llm-rec-row change">
                <div class="rec-comparison">
                    <div class="rec-before">
                        <div class="rec-color-box" style="background: {current};"></div>
                        <span class="rec-label">Before</span>
                        <span class="rec-hex">{current}</span>
                    </div>
                    <span class="rec-arrow">→</span>
                    <div class="rec-after">
                        <div class="rec-color-box" style="background: {suggested};"></div>
                        <span class="rec-label">After</span>
                        <span class="rec-hex">{suggested}</span>
                    </div>
                </div>
                <div class="rec-details">
                    <span class="rec-role">{role}</span>
                    <span class="rec-rationale">{rationale[:80]}...</span>
                </div>
            </div>
            '''
    
    # Process accessibility fixes
    for fix in aa_fixes:
        if not isinstance(fix, dict):
            continue
        
        color = fix.get("color", "?")
        role = fix.get("role", "unknown")
        issue = fix.get("issue", "contrast issue")
        fix_color = fix.get("fix", color)
        current_contrast = fix.get("current_contrast", "?")
        fixed_contrast = fix.get("fixed_contrast", "?")
        
        if fix_color and fix_color != color:
            recs_html += f'''
            <div class="llm-rec-row aa-fix">
                <div class="rec-comparison">
                    <div class="rec-before">
                        <div class="rec-color-box" style="background: {color};"></div>
                        <span class="rec-label">⚠️ {current_contrast}:1</span>
                        <span class="rec-hex">{color}</span>
                    </div>
                    <span class="rec-arrow">→</span>
                    <div class="rec-after">
                        <div class="rec-color-box" style="background: {fix_color};"></div>
                        <span class="rec-label">✓ {fixed_contrast}:1</span>
                        <span class="rec-hex">{fix_color}</span>
                    </div>
                </div>
                <div class="rec-details">
                    <span class="rec-role">{role}</span>
                    <span class="rec-issue">🔴 {issue}</span>
                </div>
            </div>
            '''
    
    if not recs_html:
        return '''
        <div class="llm-no-recs" style="padding: 20px; border-radius: 8px; border: 1px solid #28a745; background: #d4edda;">
            <p style="margin: 0; color: #155724;">✅ No color changes recommended. Your colors look good!</p>
        </div>
        <style>
            .dark .llm-no-recs { background: #14532d !important; border-color: #22c55e !important; }
            .dark .llm-no-recs p { color: #86efac !important; }
        </style>
        '''
    
    html = f'''
    <style>
        .llm-recs-container {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5 !important;
            border-radius: 12px;
            padding: 16px;
        }}
        
        .llm-rec-row {{
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 8px;
            background: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
        }}
        
        .llm-rec-row.change {{
            border-left: 4px solid #f59e0b !important;
        }}
        
        .llm-rec-row.aa-fix {{
            border-left: 4px solid #dc2626 !important;
            background: #fef2f2 !important;
        }}
        
        .llm-rec-row.keep {{
            border-left: 4px solid #22c55e !important;
            background: #f0fdf4 !important;
        }}
        
        .rec-comparison {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-right: 20px;
        }}
        
        .rec-before, .rec-after {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }}
        
        .rec-color-box {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            border: 2px solid rgba(0,0,0,0.15) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .rec-label {{
            font-size: 11px;
            font-weight: 600;
            color: #666 !important;
        }}
        
        .rec-hex {{
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 11px;
            color: #333 !important;
        }}
        
        .rec-arrow {{
            font-size: 20px;
            color: #666 !important;
            font-weight: bold;
        }}
        
        .rec-details {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .rec-role {{
            font-weight: 700;
            font-size: 14px;
            color: #1a1a1a !important;
        }}
        
        .rec-action {{
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        
        .rec-action.keep {{
            background: #dcfce7 !important;
            color: #166534 !important;
        }}
        
        .rec-rationale {{
            font-size: 12px;
            color: #666 !important;
        }}
        
        .rec-issue {{
            font-size: 12px;
            color: #991b1b !important;
            font-weight: 500;
        }}

        /* Dark mode */
        .dark .llm-recs-container {{ background: #0f172a !important; }}
        .dark .llm-rec-row {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .llm-rec-row.aa-fix {{ background: #450a0a !important; }}
        .dark .llm-rec-row.keep {{ background: #14532d !important; }}
        .dark .rec-label {{ color: #94a3b8 !important; }}
        .dark .rec-hex {{ color: #cbd5e1 !important; }}
        .dark .rec-arrow {{ color: #94a3b8 !important; }}
        .dark .rec-role {{ color: #f1f5f9 !important; }}
        .dark .rec-rationale {{ color: #94a3b8 !important; }}
        .dark .rec-issue {{ color: #fca5a5 !important; }}
        .dark .rec-action.keep {{ background: #14532d !important; color: #86efac !important; }}
    </style>
    
    <div class="llm-recs-container">
        {recs_html}
    </div>
    '''
    
    return html


def format_llm_color_recommendations_table(final_recs: dict, semantic_analysis: dict) -> list:
    """Generate table data for LLM color recommendations with accept/reject checkboxes."""
    
    rows = []
    
    if not final_recs:
        return rows
    
    color_recs = final_recs.get("color_recommendations", {})
    aa_fixes = final_recs.get("accessibility_fixes", [])
    
    # Process color recommendations
    for role, rec in color_recs.items():
        if not isinstance(rec, dict):
            continue
        if role in ["generate_ramps_for", "changes_made"]:
            continue
            
        current = rec.get("current", "?")
        suggested = rec.get("suggested", current)
        action = rec.get("action", "keep")
        rationale = rec.get("rationale", "")[:50]
        
        if action != "keep" and suggested != current:
            # Calculate contrast improvement
            try:
                from core.color_utils import get_contrast_with_white
                old_contrast = get_contrast_with_white(current)
                new_contrast = get_contrast_with_white(suggested)
                contrast_str = f"{old_contrast:.1f} → {new_contrast:.1f}"
            except (ValueError, TypeError, ZeroDivisionError):
                contrast_str = "?"
            
            rows.append([
                True,  # Accept checkbox (default True)
                role,
                current,
                rationale or action,
                suggested,
                contrast_str,
            ])
    
    # Process accessibility fixes
    for fix in aa_fixes:
        if not isinstance(fix, dict):
            continue
        
        color = fix.get("color", "?")
        role = fix.get("role", "unknown")
        issue = fix.get("issue", "contrast")[:40]
        fix_color = fix.get("fix", color)
        current_contrast = fix.get("current_contrast", "?")
        fixed_contrast = fix.get("fixed_contrast", "?")
        
        if fix_color and fix_color != color:
            rows.append([
                True,  # Accept checkbox
                f"{role} (AA fix)",
                color,
                issue,
                fix_color,
                f"{current_contrast}:1 → {fixed_contrast}:1",
            ])
    
    return rows


def format_typography_comparison_viewport(normalized_tokens, base_size: int, viewport: str) -> list:
    """Format typography comparison for a specific viewport."""
    if not normalized_tokens:
        return []
    
    # Get current typography sorted by size
    current_typo = list(normalized_tokens.typography.values())
    
    # Parse and sort sizes
    def parse_size(t):
        size_str = str(t.font_size).replace('px', '').replace('rem', '').replace('em', '')
        try:
            return float(size_str)
        except (ValueError, TypeError):
            return 16
    
    current_typo.sort(key=lambda t: -parse_size(t))
    sizes = [parse_size(t) for t in current_typo]
    
    # Use detected base or default
    base = base_size if base_size else 16
    
    # Scale factors for mobile (typically 0.85-0.9 of desktop)
    mobile_factor = 0.875 if viewport == "mobile" else 1.0
    
    # Token names (13 levels)
    token_names = [
        "display.2xl", "display.xl", "display.lg", "display.md",
        "heading.xl", "heading.lg", "heading.md", "heading.sm",
        "body.lg", "body.md", "body.sm",
        "caption", "overline"
    ]
    
    # Generate scales - use base size and round to sensible values
    def round_to_even(val):
        """Round to even numbers for cleaner type scales."""
        return int(round(val / 2) * 2)
    
    scales = {
        "1.2": [round_to_even(base * mobile_factor * (1.2 ** (8-i))) for i in range(13)],
        "1.25": [round_to_even(base * mobile_factor * (1.25 ** (8-i))) for i in range(13)],
        "1.333": [round_to_even(base * mobile_factor * (1.333 ** (8-i))) for i in range(13)],
    }
    
    # Build comparison table
    data = []
    for i, name in enumerate(token_names):
        current = f"{int(sizes[i])}px" if i < len(sizes) else "—"
        s12 = f"{scales['1.2'][i]}px"
        s125 = f"{scales['1.25'][i]}px"
        s133 = f"{scales['1.333'][i]}px"
        keep = current
        data.append([name, current, s12, s125, s133, keep])
    
    return data


def format_base_colors() -> str:
    """Format base colors (detected) separately from ramps."""
    if not state.desktop_normalized:
        return "*No colors detected*"
    
    colors = list(state.desktop_normalized.colors.values())
    colors.sort(key=lambda c: -c.frequency)
    
    lines = [
        "### 🎨 Base Colors (Detected)",
        "",
        "These are the primary colors extracted from your website:",
        "",
        "| Color | Hex | Role | Frequency | Contrast |",
        "|-------|-----|------|-----------|----------|",
    ]
    
    for color in colors[:10]:
        hex_val = color.value
        role = "Primary" if color.suggested_name and "primary" in color.suggested_name.lower() else \
               "Text" if color.suggested_name and "text" in color.suggested_name.lower() else \
               "Background" if color.suggested_name and "background" in color.suggested_name.lower() else \
               "Border" if color.suggested_name and "border" in color.suggested_name.lower() else \
               "Accent"
        freq = f"{color.frequency:,}"
        contrast = f"{color.contrast_white:.1f}:1" if color.contrast_white else "—"
        
        # Create a simple color indicator
        lines.append(f"| 🟦 | `{hex_val}` | {role} | {freq} | {contrast} |")
    
    return "\n".join(lines)


def format_color_ramps_visual(recommendations) -> str:
    """Format color ramps with visual display showing all shades."""
    if not state.desktop_normalized:
        return "*No colors to display*"
    
    colors = list(state.desktop_normalized.colors.values())
    colors.sort(key=lambda c: -c.frequency)
    
    lines = [
        "### 🌈 Generated Color Ramps",
        "",
        "Full ramp (50-950) generated for each base color:",
        "",
    ]
    
    from core.color_utils import generate_color_ramp
    
    for color in colors[:6]:  # Top 6 colors
        hex_val = color.value
        role = color.suggested_name.split('.')[1] if color.suggested_name and '.' in color.suggested_name else "color"
        
        # Generate ramp
        try:
            ramp = generate_color_ramp(hex_val)
            
            lines.append(f"**{role.upper()}** (base: `{hex_val}`)")
            lines.append("")
            lines.append("| 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|")
            
            # Create row with hex values
            row = "|"
            for i in range(10):
                if i < len(ramp):
                    row += f" `{ramp[i]}` |"
                else:
                    row += " — |"
            lines.append(row)
            lines.append("")
            
        except Exception as e:
            lines.append(f"**{role}** (`{hex_val}`) — Could not generate ramp: {str(e)}")
            lines.append("")
    
    return "\n".join(lines)


def format_radius_with_tokens() -> str:
    """Format radius with token name suggestions."""
    if not state.desktop_normalized or not state.desktop_normalized.radius:
        return "*No border radius values detected.*"
    
    radii = list(state.desktop_normalized.radius.values())
    
    lines = [
        "### 🔘 Border Radius Tokens",
        "",
        "| Detected | Suggested Token | Usage |",
        "|----------|-----------------|-------|",
    ]
    
    # Sort by pixel value
    def parse_radius(r):
        val = str(r.value).replace('px', '').replace('%', '')
        try:
            return float(val)
        except (ValueError, TypeError):
            return 999
    
    radii.sort(key=lambda r: parse_radius(r))
    
    token_map = {
        (0, 2): ("radius.none", "Sharp corners"),
        (2, 4): ("radius.xs", "Subtle rounding"),
        (4, 6): ("radius.sm", "Small elements"),
        (6, 10): ("radius.md", "Buttons, cards"),
        (10, 16): ("radius.lg", "Modals, panels"),
        (16, 32): ("radius.xl", "Large containers"),
        (32, 100): ("radius.2xl", "Pill shapes"),
    }
    
    for r in radii[:8]:
        val = str(r.value)
        px = parse_radius(r)
        
        if "%" in str(r.value) or px >= 50:
            token = "radius.full"
            usage = "Circles, avatars"
        else:
            token = "radius.md"
            usage = "General use"
            for (low, high), (t, u) in token_map.items():
                if low <= px < high:
                    token = t
                    usage = u
                    break
        
        lines.append(f"| {val} | `{token}` | {usage} |")
    
    return "\n".join(lines)


def format_shadows_with_tokens() -> str:
    """Format shadows with token name suggestions."""
    if not state.desktop_normalized or not state.desktop_normalized.shadows:
        return "*No shadow values detected.*"
    
    shadows = list(state.desktop_normalized.shadows.values())
    
    lines = [
        "### 🌫️ Shadow Tokens",
        "",
        "| Detected Value | Suggested Token | Use Case |",
        "|----------------|-----------------|----------|",
    ]
    
    shadow_sizes = ["shadow.xs", "shadow.sm", "shadow.md", "shadow.lg", "shadow.xl", "shadow.2xl"]
    
    for i, s in enumerate(shadows[:6]):
        val = str(s.value)[:40] + ("..." if len(str(s.value)) > 40 else "")
        token = shadow_sizes[i] if i < len(shadow_sizes) else f"shadow.custom-{i}"
        
        # Guess use case based on index
        use_cases = ["Subtle elevation", "Cards, dropdowns", "Modals, dialogs", "Popovers", "Floating elements", "Dramatic effect"]
        use = use_cases[i] if i < len(use_cases) else "Custom"
        
        lines.append(f"| `{val}` | `{token}` | {use} |")
    
    return "\n".join(lines)


def format_spacing_comparison(recommendations) -> list:
    """Format spacing comparison table."""
    if not state.desktop_normalized:
        return []
    
    # Get current spacing
    current_spacing = list(state.desktop_normalized.spacing.values())
    current_spacing.sort(key=lambda s: s.value_px)
    
    data = []
    for s in current_spacing[:10]:
        current = f"{s.value_px}px"
        grid_8 = f"{snap_to_grid(s.value_px, 8)}px"
        grid_4 = f"{snap_to_grid(s.value_px, 4)}px"
        
        # Mark if value fits
        if s.value_px == snap_to_grid(s.value_px, 8):
            grid_8 += " ✓"
        if s.value_px == snap_to_grid(s.value_px, 4):
            grid_4 += " ✓"
        
        data.append([current, grid_8, grid_4])
    
    return data


def snap_to_grid(value: float, base: int) -> int:
    """Snap value to grid."""
    return round(value / base) * base


def reset_to_original():
    """Reset all upgrade selections to defaults."""
    state.selected_upgrades = {}
    state.log("")
    state.log("↩️ Reset all upgrade selections to original values.")

    return (
        "Scale 1.25 (Major Third) ⭐",     # type_scale_radio
        "8px Base Grid ⭐",                  # spacing_radio
        True,                                 # color_ramps_checkbox
        "## ↩️ Reset Complete\n\nAll selections reverted to defaults. Review and apply again when ready.",  # apply_status
        state.get_logs(),                     # stage2_log
    )


def apply_selected_upgrades(type_choice: str, spacing_choice: str, apply_ramps: bool, color_recs_table: list = None):
    """Apply selected upgrade options including LLM color recommendations."""
    if not state.upgrade_recommendations:
        return "## ❌ Run Analysis First\n\nPlease run the **v2 Analysis** before applying upgrades.", state.get_logs()

    state.log("")
    state.log("═" * 50)
    state.log("✨ APPLYING SELECTED UPGRADES")
    state.log("═" * 50)

    # Store selections
    state.selected_upgrades = {
        "type_scale": type_choice,
        "spacing": spacing_choice,
        "color_ramps": apply_ramps,
    }

    state.log(f"   📐 Type Scale: {type_choice}")
    state.log(f"   📏 Spacing: {spacing_choice}")
    state.log(f"   🌈 Color Ramps: {'Yes' if apply_ramps else 'No'}")

    # Process accepted color recommendations
    accepted_color_changes = []
    rejected_count = 0
    # Normalize color_recs_table: Gradio 6 may pass a DataFrame or list-of-lists
    _color_rows = []
    if color_recs_table is not None:
        try:
            import pandas as pd
            if isinstance(color_recs_table, pd.DataFrame) and not color_recs_table.empty:
                _color_rows = color_recs_table.values.tolist()
            elif isinstance(color_recs_table, (list, tuple)) and len(color_recs_table) > 0:
                _color_rows = list(color_recs_table)
        except Exception:
            if isinstance(color_recs_table, (list, tuple)):
                _color_rows = list(color_recs_table)

    if _color_rows:
        state.log("")
        state.log("   🎨 LLM Color Recommendations:")
        for row in _color_rows:
            if len(row) >= 5:
                accept = row[0]  # Boolean checkbox
                role = row[1]    # Role name
                current = row[2] # Current color
                issue = row[3]   # Issue description
                suggested = row[4]  # Suggested color

                if accept and suggested and current != suggested:
                    accepted_color_changes.append({
                        "role": role,
                        "from": current,
                        "to": suggested,
                        "reason": issue,
                    })
                    state.log(f"   ├─ ✅ ACCEPTED: {role}")
                    state.log(f"   │  └─ {current} → {suggested}")
                elif not accept:
                    rejected_count += 1
                    state.log(f"   ├─ ❌ REJECTED: {role} (keeping {current})")

    # Store accepted changes
    state.selected_upgrades["color_changes"] = accepted_color_changes

    state.log("")
    if accepted_color_changes:
        state.log(f"   📊 {len(accepted_color_changes)} color change(s) will be applied to export")
    if rejected_count:
        state.log(f"   📊 {rejected_count} color change(s) rejected (keeping original)")

    state.log("")
    state.log("✅ Upgrades applied! Proceed to Stage 3 for export.")
    state.log("═" * 50)

    # Build visible feedback summary
    summary_parts = []
    summary_parts.append(f"**Type Scale:** {type_choice}")
    summary_parts.append(f"**Spacing:** {spacing_choice}")
    summary_parts.append(f"**Color Ramps:** {'✅ Enabled' if apply_ramps else '❌ Disabled'}")
    if accepted_color_changes:
        summary_parts.append(f"**Color Changes:** {len(accepted_color_changes)} accepted")
    if rejected_count:
        summary_parts.append(f"**Rejected:** {rejected_count} kept as-is")

    status_md = f"""## ✅ Upgrades Applied Successfully!

{chr(10).join('- ' + p for p in summary_parts)}

👉 **Proceed to Stage 3** to export your upgraded tokens.
"""
    return status_md, state.get_logs()


# =============================================================================
# EXPORT HELPERS — Semantic Token Naming
# =============================================================================

def _get_radius_token_name(value_str, seen_names: dict = None) -> str:
    """Map radius px value to semantic token name (radius.sm, radius.md, etc.)."""
    val = str(value_str).replace('px', '').replace('%', '')
    try:
        px = float(val)
    except (ValueError, TypeError):
        return "radius.md"

    # Handle percentage values (e.g., "50%" for circular)
    if "%" in str(value_str):
        base_name = "radius.full"
    # "none" is ONLY for exactly 0px
    elif px == 0:
        base_name = "radius.none"
    elif px >= 9999:
        # Large values (like 9999px) are essentially "full"
        base_name = "radius.full"
    else:
        # Semantic naming based on pixel ranges (inclusive both ends for clarity)
        mapping = [
            (1, 1, "radius.xs"),      # 1px = xs
            (2, 3, "radius.sm"),      # 2-3px = sm
            (4, 7, "radius.md"),      # 4-7px = md
            (8, 11, "radius.lg"),     # 8-11px = lg
            (12, 19, "radius.xl"),    # 12-19px = xl
            (20, 31, "radius.2xl"),   # 20-31px = 2xl
            (32, 99, "radius.3xl"),   # 32-99px = 3xl
        ]
        base_name = "radius.md"
        for low, high, name in mapping:
            if low <= px <= high:
                base_name = name
                break

    # Handle duplicates: if two radii map to same semantic name, skip the duplicate.
    # Old behavior appended ".{px}" which created invalid nested DTCG structures.
    if seen_names is not None:
        if base_name in seen_names:
            return None  # Signal caller to skip this duplicate radius
        seen_names[base_name] = True
    return base_name


def _get_shadow_blur(value_str: str) -> float:
    """Extract blur radius from shadow value for sorting."""
    import re
    # Shadow format: "Xpx Ypx BLURpx SPREADpx color"
    parts = re.findall(r'([\d.]+)px', str(value_str))
    if len(parts) >= 3:
        return float(parts[2])  # blur is 3rd px value
    elif len(parts) >= 1:
        return float(parts[0])
    return 0


def _parse_shadow_to_tokens_studio(value_str: str) -> dict:
    """Parse CSS shadow string to Figma Tokens Studio boxShadow format.

    Input: "rgba(0, 0, 0, 0.5) 0px 2px 4px 0px" or "0px 2px 4px 0px rgba(0,0,0,0.5)"
    Output: {"x": "0", "y": "2", "blur": "4", "spread": "0", "color": "rgba(0,0,0,0.5)", "type": "dropShadow"}
    """
    import re
    value_str = str(value_str).strip()

    # Extract color (rgba/rgb/hex)
    color_match = re.search(r'(rgba?\([^)]+\)|#[0-9a-fA-F]{3,8})', value_str)
    color = color_match.group(1) if color_match else "rgba(0,0,0,0.25)"

    # Extract px values
    px_values = re.findall(r'(-?[\d.]+)px', value_str)

    # Standard order: x y blur spread
    x = px_values[0] if len(px_values) > 0 else "0"
    y = px_values[1] if len(px_values) > 1 else "0"
    blur = px_values[2] if len(px_values) > 2 else "0"
    spread = px_values[3] if len(px_values) > 3 else "0"

    # Determine if inset
    shadow_type = "innerShadow" if "inset" in value_str.lower() else "dropShadow"

    return {
        "x": x,
        "y": y,
        "blur": blur,
        "spread": spread,
        "color": color,
        "type": shadow_type,
    }


# =============================================================================
# W3C DTCG FORMAT HELPERS
# =============================================================================

def _flat_key_to_nested(flat_key: str, value: dict, root: dict):
    """Convert 'color.brand.primary' into nested dict structure.

    Example: _flat_key_to_nested('color.brand.primary', token, {})
    Result: {'color': {'brand': {'primary': token}}}

    Safety: If a path segment is already a DTCG leaf token ($type/$value),
    the new token is SKIPPED to avoid creating invalid nested structures
    like: {"$type":"color","$value":"#abc","2":{"$type":"color","$value":"#def"}}
    """
    parts = flat_key.split('.')
    current = root
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        node = current[part]
        # Guard: don't navigate into an existing leaf token
        if isinstance(node, dict) and ('$type' in node or '$value' in node):
            # This path would nest a child inside a DTCG leaf — skip silently
            return
        current = node
    current[parts[-1]] = value


def _to_dtcg_token(value, token_type: str, description: str = None,
                    source: str = None, extensions: dict = None) -> dict:
    """Wrap value in W3C DTCG v1 (2025.10) format.

    Spec: https://www.designtokens.org/tr/drafts/format/

    Args:
        value: The token value
        token_type: W3C DTCG type — must be one of:
            color, dimension, fontFamily, fontWeight, number,
            duration, cubicBezier, shadow, strokeStyle, border,
            transition, gradient, typography
        description: Optional human-readable description
        source: Optional source indicator (extracted, recommended, semantic)
        extensions: Optional dict for $extensions (custom metadata like frequency, confidence)
    """
    token = {"$type": token_type, "$value": value}
    if description and source:
        token["$description"] = f"[{source}] {description}"
    elif description:
        token["$description"] = description
    if extensions:
        token["$extensions"] = {"com.design-system-automation": extensions}
    return token


def _shadow_to_dtcg(shadow_dict: dict) -> dict:
    """Convert our internal shadow format to W3C DTCG shadow spec.

    Input: {"x": "0", "y": "2", "blur": "4", "spread": "0", "color": "rgba(...)"}
    Output: {"color": "...", "offsetX": "0px", "offsetY": "2px", "blur": "4px", "spread": "0px"}
    """
    return {
        "color": shadow_dict.get("color", "rgba(0,0,0,0.25)"),
        "offsetX": str(shadow_dict.get("x", "0")) + "px",
        "offsetY": str(shadow_dict.get("y", "0")) + "px",
        "blur": str(shadow_dict.get("blur", "0")) + "px",
        "spread": str(shadow_dict.get("spread", "0")) + "px",
    }


def _get_semantic_color_overrides() -> dict:
    """Build color hex->semantic name map.

    v3.2: Color classifier is the PRIMARY naming authority (deterministic, reproducible).
    AURORA is a SECONDARY enhancer — it can only ADD semantic role names
    (brand.primary, text.secondary, etc.) but cannot override palette names.

    Authority chain:
      1. Color classifier (rule-based, covers ALL colors)
      2. AURORA naming_map (LLM, only brand/text/bg/border/feedback roles accepted)
      3. Normalizer suggested_name (fallback)
    """
    overrides = {}  # hex -> semantic_name

    # PRIMARY: Color classifier (deterministic, covers ALL colors)
    classified = getattr(state, 'color_classification', None)
    if classified and hasattr(classified, 'colors'):
        for cc in classified.colors:
            hex_clean = cc.hex.strip().lower()
            if hex_clean.startswith('#') and cc.token_name:
                overrides[hex_clean] = cc.token_name

    # SECONDARY: AURORA naming_map — ONLY accept semantic role upgrades
    # AURORA can promote "color.blue.500" to "color.brand.primary"
    # but cannot rename palette colors to different palette names
    _SEMANTIC_ROLES = {'brand.', 'text.', 'bg.', 'border.', 'feedback.'}
    brand_result = getattr(state, 'brand_result', None)
    if brand_result:
        naming_map = getattr(brand_result, 'naming_map', None)
        if isinstance(naming_map, dict) and naming_map:
            for hex_val, name in naming_map.items():
                hex_clean = str(hex_val).strip().lower()
                if not hex_clean.startswith('#') or not name:
                    continue
                clean_name = name if name.startswith('color.') else f'color.{name}'
                # Only accept semantic role names from AURORA
                name_after_color = clean_name[6:]  # strip "color."
                is_semantic_role = any(name_after_color.startswith(r) for r in _SEMANTIC_ROLES)
                if is_semantic_role:
                    overrides[hex_clean] = clean_name

    return overrides


def _is_valid_hex_color(value: str) -> bool:
    """Validate that a string is a proper hex color (not CSS garbage)."""
    import re
    if not value or not isinstance(value, str):
        return False
    # Must be exactly #RGB, #RRGGBB, or #RRGGBBAA
    clean = value.strip().lower()
    return bool(re.match(r'^#([a-f0-9]{3}|[a-f0-9]{6}|[a-f0-9]{8})$', clean))


def _generate_color_name_from_hex(hex_val: str, used_names: set = None) -> str:
    """DEPRECATED: Use normalizer._generate_preliminary_name() instead.

    Kept as thin wrapper for backward compatibility.
    Delegates to normalizer's naming logic via color_utils.categorize_color().
    """
    from core.color_utils import categorize_color, parse_color
    import colorsys

    used_names = used_names or set()

    hex_clean = hex_val.lstrip('#').lower()
    if len(hex_clean) == 3:
        hex_clean = ''.join([c * 2 for c in hex_clean])

    try:
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
    except (ValueError, IndexError):
        return "color.other.500"

    h, l, s = colorsys.rgb_to_hls(r, g, b)
    color_family = categorize_color(hex_val) or "neutral"

    # Numeric shade from lightness (matches normalizer._generate_preliminary_name)
    if l >= 0.95: shade = "50"
    elif l >= 0.85: shade = "100"
    elif l >= 0.75: shade = "200"
    elif l >= 0.65: shade = "300"
    elif l >= 0.50: shade = "400"
    elif l >= 0.40: shade = "500"
    elif l >= 0.30: shade = "600"
    elif l >= 0.20: shade = "700"
    elif l >= 0.10: shade = "800"
    else: shade = "900"

    base_name = f"color.{color_family}.{shade}"
    final_name = base_name
    suffix = 1
    while final_name in used_names:
        suffix += 1
        final_name = f"{base_name}_{suffix}"
    return final_name


def _consolidate_colors(colors_dict: dict, overrides: dict, max_colors: int = 30) -> dict:
    """Consolidate colors: semantic first, then top by frequency, capped."""
    if not colors_dict:
        return {}

    result = {}
    remaining = []
    used_generated_names = set()  # Track generated names to avoid conflicts

    for name, c in colors_dict.items():
        hex_val = c.value.lower() if hasattr(c, 'value') else str(c.get('value', '')).lower()

        # IMPORTANT: Skip invalid/garbage color values (CSS parsing errors)
        if not _is_valid_hex_color(hex_val):
            continue

        freq = c.frequency if hasattr(c, 'frequency') else c.get('frequency', 0)

        # Check if this color has a semantic override
        semantic_name = overrides.get(hex_val)
        if semantic_name:
            result[semantic_name] = {
                "value": hex_val,
                "type": "color",
                "source": "semantic",
            }
        else:
            # Check for garbage names (firecrawl.N, numeric-only, etc.)
            base_name = (c.suggested_name if hasattr(c, 'suggested_name') else name) or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").lower()

            # Detect garbage names and generate proper color-based names
            is_garbage_name = (
                'firecrawl' in clean_name.lower() or
                clean_name.split('.')[-1].isdigit() or  # Ends with just a number
                len(clean_name.split('.')) == 2 and clean_name.split('.')[-1].isdigit()  # color.34
            )

            if is_garbage_name:
                # Generate proper name based on color characteristics
                clean_name = _generate_color_name_from_hex(hex_val, used_generated_names)
                used_generated_names.add(clean_name)
            elif not clean_name.startswith("color."):
                clean_name = f"color.{clean_name}"

            remaining.append((clean_name, hex_val, freq))

    # Sort remaining by frequency (highest first), take up to max
    remaining.sort(key=lambda x: -x[2])
    slots_left = max_colors - len(result)
    for clean_name, hex_val, freq in remaining[:slots_left]:
        if clean_name not in result:
            result[clean_name] = {
                "value": hex_val,
                "type": "color",
                "source": "detected",
            }

    return result


def preview_color_classification(convention: str = "semantic"):
    """Preview color classification before export. 100% rule-based, no LLM."""
    from core.color_classifier import classify_colors, generate_classification_preview

    if not state.desktop_normalized or not state.desktop_normalized.colors:
        return "⚠️ No colors extracted yet. Run Stage 1 extraction first."

    result = classify_colors(
        state.desktop_normalized.colors,
        convention=convention or "semantic",
        log_callback=state.log,
    )

    # Store for use by export functions
    state.color_classification = result

    preview = generate_classification_preview(result)

    # Also append the decision log
    log_section = "\n\n📋 DECISION LOG:\n" + "\n".join(result.log)

    return preview + log_section


def export_stage1_json(convention: str = "semantic"):
    """Export Stage 1 tokens (as-is extraction) to W3C DTCG format."""
    if not state.desktop_normalized:
        gr.Warning("No tokens extracted yet. Complete Stage 1 extraction first.")
        return json.dumps({
            "error": "No tokens extracted yet.",
            "how_to_fix": "Go to Step 1, enter a URL, discover pages, and extract tokens first.",
            "stage": "Stage 1 required"
        }, indent=2)

    # W3C DTCG format: nested structure, no wrapper, $value/$type
    result = {}
    token_count = 0

    # =========================================================================
    # COLORS — Nested structure with $value, $type, $description
    # =========================================================================
    if state.desktop_normalized and state.desktop_normalized.colors:
        from core.color_classifier import classify_colors
        classification = classify_colors(
            state.desktop_normalized.colors,
            convention=convention or "semantic",
            log_callback=state.log,
        )
        for c in classification.colors:
            ext = {"frequency": c.frequency, "confidence": c.confidence, "category": c.category}
            if c.evidence:
                ext["evidence"] = c.evidence[:3]  # Top 3 evidence items
            dtcg_token = _to_dtcg_token(
                c.hex, "color",
                description=f"{c.category}: {c.role}",
                extensions=ext,
            )
            _flat_key_to_nested(c.token_name, dtcg_token, result)
            token_count += 1

    # =========================================================================
    # TYPOGRAPHY — Nested structure with viewport suffix
    # =========================================================================
    # Desktop typography
    if state.desktop_normalized and state.desktop_normalized.typography:
        for name, t in state.desktop_normalized.typography.items():
            base_name = t.suggested_name or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
            if not clean_name.startswith("font."):
                clean_name = f"font.{clean_name}"

            flat_key = f"{clean_name}.desktop"
            typo_value = {
                "fontFamily": t.font_family,
                "fontSize": t.font_size,
                "fontWeight": str(t.font_weight),
                "lineHeight": t.line_height or "1.5",
            }
            dtcg_token = _to_dtcg_token(typo_value, "typography", description="Extracted from site")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    # Mobile typography
    if state.mobile_normalized and state.mobile_normalized.typography:
        for name, t in state.mobile_normalized.typography.items():
            base_name = t.suggested_name or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
            if not clean_name.startswith("font."):
                clean_name = f"font.{clean_name}"

            flat_key = f"{clean_name}.mobile"
            typo_value = {
                "fontFamily": t.font_family,
                "fontSize": t.font_size,
                "fontWeight": str(t.font_weight),
                "lineHeight": t.line_height or "1.5",
            }
            dtcg_token = _to_dtcg_token(typo_value, "typography", description="Extracted from site")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    # =========================================================================
    # SPACING — Nested structure with viewport suffix
    # =========================================================================
    # Desktop spacing
    if state.desktop_normalized and state.desktop_normalized.spacing:
        for name, s in state.desktop_normalized.spacing.items():
            base_name = s.suggested_name or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
            if not clean_name.startswith("space."):
                clean_name = f"space.{clean_name}"

            flat_key = f"{clean_name}.desktop"
            dtcg_token = _to_dtcg_token(s.value, "dimension", description="Extracted from site")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    # Mobile spacing
    if state.mobile_normalized and state.mobile_normalized.spacing:
        for name, s in state.mobile_normalized.spacing.items():
            base_name = s.suggested_name or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
            if not clean_name.startswith("space."):
                clean_name = f"space.{clean_name}"

            flat_key = f"{clean_name}.mobile"
            dtcg_token = _to_dtcg_token(s.value, "dimension", description="Extracted from site")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    # =========================================================================
    # BORDER RADIUS — W3C DTCG "dimension" type
    # =========================================================================
    if state.desktop_normalized and state.desktop_normalized.radius:
        seen_radius = {}
        for name, r in state.desktop_normalized.radius.items():
            token_name = _get_radius_token_name(r.value, seen_radius)
            if token_name is None:
                continue  # Duplicate radius — skip
            flat_key = token_name
            ext = {"frequency": r.frequency}
            if hasattr(r, 'fits_base_4') and r.fits_base_4 is not None:
                ext["fitsBase4"] = r.fits_base_4
            if hasattr(r, 'fits_base_8') and r.fits_base_8 is not None:
                ext["fitsBase8"] = r.fits_base_8
            dtcg_token = _to_dtcg_token(r.value, "dimension",
                                         description=f"Border radius ({name})",
                                         extensions=ext)
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    # =========================================================================
    # SHADOWS — W3C DTCG shadow format
    # =========================================================================
    if state.desktop_normalized and state.desktop_normalized.shadows:
        shadow_tier_names = ["xs", "sm", "md", "lg", "xl", "2xl"]
        sorted_shadows = sorted(
            state.desktop_normalized.shadows.items(),
            key=lambda x: _get_shadow_blur(x[1].value),
        )
        for i, (name, s) in enumerate(sorted_shadows):
            size_name = shadow_tier_names[i] if i < len(shadow_tier_names) else str(i + 1)
            flat_key = f"shadow.{size_name}"
            parsed = _parse_shadow_to_tokens_studio(s.value)
            dtcg_shadow_value = _shadow_to_dtcg(parsed)
            ext = {"frequency": s.frequency, "rawCSS": s.value}
            if hasattr(s, 'blur_px') and s.blur_px is not None:
                ext["blurPx"] = s.blur_px
            dtcg_token = _to_dtcg_token(dtcg_shadow_value, "shadow",
                                         description=f"Elevation {size_name}",
                                         extensions=ext)
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    json_str = json.dumps(result, indent=2, default=str)
    gr.Info(f"Stage 1 exported: {token_count} tokens (W3C DTCG format)")
    return json_str


def export_tokens_json(convention: str = "semantic"):
    """Export final tokens with selected upgrades applied - FLAT structure for Figma Tokens Studio."""
    if not state.desktop_normalized:
        gr.Warning("No tokens extracted yet. Complete Stage 1 extraction first.")
        return json.dumps({
            "error": "No tokens extracted yet.",
            "how_to_fix": "Complete Stage 1 extraction first, then optionally run Stage 2 analysis before exporting.",
            "stage": "Stage 1 required"
        }, indent=2)

    # Get selected upgrades
    upgrades = getattr(state, 'selected_upgrades', {})
    if not upgrades:
        state.log("⚠️ Exporting final JSON without Stage 2 upgrades applied. Consider running Stage 2 analysis first.")
    type_scale_choice = upgrades.get('type_scale', 'Keep Current')
    spacing_choice = upgrades.get('spacing', 'Keep Current')
    apply_ramps = upgrades.get('color_ramps', True)
    
    # Determine ratio from choice
    ratio = None
    if "1.2" in type_scale_choice:
        ratio = 1.2
    elif "1.25" in type_scale_choice:
        ratio = 1.25
    elif "1.333" in type_scale_choice:
        ratio = 1.333
    
    # Determine spacing base
    spacing_base = None
    if "8px" in spacing_choice:
        spacing_base = 8
    elif "4px" in spacing_choice:
        spacing_base = 4
    
    # W3C DTCG format: nested structure, no wrapper
    result = {}
    token_count = 0

    fonts_info = get_detected_fonts()
    primary_font = fonts_info.get("primary", "sans-serif")
    
    # =========================================================================
    # COLORS — Rule-based classification + optional ramps
    # =========================================================================
    if state.desktop_normalized and state.desktop_normalized.colors:
        from core.color_utils import generate_color_ramp
        from core.color_classifier import classify_colors

        classification = classify_colors(
            state.desktop_normalized.colors,
            convention=convention or "semantic",
            log_callback=state.log,
        )

        # Semantic categories get light/dark variants; palette gets full 50-900 ramps
        _SEMANTIC_CATS = {"brand", "text", "bg", "border", "feedback"}
        _PALETTE_SHADES = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]
        _SEMANTIC_VARIANT_SHADES = ["50", "200", "800", "950"]

        # Track which palette hue families already have ramps (avoid duplicates)
        _palette_hues_with_ramps = set()

        for c in classification.colors:
            flat_key = c.token_name
            is_semantic = c.category in _SEMANTIC_CATS

            if apply_ramps and not is_semantic:
                # PALETTE colors: full 50-900 ramp under hue family
                # token_name = "color.blue.700" → base = "color.blue" (strip shade)
                parts = flat_key.rsplit(".", 1)
                hue_base = parts[0] if len(parts) > 1 else flat_key

                # Only one ramp per hue family (first/most-used color wins)
                if hue_base in _palette_hues_with_ramps:
                    continue
                _palette_hues_with_ramps.add(hue_base)

                try:
                    ramp = generate_color_ramp(c.hex)
                    for shade in _PALETTE_SHADES:
                        shade_hex = ramp.get(shade)
                        if shade_hex:
                            shade_key = f"{hue_base}.{shade}"
                            dtcg_token = _to_dtcg_token(shade_hex, "color")
                            _flat_key_to_nested(shade_key, dtcg_token, result)
                            token_count += 1
                except (ValueError, KeyError, TypeError, IndexError):
                    dtcg_token = _to_dtcg_token(c.hex, "color")
                    _flat_key_to_nested(flat_key, dtcg_token, result)
                    token_count += 1

            elif apply_ramps and is_semantic:
                # SEMANTIC colors: base + tint/shade variants
                # Build as a namespace dict (not sequential leaf calls)
                # so that base and variants coexist without nesting conflict
                try:
                    ramp = generate_color_ramp(c.hex)
                    # Emit base as "DEFAULT" inside a namespace
                    default_key = f"{flat_key}.DEFAULT"
                    dtcg_token = _to_dtcg_token(c.hex, "color")
                    _flat_key_to_nested(default_key, dtcg_token, result)
                    token_count += 1
                    for variant_shade in _SEMANTIC_VARIANT_SHADES:
                        variant_hex = ramp.get(variant_shade)
                        if variant_hex:
                            variant_key = f"{flat_key}.{variant_shade}"
                            dtcg_token = _to_dtcg_token(variant_hex, "color")
                            _flat_key_to_nested(variant_key, dtcg_token, result)
                            token_count += 1
                except (ValueError, KeyError, TypeError, IndexError):
                    # Fallback: just base color
                    dtcg_token = _to_dtcg_token(c.hex, "color")
                    _flat_key_to_nested(flat_key, dtcg_token, result)
                    token_count += 1

            else:
                # No ramps — base color only
                dtcg_token = _to_dtcg_token(c.hex, "color")
                _flat_key_to_nested(flat_key, dtcg_token, result)
                token_count += 1
    
    # =========================================================================
    # TYPOGRAPHY - FLAT structure with viewport suffix
    # =========================================================================
    base_size = get_base_font_size()
    token_names = [
        "font.display.2xl", "font.display.xl", "font.display.lg", "font.display.md",
        "font.heading.xl", "font.heading.lg", "font.heading.md", "font.heading.sm",
        "font.body.lg", "font.body.md", "font.body.sm", "font.caption", "font.overline"
    ]
    
    # Weight + lineHeight mapping by token tier
    _weight_map = {
        "display": "700", "heading": "600",
        "body": "400", "caption": "400", "overline": "500",
    }
    _lh_map = {
        "display": "1.2", "heading": "1.3",
        "body": "1.5", "caption": "1.4", "overline": "1.2",
    }

    def _tier_from_token(token_name: str) -> str:
        """Extract tier (display/heading/body/caption/overline) from token name."""
        for tier in ("display", "heading", "body", "caption", "overline"):
            if tier in token_name:
                return tier
        return "body"

    # Desktop typography — W3C DTCG format
    MIN_FONT_SIZE_DESKTOP = 10  # Floor: no text style below 10px
    MIN_FONT_SIZE_MOBILE = 10   # Floor: same for mobile
    if ratio:
        scales = [max(MIN_FONT_SIZE_DESKTOP, int(round(base_size * (ratio ** (8-i)) / 2) * 2)) for i in range(13)]
        for i, token_name in enumerate(token_names):
            tier = _tier_from_token(token_name)
            flat_key = f"{token_name}.desktop"
            typo_value = {
                "fontFamily": primary_font,
                "fontSize": f"{scales[i]}px",
                "fontWeight": _weight_map.get(tier, "400"),
                "lineHeight": _lh_map.get(tier, "1.5"),
            }
            dtcg_token = _to_dtcg_token(typo_value, "typography")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1
    elif state.desktop_normalized and state.desktop_normalized.typography:
        for name, t in state.desktop_normalized.typography.items():
            base_name = t.suggested_name or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
            if not clean_name.startswith("font."):
                clean_name = f"font.{clean_name}"

            flat_key = f"{clean_name}.desktop"
            typo_value = {
                "fontFamily": t.font_family,
                "fontSize": t.font_size,
                "fontWeight": str(t.font_weight),
                "lineHeight": t.line_height or "1.5",
            }
            dtcg_token = _to_dtcg_token(typo_value, "typography")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1

    # Mobile typography — W3C DTCG format
    if ratio:
        mobile_factor = 0.875
        scales = [max(MIN_FONT_SIZE_MOBILE, int(round(base_size * mobile_factor * (ratio ** (8-i)) / 2) * 2)) for i in range(13)]
        for i, token_name in enumerate(token_names):
            tier = _tier_from_token(token_name)
            flat_key = f"{token_name}.mobile"
            typo_value = {
                "fontFamily": primary_font,
                "fontSize": f"{scales[i]}px",
                "fontWeight": _weight_map.get(tier, "400"),
                "lineHeight": _lh_map.get(tier, "1.5"),
            }
            dtcg_token = _to_dtcg_token(typo_value, "typography")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1
    elif state.mobile_normalized and state.mobile_normalized.typography:
        for name, t in state.mobile_normalized.typography.items():
            base_name = t.suggested_name or name
            clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
            if not clean_name.startswith("font."):
                clean_name = f"font.{clean_name}"

            flat_key = f"{clean_name}.mobile"
            typo_value = {
                "fontFamily": t.font_family,
                "fontSize": t.font_size,
                "fontWeight": str(t.font_weight),
                "lineHeight": t.line_height or "1.5",
            }
            dtcg_token = _to_dtcg_token(typo_value, "typography")
            _flat_key_to_nested(flat_key, dtcg_token, result)
            token_count += 1
    
    # =========================================================================
    # SPACING — W3C DTCG format with nested structure
    # =========================================================================
    spacing_token_names = [
        "space.1", "space.2", "space.3", "space.4", "space.5",
        "space.6", "space.8", "space.10", "space.12", "space.16"
    ]

    if spacing_base:
        # Generate grid-aligned spacing for both viewports
        for i, token_name in enumerate(spacing_token_names):
            value = spacing_base * (i + 1)

            # Desktop
            desktop_key = f"{token_name}.desktop"
            dtcg_token = _to_dtcg_token(f"{value}px", "dimension")
            _flat_key_to_nested(desktop_key, dtcg_token, result)
            token_count += 1

            # Mobile (same values)
            mobile_key = f"{token_name}.mobile"
            dtcg_token = _to_dtcg_token(f"{value}px", "dimension")
            _flat_key_to_nested(mobile_key, dtcg_token, result)
            token_count += 1
    else:
        # Keep original with nested structure
        if state.desktop_normalized and state.desktop_normalized.spacing:
            for name, s in state.desktop_normalized.spacing.items():
                base_name = s.suggested_name or name
                clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
                if not clean_name.startswith("space."):
                    clean_name = f"space.{clean_name}"

                desktop_key = f"{clean_name}.desktop"
                dtcg_token = _to_dtcg_token(s.value, "dimension")
                _flat_key_to_nested(desktop_key, dtcg_token, result)
                token_count += 1

        if state.mobile_normalized and state.mobile_normalized.spacing:
            for name, s in state.mobile_normalized.spacing.items():
                base_name = s.suggested_name or name
                clean_name = base_name.replace(" ", ".").replace("_", ".").replace("-", ".").lower()
                if not clean_name.startswith("space."):
                    clean_name = f"space.{clean_name}"

                mobile_key = f"{clean_name}.mobile"
                dtcg_token = _to_dtcg_token(s.value, "dimension")
                _flat_key_to_nested(mobile_key, dtcg_token, result)
                token_count += 1

    # =========================================================================
    # BORDER RADIUS — W3C DTCG format (uses "dimension" type per spec)
    # =========================================================================
    if state.desktop_normalized and state.desktop_normalized.radius:
        seen_radius = {}
        for name, r in state.desktop_normalized.radius.items():
            token_name = _get_radius_token_name(r.value, seen_radius)
            if token_name is None:
                continue  # Duplicate radius — skip
            dtcg_token = _to_dtcg_token(r.value, "dimension")
            _flat_key_to_nested(token_name, dtcg_token, result)
            token_count += 1

    # =========================================================================
    # SHADOWS — W3C DTCG format — always produce 5 elevation levels (xs→xl)
    # Interpolates between extracted shadows to fill missing levels.
    # =========================================================================
    TARGET_SHADOW_COUNT = 5
    shadow_names = ["shadow.xs", "shadow.sm", "shadow.md", "shadow.lg", "shadow.xl"]

    if state.desktop_normalized and state.desktop_normalized.shadows:
        sorted_shadows = sorted(
            state.desktop_normalized.shadows.items(),
            key=lambda x: _get_shadow_blur(x[1].value),
        )

        # Parse all extracted shadows into numeric components
        parsed_shadows = []
        for name, s in sorted_shadows:
            p = _parse_shadow_to_tokens_studio(s.value)
            parsed_shadows.append({
                "x": float(p.get("x", 0)),
                "y": float(p.get("y", 0)),
                "blur": float(p.get("blur", 0)),
                "spread": float(p.get("spread", 0)),
                "color": p.get("color", "rgba(0,0,0,0.25)"),
            })

        # Interpolation helpers
        def _lerp(a, b, t):
            return a + (b - a) * t

        def _lerp_shadow(s1, s2, t):
            """Interpolate between two shadow dicts at factor t (0.0=s1, 1.0=s2)."""
            import re
            interp = {
                "x": round(_lerp(s1["x"], s2["x"], t), 1),
                "y": round(_lerp(s1["y"], s2["y"], t), 1),
                "blur": round(_lerp(s1["blur"], s2["blur"], t), 1),
                "spread": round(_lerp(s1["spread"], s2["spread"], t), 1),
            }
            alpha1, alpha2 = 0.25, 0.25
            m1 = re.search(r'rgba?\([^)]*,\s*([\d.]+)\)', s1["color"])
            m2 = re.search(r'rgba?\([^)]*,\s*([\d.]+)\)', s2["color"])
            if m1: alpha1 = float(m1.group(1))
            if m2: alpha2 = float(m2.group(1))
            interp_alpha = round(_lerp(alpha1, alpha2, t), 3)
            interp["color"] = f"rgba(0, 0, 0, {interp_alpha})"
            return interp

        final_shadows = []
        n = len(parsed_shadows)
        if n >= TARGET_SHADOW_COUNT:
            final_shadows = parsed_shadows[:TARGET_SHADOW_COUNT]
        elif n == 1:
            base = parsed_shadows[0]
            for i in range(TARGET_SHADOW_COUNT):
                factor = (i + 1) / 3.0
                final_shadows.append({
                    "x": round(base["x"] * factor, 1),
                    "y": round(max(1, base["y"] * factor), 1),
                    "blur": round(max(1, base["blur"] * factor), 1),
                    "spread": round(base["spread"] * factor, 1),
                    "color": f"rgba(0, 0, 0, {round(0.04 + i * 0.04, 3)})",
                })
        elif n >= 2:
            for i in range(TARGET_SHADOW_COUNT):
                t = i / (TARGET_SHADOW_COUNT - 1)
                src_pos = t * (n - 1)
                lo = int(src_pos)
                hi = min(lo + 1, n - 1)
                frac = src_pos - lo
                final_shadows.append(_lerp_shadow(parsed_shadows[lo], parsed_shadows[hi], frac))

        for i, shadow in enumerate(final_shadows):
            token_name = shadow_names[i] if i < len(shadow_names) else f"shadow.{i + 1}"
            dtcg_value = {
                "color": shadow["color"],
                "offsetX": f"{shadow['x']}px",
                "offsetY": f"{shadow['y']}px",
                "blur": f"{shadow['blur']}px",
                "spread": f"{shadow['spread']}px",
            }
            dtcg_token = _to_dtcg_token(dtcg_value, "shadow")
            _flat_key_to_nested(token_name, dtcg_token, result)
            token_count += 1

    json_str = json.dumps(result, indent=2, default=str)
    upgrades_note = " (with upgrades)" if upgrades else " (no upgrades applied)"
    gr.Info(f"Final export: {token_count} tokens{upgrades_note}")
    return json_str


# =============================================================================
# UI HELPERS
# =============================================================================

def _render_stepper(active: int = 1, completed: list = None) -> str:
    """Render the horizontal progress stepper HTML.

    Args:
        active: Current active step (1-5)
        completed: List of completed step numbers
    """
    if completed is None:
        completed = []

    steps = [
        ("1", "Discover"),
        ("2", "Extract"),
        ("3", "Analyze"),
        ("4", "Review"),
        ("5", "Export"),
    ]

    parts = []
    for i, (num, label) in enumerate(steps):
        step_num = i + 1
        if step_num in completed:
            cls = "completed"
            icon = "✓"
        elif step_num == active:
            cls = "active"
            icon = num
        else:
            cls = ""
            icon = num

        parts.append(f'<div class="step-item {cls}"><span class="step-num">{icon}</span>{label}</div>')

        if i < len(steps) - 1:
            conn_cls = "done" if step_num in completed else ""
            parts.append(f'<div class="step-connector {conn_cls}"></div>')

    return f'<div class="progress-stepper">{"".join(parts)}</div>'


def _render_benchmark_cards(benchmark_comparisons, benchmark_advice) -> str:
    """Render visual benchmark cards with progress bars instead of markdown table."""
    if not benchmark_comparisons:
        return "<div class='placeholder-msg'>No benchmark comparison available</div>"

    medals = ["🥇", "🥈", "🥉"]
    cards_html = []

    # Recommendation banner
    rec_html = ""
    if benchmark_advice and benchmark_advice.recommended_benchmark_name:
        rec_html = f"""
        <div style="background: #f5f3ff; border: 1px solid #c4b5fd; border-radius: 8px;
                    padding: 14px 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">🏆</span>
            <div>
                <div style="font-weight: 600; color: #4C1D95; font-size: 14px;">
                    Recommended: {benchmark_advice.recommended_benchmark_name}
                </div>
                <div style="font-size: 12px; color: #6D28D9; margin-top: 2px;">
                    {benchmark_advice.reasoning or ''}
                </div>
            </div>
        </div>"""

    for i, c in enumerate(benchmark_comparisons[:5]):
        b = c.benchmark
        medal = medals[i] if i < 3 else f"#{i+1}"

        def bar_color(pct):
            if pct >= 80: return "#10b981"
            elif pct >= 50: return "#f59e0b"
            else: return "#ef4444"

        categories = [
            ("Type", c.type_match_pct),
            ("Spacing", c.spacing_match_pct),
            ("Colors", c.color_match_pct),
            ("Radius", c.radius_match_pct),
            ("Shadows", c.shadow_match_pct),
        ]

        bars = ""
        for cat_name, pct in categories:
            color = bar_color(pct)
            bars += f"""
            <div class="bm-bar-row">
                <div class="bm-bar-label">{cat_name}</div>
                <div class="bm-bar-track">
                    <div class="bm-bar-fill" style="width: {pct:.0f}%; background: {color};"></div>
                </div>
                <div class="bm-bar-value" style="color: {color};">{pct:.0f}%</div>
            </div>"""

        cards_html.append(f"""
        <div class="bm-card">
            <div class="bm-card-header">
                <div style="display: flex; align-items: center;">
                    <span class="bm-medal">{medal}</span>
                    <span class="bm-card-name">{b.icon} {b.short_name}</span>
                </div>
                <div class="bm-card-pct">{c.overall_match_pct:.0f}%</div>
            </div>
            {bars}
        </div>""")

    # Alignment changes
    changes_html = ""
    if benchmark_advice and benchmark_advice.alignment_changes:
        items = []
        for change in benchmark_advice.alignment_changes[:4]:
            token_type = change.get('token_type', '')
            icon = {"typography": "📐", "spacing": "📏", "colors": "🎨", "radius": "🔘", "shadows": "🌗"}.get(token_type, "🔧")
            items.append(f"<li>{icon} <strong>{change.get('change', '?')}</strong>: {change.get('from', '?')} → {change.get('to', '?')}</li>")
        changes_html = f"""
        <div style="margin-top: 16px; padding: 14px 18px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #1e293b;">🔧 To Align with Top Match</div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #1a1a1a; line-height: 1.8;">
                {''.join(items)}
            </ul>
        </div>"""

    return f"""
    {rec_html}
    <div class="bm-card-grid">
        {''.join(cards_html)}
    </div>
    {changes_html}
    """


def _render_as_is_to_be(category: str, as_is_value: str, as_is_detail: str,
                         to_be_value: str, to_be_detail: str, icon: str = "📐") -> str:
    """Render an As-Is → To-Be comparison card for a token category."""
    return f"""
    <div class="comparison-grid">
        <div class="comparison-card as-is">
            <div class="comparison-label as-is-label">{icon} {category} — AS-IS</div>
            <div class="comparison-value">{as_is_value}</div>
            <div class="comparison-detail">{as_is_detail}</div>
        </div>
        <div class="comparison-arrow">→</div>
        <div class="comparison-card to-be">
            <div class="comparison-label to-be-label">{icon} {category} — TO-BE</div>
            <div class="comparison-value">{to_be_value}</div>
            <div class="comparison-detail">{to_be_detail}</div>
        </div>
    </div>
    """


# =============================================================================
# UI BUILDING
# =============================================================================

def create_ui():
    """Create the Gradio interface with corporate branding."""
    
    # Corporate theme — Deep Violet accent (distinctive, not blue)
    corporate_theme = gr.themes.Base(
        primary_hue=gr.themes.colors.violet,
        secondary_hue=gr.themes.colors.slate,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
    ).set(
        # Colors
        body_background_fill="#f8fafc",
        body_background_fill_dark="#0f172a",
        block_background_fill="white",
        block_background_fill_dark="#1e293b",
        block_border_color="#e2e8f0",
        block_border_color_dark="#334155",
        block_label_background_fill="#f5f3ff",
        block_label_background_fill_dark="#1e293b",
        block_title_text_color="#0f172a",
        block_title_text_color_dark="#f1f5f9",

        # Primary button — Deep Violet
        button_primary_background_fill="#6D28D9",
        button_primary_background_fill_hover="#5B21B6",
        button_primary_text_color="white",

        # Secondary button
        button_secondary_background_fill="#f5f3ff",
        button_secondary_background_fill_hover="#ede9fe",
        button_secondary_text_color="#1e293b",

        # Input fields
        input_background_fill="#ffffff",
        input_background_fill_dark="#1e293b",
        input_border_color="#cbd5e1",
        input_border_color_dark="#475569",

        # Shadows and radius
        block_shadow="0 1px 3px rgba(0,0,0,0.1)",
        block_shadow_dark="0 1px 3px rgba(0,0,0,0.3)",
        block_border_width="1px",
        block_radius="8px",

        # Text
        body_text_color="#1e293b",
        body_text_color_dark="#e2e8f0",
        body_text_size="14px",
    )
    
    # Custom CSS — Deep Violet theme + Progress Stepper + Always-visible log
    custom_css = """
    /* ═══════════════════════════════════════════════════════════════
       GLOBAL
       ═══════════════════════════════════════════════════════════════ */
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       HEADER — Deep Violet gradient
       ═══════════════════════════════════════════════════════════════ */
    .app-header {
        background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 50%, #8B5CF6 100%);
        padding: 28px 32px;
        border-radius: 12px;
        margin-bottom: 8px;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .app-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -30%;
        width: 60%;
        height: 200%;
        background: radial-gradient(ellipse, rgba(255,255,255,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .app-header h1 {
        margin: 0 0 6px 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    .app-header p {
        margin: 0;
        opacity: 0.85;
        font-size: 13px;
    }

    /* ═══════════════════════════════════════════════════════════════
       PROGRESS STEPPER — horizontal workflow indicator
       ═══════════════════════════════════════════════════════════════ */
    .progress-stepper {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px 20px;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        margin-bottom: 20px;
        gap: 0;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        color: #94a3b8;
        transition: all 0.3s ease;
        white-space: nowrap;
    }
    .step-item.active {
        background: #f5f3ff;
        color: #6D28D9;
        font-weight: 600;
    }
    .step-item.completed {
        color: #10b981;
        font-weight: 500;
    }
    .step-num {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        background: #e2e8f0;
        color: #94a3b8;
        flex-shrink: 0;
    }
    .step-item.active .step-num {
        background: #6D28D9;
        color: white;
    }
    .step-item.completed .step-num {
        background: #10b981;
        color: white;
    }
    .step-connector {
        width: 32px;
        height: 2px;
        background: #e2e8f0;
        flex-shrink: 0;
    }
    .step-connector.done {
        background: #10b981;
    }

    /* ═══════════════════════════════════════════════════════════════
       STAGE HEADERS — Violet accent
       ═══════════════════════════════════════════════════════════════ */
    .stage-header {
        background: linear-gradient(90deg, #f5f3ff 0%, #ffffff 100%);
        padding: 16px 20px;
        border-radius: 8px;
        border-left: 4px solid #6D28D9;
        margin-bottom: 16px;
    }
    .stage-header h2 {
        margin: 0;
        font-size: 18px;
        color: #1e293b;
    }

    /* ═══════════════════════════════════════════════════════════════
       LOG — Always visible during loading (z-index trick)
       ═══════════════════════════════════════════════════════════════ */
    .log-container textarea {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
        line-height: 1.6 !important;
        background: #0f172a !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    /* Keep log visible above Gradio loading overlay */
    .always-visible-log {
        position: relative;
        z-index: 1001;
    }
    .always-visible-log .wrap {
        opacity: 1 !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       COLOR SWATCH
       ═══════════════════════════════════════════════════════════════ */
    .color-swatch {
        display: inline-block;
        width: 24px;
        height: 24px;
        border-radius: 4px;
        margin-right: 8px;
        vertical-align: middle;
        border: 1px solid rgba(0,0,0,0.1);
    }

    /* ═══════════════════════════════════════════════════════════════
       SCORE BADGES
       ═══════════════════════════════════════════════════════════════ */
    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
    }
    .score-badge.high { background: #dcfce7; color: #166534; }
    .score-badge.medium { background: #fef3c7; color: #92400e; }
    .score-badge.low { background: #fee2e2; color: #991b1b; }

    /* ═══════════════════════════════════════════════════════════════
       BENCHMARK CARDS — Visual cards with progress bars
       ═══════════════════════════════════════════════════════════════ */
    .benchmark-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .benchmark-card.selected {
        border-color: #6D28D9;
        background: #f5f3ff;
    }
    .bm-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;
        margin: 16px 0;
    }
    .bm-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        transition: all 0.2s ease;
    }
    .bm-card:first-child {
        border: 2px solid #6D28D9;
        box-shadow: 0 0 0 3px rgba(109,40,217,0.1);
    }
    .bm-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .bm-card-name {
        font-weight: 600;
        font-size: 15px;
        color: #1e293b;
    }
    .bm-card-pct {
        font-weight: 700;
        font-size: 20px;
        color: #6D28D9;
    }
    .bm-card:first-child .bm-card-pct {
        color: #6D28D9;
    }
    .bm-bar-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .bm-bar-label {
        width: 70px;
        font-size: 11px;
        color: #64748b;
        text-align: right;
        flex-shrink: 0;
    }
    .bm-bar-track {
        flex: 1;
        height: 6px;
        background: #e2e8f0;
        border-radius: 3px;
        overflow: hidden;
    }
    .bm-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    .bm-bar-value {
        width: 40px;
        font-size: 11px;
        color: #475569;
        font-weight: 600;
    }
    .bm-medal {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        font-size: 14px;
        margin-right: 6px;
    }

    /* ═══════════════════════════════════════════════════════════════
       AS-IS vs TO-BE COMPARISON CARDS
       ═══════════════════════════════════════════════════════════════ */
    .comparison-grid {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        gap: 0;
        margin: 16px 0;
        align-items: stretch;
    }
    .comparison-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
    }
    .comparison-card.as-is {
        border-left: 4px solid #94a3b8;
    }
    .comparison-card.to-be {
        border-left: 4px solid #6D28D9;
        background: #faf5ff;
    }
    .comparison-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 12px;
        font-size: 24px;
        color: #6D28D9;
    }
    .comparison-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    .comparison-label.as-is-label { color: #94a3b8; }
    .comparison-label.to-be-label { color: #6D28D9; }
    .comparison-value {
        font-size: 22px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 4px;
    }
    .comparison-detail {
        font-size: 12px;
        color: #64748b;
    }

    /* ═══════════════════════════════════════════════════════════════
       ACTION ITEMS
       ═══════════════════════════════════════════════════════════════ */
    .action-item {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 8px;
    }
    .action-item.high-priority {
        border-left: 4px solid #ef4444;
    }
    .action-item.medium-priority {
        border-left: 4px solid #f59e0b;
    }

    /* ═══════════════════════════════════════════════════════════════
       PROGRESS BAR (generic)
       ═══════════════════════════════════════════════════════════════ */
    .progress-bar {
        height: 4px;
        background: #e2e8f0;
        border-radius: 2px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #6D28D9, #8B5CF6);
        transition: width 0.3s ease;
    }

    /* ═══════════════════════════════════════════════════════════════
       TABLES
       ═══════════════════════════════════════════════════════════════ */
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th {
        background: #f5f3ff;
        color: #1e293b;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
    }
    td {
        padding: 12px;
        color: #1e293b;
        border-bottom: 1px solid #e2e8f0;
    }

    /* ═══════════════════════════════════════════════════════════════
       SECTION DESCRIPTIONS
       ═══════════════════════════════════════════════════════════════ */
    .section-desc p, .section-desc {
        font-size: 13px !important;
        color: #64748b !important;
        line-height: 1.5 !important;
        margin-top: -4px !important;
        margin-bottom: 12px !important;
    }
    .dark .section-desc p, .dark .section-desc {
        color: #94a3b8 !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       SUCCESS / ERROR MESSAGES
       ═══════════════════════════════════════════════════════════════ */
    .success-msg { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin: 8px 0; }
    .success-msg h2 { color: #166534 !important; }
    .dark .success-msg { background: #052e16 !important; border-color: #166534 !important; }
    .dark .success-msg h2 { color: #bbf7d0 !important; }
    .dark .success-msg p { color: #d1d5db !important; }
    .error-msg { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin: 8px 0; }
    .error-msg h2 { color: #991b1b !important; }
    .dark .error-msg { background: #450a0a !important; border-color: #991b1b !important; }
    .dark .error-msg h2 { color: #fecaca !important; }
    .dark .error-msg p { color: #d1d5db !important; }

    /* ═══════════════════════════════════════════════════════════════
       PLACEHOLDER MESSAGES
       ═══════════════════════════════════════════════════════════════ */
    .placeholder-msg {
        padding: 20px;
        background: #f5f3ff;
        border-radius: 8px;
        color: #6D28D9;
        border: 1px dashed #c4b5fd;
        text-align: center;
    }
    .placeholder-msg.placeholder-lg {
        padding: 40px;
    }

    /* ═══════════════════════════════════════════════════════════════
       DARK MODE
       ═══════════════════════════════════════════════════════════════ */

    /* Stepper */
    .dark .progress-stepper {
        background: #1e293b;
        border-color: #334155;
    }
    .dark .step-item { color: #64748b; }
    .dark .step-item.active { background: #2e1065; color: #c4b5fd; }
    .dark .step-item.completed { color: #34d399; }
    .dark .step-num { background: #334155; color: #64748b; }
    .dark .step-item.active .step-num { background: #7C3AED; color: white; }
    .dark .step-item.completed .step-num { background: #10b981; color: white; }
    .dark .step-connector { background: #334155; }
    .dark .step-connector.done { background: #10b981; }

    /* Stage header */
    .dark .stage-header {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        border-left-color: #7C3AED;
    }
    .dark .stage-header h2 { color: #f1f5f9; }
    .dark .stage-header-subtitle, .dark .tip-text { color: #94a3b8 !important; }

    /* Benchmark cards */
    .dark .benchmark-card { background: #1e293b; border-color: #334155; }
    .dark .benchmark-card.selected { border-color: #7C3AED; background: #2e1065; }
    .dark .bm-card { background: #1e293b; border-color: #334155; }
    .dark .bm-card:first-child { border-color: #7C3AED; box-shadow: 0 0 0 3px rgba(124,58,237,0.15); }
    .dark .bm-card-name { color: #f1f5f9; }
    .dark .bm-card-pct { color: #c4b5fd; }
    .dark .bm-bar-label { color: #94a3b8; }
    .dark .bm-bar-track { background: #334155; }
    .dark .bm-bar-value { color: #cbd5e1; }

    /* Comparison cards */
    .dark .comparison-card { background: #1e293b; border-color: #334155; }
    .dark .comparison-card.to-be { background: #2e1065; border-left-color: #7C3AED; }
    .dark .comparison-arrow { color: #c4b5fd; }
    .dark .comparison-label.to-be-label { color: #c4b5fd; }
    .dark .comparison-value { color: #f1f5f9; }
    .dark .comparison-detail { color: #94a3b8; }

    /* Action items */
    .dark .action-item {
        background: #1e293b;
        border-color: #475569;
        color: #e2e8f0;
    }
    .dark .action-item.high-priority { border-left-color: #ef4444; }
    .dark .action-item.medium-priority { border-left-color: #f59e0b; }

    /* Placeholder */
    .dark .placeholder-msg {
        background: #1e1b2e !important;
        color: #a78bfa !important;
        border-color: #4c1d95 !important;
    }

    /* Tables */
    .dark table th {
        background: #1e293b !important;
        color: #e2e8f0 !important;
        border-bottom-color: #475569 !important;
    }
    .dark table td {
        color: #e2e8f0 !important;
        border-bottom-color: #334155 !important;
    }
    .dark table tr { background: #0f172a !important; }
    .dark table tr:nth-child(even) { background: #1e293b !important; }

    /* Typography preview */
    .dark .typography-preview { background: #1e293b !important; }
    .dark .typography-preview th { background: #334155 !important; color: #e2e8f0 !important; border-bottom-color: #475569 !important; }
    .dark .typography-preview td { color: #e2e8f0 !important; }
    .dark .typography-preview .meta-row { background: #1e293b !important; border-top-color: #334155 !important; }
    .dark .typography-preview .scale-name,
    .dark .typography-preview .scale-label { color: #f1f5f9 !important; background: #475569 !important; }
    .dark .typography-preview .meta { color: #cbd5e1 !important; }
    .dark .typography-preview .preview-cell { background: #0f172a !important; border-bottom-color: #334155 !important; }
    .dark .typography-preview .preview-text { color: #f1f5f9 !important; }
    .dark .typography-preview tr:hover .preview-cell { background: #1e293b !important; }

    /* Colors AS-IS preview */
    .dark .colors-asis-header { color: #e2e8f0 !important; background: #1e293b !important; }
    .dark .colors-asis-preview { background: #0f172a !important; }
    .dark .color-row-asis { background: #1e293b !important; border-color: #475569 !important; }
    .dark .color-name-asis { color: #f1f5f9 !important; }
    .dark .frequency { color: #cbd5e1 !important; }
    .dark .color-meta-asis .aa-pass { color: #22c55e !important; background: #14532d !important; }
    .dark .color-meta-asis .aa-fail { color: #f87171 !important; background: #450a0a !important; }
    .dark .context-badge { background: #334155 !important; color: #e2e8f0 !important; }

    /* Color ramps preview */
    .dark .color-ramps-preview { background: #0f172a !important; }
    .dark .ramps-header-info { color: #e2e8f0 !important; background: #1e293b !important; }
    .dark .ramp-header { background: #1e293b !important; }
    .dark .ramp-header-label { color: #cbd5e1 !important; }
    .dark .color-row { background: #1e293b !important; border-color: #475569 !important; }
    .dark .color-name { color: #f1f5f9 !important; background: #475569 !important; }
    .dark .color-hex { color: #cbd5e1 !important; }

    /* Spacing preview */
    .dark .spacing-asis-preview { background: #0f172a !important; }
    .dark .spacing-row-asis { background: #1e293b !important; }
    .dark .spacing-label { color: #f1f5f9 !important; }

    /* Radius preview */
    .dark .radius-asis-preview { background: #0f172a !important; }
    .dark .radius-item { background: #1e293b !important; }
    .dark .radius-label { color: #f1f5f9 !important; }

    /* Shadows preview */
    .dark .shadows-asis-preview { background: #0f172a !important; }
    .dark .shadow-item { background: #1e293b !important; }
    .dark .shadow-box { background: #334155 !important; }
    .dark .shadow-label { color: #f1f5f9 !important; }
    .dark .shadow-value { color: #94a3b8 !important; }

    /* Semantic color ramps */
    .dark .sem-ramps-preview { background: #0f172a !important; }
    .dark .sem-category { background: #1e293b !important; border-color: #475569 !important; }
    .dark .sem-cat-title { color: #f1f5f9 !important; border-bottom-color: #475569 !important; }
    .dark .sem-color-row { background: #0f172a !important; border-color: #334155 !important; }
    .dark .sem-role { color: #f1f5f9 !important; }
    .dark .sem-hex { color: #cbd5e1 !important; }
    .dark .llm-rec { background: #422006 !important; border-color: #b45309 !important; }
    .dark .rec-label { color: #fbbf24 !important; }
    .dark .rec-issue { color: #fde68a !important; }
    .dark .rec-arrow { color: #fbbf24 !important; }
    .dark .llm-summary { background: #2e1065 !important; border-color: #7C3AED !important; }
    .dark .llm-summary h4 { color: #c4b5fd !important; }
    .dark .llm-summary ul, .dark .llm-summary li { color: #ddd6fe !important; }

    /* Score badges */
    .dark .score-badge.high { background: #14532d; color: #86efac; }
    .dark .score-badge.medium { background: #422006; color: #fde68a; }
    .dark .score-badge.low { background: #450a0a; color: #fca5a5; }

    /* Markdown tables */
    .dark .prose table th, .dark .markdown-text table th { background: #1e293b !important; color: #e2e8f0 !important; border-color: #475569 !important; }
    .dark .prose table td, .dark .markdown-text table td { color: #e2e8f0 !important; border-color: #334155 !important; }
    .dark .prose table tr, .dark .markdown-text table tr { background: #0f172a !important; }
    .dark .prose table tr:nth-child(even), .dark .markdown-text table tr:nth-child(even) { background: #1e293b !important; }

    /* Generic dark HTML text */
    .dark .gradio-html p, .dark .gradio-html span, .dark .gradio-html div { color: #e2e8f0; }
    """
    
    with gr.Blocks(
        title="Design System Automation v3",
        theme=corporate_theme,
        css=custom_css
    ) as app:
        
        # Header with branding
        gr.HTML("""
        <div class="app-header">
            <h1>🎨 Design System Automation</h1>
            <p>Reverse-engineer design systems from live websites • AI-powered analysis • Figma-ready export</p>
        </div>
        """)

        # Progress stepper — always visible, updated by JS
        progress_stepper = gr.HTML(
            value=_render_stepper(active=1),
            elem_classes=["progress-stepper-wrap"]
        )

        # =================================================================
        # CONFIGURATION
        # =================================================================

        with gr.Accordion("⚙️ Configuration", open=not bool(HF_TOKEN_FROM_ENV)):
            gr.Markdown("**HuggingFace Token** — Required for Stage 2 AI analysis (LLM agents). "
                        "Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). "
                        "Stage 1 (extraction) works without a token. If set as an environment variable, it loads automatically.",
                        elem_classes=["section-desc"])
            with gr.Row():
                hf_token_input = gr.Textbox(
                    label="HF Token", placeholder="hf_xxxx" if not HF_TOKEN_FROM_ENV else "Token loaded from environment",
                    type="password", scale=4, value="",
                )
                save_token_btn = gr.Button("💾 Save", scale=1)
            token_status = gr.Markdown("✅ Token loaded from environment" if HF_TOKEN_FROM_ENV else "⏳ Enter token")
            
            def save_token(token):
                if token and len(token) > 10:
                    os.environ["HF_TOKEN"] = token.strip()
                    return "✅ **Token saved!** You can now use Stage 2 AI analysis. Close this section and enter a URL below to begin."
                return "❌ **Invalid token** — please enter a valid HuggingFace token (starts with `hf_`, at least 10 characters). Get one free at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)."
            
            save_token_btn.click(save_token, [hf_token_input], [token_status])
        
        # =================================================================
        # URL INPUT & PAGE DISCOVERY
        # =================================================================
        
        with gr.Accordion("🔍 Step 1: Discover Pages", open=True):
            gr.Markdown("Enter the homepage URL of any website. The crawler will find up to 20 internal pages "
                        "(homepage, about, contact, product pages, etc.). You then select which pages to scan "
                        "for design tokens (colors, typography, spacing, radius, and shadows).",
                        elem_classes=["section-desc"])

            with gr.Row():
                url_input = gr.Textbox(label="Website URL", placeholder="https://example.com", scale=4)
                discover_btn = gr.Button("🔍 Discover Pages", variant="primary", scale=1)
            gr.Markdown("*Enter the full URL including `https://` — the crawler will follow internal links from this page.*",
                        elem_classes=["section-desc"])

            discover_status = gr.Markdown("")

            with gr.Row():
                log_output = gr.Textbox(label="📋 Log", lines=8, interactive=False)

            pages_table = gr.Dataframe(
                headers=["Select", "URL", "Title", "Type", "Status"],
                datatype=["bool", "str", "str", "str", "str"],
                label="Discovered Pages",
                interactive=True,
                visible=False,
            )
            gr.Markdown("*Use the **Select** checkbox to choose pages for extraction. Uncheck pages you want to skip "
                        "(login pages, error pages, etc.). **Type** shows the detected page category. Up to 10 pages will be processed.*",
                        elem_classes=["section-desc"])

            gr.Markdown("*Extraction scans each selected page at two viewport sizes — Desktop (1440px) and Mobile (375px) — "
                        "pulling colors, typography, spacing, radius, and shadows from computed CSS.*",
                        elem_classes=["section-desc"])
            extract_btn = gr.Button("🚀 Extract Tokens (Desktop + Mobile)", variant="primary", visible=False)
        
        # =================================================================
        # STAGE 1: EXTRACTION REVIEW
        # =================================================================
        
        with gr.Accordion("📊 Stage 1: Review Extracted Tokens", open=False) as stage1_accordion:

            extraction_status = gr.Markdown("")

            gr.Markdown("Review the design tokens extracted from your website. Use the **viewport toggle** to switch between "
                        "Desktop (1440px) and Mobile (375px) data. **Accept or reject** individual tokens using the checkboxes — "
                        "rejected tokens will be excluded from your design system export.",
                        elem_classes=["section-desc"])

            viewport_toggle = gr.Radio(
                choices=["Desktop (1440px)", "Mobile (375px)"],
                value="Desktop (1440px)",
                label="Viewport",
            )

            with gr.Tabs():
                with gr.Tab("🎨 Colors"):
                    gr.Markdown("*Each row is a unique color found on the site. **Confidence** shows extraction certainty. "
                                "**AA** indicates WCAG accessibility pass/fail for normal text. **Context** shows where the color was used.*",
                                elem_classes=["section-desc"])
                    colors_table = gr.Dataframe(
                        headers=["Accept", "Color", "Suggested Name", "Frequency", "Confidence", "Contrast", "AA", "Context"],
                        datatype=["bool", "str", "str", "number", "str", "str", "str", "str"],
                        label="Colors",
                        interactive=True,
                    )
                    with gr.Accordion("👁️ Visual Preview", open=False):
                        stage1_colors_preview = gr.HTML(
                            value="<div class='placeholder-msg'>Colors preview will appear after extraction...</div>",
                            label="Colors Preview"
                        )

                with gr.Tab("📝 Typography"):
                    gr.Markdown("*Detected font styles sorted by frequency. **Size** is computed font-size, **Weight** is font-weight "
                                "(400=regular, 700=bold). **Suggested Name** is a semantic token name (e.g., heading.xl). "
                                "Uncheck rows to exclude from your design system.*",
                                elem_classes=["section-desc"])
                    typography_table = gr.Dataframe(
                        headers=["Accept", "Font", "Size", "Weight", "Line Height", "Suggested Name", "Frequency", "Confidence"],
                        datatype=["bool", "str", "str", "str", "str", "str", "number", "str"],
                        label="Typography",
                        interactive=True,
                    )
                    with gr.Accordion("👁️ Visual Preview", open=False):
                        stage1_typography_preview = gr.HTML(
                            value="<div class='placeholder-msg'>Typography preview will appear after extraction...</div>",
                            label="Typography Preview"
                        )

                with gr.Tab("📏 Spacing"):
                    gr.Markdown("*Spacing values (margins, paddings, gaps) extracted from the site. **Base 8** shows whether "
                                "the value aligns with the 8px grid standard. Values are sorted smallest to largest. "
                                "Uncheck irregular spacing values you want to exclude.*",
                                elem_classes=["section-desc"])
                    spacing_table = gr.Dataframe(
                        headers=["Accept", "Value", "Pixels", "Suggested Name", "Frequency", "Base 8", "Confidence"],
                        datatype=["bool", "str", "str", "str", "number", "str", "str"],
                        label="Spacing",
                        interactive=True,
                    )
                    with gr.Accordion("👁️ Visual Preview", open=False):
                        stage1_spacing_preview = gr.HTML(
                            value="<div class='placeholder-msg'>Spacing preview will appear after extraction...</div>",
                            label="Spacing Preview"
                        )

                with gr.Tab("🔘 Radius"):
                    gr.Markdown("*Border-radius values found across UI elements (buttons, cards, inputs). **Context** shows "
                                "which elements use each value. A consistent radius scale creates a cohesive UI.*",
                                elem_classes=["section-desc"])
                    radius_table = gr.Dataframe(
                        headers=["Accept", "Value", "Frequency", "Context"],
                        datatype=["bool", "str", "number", "str"],
                        label="Border Radius",
                        interactive=True,
                    )
                    with gr.Accordion("👁️ Visual Preview", open=False):
                        stage1_radius_preview = gr.HTML(
                            value="<div class='placeholder-msg'>Radius preview will appear after extraction...</div>",
                            label="Radius Preview"
                        )

                with gr.Tab("🌑 Shadows"):
                    gr.Markdown("*Box shadow values used for elevation and depth across the site. "
                                "Shows blur radius, spread, and color for each shadow layer.*",
                                elem_classes=["section-desc"])
                    stage1_shadows_preview = gr.HTML(
                        value="<div class='placeholder-msg'>Shadows preview will appear after extraction...</div>",
                        label="Shadows Preview"
                    )

                with gr.Tab("🧠 Semantic Colors"):
                    gr.Markdown("*Colors automatically categorized by their usage role: Brand (primary, secondary, accent), "
                                "Text (headings, body, muted), Background, Border, and Feedback (success, warning, error).*",
                                elem_classes=["section-desc"])
                    stage1_semantic_preview = gr.HTML(
                        value="<div class='placeholder-msg'>Semantic color analysis will appear after extraction...</div>",
                        label="Semantic Colors Preview"
                    )
            
            gr.Markdown("---")
            gr.Markdown("When you are satisfied with the accepted tokens, **proceed to Stage 2** for AI-powered analysis "
                        "and improvement suggestions. Or **download the raw Stage 1 JSON** for immediate use in Figma Tokens Studio.",
                        elem_classes=["section-desc"])
            with gr.Row():
                proceed_stage2_btn = gr.Button("➡️ Proceed to Stage 2: AI Upgrades", variant="primary")
                download_stage1_btn = gr.Button("📥 Download Stage 1 JSON", variant="secondary")
        
        # =================================================================
        # STAGE 2: AI UPGRADES
        # =================================================================
        
        with gr.Accordion("🧠 Stage 2: AI-Powered Analysis", open=False) as stage2_accordion:

            # Stage header
            gr.HTML("""
            <div class="stage-header">
                <h2>🧠 Stage 2: Multi-Agent Analysis</h2>
                <p class="stage-header-subtitle" style="color: #64748b; margin-top: 4px;">Rule Engine + Benchmark Research + LLM Agents</p>
            </div>
            """)

            stage2_status = gr.Markdown("Click **'Run Analysis'** below to start AI-powered design system analysis. "
                                       "This runs a 4-layer pipeline: Rule Engine → Benchmark Research → LLM Agents → Head Synthesizer.")

            # ── Config + Run button ──
            with gr.Row():
                with gr.Column(scale=3):
                    benchmark_checkboxes = gr.CheckboxGroup(
                        choices=[
                            ("🟢 Material Design 3", "material_design_3"),
                            ("🍎 Apple HIG", "apple_hig"),
                            ("🛒 Shopify Polaris", "shopify_polaris"),
                            ("🔵 Atlassian", "atlassian_design"),
                            ("🔷 IBM Carbon", "ibm_carbon"),
                            ("🌊 Tailwind CSS", "tailwind_css"),
                            ("🐜 Ant Design", "ant_design"),
                            ("⚡ Chakra UI", "chakra_ui"),
                        ],
                        value=["material_design_3", "shopify_polaris", "atlassian_design"],
                        label="📊 Benchmarks to Compare Against",
                    )
                with gr.Column(scale=1):
                    analyze_btn_v2 = gr.Button(
                        "🚀 Run Analysis",
                        variant="primary",
                        size="lg",
                    )
                    gr.Markdown(
                        "<small style='color: #64748b;'>Cost: ~$0.003 per run</small>",
                        elem_classes=["section-desc"])

            # ── Always-visible log panel ──
            with gr.Group(elem_classes=["always-visible-log"]):
                stage2_log = gr.Textbox(
                    label="📋 Live Analysis Log",
                    lines=20,
                    interactive=False,
                    elem_classes=["log-container"]
                )

            # ═══════════════════════════════════════════════
            # TAB-BASED RESULTS (reduce scrolling)
            # ═══════════════════════════════════════════════
            with gr.Tabs():

                # ── Tab 1: Scores & Actions ──
                with gr.Tab("📊 Scores & Actions"):
                    gr.Markdown("*Overall scores for your design system. Each score is 0–100. "
                                "Priority actions show the highest-impact fixes.*",
                                elem_classes=["section-desc"])

                    scores_dashboard = gr.HTML(
                        value="<div class='placeholder-msg placeholder-lg'>Scores will appear after analysis...</div>",
                        label="Scores"
                    )

                    priority_actions_html = gr.HTML(
                        value="<div class='placeholder-msg'>Priority actions will appear after analysis...</div>",
                        label="Priority Actions"
                    )

                    # As-Is vs To-Be summary cards
                    stage2_asis_tobe = gr.HTML(
                        value="<div class='placeholder-msg'>As-Is → To-Be transformation summary will appear after analysis...</div>",
                        label="Transformation Summary"
                    )

                # ── Tab 2: Benchmarks ──
                with gr.Tab("📈 Benchmarks"):
                    gr.Markdown("*Your tokens compared against industry design systems. Visual cards show per-category match.*",
                                elem_classes=["section-desc"])
                    benchmark_comparison_md = gr.HTML(
                        value="<div class='placeholder-msg'>Benchmark comparison will appear after analysis...</div>",
                        label="Benchmarks"
                    )

                # ── Tab 3: Typography ──
                with gr.Tab("📐 Typography"):
                    gr.Markdown("*Type scale analysis with standard ratio comparisons. Choose a scale to apply.*",
                                elem_classes=["section-desc"])

                    with gr.Accordion("👁️ Typography Visual Preview", open=True):
                        stage2_typography_preview = gr.HTML(
                            value="<div class='placeholder-msg'>Typography preview will appear after analysis...</div>",
                            label="Typography Preview"
                        )

                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("### 🖥️ Desktop (1440px)")
                            typography_desktop = gr.Dataframe(
                                headers=["Token", "Current", "Scale 1.2", "Scale 1.25 ⭐", "Scale 1.333", "Keep"],
                                datatype=["str", "str", "str", "str", "str", "str"],
                                label="Desktop Typography",
                                interactive=False,
                            )
                        with gr.Column(scale=2):
                            gr.Markdown("### 📱 Mobile (375px)")
                            typography_mobile = gr.Dataframe(
                                headers=["Token", "Current", "Scale 1.2", "Scale 1.25 ⭐", "Scale 1.333", "Keep"],
                                datatype=["str", "str", "str", "str", "str", "str"],
                                label="Mobile Typography",
                                interactive=False,
                            )

                    with gr.Row():
                        with gr.Column():
                            type_scale_radio = gr.Radio(
                                choices=["Keep Current", "Scale 1.2 (Minor Third)", "Scale 1.25 (Major Third) ⭐", "Scale 1.333 (Perfect Fourth)"],
                                value="Scale 1.25 (Major Third) ⭐",
                                label="Select Type Scale",
                                interactive=True,
                            )
                            gr.Markdown("*Font family preserved. Sizes rounded to even numbers.*",
                                        elem_classes=["section-desc"])

                # ── Tab 4: Colors ──
                with gr.Tab("🎨 Colors"):
                    gr.Markdown("*Complete color analysis: base colors, AI ramps (50–950), and recommendations.*",
                                elem_classes=["section-desc"])

                    # Color Naming Convention Preview
                    with gr.Accordion("🏷️ Naming Convention — Preview Before Export", open=True):
                        gr.Markdown("**Choose how colors are named.** 100% rule-based — no LLM.",
                                    elem_classes=["section-desc"])
                        with gr.Row():
                            naming_convention_stage2 = gr.Dropdown(
                                choices=["semantic", "tailwind", "material"],
                                value="semantic",
                                label="🎨 Naming Convention",
                                info="semantic = color.brand.primary | tailwind = brand-primary | material = color.brand.primary",
                                scale=2,
                            )
                            preview_colors_btn_stage2 = gr.Button("👁️ Preview", variant="secondary", scale=1)
                        color_preview_output_stage2 = gr.Textbox(
                            label="Color Classification Preview (Rule-Based)",
                            lines=18, max_lines=40, interactive=False,
                            placeholder="Click 'Preview' to see how colors will be named in the export.",
                        )

                    # LLM Recommendations
                    with gr.Accordion("🤖 LLM Color Recommendations", open=True):
                        gr.Markdown("*AI-suggested accessibility fixes and improvements.*",
                                    elem_classes=["section-desc"])
                        llm_color_recommendations = gr.HTML(
                            value="<div class='placeholder-msg'>LLM recommendations will appear after analysis...</div>",
                            label="LLM Recommendations"
                        )
                        color_recommendations_table = gr.Dataframe(
                            headers=["Accept", "Role", "Current", "Issue", "Suggested", "Contrast"],
                            datatype=["bool", "str", "str", "str", "str", "str"],
                            label="Color Recommendations",
                            interactive=True,
                            col_count=(6, "fixed"),
                        )

                    # Color Ramps
                    with gr.Accordion("👁️ Color Ramps (Semantic Groups)", open=True):
                        stage2_color_ramps_preview = gr.HTML(
                            value="<div class='placeholder-msg'>Color ramps preview will appear after analysis...</div>",
                            label="Color Ramps Preview"
                        )

                    base_colors_display = gr.Markdown("*Base colors will appear after analysis*")
                    color_ramps_display = gr.Markdown("*Color ramps will appear after analysis*")
                    color_ramps_checkbox = gr.Checkbox(
                        label="✓ Generate color ramps (keeps base colors, adds 50-950 shades)",
                        value=True,
                    )

                # ── Tab 5: Spacing / Radius / Shadows ──
                with gr.Tab("📏 Spacing · Radius · Shadows"):

                    gr.Markdown("## 📏 Spacing")
                    gr.Markdown("*Spacing values compared against 8px and 4px grids.*",
                                elem_classes=["section-desc"])
                    with gr.Row():
                        with gr.Column(scale=2):
                            spacing_comparison = gr.Dataframe(
                                headers=["Current", "8px Grid", "4px Grid"],
                                datatype=["str", "str", "str"],
                                label="Spacing Comparison",
                                interactive=False,
                            )
                        with gr.Column(scale=1):
                            spacing_radio = gr.Radio(
                                choices=["Keep Current", "8px Base Grid ⭐", "4px Base Grid"],
                                value="8px Base Grid ⭐",
                                label="Spacing System",
                                interactive=True,
                            )

                    gr.Markdown("---")
                    gr.Markdown("## 🔘 Border Radius")
                    gr.Markdown("*Radius tokens mapped to standard scale (none → full).*",
                                elem_classes=["section-desc"])
                    radius_display = gr.Markdown("*Radius tokens will appear after analysis*")

                    gr.Markdown("---")
                    gr.Markdown("## 🌫️ Shadows")
                    gr.Markdown("*Elevation tokens (shadow.xs → shadow.2xl).*",
                                elem_classes=["section-desc"])
                    shadows_display = gr.Markdown("*Shadow tokens will appear after analysis*")

            # ── Apply / Reset ──
            gr.Markdown("---")
            gr.Markdown("**Apply** saves your choices to the export. **Reset** reverts to extracted values.",
                        elem_classes=["section-desc"])
            with gr.Row():
                apply_upgrades_btn = gr.Button("✨ Apply Selected Upgrades", variant="primary", scale=2)
                reset_btn = gr.Button("↩️ Reset to Original", variant="secondary", scale=1)
            apply_status = gr.Markdown("", elem_classes=["apply-status-box"])
        
        # =================================================================
        # STAGE 3: EXPORT
        # =================================================================
        
        with gr.Accordion("📦 Stage 3: Export", open=False) as stage3_accordion:
            gr.Markdown("Export your finalized design tokens as JSON, compatible with **Figma Tokens Studio**.",
                        elem_classes=["section-desc"])
            gr.Markdown("""
- **Naming Convention:** Choose how colors are named in the export. Preview before exporting to verify.
- **Stage 1 JSON (As-Is):** Raw extracted tokens — useful for archival or baseline comparison.
- **Final JSON (Upgraded):** Tokens with your selected improvements applied. **Recommended export.**
            """, elem_classes=["section-desc"])

            with gr.Row():
                naming_convention = gr.Dropdown(
                    choices=["semantic", "tailwind", "material"],
                    value="semantic",
                    label="🎨 Naming Convention",
                    info="semantic = color.brand.primary | tailwind = brand-primary | material = color.brand.primary",
                    scale=2,
                )
                preview_colors_btn = gr.Button("👁️ Preview Color Names", variant="secondary", scale=1)

            color_preview_output = gr.Textbox(
                label="Color Classification Preview (Rule-Based — No LLM)",
                lines=15,
                max_lines=30,
                interactive=False,
            )

            with gr.Row():
                export_stage1_btn = gr.Button("📥 Export Stage 1 (As-Is)", variant="secondary")
                export_final_btn = gr.Button("📥 Export Final (Upgraded)", variant="primary")

            gr.Markdown("*The generated JSON uses a flat token structure compatible with Figma Tokens Studio. "
                        "Copy the contents or save as a `.json` file.*",
                        elem_classes=["section-desc"])
            export_output = gr.Code(label="Tokens JSON", language="json", lines=25)

            # Stage 2 color naming preview (primary — visible before export)
            preview_colors_btn_stage2.click(
                preview_color_classification,
                inputs=[naming_convention_stage2],
                outputs=[color_preview_output_stage2],
            )
            # Sync naming convention: Stage 2 dropdown → Stage 3 dropdown
            naming_convention_stage2.change(
                lambda v: v,
                inputs=[naming_convention_stage2],
                outputs=[naming_convention],
            )
            # Stage 3 also syncs back
            naming_convention.change(
                lambda v: v,
                inputs=[naming_convention],
                outputs=[naming_convention_stage2],
            )

            # Stage 3 preview (kept for convenience)
            preview_colors_btn.click(
                preview_color_classification,
                inputs=[naming_convention],
                outputs=[color_preview_output],
            )
            export_stage1_btn.click(
                export_stage1_json,
                inputs=[naming_convention],
                outputs=[export_output],
            )
            export_final_btn.click(
                export_tokens_json,
                inputs=[naming_convention],
                outputs=[export_output],
            )
        
        # =================================================================
        # EVENT HANDLERS
        # =================================================================

        # Store data for viewport toggle
        desktop_data = gr.State({})
        mobile_data = gr.State({})

        # ── Discover pages ──
        discover_btn.click(
            fn=discover_pages,
            inputs=[url_input],
            outputs=[discover_status, log_output, pages_table],
        ).then(
            fn=lambda: (gr.update(visible=True), gr.update(visible=True),
                        _render_stepper(active=2, completed=[1])),
            outputs=[pages_table, extract_btn, progress_stepper],
        )

        # ── Extract tokens ──
        extract_btn.click(
            fn=extract_tokens,
            inputs=[pages_table],
            outputs=[extraction_status, log_output, desktop_data, mobile_data,
                     stage1_typography_preview, stage1_colors_preview,
                     stage1_semantic_preview,
                     stage1_spacing_preview, stage1_radius_preview, stage1_shadows_preview],
        ).then(
            fn=lambda d: (d.get("colors", []), d.get("typography", []), d.get("spacing", []), d.get("radius", [])),
            inputs=[desktop_data],
            outputs=[colors_table, typography_table, spacing_table, radius_table],
        ).then(
            fn=lambda: (gr.update(open=True), gr.update(open=True),
                        _render_stepper(active=3, completed=[1, 2])),
            outputs=[stage1_accordion, stage2_accordion, progress_stepper],
        )

        # ── Viewport toggle ──
        viewport_toggle.change(
            fn=switch_viewport,
            inputs=[viewport_toggle],
            outputs=[colors_table, typography_table, spacing_table, radius_table],
        )

        # ── Stage 2: Analyze ──
        analyze_btn_v2.click(
            fn=run_stage2_analysis_v2,
            inputs=[benchmark_checkboxes],
            outputs=[
                stage2_status,
                stage2_log,
                benchmark_comparison_md,
                scores_dashboard,
                priority_actions_html,
                color_recommendations_table,
                typography_desktop,
                typography_mobile,
                stage2_typography_preview,
                stage2_color_ramps_preview,
                llm_color_recommendations,
                spacing_comparison,
                base_colors_display,
                color_ramps_display,
                radius_display,
                shadows_display,
                color_preview_output_stage2,
                stage2_asis_tobe,
            ],
        ).then(
            fn=lambda: (gr.update(open=True),
                        _render_stepper(active=4, completed=[1, 2, 3])),
            outputs=[stage3_accordion, progress_stepper],
        )

        # ── Stage 2: Apply upgrades ──
        apply_upgrades_btn.click(
            fn=apply_selected_upgrades,
            inputs=[type_scale_radio, spacing_radio, color_ramps_checkbox, color_recommendations_table],
            outputs=[apply_status, stage2_log],
        ).then(
            fn=lambda: (gr.update(open=True),
                        _render_stepper(active=5, completed=[1, 2, 3, 4])),
            outputs=[stage3_accordion, progress_stepper],
        )

        # ── Stage 2: Reset to original ──
        reset_btn.click(
            fn=reset_to_original,
            outputs=[type_scale_radio, spacing_radio, color_ramps_checkbox, apply_status, stage2_log],
        )

        # ── Stage 1: Download JSON ──
        download_stage1_btn.click(
            fn=export_stage1_json,
            outputs=[export_output],
        )

        # ── Proceed to Stage 2 ──
        proceed_stage2_btn.click(
            fn=lambda: gr.update(open=True),
            outputs=[stage2_accordion],
        )
        
        # =================================================================
        # FOOTER
        # =================================================================
        
        gr.Markdown("""
        ---
        <div style="text-align: center; color: #94a3b8; font-size: 12px; padding: 12px 0;">
        <strong>Design System Automation v3</strong> · Playwright + Firecrawl + HuggingFace<br/>
        Rule Engine (FREE) + ReAct LLM Agents (AURORA · ATLAS · SENTINEL · NEXUS)
        </div>
        """)
    
    return app


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
