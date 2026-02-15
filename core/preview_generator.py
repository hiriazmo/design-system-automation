"""
Preview Generator for Typography and Color Previews

Generates HTML previews for:
1. Typography - Actual font rendering with detected styles
2. Colors AS-IS - Simple swatches showing extracted colors (Stage 1)
3. Color Ramps - 11 shades (50-950) with AA compliance (Stage 2)
4. Spacing AS-IS - Visual spacing blocks
5. Radius AS-IS - Rounded corner examples
6. Shadows AS-IS - Shadow examples
"""

from typing import Optional
import colorsys
import re


# =============================================================================
# STAGE 1: AS-IS PREVIEWS (No enhancements, just raw extracted values)
# =============================================================================

def generate_colors_asis_preview_html(
    color_tokens: dict,
    background: str = "#FAFAFA",
    max_colors: int = 50
) -> str:
    """
    Generate HTML preview for AS-IS colors (Stage 1).
    
    Shows simple color swatches without generated ramps.
    Sorted by frequency (most used first).
    
    Args:
        color_tokens: Dict of colors {name: {value: "#hex", ...}}
        background: Background color
        max_colors: Maximum colors to display (default 50)
    
    Returns:
        HTML string for Gradio HTML component
    """
    
    # Sort by frequency (highest first)
    sorted_tokens = []
    for name, token in color_tokens.items():
        if isinstance(token, dict):
            freq = token.get("frequency", 0)
        else:
            freq = 0
        sorted_tokens.append((name, token, freq))
    
    sorted_tokens.sort(key=lambda x: -x[2])  # Descending by frequency
    
    rows_html = ""
    
    for name, token, freq in sorted_tokens[:max_colors]:
        # Get hex value
        if isinstance(token, dict):
            hex_val = token.get("value", "#888888")
            frequency = token.get("frequency", 0)
            contexts = token.get("contexts", [])
            contrast_white = token.get("contrast_white", 0)
            contrast_black = token.get("contrast_black", 0)
        else:
            hex_val = str(token)
            frequency = 0
            contexts = []
            contrast_white = 0
            contrast_black = 0
        
        # Clean up hex
        if not hex_val.startswith("#"):
            hex_val = f"#{hex_val}"
        
        # Determine text color based on background luminance
        # Use contrast ratios to pick best text color
        text_color = "#1a1a1a" if contrast_white and contrast_white < 4.5 else "#ffffff"
        if not contrast_white:
            # Fallback: calculate from hex
            try:
                r = int(hex_val[1:3], 16)
                g = int(hex_val[3:5], 16)
                b = int(hex_val[5:7], 16)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                text_color = "#1a1a1a" if luminance > 0.5 else "#ffffff"
            except:
                text_color = "#1a1a1a"
        
        # Clean name
        display_name = name.replace("_", " ").replace("-", " ").replace(".", " ").title()
        if len(display_name) > 25:
            display_name = display_name[:22] + "..."
        
        # AA compliance check
        aa_status = "✓ AA" if contrast_white and contrast_white >= 4.5 else "✗ AA" if contrast_white else ""
        aa_class = "aa-pass" if contrast_white and contrast_white >= 4.5 else "aa-fail"
        
        # Context badges (limit to 3)
        context_html = ""
        for ctx in contexts[:3]:
            ctx_display = ctx[:12] + "..." if len(ctx) > 12 else ctx
            context_html += f'<span class="context-badge">{ctx_display}</span>'
        
        rows_html += f'''
        <div class="color-row-asis">
            <div class="color-swatch-large" style="background-color: {hex_val};">
                <span class="swatch-hex" style="color: {text_color};">{hex_val}</span>
            </div>
            <div class="color-info-asis">
                <div class="color-name-asis">{display_name}</div>
                <div class="color-meta-asis">
                    <span class="frequency">Used {frequency}x</span>
                    <span class="{aa_class}">{aa_status}</span>
                </div>
                <div class="context-row">
                    {context_html}
                </div>
            </div>
        </div>
        '''
    
    # Show count info
    total_colors = len(color_tokens)
    showing = min(max_colors, total_colors)
    count_info = f"Showing {showing} of {total_colors} colors (sorted by frequency)"
    
    html = f'''
    <style>
        .colors-asis-header {{
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 14px;
            color: #333 !important;
            margin-bottom: 16px;
            padding: 8px 12px;
            background: #e8e8e8 !important;
            border-radius: 6px;
        }}
        
        .colors-asis-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: {background} !important;
            border-radius: 12px;
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 16px;
            max-height: 800px;
            overflow-y: auto;
        }}
        
        .color-row-asis {{
            display: flex;
            align-items: center;
            background: #ffffff !important;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #d0d0d0 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        
        .color-swatch-large {{
            width: 80px;
            height: 80px;
            border-radius: 8px;
            border: 2px solid rgba(0,0,0,0.15) !important;
            margin-right: 16px;
            flex-shrink: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .swatch-hex {{
            font-size: 11px;
            font-family: 'SF Mono', Monaco, monospace;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.4);
        }}
        
        .color-info-asis {{
            flex: 1;
            min-width: 0;
        }}
        
        .color-name-asis {{
            font-weight: 700;
            font-size: 14px;
            color: #1a1a1a !important;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .color-meta-asis {{
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 6px;
        }}
        
        .frequency {{
            font-size: 12px;
            color: #333 !important;
            font-weight: 500;
        }}
        
        .context-row {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }}
        
        .context-badge {{
            font-size: 10px;
            background: #d0d0d0 !important;
            padding: 2px 8px;
            border-radius: 4px;
            color: #222 !important;
        }}
        
        .aa-pass {{
            font-size: 11px;
            color: #166534 !important;
            font-weight: 700;
            background: #dcfce7 !important;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .aa-fail {{
            font-size: 11px;
            color: #991b1b !important;
            font-weight: 700;
            background: #fee2e2 !important;
            padding: 2px 6px;
            border-radius: 4px;
        }}

        /* Dark mode overrides */
        .dark .colors-asis-header {{ color: #e2e8f0 !important; background: #1e293b !important; }}
        .dark .colors-asis-preview {{ background: #0f172a !important; }}
        .dark .color-row-asis {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .color-name-asis {{ color: #f1f5f9 !important; }}
        .dark .frequency {{ color: #cbd5e1 !important; }}
        .dark .context-badge {{ background: #334155 !important; color: #e2e8f0 !important; }}
        .dark .aa-pass {{ color: #22c55e !important; background: #14532d !important; }}
        .dark .aa-fail {{ color: #f87171 !important; background: #450a0a !important; }}
    </style>
    
    <div class="colors-asis-header">{count_info}</div>
    <div class="colors-asis-preview">
        {rows_html}
    </div>
    '''
    
    return html


