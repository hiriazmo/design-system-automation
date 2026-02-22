// Design Token Creator - Figma Plugin (v7)
// Supports W3C DTCG format ($value, $type) and legacy formats
// Compatible with Figma's JavaScript engine (ES5)

figma.showUI(__html__, { width: 450, height: 700 });

// ==========================================
// W3C DTCG FORMAT DETECTION
// ==========================================

// Detect if the token structure uses W3C DTCG format ($value, $type)
function isDTCGFormat(obj) {
  if (!obj || typeof obj !== 'object') return false;

  function checkRecursive(o) {
    if (!o || typeof o !== 'object') return false;
    // Check for $value or $type properties
    if (o['$value'] !== undefined || o['$type'] !== undefined) {
      return true;
    }
    var keys = Object.keys(o);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (key.charAt(0) !== '$' && checkRecursive(o[keys[i]])) {
        return true;
      }
    }
    return false;
  }
  return checkRecursive(obj);
}

// Helper function to convert hex to RGB
function hexToRgb(hex) {
  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16) / 255,
    g: parseInt(result[2], 16) / 255,
    b: parseInt(result[3], 16) / 255
  } : { r: 0, g: 0, b: 0 };
}

// Helper to convert font weight to Figma font style name
function getFontStyleFromWeight(weight) {
  var weightStr = String(weight).toLowerCase();
  var weightMap = {
    '100': 'Thin',
    '200': 'ExtraLight',
    '300': 'Light',
    '400': 'Regular',
    '500': 'Medium',
    '600': 'SemiBold',
    '700': 'Bold',
    '800': 'ExtraBold',
    '900': 'Black',
    'thin': 'Thin',
    'extralight': 'ExtraLight',
    'light': 'Light',
    'regular': 'Regular',
    'medium': 'Medium',
    'semibold': 'SemiBold',
    'bold': 'Bold',
    'extrabold': 'ExtraBold',
    'black': 'Black'
  };
  return weightMap[weightStr] || 'Regular';
}

// Helper to parse numeric value from string like "16px", "1.5", etc.
function parseNumericValue(value) {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    var num = parseFloat(value.replace(/[^0-9.-]/g, ''));
    return isNaN(num) ? 0 : num;
  }
  return 0;
}

// Check if a value looks like a color (hex code)
function isColorValue(value) {
  if (typeof value !== 'string') return false;
  return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(value);
}

// Check if a value looks like a spacing/size value
function isSpacingValue(value) {
  if (typeof value !== 'string') return false;
  return /^-?\d+(\.\d+)?(px|rem|em|%)?$/.test(value);
}

// Recursively extract all color tokens from nested structure
// Supports both DTCG ($value, $type) and legacy (value, type) formats
function extractColors(obj, prefix, results, useDTCG) {
  prefix = prefix || '';
  results = results || [];

  var keys = Object.keys(obj);
  for (var i = 0; i < keys.length; i++) {
    var key = keys[i];
    // Skip DTCG meta properties
    if (key.charAt(0) === '$') continue;

    var value = obj[key];
    var newKey = prefix ? prefix + '/' + key : key;

    if (typeof value === 'string' && isColorValue(value)) {
      // Direct color value
      results.push({
        name: newKey,
        value: value,
        type: 'color'
      });
    } else if (value && typeof value === 'object') {
      // Check for DTCG format ($value with $type === 'color')
      if (value['$value'] !== undefined && value['$type'] === 'color') {
        results.push({
          name: newKey,
          value: value['$value'],
          type: 'color',
          description: value['$description'] || ''
        });
      }
      // Check for legacy format (value property)
      else if (value.value && isColorValue(value.value)) {
        results.push({
          name: newKey,
          value: value.value,
          type: 'color',
          description: value.description || ''
        });
      }
      // Recurse into nested object (skip if it has $type - it's a token)
      else if (!value['$type'] && !value.type) {
        extractColors(value, newKey, results, useDTCG);
      }
    }
  }
  return results;
}

// Recursively extract spacing/dimension tokens
// Supports both DTCG ($value, $type) and legacy (value, type) formats
function extractSpacing(obj, prefix, results) {
  prefix = prefix || '';
  results = results || [];

  var keys = Object.keys(obj);
  for (var i = 0; i < keys.length; i++) {
    var key = keys[i];
    // Skip DTCG meta properties
    if (key.charAt(0) === '$') continue;

    var value = obj[key];
    var newKey = prefix ? prefix + '/' + key : key;

    if (typeof value === 'string' && isSpacingValue(value)) {
      // Direct spacing value
      results.push({
        name: newKey,
        value: value,
        type: 'spacing'
      });
    } else if (value && typeof value === 'object') {
      // Check for DTCG format ($value with $type === 'dimension')
      if (value['$value'] !== undefined && value['$type'] === 'dimension') {
        results.push({
          name: newKey,
          value: value['$value'],
          type: 'dimension',
          description: value['$description'] || ''
        });
      }
      // Check for legacy format (value property)
      else if (value.value && (typeof value.value === 'string' || typeof value.value === 'number')) {
        results.push({
          name: newKey,
          value: value.value,
          type: value.type || 'spacing',
          description: value.description || ''
        });
      }
      // Recurse into nested object (skip if it has $type or type - it's a token)
      else if (!value['$type'] && !value.type) {
        extractSpacing(value, newKey, results);
      }
    }
  }
  return results;
}

