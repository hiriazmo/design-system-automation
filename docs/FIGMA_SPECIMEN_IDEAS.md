# Figma Design System Specimen Page Ideas

## Purpose
After importing the JSON (AS-IS or TO-BE) via your plugin, you need a visual way to **display and review** the design tokens. This document provides layout ideas and methods to auto-generate specimen pages.

---

## Specimen Page Layout

### Overall Structure
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   DESIGN SYSTEM SPECIMEN                                                    │
│   [AS-IS] or [TO-BE]                                                       │
│   Source: example.com | Generated: Jan 29, 2026                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────┐  ┌─────────────────────────────┐        │
│   │     TYPOGRAPHY DESKTOP      │  │     TYPOGRAPHY MOBILE       │        │
│   └─────────────────────────────┘  └─────────────────────────────┘        │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────┐          │
│   │                         COLORS                               │          │
│   │   Brand | Text | Background | Border | Feedback              │          │
│   └─────────────────────────────────────────────────────────────┘          │
│                                                                             │
│   ┌─────────────────────────────┐  ┌─────────────────────────────┐        │
│   │          SPACING            │  │       BORDER RADIUS         │        │
│   └─────────────────────────────┘  └─────────────────────────────┘        │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────┐          │
│   │                        SHADOWS                               │          │
│   └─────────────────────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section 1: Typography

