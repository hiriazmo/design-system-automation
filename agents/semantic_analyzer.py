"""
Agent 1C: Semantic Color Analyzer
Design System Extractor v2

Persona: Design System Semanticist

Responsibilities:
- Analyze colors based on their actual CSS usage
- Categorize into semantic roles (brand, text, background, border, feedback)
- Use LLM to understand color relationships and hierarchy
- Provide structured output for Stage 1 UI and Stage 2 analysis
"""

import json
import re
from typing import Optional, Callable
from datetime import datetime

from core.color_utils import (
    parse_color,
    get_contrast_with_white,
    get_contrast_with_black,
    check_wcag_compliance,
)


class SemanticColorAnalyzer:
    """
    Analyzes extracted colors and categorizes them by semantic role.
    
    Uses LLM to understand:
    - Which colors are brand/primary colors (used on buttons, CTAs)
    - Which colors are for text (used with 'color' property)
    - Which colors are backgrounds (used with 'background-color')
    - Which colors are borders (used with 'border-color')
    - Which colors are feedback states (error, success, warning)
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize the semantic analyzer.
        
        Args:
            llm_provider: Optional LLM provider for AI analysis.
                         If None, uses rule-based fallback.
        """
        self.llm_provider = llm_provider
        self.analysis_result = {}
        self.logs = []
        
    def log(self, message: str):
        """Add timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        
    def get_logs(self) -> str:
        """Get all logs as string."""
        return "\n".join(self.logs)
    
    def _prepare_color_data_for_llm(self, colors: dict) -> str:
        """
        Prepare color data in a format optimized for LLM analysis.
        
        Args:
            colors: Dict of color tokens with metadata
            
        Returns:
            Formatted string for LLM prompt
        """
        color_entries = []
        
        for name, token in colors.items():
            # Handle both dict and object formats
            if hasattr(token, 'value'):
                hex_val = token.value
                frequency = token.frequency
                contexts = token.contexts if hasattr(token, 'contexts') else []
                elements = token.elements if hasattr(token, 'elements') else []
                css_props = token.css_properties if hasattr(token, 'css_properties') else []
            else:
                hex_val = token.get('value', '#000000')
                frequency = token.get('frequency', 0)
                contexts = token.get('contexts', [])
                elements = token.get('elements', [])
                css_props = token.get('css_properties', [])
            
            # Calculate color properties
            contrast_white = get_contrast_with_white(hex_val)
            contrast_black = get_contrast_with_black(hex_val)
            
            # Determine luminance
            try:
                r = int(hex_val[1:3], 16)
                g = int(hex_val[3:5], 16)
                b = int(hex_val[5:7], 16)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                
                # Calculate saturation
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                saturation = (max_c - min_c) / 255 if max_c > 0 else 0
            except:
                luminance = 0.5
                saturation = 0
            
            entry = {
                "hex": hex_val,
                "name": name,
                "frequency": frequency,
                "css_properties": css_props[:5],  # Limit for prompt size
                "elements": elements[:5],
                "contexts": contexts[:3],
                "luminance": round(luminance, 2),
                "saturation": round(saturation, 2),
                "contrast_on_white": round(contrast_white, 2),
                "contrast_on_black": round(contrast_black, 2),
                "aa_compliant_on_white": contrast_white >= 4.5,
            }
            color_entries.append(entry)
        
        # Sort by frequency for LLM to see most important first
        color_entries.sort(key=lambda x: -x['frequency'])
        
        # Limit to top 50 colors for LLM (avoid token limits)
        return json.dumps(color_entries[:50], indent=2)
    
    def _build_llm_prompt(self, color_data: str) -> str:
        """Build the prompt for LLM semantic analysis."""
        
        return f"""You are a Design System Analyst specializing in color semantics.

TASK: Analyze these extracted colors and categorize them by their semantic role in the UI.

EXTRACTED COLORS (sorted by frequency):
{color_data}

ANALYSIS RULES:
1. BRAND/PRIMARY colors are typically:
   - Used on buttons, links, CTAs (elements: button, a, input[type=submit])
   - Applied via background-color on interactive elements
   - Saturated (saturation > 0.3) and not gray
   - High frequency on interactive elements