// Build typography styles from separated fontSize, fontWeight, lineHeight objects
function buildTypographyFromSeparated(typography, fontFamilyPrimary) {
  var results = [];
  
  if (!typography || !typography.fontSize) {
    return results;
  }
  
  var fontSizes = typography.fontSize;
  var fontWeights = typography.fontWeight || {};
  var lineHeights = typography.lineHeight || {};
  var letterSpacings = typography.letterSpacing || {};
  
  // Get default font family
  var defaultFontFamily = fontFamilyPrimary || 'Inter';
  if (typography.fontFamily && typography.fontFamily.primary) {
    defaultFontFamily = typography.fontFamily.primary;
    // Clean up font family string (remove fallbacks)
    if (defaultFontFamily.indexOf(',') > -1) {
      defaultFontFamily = defaultFontFamily.split(',')[0].trim();
    }
  }
  
  // Create a text style for each fontSize entry
  var sizeKeys = Object.keys(fontSizes);
  for (var i = 0; i < sizeKeys.length; i++) {
    var styleName = sizeKeys[i];
    var fontSize = fontSizes[styleName];
    
    // Determine font weight based on style name
    var fontWeight = '400'; // default
    if (styleName.indexOf('display') > -1 || styleName.indexOf('heading') > -1) {
      fontWeight = fontWeights.bold || fontWeights.semibold || '600';
    } else if (styleName.indexOf('body') > -1) {
      fontWeight = fontWeights.regular || '400';
    } else if (styleName.indexOf('caption') > -1 || styleName.indexOf('label') > -1) {
      fontWeight = fontWeights.regular || '400';
    }
    
    // Get matching line height
    var lineHeight = lineHeights[styleName] || '1.5';
    
    // Get matching letter spacing
    var letterSpacing = letterSpacings[styleName] || '0';
    
    results.push({
      name: styleName,
      type: 'typography',
      value: {
        fontFamily: defaultFontFamily,
        fontSize: fontSize,
        fontWeight: fontWeight,
        lineHeight: lineHeight,
        letterSpacing: letterSpacing
      }
    });
  }
  
  return results;
}

// Extract typography tokens (handles DTCG, combined, and separated formats)
function extractTypography(typography, results) {
  results = results || [];

  if (!typography) return results;

  // Check if this is separated format (has fontSize as object of scales)
  if (typography.fontSize && typeof typography.fontSize === 'object' && !typography.fontSize.value && !typography.fontSize['$value']) {
    // Separated format - build from fontSize, fontWeight, lineHeight
    var builtTypography = buildTypographyFromSeparated(typography);
    for (var i = 0; i < builtTypography.length; i++) {
      results.push(builtTypography[i]);
    }
    return results;
  }

  // Otherwise, try to extract as nested combined typography tokens
  function recurse(obj, prefix) {
    var keys = Object.keys(obj);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      // Skip DTCG meta properties
      if (key.charAt(0) === '$') continue;

      var value = obj[key];
      var newKey = prefix ? prefix + '/' + key : key;

      // Skip fontFamily, fontSize, fontWeight, lineHeight scale objects
      if (key === 'fontFamily' || key === 'fontSize' || key === 'fontWeight' ||
          key === 'lineHeight' || key === 'letterSpacing') {
        continue;
      }

      if (value && typeof value === 'object') {
        // Check for DTCG format ($type === 'typography')
        if (value['$type'] === 'typography' && value['$value']) {
          results.push({
            name: newKey,
            type: 'typography',
            value: value['$value'],
            description: value['$description'] || ''
          });
        }
        // Check for legacy format (type === 'typography' or value.fontSize)
        else if (value.type === 'typography' || (value.value && value.value.fontSize)) {
          results.push({
            name: newKey,
            type: 'typography',
            value: value.value || value,
            description: value.description || ''
          });
        }
        // Recurse if not a token
        else if (!value['$type'] && !value.type) {
          recurse(value, newKey);
        }
      }
    }
  }

  recurse(typography, '');
  return results;
}

// Extract shadow tokens (DTCG and legacy formats)
function extractShadows(obj, prefix, results) {
  prefix = prefix || '';
  results = results || [];

  var keys = Object.keys(obj);
  for (var i = 0; i < keys.length; i++) {
    var key = keys[i];
    // Skip DTCG meta properties
    if (key.charAt(0) === '$') continue;

    var value = obj[key];
    var newKey = prefix ? prefix + '/' + key : key;

    if (value && typeof value === 'object') {
      // Check for DTCG format ($type === 'shadow')
      if (value['$type'] === 'shadow' && value['$value']) {
        results.push({
          name: newKey,
          type: 'shadow',
          value: value['$value'],
          description: value['$description'] || ''
        });
      }
      // Check for legacy format (type === 'boxShadow')
      else if (value.type === 'boxShadow' && value.value) {
        results.push({
          name: newKey,
          type: 'shadow',
          value: value.value,
          description: value.description || ''
        });
      }
      // Recurse if not a token
      else if (!value['$type'] && !value.type) {
        extractShadows(value, newKey, results);
      }
    }
  }
  return results;
}

// Parse color string to RGBA (handles hex, rgba, etc.)
function parseColorToRGBA(colorStr) {
  if (!colorStr) return { r: 0, g: 0, b: 0, a: 0.25 };

  // Handle hex
  if (colorStr.charAt(0) === '#') {
    var hex = colorStr;
    // Handle 8-char hex (with alpha)
    if (hex.length === 9) {
      var alpha = parseInt(hex.slice(7, 9), 16) / 255;
      hex = hex.slice(0, 7);
      var rgb = hexToRgb(hex);
      return { r: rgb.r, g: rgb.g, b: rgb.b, a: alpha };
    }
    var rgb = hexToRgb(hex);
    return { r: rgb.r, g: rgb.g, b: rgb.b, a: 1 };
  }

  // Handle rgba()
  var rgbaMatch = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (rgbaMatch) {
    return {
      r: parseInt(rgbaMatch[1]) / 255,
      g: parseInt(rgbaMatch[2]) / 255,
      b: parseInt(rgbaMatch[3]) / 255,
      a: rgbaMatch[4] ? parseFloat(rgbaMatch[4]) : 1
    };
  }

  return { r: 0, g: 0, b: 0, a: 0.25 };
}

