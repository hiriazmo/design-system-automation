# Design Token Creator - Figma Plugin

A powerful, free Figma plugin that automatically creates color styles, text styles, and spacing tokens from your design tokens JSON file.

## 🎯 What It Does

Upload a JSON file with your design tokens and the plugin will automatically create:

- ✅ **Color Styles** - All your brand colors as Figma color styles
- ✅ **Text Styles** - Complete typography system with font families, sizes, weights, and line heights
- ✅ **Spacing Tokens** - All spacing units for consistent layouts

## 🚀 Quick Start

1. **Create an empty Figma file**
2. **Open the plugin** (Plugins → Development → Design Token Creator)
3. **Upload your JSON** file with design tokens
4. **Click "Apply to Document"**
5. **Check your Assets panel** - All styles are created! ✨

## 📋 Features

- 🎨 **Beautiful UI** - Clean, intuitive interface
- 📤 **Multiple Input Methods** - Upload file or paste JSON
- 👁️ **Token Preview** - See all tokens before applying
- ⏳ **Progress Indicator** - Real-time feedback while creating styles
- 🎯 **Accurate Naming** - Tokens organized by category (colors/, typography/, spacing/)
- 💾 **No Data Loss** - Your original file remains unchanged
- 🆓 **Completely Free** - No credits needed, no limitations

## 📁 Project Structure

```
design-token-creator/
├── manifest.json          # Plugin configuration
├── src/
│   └── code.js           # Main plugin code
├── ui/
│   └── ui.html           # Plugin interface
├── INSTALLATION.md       # Installation guide
└── README.md            # This file
```

## 🔧 Installation

See [INSTALLATION.md](./INSTALLATION.md) for detailed setup instructions.

### Quick Install

1. Clone or download this folder
2. In Figma: Plugins → Development → New plugin → Link existing plugin
3. Select this folder
4. Done!

## 📝 JSON Format

Your design tokens should follow this structure:

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

## 🎨 Example Usage

### Input JSON
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
          "fontFamily": "Montserrat",
          "fontWeight": "700",
          "fontSize": "32px",
          "lineHeight": "1.3"
        },
        "type": "typography"
      }
    }
  }
}
```

### Output in Figma
- **Color Styles**: `colors/primary`, `colors/secondary`
- **Text Styles**: `typography/heading`
- All automatically available in your Assets panel!

## 🛠️ How It Works

1. **Parse JSON** - Plugin reads your design tokens
2. **Validate** - Checks for correct format and values
3. **Create Styles** - Generates Figma styles for each token
4. **Apply** - Adds styles to your document
5. **Confirm** - Shows success message with count

## 💡 Tips

- Use consistent naming conventions in your JSON
- Test with a small set of tokens first
- Keep your JSON file organized by category
- Update tokens regularly as your design system evolves
- Share the JSON file with your team for consistency

## 🐛 Troubleshooting

**Plugin won't load?**
- Check folder structure matches exactly
- Ensure manifest.json is in root folder
- Restart Figma

**Styles not created?**
- Verify JSON is valid (use jsonlint.com)
- Check token names don't have special characters
- Make sure hex colors are valid format

**Wrong style values?**
- Double-check JSON values
- Verify font sizes include "px"
- Ensure hex colors start with #

## 📚 Learn More

- [Figma Plugin API Documentation](https://www.figma.com/plugin-docs/)
- [Design Tokens Format](https://design-tokens.github.io/community-group/format/)
- [Figma Styles Documentation](https://help.figma.com/en/articles/12453487-Styles)

## 🎯 What's Next?

After creating your styles:

1. Create components using these styles
2. Build design system documentation
3. Publish as a shared library
4. Share with your team
5. Keep tokens updated as system evolves

## 📄 License

This plugin is free to use and modify for your own projects.

## ✨ Credits

Created to help design teams implement design systems efficiently in Figma.

---

**Ready to get started?** See [INSTALLATION.md](./INSTALLATION.md) for step-by-step setup instructions.