2. TEXT colors are typically:
   - Applied via "color" CSS property (not background-color)
   - Used on text elements (p, span, h1-h6, label)
   - Form a hierarchy: primary (darkest), secondary (medium), muted (lightest)
   - Low saturation (grays)

3. BACKGROUND colors are typically:
   - Applied via "background-color" on containers
   - Used on div, section, main, body, card elements
   - Light colors (luminance > 0.8) for light themes
   - May include dark backgrounds for inverse sections

4. BORDER colors are typically:
   - Applied via border-color properties
   - Often gray/neutral
   - Lower frequency than text/background

5. FEEDBACK colors are:
   - Red variants = error
   - Green variants = success  
   - Yellow/orange = warning
   - Blue variants = info
   - Often used with specific class contexts

OUTPUT FORMAT (JSON):
{{
  "brand": {{
    "primary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "secondary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "accent": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}}
  }},
  "text": {{
    "primary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "secondary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "muted": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "inverse": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}}
  }},
  "background": {{
    "primary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "secondary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "tertiary": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "inverse": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}}
  }},
  "border": {{
    "default": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "strong": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}}
  }},
  "feedback": {{
    "error": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "success": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "warning": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}},
    "info": {{"hex": "#xxx", "confidence": "high|medium|low", "reason": "..."}}
  }},
  "summary": {{
    "total_colors_analyzed": 50,
    "brand_colors_found": 2,
    "has_clear_hierarchy": true,
    "accessibility_notes": "..."
  }}
}}

IMPORTANT:
- Only include roles where you found a matching color
- Set confidence based on how certain you are
- Provide brief reasoning for each categorization
- If no color fits a role, omit that key