### Desktop Typography (Left Column)
```
┌─────────────────────────────────────────────────────────────────┐
│  TYPOGRAPHY — DESKTOP (1440px)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Display XL                                                     │
│  The quick brown fox                                           │
│  ───────────────────────────────────────────────               │
│  Open Sans · 72px · Bold · 1.1 line-height                     │
│  Token: font.display.xl.desktop                                │
│                                                                 │
│  ─────────────────────────────────────────────────────────     │
│                                                                 │
│  Heading 1                                                      │
│  The quick brown fox jumps                                     │
│  ───────────────────────────────────────────────               │
│  Open Sans · 48px · Bold · 1.2 line-height                     │
│  Token: font.heading.1.desktop                                 │
│                                                                 │
│  ─────────────────────────────────────────────────────────     │
│                                                                 │
│  Heading 2                                                      │
│  The quick brown fox jumps over                                │
│  ───────────────────────────────────────────────               │
│  Open Sans · 36px · Semibold · 1.25 line-height                │
│  Token: font.heading.2.desktop                                 │
│                                                                 │
│  ─────────────────────────────────────────────────────────     │
│                                                                 │
│  Heading 3                                                      │
│  The quick brown fox jumps over the lazy dog                   │
│  ───────────────────────────────────────────────               │
│  Open Sans · 28px · Semibold · 1.3 line-height                 │
│  Token: font.heading.3.desktop                                 │
│                                                                 │
│  ─────────────────────────────────────────────────────────     │
│                                                                 │
│  Body Large                                                     │
│  The quick brown fox jumps over the lazy dog. Pack my box      │
│  with five dozen liquor jugs.                                  │
│  ───────────────────────────────────────────────               │
│  Open Sans · 18px · Regular · 1.5 line-height                  │
│  Token: font.body.lg.desktop                                   │
│                                                                 │
│  ─────────────────────────────────────────────────────────     │
│                                                                 │
│  Body                                                           │
│  The quick brown fox jumps over the lazy dog. Pack my box      │
│  with five dozen liquor jugs. How vexingly quick daft zebras   │
│  jump!                                                         │
│  ───────────────────────────────────────────────               │
│  Open Sans · 16px · Regular · 1.5 line-height                  │
│  Token: font.body.desktop                                      │
│                                                                 │
│  ─────────────────────────────────────────────────────────     │
│                                                                 │
│  Caption                                                        │
│  The quick brown fox jumps over the lazy dog                   │
│  ───────────────────────────────────────────────               │
│  Open Sans · 12px · Regular · 1.4 line-height                  │
│  Token: font.caption.desktop                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile Typography (Right Column)
Same structure but with mobile values:
- Smaller sizes (e.g., Display XL: 48px instead of 72px)
- Token names: font.display.xl.mobile

### Typography Comparison View (Alternative)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TYPOGRAPHY SCALE COMPARISON                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Token              Desktop         Mobile          Ratio                   │
│  ─────────────────────────────────────────────────────────────────────     │
│  display.xl         72px            48px            1.5x                   │
│  heading.1          48px            36px            1.33x                  │
│  heading.2          36px            28px            1.29x                  │
│  heading.3          28px            24px            1.17x                  │
│  body.lg            18px            16px            1.13x                  │
│  body               16px            16px            1x                     │
│  caption            12px            12px            1x                     │
│                                                                             │
│  Scale Ratio: 1.25 (Major Third)                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section 2: Colors

### Semantic Color Groups
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  COLORS                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🎨 BRAND                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                                  │
│  │          │  │          │  │          │                                  │
│  │ #06b2c4  │  │ #c1df1f  │  │ #3860be  │                                  │
│  │          │  │          │  │          │                                  │
│  └──────────┘  └──────────┘  └──────────┘                                  │
│   Primary       Secondary     Accent                                        │
│   AA: ⚠️ 3.2    AA: ⚠️ 2.1    AA: ✓ 4.8                                    │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  📝 TEXT                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │          │  │          │  │          │  │          │                   │
│  │ #1a1a1a  │  │ #373737  │  │ #666666  │  │ #999999  │                   │
│  │          │  │          │  │          │  │          │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│   Primary       Secondary     Tertiary      Muted                          │
│   AA: ✓ 16.1    AA: ✓ 12.6    AA: ✓ 5.7     AA: ⚠️ 3.0                    │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  🖼️ BACKGROUND                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │          │  │          │  │          │  │          │                   │
│  │ #ffffff  │  │ #f5f5f5  │  │ #e8e8e8  │  │ #1a1a1a  │                   │
│  │          │  │          │  │          │  │          │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│   Primary       Secondary     Tertiary      Inverse                        │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  📏 BORDER                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                                  │
│  │  ┌────┐  │  │  ┌────┐  │  │  ┌────┐  │                                  │
│  │  │    │  │  │  │    │  │  │  │    │  │                                  │
│  │  └────┘  │  │  └────┘  │  │  └────┘  │                                  │
│  └──────────┘  └──────────┘  └──────────┘                                  │
│   #e0e0e0       #d0d0d0       #c0c0c0                                      │
│   Default       Strong        Focus                                        │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  🚨 FEEDBACK                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │          │  │          │  │          │  │          │                   │
│  │ #dc2626  │  │ #16a34a  │  │ #f59e0b  │  │ #3b82f6  │                   │
│  │          │  │          │  │          │  │          │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│   Error         Success       Warning       Info                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Color Ramps (If Generated)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  COLOR RAMPS                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Brand Primary                                                              │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐                 │
│  │ 50 │100 │200 │300 │400 │500 │600 │700 │800 │900 │950 │                 │
│  │    │    │    │    │    │ ◆  │    │    │    │    │    │                 │
│  └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘                 │
│   ◆ = Base color (#06b2c4)                                                 │
│                                                                             │
│  Neutral                                                                    │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐                 │
│  │ 50 │100 │200 │300 │400 │500 │600 │700 │800 │900 │950 │                 │
│  └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section 3: Spacing

### Visual Spacing Scale
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPACING SCALE (8px Grid)                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Token           Value    Visual                                            │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  space.0         0px      (none)                                           │
│                                                                             │
│  space.1         4px      ████                                             │
│                                                                             │
│  space.2         8px      ████████                                         │
│                                                                             │
│  space.3         12px     ████████████                                     │
│                                                                             │
│  space.4         16px     ████████████████                                 │
│                                                                             │
│  space.5         20px     ████████████████████                             │
│                                                                             │
│  space.6         24px     ████████████████████████                         │
│                                                                             │
│  space.8         32px     ████████████████████████████████                 │
│                                                                             │
│  space.10        40px     ████████████████████████████████████████         │
│                                                                             │
│  space.12        48px     ████████████████████████████████████████████████ │
│                                                                             │
│  space.16        64px     ████████████████████████████████████████████...  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Spacing with Boxes
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPACING — VISUAL REFERENCE                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  4px        8px         16px          24px           32px          48px    │
│  space.1    space.2     space.4       space.6        space.8       space.12│
│                                                                             │
│   ┌┐        ┌──┐        ┌────┐        ┌──────┐       ┌────────┐    ┌──────┐│
│   └┘        └──┘        │    │        │      │       │        │    │      ││
│                         └────┘        │      │       │        │    │      ││
│                                       └──────┘       │        │    │      ││
│                                                      └────────┘    │      ││
│                                                                    │      ││
│                                                                    └──────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section 4: Border Radius

### Radius Visual Display
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BORDER RADIUS                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ╭────────╮        │
│  │        │    │        │    │        │    │        │    │        │        │
│  │        │    │        │    │        │    │        │    │        │        │
│  │        │    │        │    │        │    │        │    │        │        │
│  └────────┘    └────────┘    └────────┘    └────────┘    ╰────────╯        │
│                                                                             │
│   0px           4px           8px           12px          9999px           │
│   radius.none   radius.sm     radius.md     radius.lg     radius.full      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section 5: Shadows

### Shadow Visual Display
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SHADOWS / ELEVATION                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │
│  │             │      │             │      │             │                 │
│  │             │      │             │      │             │                 │
│  │   Level 1   │      │   Level 2   │      │   Level 3   │                 │
│  │             │      │             │      │             │                 │
│  │             │      │             │      │             │                 │
│  └─────────────┘      └─────────────┘      └─────────────┘                 │
│   ░░░░░░░░░░░░░        ▒▒▒▒▒▒▒▒▒▒▒▒▒        ▓▓▓▓▓▓▓▓▓▓▓▓▓                 │
│                                                                             │
│   shadow.sm            shadow.md            shadow.lg                       │
│   0 1px 2px            0 4px 8px            0 8px 24px                     │
│   rgba(0,0,0,0.05)     rgba(0,0,0,0.1)      rgba(0,0,0,0.15)               │
│                                                                             │
│   Use: Subtle lift     Use: Cards, menus    Use: Modals, dialogs           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Methods to Auto-Generate Specimen in Figma

### Method 1: Figma Plugin Extension (Recommended)

Extend your existing plugin to:
1. Import JSON → Create Variables (already done)
2. **NEW: Generate Specimen Page**
   - Create a new page called "📋 Design System Specimen"
   - Auto-generate frames for each token category
   - Apply variables to the specimen elements

**Plugin Code Concept:**
```javascript
// After importing variables...
async function generateSpecimenPage() {
  // Create page
  const page = figma.createPage();
  page.name = "📋 Design System Specimen";
  
  // Create Typography section
  const typoFrame = createTypographySpecimen(typographyVariables);
  
  // Create Colors section
  const colorFrame = createColorSpecimen(colorVariables);
  
  // Create Spacing section
  const spacingFrame = createSpacingSpecimen(spacingVariables);
  
  // ... etc
}
```

### Method 2: Figma Template + Variables

1. **Create a Master Template** (one-time setup):
   - Design the specimen layout manually
   - Use placeholder text/colors
   
2. **Connect to Variables**:
   - Bind text layers to typography variables
   - Bind fills to color variables
   - Bind auto-layout gaps to spacing variables

3. **On Import**:
   - Variables update → Specimen auto-updates

**Advantage:** Beautiful, customized design
**Disadvantage:** Manual template creation

### Method 3: Community Plugin — "Design Tokens to Figma"

Use existing plugins that can generate visual specimens:
- **Tokens Studio for Figma** — Has specimen generation
- **Themer** — Creates color ramps visually
- **Design System Organizer** — Structures tokens

### Method 4: Widget (Most Interactive)

Create a **Figma Widget** that:
- Reads variables from the document
- Renders an interactive specimen
- Updates in real-time

**Advantage:** Live, interactive
**Disadvantage:** More complex to build

---

## Recommended Approach for You

Given you already have a plugin:

### Quick Win (30 min)
1. Create a **Figma template file** with the specimen layout
2. Manually connect elements to variables
3. Duplicate template for each project

### Better Solution (2-4 hours)
Extend your plugin to auto-generate the specimen page:

```javascript
// Add to your existing plugin
figma.ui.onmessage = async (msg) => {
  if (msg.type === 'import-json') {
    // Your existing import code...
    await importVariables(msg.data);
    
    // NEW: Generate specimen
    if (msg.generateSpecimen) {
      await generateSpecimenPage();
    }
  }
};