def generate_spacing_asis_preview_html(
    spacing_tokens: dict,
    background: str = "#FAFAFA"
) -> str:
    """
    Generate HTML preview for AS-IS spacing (Stage 1).
    
    Shows visual blocks representing each spacing value.
    """
    
    rows_html = ""
    
    # Sort by pixel value
    sorted_tokens = []
    for name, token in spacing_tokens.items():
        if isinstance(token, dict):
            value_px = token.get("value_px", 0)
            value = token.get("value", "0px")
        else:
            value = str(token)
            value_px = float(re.sub(r'[^0-9.]', '', value) or 0)
        sorted_tokens.append((name, token, value_px, value))
    
    sorted_tokens.sort(key=lambda x: x[2])
    
    for name, token, value_px, value in sorted_tokens[:15]:
        # Cap visual width at 200px
        visual_width = min(value_px, 200)
        
        rows_html += f'''
        <div class="spacing-row-asis">
            <div class="spacing-label">{value}</div>
            <div class="spacing-bar" style="width: {visual_width}px;"></div>
        </div>
        '''
    
    html = f'''
    <style>
        .spacing-asis-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5 !important;
            border-radius: 12px;
            padding: 20px;
        }}
        
        .spacing-row-asis {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            background: #ffffff !important;
            padding: 8px 12px;
            border-radius: 6px;
        }}
        
        .spacing-label {{
            width: 80px;
            font-size: 14px;
            font-weight: 600;
            color: #1a1a1a !important;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        
        .spacing-bar {{
            height: 24px;
            background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%) !important;
            border-radius: 4px;
            min-width: 4px;
        }}

        /* Dark mode */
        .dark .spacing-asis-preview {{ background: #0f172a !important; }}
        .dark .spacing-row-asis {{ background: #1e293b !important; }}
        .dark .spacing-label {{ color: #f1f5f9 !important; }}
    </style>
    
    <div class="spacing-asis-preview">
        {rows_html}
    </div>
    '''
    
    return html


def generate_radius_asis_preview_html(
    radius_tokens: dict,
    background: str = "#FAFAFA"
) -> str:
    """
    Generate HTML preview for AS-IS border radius (Stage 1).
    
    Shows boxes with each radius value applied.
    """
    
    rows_html = ""
    
    for name, token in list(radius_tokens.items())[:12]:
        if isinstance(token, dict):
            value = token.get("value", "0px")
        else:
            value = str(token)
        
        rows_html += f'''
        <div class="radius-item">
            <div class="radius-box" style="border-radius: {value};"></div>
            <div class="radius-label">{value}</div>
        </div>
        '''
    
    html = f'''
    <style>
        .radius-asis-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5 !important;
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .radius-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            background: #ffffff !important;
            padding: 12px;
            border-radius: 8px;
        }}
        
        .radius-box {{
            width: 60px;
            height: 60px;
            background: #3b82f6 !important;
            margin-bottom: 8px;
        }}
        
        .radius-label {{
            font-size: 13px;
            font-weight: 600;
            color: #1a1a1a !important;
            font-family: 'SF Mono', Monaco, monospace;
        }}

        /* Dark mode */
        .dark .radius-asis-preview {{ background: #0f172a !important; }}
        .dark .radius-item {{ background: #1e293b !important; }}
        .dark .radius-label {{ color: #f1f5f9 !important; }}
    </style>
    
    <div class="radius-asis-preview">
        {rows_html}
    </div>
    '''
    
    return html


