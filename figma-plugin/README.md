# Design System Automation — Figma Plugin

Import design tokens into Figma and auto-generate a visual spec page. Works with W3C DTCG format (from the Design System Automation app) and legacy JSON formats.

![Figma Plugin](https://img.shields.io/badge/Figma-Plugin-ff7262) ![Version](https://img.shields.io/badge/version-7.0-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## What It Does

Upload a JSON file with your design tokens. The plugin creates:

- **Figma Variables** — Color, number, and string variable collections
- **Paint Styles** — Every color as a reusable Figma paint style
- **Text Styles** — Typography with font family, size, weight, and line height
- **Effect Styles** — Shadows as Figma effect styles
- **Visual Spec Page** — Auto-generated frames showing all your tokens organized by category, with AA compliance badges on every color

The plugin auto-detects whether your JSON uses the **W3C DTCG format** (`$value`, `$type`) or a **legacy format** (`value`, `type`) and handles both.

---

## Quick Setup (5 Minutes)

### 1. Download the plugin

Clone this repo or download just the `figma-plugin/` folder. You need these three files:

```
figma-plugin/
  manifest.json
  src/code.js
  ui/ui.html
```

### 2. Load into Figma

1. Open **Figma** (desktop app)
2. Go to **Plugins** > **Development** > **Import plugin from manifest...**
3. Select the `manifest.json` file from this folder
4. Done — the plugin is now available under **Plugins > Development**

### 3. Run it

1. Open any Figma file (or create a new one)
2. Go to **Plugins** > **Development** > **Design System Automation — Token Importer**
3. Upload your JSON file or paste JSON directly
4. Click **"Apply to Document"**
5. Check the **Assets** panel — all your styles and variables are created

---

## How to Get Your Token JSON

### Option A: Use the Design System Automation App (Recommended)

1. Go to the [Design System Automation app](https://huggingface.co/spaces/riazmo/Design-System-Automation)
2. Enter any website URL
3. Click Extract — the app analyzes the site and extracts all design tokens
4. Download the **AS-IS JSON** (W3C DTCG format)
5. Upload it to this plugin

### Option B: Create JSON Manually

The plugin accepts two formats:

**W3C DTCG Format** (recommended — output from the app):
```json
{
  "color": {
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "#0066ff",
        "$description": "Primary brand color"
      }
    },
    "text": {
      "primary": {
        "$type": "color",
        "$value": "#1a1a1a"
      }
    }
  },
  "font": {
    "heading": {
      "lg": {
        "$type": "typography",
        "$value": {
          "fontFamily": "Inter",
          "fontSize": "32px",
          "fontWeight": "700",
          "lineHeight": "1.3"
        }
      }
    }
  },
  "spacing": {
    "md": {
      "$type": "dimension",
      "$value": "16px"
    }
  },
  "radius": {
    "md": {
      "$type": "dimension",
      "$value": "8px"
    }
  },
  "shadow": {
    "sm": {
      "$type": "shadow",
      "$value": {
        "offsetX": "0px",
        "offsetY": "2px",
        "blur": "8px",
        "spread": "0px",
        "color": "#00000026"
      }
    }
  }
}
```

**Legacy Format** (also supported):
```json
{
  "global": {
    "colors": {
      "primary": { "value": "#0066ff", "type": "color" },
      "secondary": { "value": "#ff007f", "type": "color" }
    },
    "typography": {
      "heading": {
        "value": {
          "fontFamily": "Inter",
          "fontWeight": "700",
          "fontSize": "32px",
          "lineHeight": "1.3"
        },
        "type": "typography"
      }
    },
    "spacing": {
      "md": { "value": "16px", "type": "spacing" }
    }
  }
}
```

---

## The Visual Spec Page

After importing, the plugin generates a visual spec page with separate frames for each token category:

```
+------------------------------------------------------------------+
| TYPOGRAPHY (Desktop)          TYPOGRAPHY (Mobile)                  |
| H1  48px/Bold  Inter         H1  32px/Bold  Inter                |
| H2  36px/Bold  Inter         H2  28px/Bold  Inter                |
| Body 16px/Regular Inter      Body 14px/Regular Inter             |
+------------------------------------------------------------------+
| COLORS                                                            |
| BRAND         TEXT           BACKGROUND      FEEDBACK             |
| +------+      +------+      +------+        +------+             |
| |Primary|     |Primary|     |Primary|       | Error|             |
| +------+      +------+      +------+        +------+             |
| #0066ff       #1a1a1a       #ffffff         #dc2626              |
| AA:Pass       AA:Pass                       AA:Pass              |
+------------------------------------------------------------------+
| SPACING          RADIUS            SHADOWS                        |
| 4  8  16  24     sm md lg full     xs  sm  md  lg  xl            |
+------------------------------------------------------------------+
```

Every color swatch shows its AA compliance status (Pass/Fail against white and black backgrounds).

---

## AS-IS vs TO-BE Workflow

The full Design System Automation workflow uses this plugin twice:

1. **Extract AS-IS** — Run the app on a website, download JSON, import to Figma
2. **Review** — See the current state of the design system as a visual spec
3. **AI Analysis** — The app's 4 AI agents analyze and suggest improvements
4. **Accept/Reject** — Choose which suggestions to keep
5. **Export TO-BE** — Download the improved JSON, import to Figma
6. **Compare** — Place AS-IS and TO-BE visual specs side by side

This gives you a clear before/after view of every change.

---

## Plugin Features

| Feature | Description |
|---------|-------------|
| DTCG Auto-Detection | Automatically detects W3C DTCG vs legacy JSON format |
| Figma Variables | Creates Color, Number, and String variable collections |
| Paint Styles | Every color token becomes a reusable paint style |
| Text Styles | Typography tokens with font, size, weight, line height |
| Effect Styles | Shadow tokens as Figma drop shadow effects |
| Visual Spec | Auto-generated spec page with organized frames |
| AA Badges | Contrast ratio check on every color swatch |
| File Upload | Upload JSON file or paste directly |
| Token Preview | See all detected tokens before applying |
| Progress Bar | Real-time feedback while creating styles |

---

## Troubleshooting

**Plugin won't load?**
- Make sure you're using the Figma desktop app (not the browser version)
- Check that `manifest.json`, `src/code.js`, and `ui/ui.html` are all present
- Try: Plugins > Development > Import plugin from manifest... and re-select

**Styles not appearing?**
- Open the **Assets** panel (left sidebar) and check under Local styles
- Make sure you clicked "Apply to Document" and waited for the progress bar
- Try refreshing: Cmd+R (Mac) or Ctrl+R (Windows)

**JSON upload fails?**
- Validate your JSON at [jsonlint.com](https://jsonlint.com)
- Check that hex colors use the full 6-digit format: `#0066ff` (not `#06f`)
- Make sure font sizes include units: `"32px"` (not `"32"`)

**Fonts look wrong?**
- Figma needs the font installed on your system or available through Google Fonts
- If a font isn't found, Figma falls back to a default — install the font and re-run

---

## Project Structure

```
figma-plugin/
  manifest.json      # Plugin configuration (name, entry points)
  README.md          # This file
  src/
    code.js          # Main plugin logic (v7, ~1400 lines)
  ui/
    ui.html          # Plugin UI panel
```

---

## Compatibility

- **Figma**: Desktop app (latest version recommended)
- **JSON Formats**: W3C DTCG v1, Tokens Studio, legacy `{value, type}` format
- **Token Types**: Colors, typography, spacing, border radius, shadows
- **Downstream**: Works with tokens exported from Tokens Studio, Style Dictionary, or the Design System Automation app

---

## License

MIT — free to use, modify, and distribute.

---

Built as part of [Design System Automation](https://github.com/hiriazmo/design-system-automation) — an open-source tool that extracts, analyzes, and improves design systems from any live website.