async function generateSpecimenPage() {
  const page = figma.createPage();
  page.name = `📋 Specimen — ${new Date().toLocaleDateString()}`;
  figma.currentPage = page;
  
  let yOffset = 0;
  
  // Typography
  yOffset = await createTypographySection(0, yOffset);
  
  // Colors  
  yOffset = await createColorSection(0, yOffset + 100);
  
  // Spacing
  yOffset = await createSpacingSection(0, yOffset + 100);
  
  // Radius
  yOffset = await createRadiusSection(0, yOffset + 100);
  
  // Shadows
  await createShadowSection(0, yOffset + 100);
  
  figma.viewport.scrollAndZoomIntoView(page.children);
}
```

---

## AS-IS vs TO-BE Comparison View

For comparing before/after:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  COMPARISON: AS-IS → TO-BE                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TYPOGRAPHY                                                                 │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  Token              AS-IS           TO-BE           Change                  │
│  display.xl         72px            72px            —                       │
│  heading.1          46px            48px            +2px (scale aligned)    │
│  heading.2          34px            36px            +2px (scale aligned)    │
│  body               16px            16px            —                       │
│                                                                             │
│  Scale Ratio:       ~1.18 (random)  1.25 (Major Third)  ✓ Improved         │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  COLORS                                                                     │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  Token              AS-IS           TO-BE           Change                  │
│                                                                             │
│  brand.primary      #06b2c4         #0891a8         AA: 3.2 → 4.6 ✓        │
│                     ┌────┐          ┌────┐                                 │
│                     │    │    →     │    │                                 │
│                     └────┘          └────┘                                 │
│                                                                             │
│  text.primary       #373737         #373737         — (no change)          │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  SPACING                                                                    │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  Grid:              Mixed           8px             ✓ Standardized         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

| Method | Effort | Best For |
|--------|--------|----------|
| Template + Variables | Low | Quick setup, one-off projects |
| Plugin Extension | Medium | Reusable, consistent output |
| Widget | High | Interactive, real-time updates |
| Community Plugin | None | If existing solution fits |

**My Recommendation:** Extend your plugin to auto-generate the specimen page. It's a one-time investment that pays off every time you use the workflow.
