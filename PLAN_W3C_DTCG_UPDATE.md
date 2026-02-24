# PLAN: Update to W3C DTCG Design Token Format

## Overview

Update both the **Design System Automation export** and the **Figma plugin** to use the official **W3C DTCG (Design Tokens Community Group)** format - the industry standard as of October 2025.

---

## Current vs Target Format

### CURRENT (Custom/Legacy)
```json
{
  "global": {
    "colors": {
      "color.brand.primary": {
        "value": "#540b79",
        "type": "color"
      }
    },
    "typography": {
      "font.heading.xl.desktop": {
        "value": {
          "fontFamily": "Open Sans",
          "fontSize": "32px",
          "fontWeight": "700",
          "lineHeight": "1.3"
        },
        "type": "typography"
      }
    },
    "spacing": {
      "space.1.desktop": {
        "value": "8px",
        "type": "dimension"
      }
    },
    "borderRadius": {
      "radius.md": {
        "value": "8px",
        "type": "borderRadius"
      }
    },
    "shadows": {
      "shadow.sm": {
        "value": { "x": "0", "y": "2", "blur": "4", ... },
        "type": "boxShadow"
      }
    }
  }
}
```

### TARGET (W3C DTCG Standard)
```json
{
  "color": {
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "#540b79",
        "$description": "Main brand color"
      }
    }
  },
  "font": {
    "heading": {
      "xl": {
        "desktop": {
          "$type": "typography",
          "$value": {
            "fontFamily": "Open Sans",
            "fontSize": "32px",
            "fontWeight": "700",
            "lineHeight": "1.3"
          }
        }
      }
    }
  },
  "spacing": {
    "1": {
      "desktop": {
        "$type": "dimension",
        "$value": "8px"
      }
    }
  },
  "borderRadius": {
    "md": {
      "$type": "dimension",
      "$value": "8px"
    }
  },
  "shadow": {
    "sm": {
      "$type": "shadow",
      "$value": {
        "color": "#00000026",
        "offsetX": "0px",
        "offsetY": "2px",
        "blur": "4px",
        "spread": "0px"
      }
    }
  }
}
```

---

## Key Changes Summary

| Aspect | Current | DTCG Target |
|--------|---------|-------------|
| Property prefix | `value`, `type` | `$value`, `$type` |
| Root wrapper | `global` | None (flat root) |
| Token nesting | Flat keys (`color.brand.primary`) | Nested objects (`color.brand.primary`) |
| Color type | `"type": "color"` | `"$type": "color"` |
| Typography type | `"type": "typography"` | `"$type": "typography"` |
| Spacing type | `"type": "dimension"` | `"$type": "dimension"` |
| Radius type | `"type": "borderRadius"` | `"$type": "dimension"` |
| Shadow type | `"type": "boxShadow"` | `"$type": "shadow"` |

---

## Files to Update

### 1. Export Functions (`app.py`)

**File:** `/Users/yahya/design-system-extractor-v2-hf-fix/app.py`

**Functions to modify:**
- `export_stage1_json()` (~line 3095)
- `export_tokens_json()` (~line 3248)

**Changes:**
1. Remove `global` wrapper - tokens at root level
2. Change `value` → `$value`, `type` → `$type`
3. Convert flat keys to nested structure:
   - `color.brand.primary` → `{ color: { brand: { primary: {...} } } }`
   - `font.heading.xl.desktop` → `{ font: { heading: { xl: { desktop: {...} } } } }`
4. Add helper function to convert flat key to nested object
5. Update shadow format to DTCG spec
6. Keep `$description` for semantic tokens

### 2. Figma Plugin (`code.js`)

**File:** `/Users/yahya/design-system-extractor-v2-hf-fix/output_json/figma-plugin-extracted/figma-design-token-creator 5/src/code.js`

**Changes:**
1. Update `normalizeTokens()` to detect DTCG format (look for `$value`, `$type`)
2. Update `extractColors()` to handle:
   - `$value` instead of `value`
   - Nested structure traversal
3. Update `extractTypography()` to handle DTCG composite format
4. Update `extractSpacing()` for dimension tokens
5. Add shadow extraction (currently not implemented)
6. Support both legacy AND DTCG formats for backwards compatibility

### 3. Plugin UI (`ui.html`)

**File:** `/Users/yahya/design-system-extractor-v2-hf-fix/output_json/figma-plugin-extracted/figma-design-token-creator 5/ui/ui.html`

**Changes:**
1. Update `extractColorsForPreview()` to handle `$value`
2. Update `extractSpacingForPreview()` to handle `$value`
3. Update `buildTypographyPreview()` for nested + DTCG format
4. Add format detection message for DTCG
5. Add shadow preview section