Return ONLY valid JSON, no other text."""

    def _rule_based_analysis(self, colors: dict) -> dict:
        """
        Fallback rule-based analysis when LLM is not available.
        
        Uses heuristics based on:
        - CSS properties (color vs background-color vs border-color)
        - Element types (button, a, p, div, etc.)
        - Color characteristics (saturation, luminance)
        - Frequency
        """
        self.log("   Using rule-based analysis (no LLM)")
        
        result = {
            "brand": {},
            "text": {},
            "background": {},
            "border": {},
            "feedback": {},
            "summary": {
                "total_colors_analyzed": len(colors),
                "brand_colors_found": 0,
                "has_clear_hierarchy": False,
                "accessibility_notes": "",
                "method": "rule-based"
            }
        }
        
        # Categorize colors
        brand_candidates = []
        text_candidates = []
        background_candidates = []
        border_candidates = []
        feedback_candidates = {"error": [], "success": [], "warning": [], "info": []}
        
        for name, token in colors.items():
            # Extract data
            if hasattr(token, 'value'):
                hex_val = token.value
                frequency = token.frequency
                contexts = token.contexts if hasattr(token, 'contexts') else []
                elements = token.elements if hasattr(token, 'elements') else []
                css_props = token.css_properties if hasattr(token, 'css_properties') else []
            else:
                hex_val = token.get('value', '#000000')
                frequency = token.get('frequency', 0)
                contexts = token.get('contexts', [])
                elements = token.get('elements', [])
                css_props = token.get('css_properties', [])
            
            # Calculate color properties
            try:
                r = int(hex_val[1:3], 16)
                g = int(hex_val[3:5], 16)
                b = int(hex_val[5:7], 16)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                saturation = (max_c - min_c) / 255 if max_c > 0 else 0
                
                # Determine hue for feedback colors
                if max_c == min_c:
                    hue = 0
                elif max_c == r:
                    hue = 60 * ((g - b) / (max_c - min_c) % 6)
                elif max_c == g:
                    hue = 60 * ((b - r) / (max_c - min_c) + 2)
                else:
                    hue = 60 * ((r - g) / (max_c - min_c) + 4)
            except:
                luminance = 0.5
                saturation = 0
                hue = 0
            
            color_info = {
                "hex": hex_val,
                "name": name,
                "frequency": frequency,
                "luminance": luminance,
                "saturation": saturation,
                "hue": hue,
                "css_props": css_props,
                "elements": elements,
                "contexts": contexts,
            }
            
            # --- CATEGORIZATION RULES ---
            
            # BRAND: Saturated colors - multiple detection methods
            interactive_elements = ['button', 'a', 'input', 'select', 'submit', 'btn', 'cta']
            is_interactive = any(el in str(elements).lower() for el in interactive_elements)
            has_bg_prop = any('background' in str(p).lower() for p in css_props)
            
            # Method 1: Interactive elements with background
            if saturation > 0.25 and is_interactive and has_bg_prop:
                brand_candidates.append(color_info)
            # Method 2: Highly saturated + high frequency (works for Firecrawl)
            elif saturation > 0.35 and frequency > 15:
                brand_candidates.append(color_info)
            # Method 3: Very saturated colors regardless of frequency
            elif saturation > 0.5 and frequency > 5:
                brand_candidates.append(color_info)
            # Method 4: Cyan/Teal range (common brand colors)
            elif 160 <= hue <= 200 and saturation > 0.4 and frequency > 10:
                brand_candidates.append(color_info)
            # Method 5: Lime/Green-Yellow (secondary brand colors)
            elif 60 <= hue <= 90 and saturation > 0.5 and frequency > 5:
                brand_candidates.append(color_info)
            
            # TEXT: Low saturation, used with 'color' property
            has_color_prop = any(p == 'color' or (p.endswith('-color') and 'background' not in p and 'border' not in p)
                                for p in css_props)
            text_elements = ['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'label', 'div', 'text']
            is_text_element = any(el in str(elements).lower() for el in text_elements)
            
            # Text detection - low saturation grays
            if saturation < 0.15 and (has_color_prop or 'text' in str(contexts).lower()):
                text_candidates.append(color_info)
            elif saturation < 0.1 and 0.1 < luminance < 0.8:  # Gray range
                text_candidates.append(color_info)
            elif saturation < 0.1 and luminance < 0.5 and frequency > 50:  # Dark grays used a lot
                text_candidates.append(color_info)
            
            if saturation < 0.15 and (has_color_prop or 'text' in str(contexts).lower()):
                text_candidates.append(color_info)
            elif saturation < 0.1 and luminance < 0.7 and is_text_element:
                text_candidates.append(color_info)
            
            # BACKGROUND: Used with background-color on containers
            container_elements = ['div', 'section', 'main', 'body', 'article', 'header', 'footer', 'card']
            is_container = any(el in str(elements).lower() for el in container_elements)
            
            if has_bg_prop and (is_container or 'background' in str(contexts).lower()):
                if saturation < 0.15:  # Mostly neutral backgrounds
                    background_candidates.append(color_info)
            
            # BORDER: Used with border-color properties
            has_border_prop = any('border' in str(p).lower() for p in css_props)
            
            if has_border_prop or 'border' in str(contexts).lower():
                border_candidates.append(color_info)
            
            # FEEDBACK: Based on hue
            if saturation > 0.3:
                if 0 <= hue <= 30 or 330 <= hue <= 360:  # Red
                    feedback_candidates["error"].append(color_info)
                elif 90 <= hue <= 150:  # Green
                    feedback_candidates["success"].append(color_info)
                elif 30 <= hue <= 60:  # Yellow/Orange
                    feedback_candidates["warning"].append(color_info)
                elif 180 <= hue <= 250:  # Blue
                    feedback_candidates["info"].append(color_info)
        
        # --- SELECT BEST CANDIDATES ---
        
        # Brand: Sort by frequency * saturation
        brand_candidates.sort(key=lambda x: -(x['frequency'] * x['saturation']))
        if brand_candidates:
            result["brand"]["primary"] = {
                "hex": brand_candidates[0]["hex"],
                "confidence": "high" if brand_candidates[0]["frequency"] > 20 else "medium",
                "reason": f"Most frequent saturated color on interactive elements (freq: {brand_candidates[0]['frequency']})"
            }
            result["summary"]["brand_colors_found"] += 1
        if len(brand_candidates) > 1:
            result["brand"]["secondary"] = {
                "hex": brand_candidates[1]["hex"],
                "confidence": "medium",
                "reason": f"Second most frequent brand color (freq: {brand_candidates[1]['frequency']})"
            }
            result["summary"]["brand_colors_found"] += 1
        
        # Text: Sort by luminance (darkest first for primary)
        text_candidates.sort(key=lambda x: x['luminance'])
        if text_candidates:
            result["text"]["primary"] = {
                "hex": text_candidates[0]["hex"],
                "confidence": "high" if text_candidates[0]["luminance"] < 0.3 else "medium",
                "reason": f"Darkest text color (luminance: {text_candidates[0]['luminance']:.2f})"
            }
        if len(text_candidates) > 1:
            # Find secondary (mid-luminance)
            mid_idx = len(text_candidates) // 2
            result["text"]["secondary"] = {
                "hex": text_candidates[mid_idx]["hex"],
                "confidence": "medium",
                "reason": f"Mid-tone text color (luminance: {text_candidates[mid_idx]['luminance']:.2f})"
            }
        if len(text_candidates) > 2:
            result["text"]["muted"] = {
                "hex": text_candidates[-1]["hex"],
                "confidence": "medium",
                "reason": f"Lightest text color (luminance: {text_candidates[-1]['luminance']:.2f})"
            }
        
        # Check for text hierarchy
        if len(text_candidates) >= 3:
            result["summary"]["has_clear_hierarchy"] = True
        
        # Background: Sort by luminance (lightest first for primary)
        background_candidates.sort(key=lambda x: -x['luminance'])
        if background_candidates:
            result["background"]["primary"] = {
                "hex": background_candidates[0]["hex"],
                "confidence": "high" if background_candidates[0]["luminance"] > 0.9 else "medium",
                "reason": f"Lightest background (luminance: {background_candidates[0]['luminance']:.2f})"
            }
        if len(background_candidates) > 1:
            result["background"]["secondary"] = {
                "hex": background_candidates[1]["hex"],
                "confidence": "medium",
                "reason": f"Secondary background (luminance: {background_candidates[1]['luminance']:.2f})"
            }
        # Find dark background for inverse
        dark_bgs = [c for c in background_candidates if c['luminance'] < 0.2]
        if dark_bgs:
            result["background"]["inverse"] = {
                "hex": dark_bgs[0]["hex"],
                "confidence": "medium",
                "reason": f"Dark background for inverse sections (luminance: {dark_bgs[0]['luminance']:.2f})"
            }
        
        # Border: Sort by frequency
        border_candidates.sort(key=lambda x: -x['frequency'])
        if border_candidates:
            result["border"]["default"] = {
                "hex": border_candidates[0]["hex"],
                "confidence": "medium",
                "reason": f"Most common border color (freq: {border_candidates[0]['frequency']})"
            }
        
        # Feedback: Pick highest frequency for each
        for feedback_type, candidates in feedback_candidates.items():
            if candidates:
                candidates.sort(key=lambda x: -x['frequency'])
                result["feedback"][feedback_type] = {
                    "hex": candidates[0]["hex"],
                    "confidence": "medium",
                    "reason": f"Detected {feedback_type} color by hue analysis"
                }
        
        return result
    
    async def analyze_with_llm(self, colors: dict, log_callback: Optional[Callable] = None) -> dict:
        """
        Analyze colors using LLM for semantic categorization.
        
        Args:
            colors: Dict of color tokens
            log_callback: Optional callback for logging
            
        Returns:
            Semantic analysis result
        """
        def log(msg):
            self.log(msg)
            if log_callback:
                log_callback(msg)
        
        log("")
        log("=" * 60)
        log("🧠 SEMANTIC COLOR ANALYSIS (LLM)")
        log("=" * 60)
        log("")
        
        # Prepare data for LLM
        log("   📊 Preparing color data for analysis...")
        color_data = self._prepare_color_data_for_llm(colors)
        log(f"   ✅ Prepared {min(50, len(colors))} colors for analysis")
        
        # Check if LLM provider is available
        if self.llm_provider is None:
            log("   ⚠️ No LLM provider configured, using rule-based analysis")
            self.analysis_result = self._rule_based_analysis(colors)
        else:
            try:
                log("   🤖 Calling LLM for semantic analysis...")
                
                prompt = self._build_llm_prompt(color_data)
                
                # Call LLM
                response = await self.llm_provider.generate(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.3,  # Low temperature for consistent categorization
                )
                
                log("   ✅ LLM response received")
                
                # Parse JSON response
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{[\s\S]*\}', response)
                    if json_match:
                        self.analysis_result = json.loads(json_match.group())
                        self.analysis_result["summary"]["method"] = "llm"
                        log("   ✅ Successfully parsed LLM analysis")
                    else:
                        raise ValueError("No JSON found in response")
                        
                except json.JSONDecodeError as e:
                    log(f"   ⚠️ Failed to parse LLM response: {e}")
                    log("   🔄 Falling back to rule-based analysis")
                    self.analysis_result = self._rule_based_analysis(colors)
                    
            except Exception as e:
                log(f"   ❌ LLM analysis failed: {str(e)}")
                log("   🔄 Falling back to rule-based analysis")
                self.analysis_result = self._rule_based_analysis(colors)
        
        # Log results
        self._log_analysis_results(log)
        
        return self.analysis_result
    
    def analyze_sync(self, colors: dict, log_callback: Optional[Callable] = None) -> dict:
        """
        Synchronous analysis using rule-based approach.
        
        Args:
            colors: Dict of color tokens
            log_callback: Optional callback for logging
            
        Returns:
            Semantic analysis result
        """
        def log(msg):
            self.log(msg)
            if log_callback:
                log_callback(msg)
        
        log("")
        log("=" * 60)
        log("🧠 SEMANTIC COLOR ANALYSIS")
        log("=" * 60)
        log("")
        
        log(f"   📊 Analyzing {len(colors)} colors...")
        
        self.analysis_result = self._rule_based_analysis(colors)
        
        # Log results
        self._log_analysis_results(log)
        
        return self.analysis_result
    
    def _log_analysis_results(self, log: Callable):
        """Log the analysis results in a formatted way."""
        
        result = self.analysis_result
        
        log("")
        log("📊 SEMANTIC ANALYSIS RESULTS:")
        log("")
        
        # Brand colors
        if result.get("brand"):
            log("   🎨 BRAND COLORS:")
            for role, data in result["brand"].items():
                if data:
                    log(f"      {role}: {data['hex']} ({data['confidence']})")
                    log(f"         └─ {data['reason']}")
        
        # Text colors
        if result.get("text"):
            log("")
            log("   📝 TEXT COLORS:")
            for role, data in result["text"].items():
                if data:
                    log(f"      {role}: {data['hex']} ({data['confidence']})")
        
        # Background colors
        if result.get("background"):
            log("")
            log("   🖼️ BACKGROUND COLORS:")
            for role, data in result["background"].items():
                if data:
                    log(f"      {role}: {data['hex']} ({data['confidence']})")
        
        # Border colors
        if result.get("border"):
            log("")
            log("   📏 BORDER COLORS:")
            for role, data in result["border"].items():
                if data:
                    log(f"      {role}: {data['hex']} ({data['confidence']})")
        
        # Feedback colors
        if result.get("feedback"):
            log("")
            log("   🚨 FEEDBACK COLORS:")
            for role, data in result["feedback"].items():
                if data:
                    log(f"      {role}: {data['hex']} ({data['confidence']})")
        
        # Summary
        summary = result.get("summary", {})
        log("")
        log("   📈 SUMMARY:")
        log(f"      Total colors analyzed: {summary.get('total_colors_analyzed', 0)}")
        log(f"      Brand colors found: {summary.get('brand_colors_found', 0)}")
        log(f"      Clear hierarchy: {'Yes' if summary.get('has_clear_hierarchy') else 'No'}")
        log(f"      Analysis method: {summary.get('method', 'unknown')}")
        log("")


def generate_semantic_preview_html(analysis_result: dict) -> str:
    """
    Generate HTML preview showing colors organized by semantic role.
    
    Args:
        analysis_result: Output from SemanticColorAnalyzer
        
    Returns:
        HTML string for Gradio HTML component
    """
    
    # Handle empty or invalid result
    if not analysis_result:
        return '''
        <div class="sem-warning-box" style="padding: 40px; text-align: center; background: #fff3cd; border-radius: 8px; border: 1px solid #ffc107;">
            <p style="color: #856404; font-size: 14px; margin: 0;">
                ⚠️ Semantic analysis did not produce results. Check the logs for errors.
            </p>
        </div>
        <style>
            .dark .sem-warning-box { background: #422006 !important; border-color: #b45309 !important; }
            .dark .sem-warning-box p { color: #fde68a !important; }
        </style>
        '''
    
    def color_card(hex_val: str, role: str, confidence: str, reason: str = "") -> str:
        """Generate HTML for a single color card."""
        # Determine text color based on luminance
        try:
            r = int(hex_val[1:3], 16)
            g = int(hex_val[3:5], 16)
            b = int(hex_val[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            text_color = "#1a1a1a" if luminance > 0.5 else "#ffffff"
        except:
            text_color = "#1a1a1a"
        
        confidence_badge = {
            "high": '<span class="confidence high">High</span>',
            "medium": '<span class="confidence medium">Medium</span>',
            "low": '<span class="confidence low">Low</span>',
        }.get(confidence, "")
        
        return f'''
        <div class="sem-color-card">
            <div class="sem-color-swatch" style="background-color: {hex_val};">
                <span class="sem-hex-label" style="color: {text_color};">{hex_val}</span>
            </div>
            <div class="sem-color-details">
                <div class="sem-role-name">{role.replace("_", " ").title()}</div>
                {confidence_badge}
            </div>
        </div>
        '''
    
    def category_section(title: str, icon: str, colors: dict) -> str:
        """Generate HTML for a category section."""
        if not colors:
            return ""
        
        cards_html = ""
        for role, data in colors.items():
            if data and isinstance(data, dict) and "hex" in data:
                cards_html += color_card(
                    data["hex"],
                    role,
                    data.get("confidence", "medium"),
                    data.get("reason", "")
                )
        
        if not cards_html:
            return ""
        
        return f'''
        <div class="sem-category-section">
            <h3 class="sem-category-title">{icon} {title}</h3>
            <div class="sem-color-grid">
                {cards_html}
            </div>
        </div>
        '''
    
    # Build sections
    sections_html = ""
    sections_html += category_section("Brand Colors", "🎨", analysis_result.get("brand", {}))
    sections_html += category_section("Text Colors", "📝", analysis_result.get("text", {}))
    sections_html += category_section("Background Colors", "🖼️", analysis_result.get("background", {}))
    sections_html += category_section("Border Colors", "📏", analysis_result.get("border", {}))
    sections_html += category_section("Feedback Colors", "🚨", analysis_result.get("feedback", {}))
    
    # Check if any sections were created
    if not sections_html.strip():
        return '''
        <div class="sem-warning-box" style="padding: 40px; text-align: center; background: #fff3cd; border-radius: 8px; border: 1px solid #ffc107;">
            <p style="color: #856404; font-size: 14px; margin: 0;">
                ⚠️ No semantic color categories were detected. The colors may not have enough context data (elements, CSS properties) for classification.
            </p>
        </div>
        <style>
            .dark .sem-warning-box { background: #422006 !important; border-color: #b45309 !important; }
            .dark .sem-warning-box p { color: #fde68a !important; }
        </style>
        '''
    
    # Summary
    summary = analysis_result.get("summary", {})
    summary_html = f'''
    <div class="sem-summary-section">
        <h3 class="sem-summary-title">📈 Analysis Summary</h3>
        <div class="sem-summary-stats">
            <div class="sem-stat">
                <span class="sem-stat-value">{summary.get("total_colors_analyzed", 0)}</span>
                <span class="sem-stat-label">Colors Analyzed</span>
            </div>
            <div class="sem-stat">
                <span class="sem-stat-value">{summary.get("brand_colors_found", 0)}</span>
                <span class="sem-stat-label">Brand Colors</span>
            </div>
            <div class="sem-stat">
                <span class="sem-stat-value">{"✓" if summary.get("has_clear_hierarchy") else "✗"}</span>
                <span class="sem-stat-label">Clear Hierarchy</span>
            </div>
            <div class="sem-stat">
                <span class="sem-stat-value">{summary.get("method", "rule-based").upper()}</span>
                <span class="sem-stat-label">Analysis Method</span>
            </div>
        </div>
    </div>
    '''
    
    html = f'''
    <style>
        .sem-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            padding: 20px;
            background: #f5f5f5 !important;
            border-radius: 12px;
        }}
        
        .sem-category-section {{
            margin-bottom: 24px;
            background: #ffffff !important;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #d0d0d0 !important;
        }}
        
        .sem-category-title {{
            font-size: 16px;
            font-weight: 700;
            color: #1a1a1a !important;
            margin: 0 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e0e0e0 !important;
        }}
        
        .sem-color-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 12px;
        }}
        
        .sem-color-card {{
            background: #f0f0f0 !important;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #d0d0d0 !important;
        }}
        
        .sem-color-swatch {{
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .sem-hex-label {{
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}
        
        .sem-color-details {{
            padding: 10px;
            text-align: center;
            background: #ffffff !important;
        }}
        
        .sem-role-name {{
            font-size: 12px;
            font-weight: 600;
            color: #1a1a1a !important;
            margin-bottom: 4px;
        }}
        
        .sem-preview .confidence {{
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 500;
            display: inline-block;
        }}
        
        .sem-preview .confidence.high {{
            background: #dcfce7 !important;
            color: #166534 !important;
        }}
        
        .sem-preview .confidence.medium {{
            background: #fef9c3 !important;
            color: #854d0e !important;
        }}
        
        .sem-preview .confidence.low {{
            background: #fee2e2 !important;
            color: #991b1b !important;
        }}
        
        .sem-summary-section {{
            background: #ffffff !important;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #d0d0d0 !important;
        }}
        
        .sem-summary-title {{
            font-size: 16px;
            font-weight: 700;
            color: #1a1a1a !important;
            margin: 0 0 16px 0;
        }}
        
        .sem-summary-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}
        
        .sem-stat {{
            text-align: center;
            padding: 12px;
            background: #f0f0f0 !important;
            border-radius: 8px;
        }}
        
        .sem-stat-value {{
            display: block;
            font-size: 24px;
            font-weight: 700;
            color: #1a1a1a !important;
        }}
        
        .sem-stat-label {{
            display: block;
            font-size: 11px;
            color: #555 !important;
            margin-top: 4px;
        }}

        /* Dark mode */
        .dark .sem-preview {{ background: #0f172a !important; }}
        .dark .sem-category-section {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .sem-category-title {{ color: #f1f5f9 !important; border-bottom-color: #475569 !important; }}
        .dark .sem-color-card {{ background: #334155 !important; border-color: #475569 !important; }}
        .dark .sem-color-details {{ background: #1e293b !important; }}
        .dark .sem-role-name {{ color: #f1f5f9 !important; }}
        .dark .sem-preview .confidence.high {{ background: #14532d !important; color: #86efac !important; }}
        .dark .sem-preview .confidence.medium {{ background: #422006 !important; color: #fde68a !important; }}
        .dark .sem-preview .confidence.low {{ background: #450a0a !important; color: #fca5a5 !important; }}
        .dark .sem-summary-section {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .sem-summary-title {{ color: #f1f5f9 !important; }}
        .dark .sem-stat {{ background: #334155 !important; }}
        .dark .sem-stat-value {{ color: #f1f5f9 !important; }}
        .dark .sem-stat-label {{ color: #94a3b8 !important; }}
    </style>
    
    <div class="sem-preview">
        {sections_html}
        {summary_html}
    </div>
    '''
    
    return html
