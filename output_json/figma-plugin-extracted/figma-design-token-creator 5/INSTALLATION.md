# Design Token Creator - Installation Guide

A custom Figma plugin that automatically creates color styles, text styles, and spacing tokens from your design tokens JSON file.

## Features

✅ Upload JSON design tokens  
✅ Preview all tokens before applying  
✅ Create color styles automatically  
✅ Create text styles automatically  
✅ Create spacing tokens automatically  
✅ Progress indicator while processing  
✅ No credits needed - completely free  

---

## Installation Steps

### Step 1: Prepare the Plugin Files

1. You should have these files:
   - `manifest.json`
   - `src/code.js`
   - `ui/ui.html`

2. Create a folder structure:
   ```
   design-token-creator/
   ├── manifest.json
   ├── src/
   │   └── code.js
   └── ui/
       └── ui.html
   ```

### Step 2: Load Plugin into Figma

1. Open **Figma** and go to any file
2. Go to **Plugins** menu → **Development** → **New plugin**
3. Select **Link existing plugin**
4. Choose the folder containing your plugin files
5. Click **Open**

### Step 3: Run the Plugin

1. In Figma, go to **Plugins** → **Development** → **Design Token Creator**
2. The plugin panel will open on the right side

---

## How to Use

### Step 1: Upload Your JSON File

You have two options:

**Option A: Choose File**
1. Click the **"Choose File"** button
2. Select your `design-tokens.json` file
3. The plugin will load and display all tokens

**Option B: Paste JSON**
1. Click the **"Paste JSON"** button
2. Paste your JSON content
3. Click OK

### Step 2: Preview Tokens

The plugin will show you:
- **Colors** - All color tokens with hex values
- **Typography** - All text styles with size and weight
- **Spacing** - All spacing units

### Step 3: Apply to Document

1. Click **"Apply to Document"** button
2. Wait for the progress bar to complete
3. You'll see a success message

### Step 4: Check Your Styles

1. In Figma, open the **Assets** panel (left sidebar)
2. You'll see:
   - **Color Styles** folder with all your colors
   - **Text Styles** folder with all typography
   - **Spacing** tokens as text styles

---

## Your JSON Format

The plugin expects this JSON structure:

```json
{
  "global": {
    "colors": {
      "teal": {
        "value": "#00A09A",
        "type": "color"
      },
      "hot-pink": {
        "value": "#FF007F",
        "type": "color"
      }
    },
    "typography": {
      "h1": {
        "value": {
          "fontFamily": "Montserrat",
          "fontWeight": "700",
          "fontSize": "48px",
          "lineHeight": "1.2"
        },
        "type": "typography"
      }
    },
    "spacing": {
      "xs": {
        "value": "8px",
        "type": "spacing"
      }
    }
  }
}
```

---

## What Gets Created

### Color Styles
- Named as: `colors/[name]`
- Example: `colors/teal`, `colors/hot-pink`
- Can be used in any fill or stroke

### Text Styles
- Named as: `typography/[name]`
- Example: `typography/h1`, `typography/body`
- Includes font family, size, weight, and line height

### Spacing Tokens
- Named as: `spacing/[name]`
- Example: `spacing/xs`, `spacing/md`
- Stored as text styles for reference

---

## Troubleshooting

### Plugin doesn't load
- Make sure all three files are in the correct folder structure
- Check that `manifest.json` is in the root folder
- Restart Figma and try again

### Styles not appearing
- Check the Assets panel on the left sidebar
- Make sure you clicked "Apply to Document"
- Try refreshing the page (Cmd+R or Ctrl+R)

### JSON upload fails
- Verify your JSON is valid (use jsonlint.com)
- Make sure it follows the expected structure
- Check for missing commas or quotes

### Styles have wrong values
- Double-check your JSON values
- Make sure hex colors are valid (e.g., #00A09A)
- Verify font sizes include "px" (e.g., "48px")

---

## Tips & Best Practices

1. **Keep JSON organized** - Use clear token names
2. **Test first** - Create a test file before applying to main designs
3. **Update regularly** - Re-run the plugin when tokens change
4. **Use consistent naming** - Follow the naming convention (e.g., `colors/`, `typography/`)
5. **Backup your file** - Save your Figma file before running the plugin

---

## Support

If you encounter any issues:

1. Check that your JSON is valid
2. Verify the folder structure is correct
3. Make sure you're using the latest Figma version
4. Try restarting Figma

---

## What's Next?

After creating your styles:

1. **Create components** using these styles
2. **Build design system pages** showing all tokens
3. **Share with your team** by publishing as a library
4. **Keep tokens updated** as your design system evolves

---

**Enjoy your new design system!** 🎨