---

## Detailed Implementation Steps

### Step 1: Create DTCG Export Helper Functions (app.py)

```python
def _key_to_nested_path(flat_key: str) -> list:
    """Convert 'color.brand.primary' to ['color', 'brand', 'primary']"""
    return flat_key.split('.')

def _set_nested_value(obj: dict, path: list, value: dict):
    """Set a value at a nested path in a dictionary"""
    for key in path[:-1]:
        if key not in obj:
            obj[key] = {}
        obj = obj[key]
    obj[path[-1]] = value

def _to_dtcg_token(value, token_type: str, description: str = None) -> dict:
    """Convert to DTCG format with $value, $type, $description"""
    token = {
        "$type": token_type,
        "$value": value
    }
    if description:
        token["$description"] = description
    return token
```

### Step 2: Update Export Functions (app.py)

Rewrite `export_stage1_json()` and `export_tokens_json()` to:
1. Build nested structure instead of flat
2. Use `$value`, `$type`, `$description`
3. Map token types correctly:
   - `borderRadius` → `dimension` (DTCG uses dimension for radii)
   - `boxShadow` → `shadow`
   - Keep `color`, `typography`, `dimension`

### Step 3: Update Plugin Token Extraction (code.js)

Add DTCG detection and extraction:

```javascript
// Detect if DTCG format
function isDTCGFormat(obj) {
  if (!obj || typeof obj !== 'object') return false;
  var keys = Object.keys(obj);
  for (var i = 0; i < keys.length; i++) {
    var val = obj[keys[i]];
    if (val && typeof val === 'object') {
      if (val['$value'] !== undefined || val['$type'] !== undefined) {
        return true;
      }
    }
  }
  return false;
}

// Extract from DTCG format
function extractColorsDTCG(obj, prefix, results) {
  // Handle $value, $type
  // Recursively traverse nested structure
}
```

### Step 4: Update Plugin UI (ui.html)

Update preview functions to handle both formats.

### Step 5: Add Shadow Support to Plugin

Currently the plugin doesn't create Effect Styles for shadows. Add:

```javascript
// CREATE EFFECT STYLES (Shadows)
for (var si = 0; si < tokens.shadows.length; si++) {
  var shadowToken = tokens.shadows[si];
  var effectStyle = figma.createEffectStyle();
  effectStyle.name = 'shadows/' + shadowToken.name;
  effectStyle.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.25 },
    offset: { x: parseFloat(shadowToken.value.offsetX), y: parseFloat(shadowToken.value.offsetY) },
    radius: parseFloat(shadowToken.value.blur),
    spread: parseFloat(shadowToken.value.spread),
    visible: true,
    blendMode: 'NORMAL'
  }];
}
```

---

## Testing Checklist

After implementation, verify:

- [ ] Export Stage 1 JSON produces valid DTCG format
- [ ] Export Final JSON produces valid DTCG format
- [ ] Token names are properly nested (`color.brand.primary` → nested object)
- [ ] All `$value`, `$type` prefixes present
- [ ] Figma plugin successfully imports DTCG JSON
- [ ] Colors → Paint Styles created correctly
- [ ] Typography → Text Styles created correctly
- [ ] Spacing → Variables created correctly
- [ ] Border Radius → Variables created correctly
- [ ] Shadows → Effect Styles created correctly
- [ ] Plugin still works with legacy format (backwards compatible)

---

## Benefits After Implementation

1. **Interoperability** - Works with Figma, Sketch, Framer, Style Dictionary, Tokens Studio
2. **Future-proof** - Official W3C standard, adopted by industry
3. **Tool ecosystem** - Compatible with 10+ design tools
4. **Code generation** - Works with Style Dictionary for CSS/iOS/Android
5. **No vendor lock-in** - Standard format, portable

---

## Estimated Effort

| Task | Complexity | Time |
|------|------------|------|
| Export helper functions | Low | 15 min |
| Update export_stage1_json | Medium | 30 min |
| Update export_tokens_json | Medium | 30 min |
| Update plugin code.js | Medium | 45 min |
| Update plugin ui.html | Low | 20 min |
| Add shadow support to plugin | Medium | 30 min |
| Testing & fixes | Medium | 30 min |
| **Total** | | **~3 hours** |

---

## Awaiting Confirmation

Please confirm:
1. ✅ Proceed with W3C DTCG format update?
2. ✅ Update both app.py export AND Figma plugin?
3. ✅ Add shadow Effect Style support to plugin?
4. ✅ Maintain backwards compatibility for legacy format in plugin?

**Reply "approved" or provide feedback to proceed.**