// Normalize tokens from various JSON formats
// Supports W3C DTCG format and legacy formats
function normalizeTokens(rawTokens) {
  var normalized = {
    colors: [],
    typography: [],
    spacing: [],
    borderRadius: [],
    borderWidth: [],
    shadows: [],
    sizing: [],
    other: []
  };

  // Check if DTCG format (no global/tokens wrapper, uses $value/$type)
  var useDTCG = isDTCGFormat(rawTokens);
  console.log('Token format detected:', useDTCG ? 'W3C DTCG' : 'Legacy');

  // Determine the root of tokens
  var tokenRoot = rawTokens;
  if (!useDTCG) {
    // Legacy format may have wrappers
    if (rawTokens.tokens) {
      tokenRoot = rawTokens.tokens;
    } else if (rawTokens.global) {
      tokenRoot = rawTokens.global;
    }
  }

  // For DTCG format, look for category keys at root
  // DTCG: { color: {...}, font: {...}, space: {...}, shadow: {...}, radius: {...} }
  // Legacy: { global: { colors: {...}, typography: {...}, spacing: {...} } }

  // Extract colors
  var colorRoot = tokenRoot.colors || tokenRoot.color || null;
  if (colorRoot) {
    normalized.colors = extractColors(colorRoot, '', [], useDTCG);
  }

  // Extract typography
  var typoRoot = tokenRoot.typography || tokenRoot.font || null;
  if (typoRoot) {
    normalized.typography = extractTypography(typoRoot, []);
  }

  // Extract spacing
  var spacingRoot = tokenRoot.spacing || tokenRoot.space || null;
  if (spacingRoot) {
    normalized.spacing = extractSpacing(spacingRoot, '', []);
  }

  // Extract border radius (DTCG uses 'radius', legacy uses 'borderRadius')
  var radiusRoot = tokenRoot.borderRadius || tokenRoot.radius || null;
  if (radiusRoot) {
    normalized.borderRadius = extractSpacing(radiusRoot, '', []);
    // Fix type
    for (var i = 0; i < normalized.borderRadius.length; i++) {
      normalized.borderRadius[i].type = 'borderRadius';
    }
  }

  // Extract border width
  if (tokenRoot.borderWidth) {
    normalized.borderWidth = extractSpacing(tokenRoot.borderWidth, '', []);
    for (var i = 0; i < normalized.borderWidth.length; i++) {
      normalized.borderWidth[i].type = 'borderWidth';
    }
  }

  // Extract sizing
  if (tokenRoot.sizing) {
    normalized.sizing = extractSpacing(tokenRoot.sizing, '', []);
    for (var i = 0; i < normalized.sizing.length; i++) {
      normalized.sizing[i].type = 'sizing';
    }
  }

  // Extract shadows (DTCG uses 'shadow', legacy uses 'shadows')
  var shadowRoot = tokenRoot.shadows || tokenRoot.shadow || null;
  if (shadowRoot) {
    normalized.shadows = extractShadows(shadowRoot, '', []);
  }

  // Store original for reference
  normalized._original = tokenRoot;
  normalized._useDTCG = useDTCG;

  return normalized;
}