def generate_shadows_asis_preview_html(
    shadow_tokens: dict,
    background: str = "#FAFAFA"
) -> str:
    """
    Generate HTML preview for AS-IS shadows (Stage 1).
    
    Shows cards with each shadow value applied.
    """
    
    rows_html = ""
    
    for name, token in list(shadow_tokens.items())[:8]:
        if isinstance(token, dict):
            value = token.get("value", "none")
        else:
            value = str(token)
        
        # Clean name for display
        display_name = name.replace("_", " ").replace("-", " ").title()
        if len(display_name) > 15:
            display_name = display_name[:12] + "..."
        
        rows_html += f'''
        <div class="shadow-item">
            <div class="shadow-box" style="box-shadow: {value};"></div>
            <div class="shadow-label">{display_name}</div>
            <div class="shadow-value">{value[:40]}...</div>
        </div>
        '''
    
    html = f'''
    <style>
        .shadows-asis-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5 !important;
            border-radius: 12px;
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 24px;
        }}
        
        .shadow-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            background: #e8e8e8 !important;
            padding: 16px;
            border-radius: 8px;
        }}
        
        .shadow-box {{
            width: 100px;
            height: 100px;
            background: #ffffff !important;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        
        .shadow-label {{
            font-size: 13px;
            font-weight: 600;
            color: #1a1a1a !important;
            margin-bottom: 4px;
        }}
        
        .shadow-value {{
            font-size: 10px;
            color: #444 !important;
            font-family: 'SF Mono', Monaco, monospace;
            text-align: center;
            word-break: break-all;
        }}

        /* Dark mode */
        .dark .shadows-asis-preview {{ background: #0f172a !important; }}
        .dark .shadow-item {{ background: #1e293b !important; }}
        .dark .shadow-box {{ background: #334155 !important; }}
        .dark .shadow-label {{ color: #f1f5f9 !important; }}
        .dark .shadow-value {{ color: #94a3b8 !important; }}
    </style>
    
    <div class="shadows-asis-preview">
        {rows_html}
    </div>
    '''
    
    return html


# =============================================================================
# STAGE 2: TYPOGRAPHY PREVIEW (with rendered font)
# =============================================================================

def generate_typography_preview_html(
    typography_tokens: dict,
    font_family: str = "Open Sans",
    background: str = "#FAFAFA",
    sample_text: str = "The quick brown fox jumps over the lazy dog"
) -> str:
    """
    Generate HTML preview for typography tokens.
    
    Args:
        typography_tokens: Dict of typography styles {name: {font_size, font_weight, line_height, letter_spacing}}
        font_family: Primary font family detected
        background: Background color (neutral)
        sample_text: Text to render for preview
    
    Returns:
        HTML string for Gradio HTML component
    """
    
    # Sort tokens by font size (largest first)
    sorted_tokens = []
    for name, token in typography_tokens.items():
        size_str = str(token.get("font_size", "16px"))
        size_num = float(re.sub(r'[^0-9.]', '', size_str) or 16)
        sorted_tokens.append((name, token, size_num))
    
    sorted_tokens.sort(key=lambda x: -x[2])  # Descending by size
    
    # Generate rows
    rows_html = ""
    for name, token, size_num in sorted_tokens[:15]:  # Limit to 15 styles
        font_size = token.get("font_size", "16px")
        font_weight = token.get("font_weight", "400")
        line_height = token.get("line_height", "1.5")
        letter_spacing = token.get("letter_spacing", "0")
        
        # Convert weight names to numbers
        weight_map = {
            "thin": 100, "extralight": 200, "light": 300, "regular": 400,
            "medium": 500, "semibold": 600, "bold": 700, "extrabold": 800, "black": 900
        }
        if isinstance(font_weight, str) and font_weight.lower() in weight_map:
            font_weight = weight_map[font_weight.lower()]
        
        # Weight label
        weight_labels = {
            100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
            500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"
        }
        weight_label = weight_labels.get(int(font_weight) if str(font_weight).isdigit() else 400, "Regular")
        
        # Clean up name for display
        display_name = name.replace("_", " ").replace("-", " ").title()
        if len(display_name) > 15:
            display_name = display_name[:15] + "..."
        
        # Truncate sample text for large sizes
        display_text = sample_text
        if size_num > 48:
            display_text = sample_text[:30] + "..."
        elif size_num > 32:
            display_text = sample_text[:40] + "..."
        
        rows_html += f'''
        <tr class="meta-row">
            <td class="scale-name">
                <div class="scale-label">{display_name}</div>
            </td>
            <td class="meta">{font_family}</td>
            <td class="meta">{weight_label}</td>
            <td class="meta">{int(size_num)}</td>
            <td class="meta">Sentence</td>
            <td class="meta">{letter_spacing}</td>
        </tr>
        <tr>
            <td colspan="6" class="preview-cell">
                <div class="preview-text" style="
                    font-family: '{font_family}', sans-serif;
                    font-size: {font_size};
                    font-weight: {font_weight};
                    line-height: {line_height};
                    letter-spacing: {letter_spacing}px;
                ">{display_text}</div>
            </td>
        </tr>
        '''
    
    html = f'''
    <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@100;200;300;400;500;600;700;800;900&display=swap');
        
        .typography-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: {background};
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
        }}
        
        .typography-preview table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .typography-preview th {{
            text-align: left;
            padding: 12px 16px;
            font-size: 12px;
            font-weight: 600;
            color: #333;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #E0E0E0;
            background: #F5F5F5;
        }}
        
        .typography-preview td {{
            padding: 8px 16px;
            vertical-align: middle;
        }}
        
        .typography-preview .meta-row {{
            background: #F8F8F8;
            border-top: 1px solid #E8E8E8;
        }}
        
        .typography-preview .scale-name {{
            font-weight: 700;
            color: #1A1A1A;
            min-width: 120px;
        }}
        
        .typography-preview .scale-label {{
            font-size: 13px;
            font-weight: 600;
            color: #1A1A1A;
            background: #E8E8E8;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .typography-preview .meta {{
            font-size: 13px;
            color: #444;
            white-space: nowrap;
        }}
        
        .typography-preview .preview-cell {{
            padding: 16px;
            background: #FFFFFF;
            border-bottom: 1px solid #E8E8E8;
        }}
        
        .typography-preview .preview-text {{
            color: #1A1A1A;
            margin: 0;
            word-break: break-word;
        }}
        
        .typography-preview tr:hover .preview-cell {{
            background: #F5F5F5;
        }}

        /* Dark mode */
        .dark .typography-preview {{ background: #1e293b !important; }}
        .dark .typography-preview th {{ background: #334155 !important; color: #e2e8f0 !important; border-bottom-color: #475569 !important; }}
        .dark .typography-preview td {{ color: #e2e8f0 !important; }}
        .dark .typography-preview .meta-row {{ background: #1e293b !important; border-top-color: #334155 !important; }}
        .dark .typography-preview .scale-name,
        .dark .typography-preview .scale-label {{ color: #f1f5f9 !important; background: #475569 !important; }}
        .dark .typography-preview .meta {{ color: #cbd5e1 !important; }}
        .dark .typography-preview .preview-cell {{ background: #0f172a !important; border-bottom-color: #334155 !important; }}
        .dark .typography-preview .preview-text {{ color: #f1f5f9 !important; }}
        .dark .typography-preview tr:hover .preview-cell {{ background: #1e293b !important; }}
    </style>
    
    <div class="typography-preview">
        <table>
            <thead>
                <tr>
                    <th>Scale Category</th>
                    <th>Typeface</th>
                    <th>Weight</th>
                    <th>Size</th>
                    <th>Case</th>
                    <th>Letter Spacing</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    '''
    
    return html