// Main message handler
figma.ui.onmessage = async function(msg) {
  console.log('Received message:', msg.type);
  
  if (msg.type === 'create-styles') {
    try {
      var rawTokens = msg.tokens;
      var tokens = normalizeTokens(rawTokens);
      
      var createdCount = 0;
      var totalCount = 0;
      var errors = [];

      // Calculate total
      totalCount = tokens.colors.length +
                   tokens.typography.length +
                   tokens.spacing.length +
                   tokens.borderRadius.length +
                   tokens.borderWidth.length +
                   tokens.sizing.length +
                   tokens.shadows.length;

      console.log('Normalized tokens:', tokens);
      console.log('Total tokens to create:', totalCount);

      // ==========================================
      // 1. CREATE COLOR STYLES (Paint Styles)
      // ==========================================
      for (var ci = 0; ci < tokens.colors.length; ci++) {
        var colorToken = tokens.colors[ci];
        try {
          var colorStyle = figma.createPaintStyle();
          colorStyle.name = 'colors/' + colorToken.name;
          
          var hex = colorToken.value;
          var rgb = hexToRgb(hex);
          
          colorStyle.paints = [{
            type: 'SOLID',
            color: rgb,
            opacity: 1
          }];
          
          if (colorToken.description) {
            colorStyle.description = colorToken.description;
          }
          
          createdCount++;
          console.log('✓ Created color: ' + colorStyle.name + ' (' + hex + ')');
          
          figma.ui.postMessage({
            type: 'progress',
            current: createdCount,
            total: totalCount,
            message: 'Created color: ' + colorToken.name
          });
        } catch (error) {
          console.error('Error creating color ' + colorToken.name + ':', error);
          errors.push('Color ' + colorToken.name + ': ' + error.message);
        }
      }

      // ==========================================
      // 2. CREATE TEXT STYLES (Typography)
      // ==========================================
      for (var ti = 0; ti < tokens.typography.length; ti++) {
        var typoToken = tokens.typography[ti];
        try {
          var textStyle = figma.createTextStyle();
          textStyle.name = 'typography/' + typoToken.name;
          
          var value = typoToken.value;
          
          // Get font family
          var fontFamily = value.fontFamily || 'Inter';
          // Clean up font family (remove fallbacks like ", sans-serif")
          if (fontFamily.indexOf(',') > -1) {
            fontFamily = fontFamily.split(',')[0].trim();
          }
          
          var fontSize = parseNumericValue(value.fontSize) || 16;
          var fontWeight = value.fontWeight || '400';
          var lineHeight = value.lineHeight;
          var fontStyle = getFontStyleFromWeight(fontWeight);
          
          // Load and set font — cascade: exact match → same family Regular → Inter Regular
          var fontLoaded = false;
          // Try 1: exact family + weight style (e.g. "Open Sans" + "SemiBold")
          try {
            await figma.loadFontAsync({ family: fontFamily, style: fontStyle });
            textStyle.fontName = { family: fontFamily, style: fontStyle };
            fontLoaded = true;
          } catch (e1) {
            console.warn('Font ' + fontFamily + ' ' + fontStyle + ' not available');
          }
          // Try 2: same family + Regular
          if (!fontLoaded && fontStyle !== 'Regular') {
            try {
              await figma.loadFontAsync({ family: fontFamily, style: 'Regular' });
              textStyle.fontName = { family: fontFamily, style: 'Regular' };
              fontLoaded = true;
            } catch (e2) {
              console.warn('Font ' + fontFamily + ' Regular not available either');
            }
          }
          // Try 3: Inter Regular (always available in Figma)
          if (!fontLoaded) {
            try {
              await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
              textStyle.fontName = { family: 'Inter', style: 'Regular' };
            } catch (e3) {
              console.warn('Even Inter Regular failed — skipping style');
              continue;
            }
          }
          
          textStyle.fontSize = fontSize;
          
          // Set line height
          if (lineHeight) {
            var lhValue = parseNumericValue(lineHeight);
            if (lhValue <= 3) {
              // Treat as multiplier (e.g., 1.2, 1.5)
              textStyle.lineHeight = { value: lhValue * 100, unit: 'PERCENT' };
            } else {
              // Treat as pixel value
              textStyle.lineHeight = { value: lhValue, unit: 'PIXELS' };
            }
          }
          
          // Set letter spacing if provided
          if (value.letterSpacing) {
            var letterSpacing = parseNumericValue(value.letterSpacing);
            textStyle.letterSpacing = { value: letterSpacing, unit: 'PIXELS' };
          }
          
          if (typoToken.description) {
            textStyle.description = typoToken.description;
          }
          
          createdCount++;
          console.log('✓ Created typography: ' + textStyle.name);
          
          figma.ui.postMessage({
            type: 'progress',
            current: createdCount,
            total: totalCount,
            message: 'Created typography: ' + typoToken.name
          });
        } catch (error) {
          console.error('Error creating typography ' + typoToken.name + ':', error);
          errors.push('Typography ' + typoToken.name + ': ' + error.message);
        }
      }

      // ==========================================
      // 3. CREATE VARIABLES (Spacing, Border Radius, Border Width, Sizing)
      // ==========================================
      var variableGroups = [
        { tokens: tokens.spacing, collectionName: 'Spacing', prefix: 'spacing' },
        { tokens: tokens.borderRadius, collectionName: 'Border Radius', prefix: 'radius' },
        { tokens: tokens.borderWidth, collectionName: 'Border Width', prefix: 'border' },
        { tokens: tokens.sizing, collectionName: 'Sizing', prefix: 'sizing' }
      ];

      for (var gi = 0; gi < variableGroups.length; gi++) {
        var group = variableGroups[gi];
        if (group.tokens.length === 0) continue;

        try {
          // Get or create collection
          var collection;
          var existingCollections = await figma.variables.getLocalVariableCollectionsAsync();
          var existing = null;
          
          for (var ec = 0; ec < existingCollections.length; ec++) {
            if (existingCollections[ec].name === 'Design Tokens - ' + group.collectionName) {
              existing = existingCollections[ec];
              break;
            }
          }
          
          if (existing) {
            collection = existing;
          } else {
            collection = figma.variables.createVariableCollection('Design Tokens - ' + group.collectionName);
          }
          
          var modeId = collection.modes[0].modeId;
          
          // Get existing variables
          var existingVars = {};
          for (var vi = 0; vi < collection.variableIds.length; vi++) {
            var v = await figma.variables.getVariableByIdAsync(collection.variableIds[vi]);
            if (v) existingVars[v.name] = v;
          }
          
          for (var ti = 0; ti < group.tokens.length; ti++) {
            var token = group.tokens[ti];
            try {
              var varName = group.prefix + '/' + token.name;
              var numValue = parseNumericValue(token.value);
              
              var variable;
              if (existingVars[varName]) {
                variable = existingVars[varName];
              } else {
                variable = figma.variables.createVariable(varName, collection, 'FLOAT');
              }
              
              variable.setValueForMode(modeId, numValue);
              if (token.description) {
                variable.description = token.description;
              }
              
              createdCount++;
              console.log('✓ Created variable: ' + varName + ' = ' + numValue);
              
              figma.ui.postMessage({
                type: 'progress',
                current: createdCount,
                total: totalCount,
                message: 'Created ' + group.collectionName.toLowerCase() + ': ' + token.name
              });
            } catch (error) {
              console.error('Error creating variable ' + token.name + ':', error);
              errors.push(group.collectionName + ' ' + token.name + ': ' + error.message);
            }
          }
        } catch (collectionError) {
          console.error('Error with ' + group.collectionName + ' collection:', collectionError);
          errors.push(group.collectionName + ' collection: ' + collectionError.message);
        }
      }

      // ==========================================
      // 4. CREATE EFFECT STYLES (Shadows)
      // ==========================================
      for (var si = 0; si < tokens.shadows.length; si++) {
        var shadowToken = tokens.shadows[si];
        try {
          var effectStyle = figma.createEffectStyle();
          effectStyle.name = 'shadows/' + shadowToken.name;

          var sv = shadowToken.value;

          // Parse shadow values (DTCG format: offsetX, offsetY, blur, spread, color)
          var offsetX = parseNumericValue(sv.offsetX || sv.x || '0');
          var offsetY = parseNumericValue(sv.offsetY || sv.y || '0');
          var blur = parseNumericValue(sv.blur || '0');
          var spread = parseNumericValue(sv.spread || '0');
          var shadowColor = parseColorToRGBA(sv.color || 'rgba(0,0,0,0.25)');

          effectStyle.effects = [{
            type: 'DROP_SHADOW',
            color: { r: shadowColor.r, g: shadowColor.g, b: shadowColor.b, a: shadowColor.a },
            offset: { x: offsetX, y: offsetY },
            radius: blur,
            spread: spread,
            visible: true,
            blendMode: 'NORMAL'
          }];

          if (shadowToken.description) {
            effectStyle.description = shadowToken.description;
          }

          createdCount++;
          console.log('✓ Created shadow: ' + effectStyle.name);

          figma.ui.postMessage({
            type: 'progress',
            current: createdCount,
            total: totalCount,
            message: 'Created shadow: ' + shadowToken.name
          });
        } catch (error) {
          console.error('Error creating shadow ' + shadowToken.name + ':', error);
          errors.push('Shadow ' + shadowToken.name + ': ' + error.message);
        }
      }

      console.log('Completed! Created ' + createdCount + ' styles/variables');

      figma.ui.postMessage({
        type: 'complete',
        created: createdCount,
        total: totalCount,
        errors: errors
      });

    } catch (error) {
      console.error('Error in create-styles:', error);
      figma.ui.postMessage({
        type: 'error',
        message: error.message
      });
    }
  }
  
  if (msg.type === 'close') {
    figma.closePlugin();
  }

  // ==========================================
  // VISUAL SPEC GENERATOR v2
  // Creates a professional visual reference page showing all tokens
  // ==========================================
  if (msg.type === 'create-visual-spec') {
    try {
      var rawTokens = msg.tokens;

      // Validate tokens exist
      if (!rawTokens) {
        figma.ui.postMessage({
          type: 'error',
          message: 'No tokens provided. Please load a JSON file first.'
        });
        return;
      }

      console.log('Creating visual spec with tokens:', Object.keys(rawTokens));
      var tokens = normalizeTokens(rawTokens);
      console.log('Normalized tokens - colors:', tokens.colors.length, 'typography:', tokens.typography.length);

      // Use current page (Figma Starter plan has 3-page limit)
      var specPage = figma.currentPage;
      specPage.name = '🎨 Design System Spec';

      // Clear existing children
      while (specPage.children.length > 0) {
        specPage.children[0].remove();
      }

      // ── Layout constants ──
      var PAGE_PADDING = 60;
      var SECTION_GAP = 100;
      var ITEM_GAP = 16;
      var xOffset = PAGE_PADDING;
      var yOffset = PAGE_PADDING;
      var PAGE_WIDTH = 1200;

      // ── Load fonts ──
      // 1. Inter Regular/Bold for labels (always available)
      var headingStyle = 'Regular';
      var labelFont = { family: 'Inter', style: 'Regular' };
      await figma.loadFontAsync(labelFont);
      try {
        await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
        headingStyle = 'Bold';
      } catch (e) {
        console.warn('Inter Bold not available');
      }
      var headingFont = { family: 'Inter', style: headingStyle };

      // 2. Try to load the extracted font for sample text
      var sampleFontFamily = 'Inter';
      var sampleFontStyle = 'Regular';
      var sampleFontBoldStyle = headingStyle;
      // Find the primary font from typography tokens
      for (var fi = 0; fi < tokens.typography.length; fi++) {
        var ff = (tokens.typography[fi].value.fontFamily || '').split(',')[0].trim();
        if (ff && ff !== 'Inter' && ff !== 'sans-serif') {
          sampleFontFamily = ff;
          break;
        }
      }
      if (sampleFontFamily !== 'Inter') {
        try {
          await figma.loadFontAsync({ family: sampleFontFamily, style: 'Regular' });
          sampleFontStyle = 'Regular';
          // Try Bold
          try {
            await figma.loadFontAsync({ family: sampleFontFamily, style: 'Bold' });
            sampleFontBoldStyle = 'Bold';
          } catch (e2) {
            sampleFontBoldStyle = 'Regular';
          }
        } catch (e) {
          console.warn(sampleFontFamily + ' not available, falling back to Inter');
          sampleFontFamily = 'Inter';
          sampleFontStyle = 'Regular';
          sampleFontBoldStyle = headingStyle;
        }
      }
      var sampleFont = { family: sampleFontFamily, style: sampleFontStyle };
      var sampleFontBold = { family: sampleFontFamily, style: sampleFontBoldStyle };

      // ── Helper: add section title ──
      function addSectionTitle(text) {
        var title = figma.createText();
        title.fontName = headingFont;
        title.fontSize = 28;
        title.characters = text;
        title.fills = [{ type: 'SOLID', color: { r: 0.1, g: 0.1, b: 0.1 } }];
        title.x = xOffset;
        title.y = yOffset;
        specPage.appendChild(title);
        yOffset += 50;
        // Divider line
        var line = figma.createRectangle();
        line.resize(PAGE_WIDTH - PAGE_PADDING * 2, 1);
        line.x = xOffset;
        line.y = yOffset;
        line.fills = [{ type: 'SOLID', color: { r: 0.85, g: 0.85, b: 0.85 } }];
        specPage.appendChild(line);
        yOffset += 24;
      }

      // ── Helper: add sub-heading ──
      function addSubHeading(text) {
        var sub = figma.createText();
        sub.fontName = headingFont;
        sub.fontSize = 16;
        sub.characters = text;
        sub.fills = [{ type: 'SOLID', color: { r: 0.35, g: 0.35, b: 0.35 } }];
        sub.x = xOffset;
        sub.y = yOffset;
        specPage.appendChild(sub);
        yOffset += 32;
      }

      // ══════════════════════════════════════════
      // 1. WHITE BACKGROUND
      // ══════════════════════════════════════════
      // We'll place it at the end once we know the total height.
      // For now, track startY.
      var bgStartY = 0;

      // ── Page title ──
      var pageTitle = figma.createText();
      pageTitle.fontName = headingFont;
      pageTitle.fontSize = 36;
      pageTitle.characters = 'Design System Specification';
      pageTitle.fills = [{ type: 'SOLID', color: { r: 0.1, g: 0.1, b: 0.1 } }];
      pageTitle.x = xOffset;
      pageTitle.y = yOffset;
      specPage.appendChild(pageTitle);
      yOffset += 60;

      // ══════════════════════════════════════════
      // 2. COLORS — grouped by category
      // ══════════════════════════════════════════
      if (tokens.colors.length > 0) {
        addSectionTitle('COLORS');

        // Group colors by top-level category from name path
        // e.g. "brand/primary/DEFAULT" → category "brand"
        //      "blue/50"              → category "blue" (palette)
        var colorGroups = {};
        var groupOrder = [];
        for (var ci = 0; ci < tokens.colors.length; ci++) {
          var cToken = tokens.colors[ci];
          var parts = cToken.name.split('/');
          var category = parts[0] || 'other';
          if (!colorGroups[category]) {
            colorGroups[category] = [];
            groupOrder.push(category);
          }
          colorGroups[category].push(cToken);
        }

        // Semantic categories first, then palette
        var semanticOrder = ['brand', 'text', 'bg', 'background', 'border', 'feedback'];
        var sortedGroups = [];
        for (var so = 0; so < semanticOrder.length; so++) {
          if (colorGroups[semanticOrder[so]]) {
            sortedGroups.push(semanticOrder[so]);
          }
        }
        for (var go = 0; go < groupOrder.length; go++) {
          if (sortedGroups.indexOf(groupOrder[go]) === -1) {
            sortedGroups.push(groupOrder[go]);
          }
        }

        var swatchSize = 56;
        var swatchGap = 12;

        for (var gi = 0; gi < sortedGroups.length; gi++) {
          var groupName = sortedGroups[gi];
          var groupColors = colorGroups[groupName];

          // Category label
          addSubHeading(groupName.charAt(0).toUpperCase() + groupName.slice(1));

          var colorX = xOffset;
          for (var ci2 = 0; ci2 < groupColors.length; ci2++) {
            var ct = groupColors[ci2];

            // Swatch
            var swatch = figma.createRectangle();
            swatch.resize(swatchSize, swatchSize);
            swatch.x = colorX;
            swatch.y = yOffset;
            swatch.cornerRadius = 8;
            var rgb = hexToRgb(ct.value);
            swatch.fills = [{ type: 'SOLID', color: rgb }];
            swatch.strokes = [{ type: 'SOLID', color: { r: 0.88, g: 0.88, b: 0.88 } }];
            swatch.strokeWeight = 1;
            specPage.appendChild(swatch);

            // Token name (last segment, skip DEFAULT)
            var nameParts = ct.name.split('/');
            var displayName = nameParts[nameParts.length - 1];
            if (displayName === 'DEFAULT') {
              displayName = nameParts.length > 1 ? nameParts[nameParts.length - 2] : displayName;
            }
            var cLabel = figma.createText();
            cLabel.fontName = labelFont;
            cLabel.fontSize = 9;
            cLabel.characters = displayName;
            cLabel.x = colorX;
            cLabel.y = yOffset + swatchSize + 4;
            specPage.appendChild(cLabel);

            // Hex value
            var hexLabel = figma.createText();
            hexLabel.fontName = labelFont;
            hexLabel.fontSize = 8;
            hexLabel.characters = ct.value.toUpperCase();
            hexLabel.fills = [{ type: 'SOLID', color: { r: 0.55, g: 0.55, b: 0.55 } }];
            hexLabel.x = colorX;
            hexLabel.y = yOffset + swatchSize + 16;
            specPage.appendChild(hexLabel);

            colorX += swatchSize + swatchGap;
          }

          yOffset += swatchSize + 36 + ITEM_GAP;
        }

        yOffset += SECTION_GAP - ITEM_GAP;
      }

      // ══════════════════════════════════════════
      // 3. TYPOGRAPHY — Desktop & Mobile side by side
      // ══════════════════════════════════════════
      if (tokens.typography.length > 0) {
        addSectionTitle('TYPOGRAPHY');

        // Separate desktop and mobile tokens
        var desktopTypo = [];
        var mobileTypo = [];
        for (var ti = 0; ti < tokens.typography.length; ti++) {
          var tToken = tokens.typography[ti];
          var tName = tToken.name.toLowerCase();
          if (tName.indexOf('mobile') > -1) {
            mobileTypo.push(tToken);
          } else {
            desktopTypo.push(tToken);
          }
        }

        // Pangram sample texts per tier
        function getSampleText(tokenName) {
          var n = tokenName.toLowerCase();
          if (n.indexOf('display') > -1) return 'The quick brown fox jumps over the lazy dog';
          if (n.indexOf('heading') > -1) return 'The quick brown fox jumps over';
          if (n.indexOf('body') > -1) return 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.';
          if (n.indexOf('caption') > -1) return 'The quick brown fox jumps over the lazy dog';
          if (n.indexOf('overline') > -1) return 'THE QUICK BROWN FOX';
          return 'The quick brown fox jumps over the lazy dog';
        }

        // Get display tier for font weight
        function getTierFont(tokenName) {
          var n = tokenName.toLowerCase();
          if (n.indexOf('display') > -1 || n.indexOf('heading') > -1) return sampleFontBold;
          return sampleFont;
        }

        // Render a typography column
        function renderTypoColumn(typoList, columnX, columnTitle) {
          var localY = yOffset;
          // Column title
          var colTitle = figma.createText();
          colTitle.fontName = headingFont;
          colTitle.fontSize = 14;
          colTitle.characters = columnTitle;
          colTitle.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.5, b: 1 } }];
          colTitle.x = columnX;
          colTitle.y = localY;
          specPage.appendChild(colTitle);
          localY += 30;

          for (var tti = 0; tti < typoList.length; tti++) {
            var tt = typoList[tti];
            var val = tt.value;
            var fFamily = (val.fontFamily || 'Inter').split(',')[0].trim();
            var fSize = parseNumericValue(val.fontSize) || 16;
            var fWeight = val.fontWeight || '400';
            var fLineHeight = val.lineHeight || '1.5';
            var displaySize = Math.min(fSize, 48);

            // Token name label (e.g. "heading.lg")
            var tierParts = tt.name.split('/');
            // Remove 'desktop'/'mobile' from display
            var tierName = tierParts.filter(function(p) { return p !== 'desktop' && p !== 'mobile'; }).join('/');

            var nameLabel = figma.createText();
            nameLabel.fontName = labelFont;
            nameLabel.fontSize = 10;
            nameLabel.characters = tierName;
            nameLabel.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
            nameLabel.x = columnX;
            nameLabel.y = localY;
            specPage.appendChild(nameLabel);
            localY += 16;

            // Sample text in actual font
            var sample = figma.createText();
            sample.fontName = getTierFont(tt.name);
            sample.fontSize = displaySize;
            sample.characters = getSampleText(tt.name);
            sample.x = columnX;
            sample.y = localY;
            // Constrain width so long text wraps
            sample.resize(480, sample.height);
            sample.textAutoResize = 'HEIGHT';
            specPage.appendChild(sample);
            localY += sample.height + 6;

            // Spec details — font size, weight, line height
            var specLine = figma.createText();
            specLine.fontName = labelFont;
            specLine.fontSize = 10;
            specLine.characters = fFamily + '  ·  ' + fSize + 'px  ·  wt ' + fWeight + '  ·  LH ' + fLineHeight;
            specLine.fills = [{ type: 'SOLID', color: { r: 0.6, g: 0.6, b: 0.6 } }];
            specLine.x = columnX;
            specLine.y = localY;
            specPage.appendChild(specLine);
            localY += 28;
          }
          return localY;
        }

        var colWidth = 520;
        var desktopEndY = renderTypoColumn(desktopTypo, xOffset, '🖥  Desktop');
        var mobileEndY = renderTypoColumn(mobileTypo, xOffset + colWidth, '📱  Mobile');

        yOffset = Math.max(desktopEndY, mobileEndY) + SECTION_GAP;
      }

      // ══════════════════════════════════════════
      // 4. SPACING — Desktop & Mobile with square blocks
      // ══════════════════════════════════════════
      if (tokens.spacing.length > 0) {
        addSectionTitle('SPACING');

        // Separate desktop and mobile
        var desktopSpacing = [];
        var mobileSpacing = [];
        for (var spi = 0; spi < tokens.spacing.length; spi++) {
          var spToken = tokens.spacing[spi];
          var spName = spToken.name.toLowerCase();
          if (spName.indexOf('mobile') > -1) {
            mobileSpacing.push(spToken);
          } else {
            desktopSpacing.push(spToken);
          }
        }

        function renderSpacingColumn(spacingList, columnX, columnTitle) {
          var localY = yOffset;
          var colTitle = figma.createText();
          colTitle.fontName = headingFont;
          colTitle.fontSize = 14;
          colTitle.characters = columnTitle;
          colTitle.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.5, b: 1 } }];
          colTitle.x = columnX;
          colTitle.y = localY;
          specPage.appendChild(colTitle);
          localY += 30;

          var spX = columnX;
          var maxH = 0;
          for (var ssi = 0; ssi < Math.min(spacingList.length, 10); ssi++) {
            var sp = spacingList[ssi];
            var spVal = parseNumericValue(sp.value);
            var blockSize = Math.max(spVal, 8); // Minimum visible size
            var displayBlock = Math.min(blockSize, 80); // Cap for display

            // Blue square
            var sq = figma.createRectangle();
            sq.resize(displayBlock, displayBlock);
            sq.x = spX;
            sq.y = localY;
            sq.cornerRadius = 4;
            sq.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.55, b: 1 } }];
            specPage.appendChild(sq);

            // Label below
            var spParts = sp.name.split('/');
            var spDisplayName = spParts.filter(function(p) { return p !== 'desktop' && p !== 'mobile'; }).join('/');
            var sqLabel = figma.createText();
            sqLabel.fontName = labelFont;
            sqLabel.fontSize = 9;
            sqLabel.characters = spDisplayName + '\n' + sp.value;
            sqLabel.textAlignHorizontal = 'CENTER';
            sqLabel.x = spX;
            sqLabel.y = localY + displayBlock + 6;
            specPage.appendChild(sqLabel);

            if (displayBlock > maxH) maxH = displayBlock;
            spX += displayBlock + 20;
          }
          return localY + maxH + 40;
        }

        var dsEndY = renderSpacingColumn(desktopSpacing, xOffset, '🖥  Desktop');
        var msEndY = renderSpacingColumn(mobileSpacing, xOffset + colWidth, '📱  Mobile');

        yOffset = Math.max(dsEndY, msEndY) + SECTION_GAP;
      }

      // ══════════════════════════════════════════
      // 5. BORDER RADIUS
      // ══════════════════════════════════════════
      if (tokens.borderRadius.length > 0) {
        addSectionTitle('BORDER RADIUS');

        var radiusX = xOffset;
        for (var ri = 0; ri < tokens.borderRadius.length; ri++) {
          var radiusToken = tokens.borderRadius[ri];
          var radiusValue = parseNumericValue(radiusToken.value);

          var rect = figma.createRectangle();
          rect.resize(56, 56);
          rect.x = radiusX;
          rect.y = yOffset;
          rect.cornerRadius = Math.min(radiusValue, 28);
          rect.fills = [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.97 } }];
          rect.strokes = [{ type: 'SOLID', color: { r: 0.8, g: 0.8, b: 0.85 } }];
          rect.strokeWeight = 2;
          specPage.appendChild(rect);

          var rLabel = figma.createText();
          rLabel.fontName = labelFont;
          rLabel.fontSize = 9;
          rLabel.characters = radiusToken.name.split('/').pop() + '\n' + radiusToken.value;
          rLabel.textAlignHorizontal = 'CENTER';
          rLabel.x = radiusX;
          rLabel.y = yOffset + 62;
          specPage.appendChild(rLabel);

          radiusX += 80;
        }

        yOffset += 110 + SECTION_GAP;
      }

      // ══════════════════════════════════════════
      // 6. SHADOWS
      // ══════════════════════════════════════════
      if (tokens.shadows.length > 0) {
        addSectionTitle('SHADOWS');

        var shadowX = xOffset;
        for (var shi = 0; shi < tokens.shadows.length; shi++) {
          var shadowToken = tokens.shadows[shi];
          var sv = shadowToken.value;

          var offsetXVal = parseNumericValue(sv.offsetX || sv.x || '0');
          var offsetYVal = parseNumericValue(sv.offsetY || sv.y || '0');
          var blurVal = parseNumericValue(sv.blur || '0');
          var spreadVal = parseNumericValue(sv.spread || '0');
          var shColor = parseColorToRGBA(sv.color || 'rgba(0,0,0,0.25)');

          // Shadow card
          var card = figma.createRectangle();
          card.resize(90, 90);
          card.x = shadowX;
          card.y = yOffset;
          card.cornerRadius = 12;
          card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
          card.effects = [{
            type: 'DROP_SHADOW',
            color: { r: shColor.r, g: shColor.g, b: shColor.b, a: shColor.a },
            offset: { x: offsetXVal, y: offsetYVal },
            radius: blurVal,
            spread: spreadVal,
            visible: true,
            blendMode: 'NORMAL'
          }];
          specPage.appendChild(card);

          // Name + specs
          var shLabel = figma.createText();
          shLabel.fontName = labelFont;
          shLabel.fontSize = 9;
          shLabel.characters = shadowToken.name.split('/').pop() + '\nblur: ' + blurVal + 'px  y: ' + offsetYVal + 'px';
          shLabel.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
          shLabel.x = shadowX;
          shLabel.y = yOffset + 100;
          specPage.appendChild(shLabel);

          shadowX += 130;
        }

        yOffset += 140 + SECTION_GAP;
      }

      // ══════════════════════════════════════════
      // WHITE BACKGROUND — placed behind everything
      // ══════════════════════════════════════════
      var bgRect = figma.createRectangle();
      bgRect.resize(PAGE_WIDTH, yOffset + PAGE_PADDING);
      bgRect.x = 0;
      bgRect.y = 0;
      bgRect.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
      bgRect.locked = true;
      bgRect.name = 'Background';
      specPage.appendChild(bgRect);

      // Send background to back (behind all other elements)
      var children = specPage.children;
      if (children.length > 1) {
        specPage.insertChild(0, bgRect);
      }

      figma.ui.postMessage({
        type: 'spec-complete',
        message: 'Visual spec page created!'
      });

    } catch (error) {
      console.error('Error creating visual spec:', error);
      figma.ui.postMessage({
        type: 'error',
        message: 'Failed to create visual spec: ' + (error && error.message ? error.message : String(error))
      });
    }
  }
};