# =============================================================================
# COLOR RAMP PREVIEW
# =============================================================================

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex string."""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def get_luminance(rgb: tuple) -> float:
    """Calculate relative luminance for contrast ratio."""
    def adjust(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = rgb
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def get_contrast_ratio(color1: tuple, color2: tuple) -> float:
    """Calculate contrast ratio between two colors."""
    l1 = get_luminance(color1)
    l2 = get_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def generate_color_ramp(base_hex: str) -> list[dict]:
    """
    Generate 11 shades (50-950) from a base color.
    
    Uses OKLCH-like approach for perceptually uniform steps.
    """
    try:
        rgb = hex_to_rgb(base_hex)
    except:
        return []
    
    # Convert to HLS for easier manipulation
    r, g, b = [x / 255 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    # Define lightness levels for each shade
    # 50 = very light (0.95), 500 = base, 950 = very dark (0.05)
    shade_lightness = {
        50: 0.95,
        100: 0.90,
        200: 0.80,
        300: 0.70,
        400: 0.60,
        500: l,  # Keep original lightness for 500
        600: 0.45,
        700: 0.35,
        800: 0.25,
        900: 0.15,
        950: 0.08,
    }
    
    # Adjust saturation for light/dark shades
    ramp = []
    for shade, target_l in shade_lightness.items():
        # Reduce saturation for very light colors
        if target_l > 0.8:
            adjusted_s = s * 0.6
        elif target_l < 0.2:
            adjusted_s = s * 0.8
        else:
            adjusted_s = s
        
        # Generate new RGB
        new_r, new_g, new_b = colorsys.hls_to_rgb(h, target_l, adjusted_s)
        new_rgb = (int(new_r * 255), int(new_g * 255), int(new_b * 255))
        new_hex = rgb_to_hex(new_rgb)
        
        # Check AA compliance
        white = (255, 255, 255)
        black = (0, 0, 0)
        contrast_white = get_contrast_ratio(new_rgb, white)
        contrast_black = get_contrast_ratio(new_rgb, black)
        
        # AA requires 4.5:1 for normal text
        aa_on_white = contrast_white >= 4.5
        aa_on_black = contrast_black >= 4.5
        
        ramp.append({
            "shade": shade,
            "hex": new_hex,
            "rgb": new_rgb,
            "contrast_white": round(contrast_white, 2),
            "contrast_black": round(contrast_black, 2),
            "aa_on_white": aa_on_white,
            "aa_on_black": aa_on_black,
        })
    
    return ramp


def generate_color_ramps_preview_html(
    color_tokens: dict,
    background: str = "#FAFAFA",
    max_colors: int = 20
) -> str:
    """
    Generate HTML preview for color ramps.
    
    Sorts colors by frequency and filters out near-white/near-black
    to prioritize showing actual brand colors.
    
    Args:
        color_tokens: Dict of colors {name: {value: "#hex", ...}}
        background: Background color
        max_colors: Maximum colors to show ramps for
    
    Returns:
        HTML string for Gradio HTML component
    """
    
    def get_color_priority(name, token):
        """Calculate priority score for a color (higher = more important)."""
        if isinstance(token, dict):
            hex_val = token.get("value", "#888888")
            frequency = token.get("frequency", 0)
        else:
            hex_val = str(token)
            frequency = 0
        
        # Clean hex
        if not hex_val.startswith("#"):
            hex_val = f"#{hex_val}"
        
        # Calculate luminance
        try:
            r = int(hex_val[1:3], 16)
            g = int(hex_val[3:5], 16)
            b = int(hex_val[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Calculate saturation (simplified)
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            saturation = (max_c - min_c) / 255 if max_c > 0 else 0
        except:
            luminance = 0.5
            saturation = 0
        
        # Priority scoring:
        # - Penalize near-white (luminance > 0.9)
        # - Penalize near-black (luminance < 0.1)
        # - Penalize low saturation (grays)
        # - Reward high frequency
        # - Reward colors with "primary", "brand", "accent" in name
        
        score = frequency * 10  # Base score from frequency
        
        # Penalize extremes
        if luminance > 0.9:
            score -= 500  # Near white
        if luminance < 0.1:
            score -= 300  # Near black
        
        # Reward saturated colors (actual brand colors)
        score += saturation * 200
        
        # Reward named brand colors
        name_lower = name.lower()
        if any(kw in name_lower for kw in ['primary', 'brand', 'accent', 'cyan', 'blue', 'green', 'red', 'orange', 'purple']):
            score += 100
        
        # Penalize "background", "border", "text" colors
        if any(kw in name_lower for kw in ['background', 'border', 'neutral', 'gray', 'grey']):
            score -= 50
        
        return score
    
    # Sort colors by priority
    sorted_colors = []
    for name, token in color_tokens.items():
        priority = get_color_priority(name, token)
        sorted_colors.append((name, token, priority))
    
    sorted_colors.sort(key=lambda x: -x[2])  # Descending by priority
    
    rows_html = ""
    shown_count = 0
    
    for name, token, priority in sorted_colors:
        if shown_count >= max_colors:
            break
            
        # Get hex value
        if isinstance(token, dict):
            hex_val = token.get("value", "#888888")
        else:
            hex_val = str(token)
        
        # Clean up hex
        if not hex_val.startswith("#"):
            hex_val = f"#{hex_val}"
        
        # Skip invalid hex
        if len(hex_val) < 7:
            continue
        
        # Generate ramp
        ramp = generate_color_ramp(hex_val)
        if not ramp:
            continue
        
        # Clean name
        display_name = name.replace("_", " ").replace("-", " ").replace(".", " ").title()
        if len(display_name) > 18:
            display_name = display_name[:15] + "..."
        
        # Generate shade cells
        shades_html = ""
        for shade_info in ramp:
            shade = shade_info["shade"]
            hex_color = shade_info["hex"]
            aa_white = shade_info["aa_on_white"]
            aa_black = shade_info["aa_on_black"]
            
            # Determine text color for label
            text_color = "#000" if shade < 500 else "#FFF"
            
            # AA indicator
            if aa_white or aa_black:
                aa_indicator = "✓"
                aa_class = "aa-pass"
            else:
                aa_indicator = ""
                aa_class = ""
            
            shades_html += f'''
            <div class="shade-cell" style="background-color: {hex_color};" title="{hex_color} | AA: {'Pass' if aa_white or aa_black else 'Fail'}">
                <span class="shade-label" style="color: {text_color};">{shade}</span>
                <span class="aa-badge {aa_class}">{aa_indicator}</span>
            </div>
            '''
        
        rows_html += f'''
        <div class="color-row">
            <div class="color-info">
                <div class="color-swatch" style="background-color: {hex_val};"></div>
                <div class="color-meta">
                    <div class="color-name">{display_name}</div>
                    <div class="color-hex">{hex_val}</div>
                </div>
            </div>
            <div class="color-ramp">
                {shades_html}
            </div>
        </div>
        '''
        shown_count += 1
    
    # Count info
    total_colors = len(color_tokens)
    count_info = f"Showing {shown_count} of {total_colors} colors (sorted by brand priority)"
    
    html = f'''
    <style>
        .color-ramps-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5 !important;
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
        }}
        
        .color-row {{
            display: flex;
            align-items: center;
            margin-bottom: 16px;
            padding: 12px;
            background: #ffffff !important;
            border-radius: 8px;
            border: 1px solid #d0d0d0 !important;
        }}
        
        .color-row:last-child {{
            margin-bottom: 0;
        }}
        
        .color-info {{
            display: flex;
            align-items: center;
            min-width: 160px;
            margin-right: 20px;
        }}
        
        .color-swatch {{
            width: 44px;
            height: 44px;
            border-radius: 8px;
            border: 2px solid rgba(0,0,0,0.15) !important;
            margin-right: 12px;
            flex-shrink: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .color-meta {{
            flex: 1;
            min-width: 100px;
        }}
        
        .color-name {{
            font-weight: 700;
            font-size: 13px;
            color: #1a1a1a !important;
            margin-bottom: 4px;
            background: #e0e0e0 !important;
            padding: 4px 10px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .color-hex {{
            font-size: 12px;
            color: #333 !important;
            font-family: 'SF Mono', Monaco, monospace;
            margin-top: 4px;
            font-weight: 500;
        }}
        
        .color-ramp {{
            display: flex;
            gap: 4px;
            flex: 1;
        }}
        
        .shade-cell {{
            width: 48px;
            height: 48px;
            border-radius: 6px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            cursor: pointer;
            transition: transform 0.15s;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }}
        
        .shade-cell:hover {{
            transform: scale(1.1);
            z-index: 10;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        .shade-label {{
            font-size: 10px;
            font-weight: 700;
        }}
        
        .aa-badge {{
            font-size: 12px;
            margin-top: 2px;
            font-weight: 700;
        }}
        
        .aa-pass {{
            color: #166534 !important;
        }}
        
        .aa-fail {{
            color: #991b1b !important;
        }}
        
        .shade-cell:hover .shade-label,
        .shade-cell:hover .aa-badge {{
            opacity: 1;
        }}
        
        /* Header row */
        .ramp-header {{
            display: flex;
            margin-bottom: 12px;
            padding-left: 180px;
            background: #e8e8e8 !important;
            padding-top: 8px;
            padding-bottom: 8px;
            border-radius: 6px;
        }}
        
        .ramp-header-label {{
            width: 48px;
            text-align: center;
            font-size: 12px;
            font-weight: 700;
            color: #333 !important;
            margin-right: 4px;
        }}
        
        .ramps-header-info {{
            font-size: 14px;
            color: #333 !important;
            margin-bottom: 16px;
            padding: 10px 14px;
            background: #e0e0e0 !important;
            border-radius: 6px;
            font-weight: 500;
        }}

        /* Dark mode */
        .dark .color-ramps-preview {{ background: #0f172a !important; }}
        .dark .ramps-header-info {{ color: #e2e8f0 !important; background: #1e293b !important; }}
        .dark .ramp-header {{ background: #1e293b !important; }}
        .dark .ramp-header-label {{ color: #cbd5e1 !important; }}
        .dark .color-row {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .color-name {{ color: #f1f5f9 !important; background: #475569 !important; }}
        .dark .color-hex {{ color: #cbd5e1 !important; }}
    </style>
    
    <div class="color-ramps-preview">
        <div class="ramps-header-info">{count_info}</div>
        <div class="ramp-header">
            <span class="ramp-header-label">50</span>
            <span class="ramp-header-label">100</span>
            <span class="ramp-header-label">200</span>
            <span class="ramp-header-label">300</span>
            <span class="ramp-header-label">400</span>
            <span class="ramp-header-label">500</span>
            <span class="ramp-header-label">600</span>
            <span class="ramp-header-label">700</span>
            <span class="ramp-header-label">800</span>
            <span class="ramp-header-label">900</span>
            <span class="ramp-header-label">950</span>
        </div>
        {rows_html}
    </div>
    '''
    
    return html


# =============================================================================
# SEMANTIC COLOR RAMPS WITH LLM RECOMMENDATIONS (Stage 2)
# =============================================================================

def generate_semantic_color_ramps_html(
    semantic_analysis: dict,
    color_tokens: dict,
    llm_recommendations: dict = None,
    background: str = "#F5F5F5"
) -> str:
    """
    Generate HTML preview for colors organized by semantic role with LLM recommendations.
    
    Args:
        semantic_analysis: Output from SemanticColorAnalyzer
        color_tokens: Dict of all color tokens
        llm_recommendations: LLM suggestions for color improvements
        background: Background color
    
    Returns:
        HTML string for Gradio HTML component
    """
    
    def generate_single_ramp(hex_val: str) -> str:
        """Generate a single color ramp HTML."""
        ramp = generate_color_ramp(hex_val)
        if not ramp:
            return ""
        
        shades_html = ""
        for shade_info in ramp:
            shade = shade_info["shade"]
            hex_color = shade_info["hex"]
            aa_white = shade_info["aa_on_white"]
            aa_black = shade_info["aa_on_black"]
            
            text_color = "#000" if shade < 500 else "#FFF"
            aa_indicator = "✓" if aa_white or aa_black else ""
            
            shades_html += f'''
            <div class="sem-shade" style="background-color: {hex_color};">
                <span class="sem-shade-num" style="color: {text_color};">{shade}</span>
                <span class="sem-shade-aa" style="color: {text_color};">{aa_indicator}</span>
            </div>
            '''
        return shades_html
    
    def color_row_with_recommendation(hex_val: str, role: str, role_display: str, recommendation: dict = None) -> str:
        """Generate a color row with optional LLM recommendation."""
        ramp_html = generate_single_ramp(hex_val)
        
        # Calculate contrast
        try:
            from core.color_utils import get_contrast_with_white
            contrast = get_contrast_with_white(hex_val)
            aa_status = "✓ AA" if contrast >= 4.5 else f"⚠️ {contrast:.1f}:1"
            aa_class = "aa-ok" if contrast >= 4.5 else "aa-warn"
        except:
            aa_status = ""
            aa_class = ""
        
        # LLM recommendation display
        rec_html = ""
        if recommendation:
            suggested = recommendation.get("suggested", "")
            issue = recommendation.get("issue", "")
            if suggested and suggested != hex_val:
                rec_html = f'''
                <div class="llm-rec">
                    <span class="rec-label">💡 LLM:</span>
                    <span class="rec-issue">{issue}</span>
                    <span class="rec-arrow">→</span>
                    <span class="rec-suggested" style="background-color: {suggested};">{suggested}</span>
                </div>
                '''
        
        return f'''
        <div class="sem-color-row">
            <div class="sem-color-info">
                <div class="sem-swatch" style="background-color: {hex_val};"></div>
                <div class="sem-details">
                    <div class="sem-role">{role_display}</div>
                    <div class="sem-hex">{hex_val} <span class="{aa_class}">{aa_status}</span></div>
                </div>
            </div>
            <div class="sem-ramp">{ramp_html}</div>
            {rec_html}
        </div>
        '''
    
    def category_section(title: str, icon: str, colors: dict, category_key: str) -> str:
        """Generate a category section with color rows."""
        if not colors:
            return ""
        
        rows_html = ""
        for role, data in colors.items():
            if data and isinstance(data, dict) and "hex" in data:
                # Get LLM recommendation for this role
                rec = None
                if llm_recommendations:
                    color_recs = llm_recommendations.get("color_recommendations", {})
                    rec = color_recs.get(f"{category_key}.{role}", {})
                
                role_display = role.replace("_", " ").title()
                rows_html += color_row_with_recommendation(
                    data["hex"],
                    f"{category_key}.{role}",
                    role_display,
                    rec
                )
        
        if not rows_html:
            return ""
        
        return f'''
        <div class="sem-category">
            <h3 class="sem-cat-title">{icon} {title}</h3>
            {rows_html}
        </div>
        '''
    
    # Handle empty analysis
    if not semantic_analysis:
        return '''
        <div class="sem-warning-box" style="padding: 40px; text-align: center; background: #fff3cd; border-radius: 8px;">
            <p style="color: #856404; font-size: 14px;">⚠️ No semantic analysis available.</p>
        </div>
        <style>
            .dark .sem-warning-box { background: #422006 !important; border-color: #b45309 !important; }
            .dark .sem-warning-box p { color: #fde68a !important; }
        </style>
        '''
    
    # Build sections
    sections_html = ""
    sections_html += category_section("Brand Colors", "🎨", semantic_analysis.get("brand", {}), "brand")
    sections_html += category_section("Text Colors", "📝", semantic_analysis.get("text", {}), "text")
    sections_html += category_section("Background Colors", "🖼️", semantic_analysis.get("background", {}), "background")
    sections_html += category_section("Border Colors", "📏", semantic_analysis.get("border", {}), "border")
    sections_html += category_section("Feedback Colors", "🚨", semantic_analysis.get("feedback", {}), "feedback")
    
    # LLM Impact Summary
    llm_summary = ""
    if llm_recommendations:
        changes = llm_recommendations.get("changes_made", [])
        if changes:
            changes_html = "".join([f"<li>{c}</li>" for c in changes[:5]])
            llm_summary = f'''
            <div class="llm-summary">
                <h4>🤖 LLM Recommendations Applied:</h4>
                <ul>{changes_html}</ul>
            </div>
            '''
    
    html = f'''
    <style>
        .sem-ramps-preview {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5 !important;
            border-radius: 12px;
            padding: 20px;
        }}
        
        .sem-category {{
            background: #ffffff !important;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
            border: 1px solid #d0d0d0 !important;
        }}
        
        .sem-cat-title {{
            font-size: 16px;
            font-weight: 700;
            color: #1a1a1a !important;
            margin: 0 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e0e0e0 !important;
        }}
        
        .sem-color-row {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            padding: 12px;
            background: #f8f8f8 !important;
            border-radius: 6px;
            margin-bottom: 12px;
            border: 1px solid #e0e0e0 !important;
        }}
        
        .sem-color-row:last-child {{
            margin-bottom: 0;
        }}
        
        .sem-color-info {{
            display: flex;
            align-items: center;
            min-width: 180px;
            margin-right: 16px;
        }}
        
        .sem-swatch {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            border: 2px solid rgba(0,0,0,0.15) !important;
            margin-right: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .sem-details {{
            flex: 1;
        }}
        
        .sem-role {{
            font-weight: 700;
            font-size: 14px;
            color: #1a1a1a !important;
            margin-bottom: 4px;
        }}
        
        .sem-hex {{
            font-size: 12px;
            font-family: 'SF Mono', Monaco, monospace;
            color: #333 !important;
        }}
        
        .aa-ok {{
            color: #166534 !important;
            font-weight: 600;
        }}
        
        .aa-warn {{
            color: #b45309 !important;
            font-weight: 600;
        }}
        
        .sem-ramp {{
            display: flex;
            gap: 3px;
            flex: 1;
            min-width: 400px;
        }}
        
        .sem-shade {{
            width: 36px;
            height: 36px;
            border-radius: 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }}
        
        .sem-shade-num {{
            font-size: 9px;
            font-weight: 700;
        }}
        
        .sem-shade-aa {{
            font-size: 10px;
        }}
        
        .llm-rec {{
            width: 100%;
            margin-top: 10px;
            padding: 8px 12px;
            background: #fef3c7 !important;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid #f59e0b !important;
        }}
        
        .rec-label {{
            font-weight: 600;
            color: #92400e !important;
        }}
        
        .rec-issue {{
            color: #78350f !important;
            font-size: 13px;
        }}
        
        .rec-arrow {{
            color: #92400e !important;
        }}
        
        .rec-suggested {{
            padding: 4px 10px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            font-weight: 600;
            color: #fff !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}
        
        .llm-summary {{
            background: #dbeafe !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 8px;
            padding: 16px;
            margin-top: 20px;
        }}
        
        .llm-summary h4 {{
            color: #1e40af !important;
            margin: 0 0 12px 0;
            font-size: 14px;
        }}
        
        .llm-summary ul {{
            margin: 0;
            padding-left: 20px;
            color: #1e3a8a !important;
        }}
        
        .llm-summary li {{
            margin-bottom: 4px;
            font-size: 13px;
        }}

        /* Dark mode */
        .dark .sem-ramps-preview {{ background: #0f172a !important; }}
        .dark .sem-category {{ background: #1e293b !important; border-color: #475569 !important; }}
        .dark .sem-cat-title {{ color: #f1f5f9 !important; border-bottom-color: #475569 !important; }}
        .dark .sem-color-row {{ background: #0f172a !important; border-color: #334155 !important; }}
        .dark .sem-role {{ color: #f1f5f9 !important; }}
        .dark .sem-hex {{ color: #cbd5e1 !important; }}
        .dark .llm-rec {{ background: #422006 !important; border-color: #b45309 !important; }}
        .dark .rec-label {{ color: #fbbf24 !important; }}
        .dark .rec-issue {{ color: #fde68a !important; }}
        .dark .rec-arrow {{ color: #fbbf24 !important; }}
        .dark .llm-summary {{ background: #1e3a5f !important; border-color: #3b82f6 !important; }}
        .dark .llm-summary h4 {{ color: #93c5fd !important; }}
        .dark .llm-summary ul, .dark .llm-summary li {{ color: #bfdbfe !important; }}
    </style>
    
    <div class="sem-ramps-preview">
        {sections_html}
        {llm_summary}
    </div>
    '''
    
    return html


# =============================================================================
# COMBINED PREVIEW
# =============================================================================

def generate_design_system_preview_html(
    typography_tokens: dict,
    color_tokens: dict,
    font_family: str = "Open Sans",
    sample_text: str = "The quick brown fox jumps over the lazy dog"
) -> tuple[str, str]:
    """
    Generate both typography and color ramp previews.
    
    Returns:
        Tuple of (typography_html, color_ramps_html)
    """
    typography_html = generate_typography_preview_html(
        typography_tokens=typography_tokens,
        font_family=font_family,
        sample_text=sample_text,
    )
    
    color_ramps_html = generate_color_ramps_preview_html(
        color_tokens=color_tokens,
    )
    
    return typography_html, color_ramps_html
