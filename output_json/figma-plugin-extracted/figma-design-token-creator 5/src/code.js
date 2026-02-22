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

// WCAG 2.1 contrast ratio calculation
function getRelativeLuminance(rgb) {
  function sRGB(c) { return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  return 0.2126 * sRGB(rgb.r) + 0.7152 * sRGB(rgb.g) + 0.0722 * sRGB(rgb.b);
}
function getContrastRatio(hex1, hex2) {
  var l1 = getRelativeLuminance(hexToRgb(hex1));
  var l2 = getRelativeLuminance(hexToRgb(hex2));
  var lighter = Math.max(l1, l2);
  var darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}
function getAAResult(hex) {
  var onWhite = getContrastRatio(hex, '#ffffff');
  var onBlack = getContrastRatio(hex, '#000000');
  var bestRatio = Math.max(onWhite, onBlack);
  var bestOn = onWhite >= onBlack ? 'white' : 'black';
  return {
    ratio: Math.round(bestRatio * 10) / 10,
    passAA: bestRatio >= 4.5,
    passAAA: bestRatio >= 7,
    bestOn: bestOn
  };
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
  // ==========================================
  // VISUAL SPEC GENERATOR v3 — Material Design best-practices layout
  // Each section in its own Figma FRAME. AA contrast badges. Prominent labels.
  // ==========================================
  if (msg.type === 'create-visual-spec') {
    try {
      var rawTokens = msg.tokens;
      if (!rawTokens) {
        figma.ui.postMessage({ type: 'error', message: 'No tokens provided. Please load a JSON file first.' });
        return;
      }

      var tokens = normalizeTokens(rawTokens);
      var specPage = figma.currentPage;
      specPage.name = '🎨 Design System Spec';
      while (specPage.children.length > 0) { specPage.children[0].remove(); }

      // ── Constants (Material Design / Carbon inspired) ──
      var FRAME_W = 1440;
      var CONTENT_W = 1200;
      var MARGIN = 120;
      var SECTION_PAD = 48;
      var SECTION_GAP = 40;  // gap between frames on the page
      var ITEM_GAP = 16;
      var SWATCH_W = 160;
      var SWATCH_H_COLOR = 64;
      var SWATCH_META_H = 72;
      var SWATCH_GAP = 12;

      // ── Load fonts ──
      var labelFont = { family: 'Inter', style: 'Regular' };
      var boldFont = { family: 'Inter', style: 'Regular' };
      await figma.loadFontAsync(labelFont);
      try { await figma.loadFontAsync({ family: 'Inter', style: 'Bold' }); boldFont = { family: 'Inter', style: 'Bold' }; } catch (e) {}

      // Try loading extracted font
      var sampleFontFamily = 'Inter';
      var sampleFont = labelFont;
      var sampleFontBold = boldFont;
      for (var fi = 0; fi < tokens.typography.length; fi++) {
        var ff = (tokens.typography[fi].value.fontFamily || '').split(',')[0].trim();
        if (ff && ff !== 'Inter' && ff !== 'sans-serif' && ff !== 'serif') { sampleFontFamily = ff; break; }
      }
      if (sampleFontFamily !== 'Inter') {
        try {
          await figma.loadFontAsync({ family: sampleFontFamily, style: 'Regular' });
          sampleFont = { family: sampleFontFamily, style: 'Regular' };
          try { await figma.loadFontAsync({ family: sampleFontFamily, style: 'Bold' }); sampleFontBold = { family: sampleFontFamily, style: 'Bold' }; } catch (e2) { sampleFontBold = sampleFont; }
        } catch (e) { sampleFontFamily = 'Inter'; sampleFont = labelFont; sampleFontBold = boldFont; }
      }

      // Collect all frames — position them at the very end
      var allFrames = [];

      // ── Helper: create a section FRAME (positioned later) ──
      function createSectionFrame(name, contentHeight) {
        var frame = figma.createFrame();
        frame.name = name;
        frame.resize(FRAME_W, contentHeight);
        frame.x = 0;
        frame.y = 0; // will be repositioned at the end
        frame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
        frame.clipsContent = false;
        specPage.appendChild(frame);
        allFrames.push(frame);
        return frame;
      }

      // ── Helper: add text to a frame ──
      function addText(frame, text, font, size, x, y, color) {
        var t = figma.createText();
        t.fontName = font;
        t.fontSize = size;
        t.characters = text;
        t.fills = [{ type: 'SOLID', color: color || { r: 0.1, g: 0.1, b: 0.1 } }];
        t.x = x; t.y = y;
        frame.appendChild(t);
        return t;
      }

      var MUTED = { r: 0.5, g: 0.5, b: 0.5 };
      var DARK = { r: 0.12, g: 0.12, b: 0.12 };
      var BLUE = { r: 0.15, g: 0.45, b: 0.95 };

      // ══════════════════════════════════════════════════════════
      // TITLE FRAME
      // ══════════════════════════════════════════════════════════
      var titleFrame = createSectionFrame('Title', 120);
      addText(titleFrame, 'Design System Specification', boldFont, 36, MARGIN, 32, DARK);
      addText(titleFrame, 'Font: ' + sampleFontFamily, labelFont, 14, MARGIN, 80, MUTED);

      // ══════════════════════════════════════════════════════════
      // COLORS FRAME — grouped by category with AA badges
      // ══════════════════════════════════════════════════════════
      if (tokens.colors.length > 0) {
        // Group colors by category
        var colorGroups = {};
        var groupOrder = [];
        for (var ci = 0; ci < tokens.colors.length; ci++) {
          var cat = tokens.colors[ci].name.split('/')[0] || 'other';
          if (!colorGroups[cat]) { colorGroups[cat] = []; groupOrder.push(cat); }
          colorGroups[cat].push(tokens.colors[ci]);
        }
        // Sort: semantic first, then palette
        var semOrder = ['brand', 'text', 'bg', 'background', 'border', 'feedback'];
        var sortedGroups = [];
        for (var so = 0; so < semOrder.length; so++) { if (colorGroups[semOrder[so]]) sortedGroups.push(semOrder[so]); }
        for (var go = 0; go < groupOrder.length; go++) { if (sortedGroups.indexOf(groupOrder[go]) === -1) sortedGroups.push(groupOrder[go]); }

        // Calculate initial height estimate (will be resized at end)
        var colorsPerRow = Math.floor((CONTENT_W - 140 + SWATCH_GAP) / (SWATCH_W + SWATCH_GAP));
        var totalColorH = 2000; // generous initial estimate, resized later

        var colorFrame = createSectionFrame('Colors', totalColorH);
        var cy = SECTION_PAD;

        // Section title
        addText(colorFrame, 'COLORS', boldFont, 32, MARGIN, cy, DARK);
        cy += 48;

        // Helper to render a single color card at position
        function renderColorCard(frame, ct, sx, sy) {
            var swatch = figma.createRectangle();
            swatch.resize(SWATCH_W, SWATCH_H_COLOR);
            swatch.x = sx; swatch.y = sy;
            swatch.topLeftRadius = 8; swatch.topRightRadius = 8;
            swatch.fills = [{ type: 'SOLID', color: hexToRgb(ct.value) }];
            frame.appendChild(swatch);

            // AA badge
            var aa = getAAResult(ct.value);
            var badgeText = aa.passAA ? 'AA ✓ ' + aa.ratio + ':1' : 'AA ✗ ' + aa.ratio + ':1';
            var badgeColor = aa.bestOn === 'white' ? { r: 1, g: 1, b: 1 } : { r: 0, g: 0, b: 0 };
            addText(frame, badgeText, labelFont, 10, sx + 8, sy + SWATCH_H_COLOR - 18, badgeColor);

            // Metadata area
            var metaBg = figma.createRectangle();
            metaBg.resize(SWATCH_W, SWATCH_META_H);
            metaBg.x = sx; metaBg.y = sy + SWATCH_H_COLOR;
            metaBg.bottomLeftRadius = 8; metaBg.bottomRightRadius = 8;
            metaBg.fills = [{ type: 'SOLID', color: { r: 0.97, g: 0.97, b: 0.98 } }];
            metaBg.strokes = [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }];
            metaBg.strokeWeight = 1;
            frame.appendChild(metaBg);

            var nameParts = ct.name.split('/');
            var displayName = nameParts.filter(function(p) { return p !== 'DEFAULT'; }).join('/');
            addText(frame, displayName, boldFont, 11, sx + 10, sy + SWATCH_H_COLOR + 8, DARK);
            addText(frame, ct.value.toUpperCase(), labelFont, 11, sx + 10, sy + SWATCH_H_COLOR + 26, MUTED);

            var contrastText = aa.passAA ? 'AA Pass on ' + aa.bestOn : 'AA Fail (' + aa.ratio + ':1)';
            var contrastColor = aa.passAA ? { r: 0.13, g: 0.55, b: 0.13 } : { r: 0.85, g: 0.18, b: 0.18 };
            addText(frame, contrastText, labelFont, 10, sx + 10, sy + SWATCH_H_COLOR + 44, contrastColor);
        }

        var isSemantic = { 'brand': 1, 'text': 1, 'bg': 1, 'background': 1, 'border': 1, 'feedback': 1 };
        var CARD_H = SWATCH_H_COLOR + SWATCH_META_H + ITEM_GAP;

        for (var gi = 0; gi < sortedGroups.length; gi++) {
          var gName = sortedGroups[gi];
          var gColors = colorGroups[gName];

          // Group heading
          addText(colorFrame, gName.charAt(0).toUpperCase() + gName.slice(1), boldFont, 18, MARGIN, cy, DARK);
          cy += 36;

          if (isSemantic[gName]) {
            // ── SEMANTIC LAYOUT: sub-group by 2nd path segment, each on own row ──
            // e.g. brand/primary/DEFAULT, brand/primary/50 → sub-group "primary"
            //      feedback/error/DEFAULT, feedback/info/DEFAULT → sub-groups "error", "info"
            var subGroups = {};
            var subOrder = [];
            for (var si = 0; si < gColors.length; si++) {
              var sp = gColors[si].name.split('/');
              var subKey = sp.length > 1 ? sp[1] : sp[0];
              if (!subGroups[subKey]) { subGroups[subKey] = []; subOrder.push(subKey); }
              subGroups[subKey].push(gColors[si]);
            }

            for (var ski = 0; ski < subOrder.length; ski++) {
              var subName = subOrder[ski];
              var subColors = subGroups[subName];

              // Row label on the left
              addText(colorFrame, subName, boldFont, 13, MARGIN, cy + 30, MUTED);

              // Swatches start after label
              var labelW = 140;
              for (var sci = 0; sci < subColors.length; sci++) {
                var scx = MARGIN + labelW + sci * (SWATCH_W + SWATCH_GAP);
                renderColorCard(colorFrame, subColors[sci], scx, cy);
              }

              cy += CARD_H + 8;
            }
          } else {
            // ── PALETTE LAYOUT: horizontal grid (50-900 ramp) ──
            for (var ci2 = 0; ci2 < gColors.length; ci2++) {
              var ct = gColors[ci2];
              var col = ci2 % colorsPerRow;
              var row = Math.floor(ci2 / colorsPerRow);
              var sx = MARGIN + col * (SWATCH_W + SWATCH_GAP);
              var sy = cy + row * CARD_H;
              renderColorCard(colorFrame, ct, sx, sy);
            }

            var gRows = Math.ceil(gColors.length / colorsPerRow);
            cy += gRows * CARD_H + 16;
          }

          cy += 8; // gap between groups
        }

        // Resize color frame to actual content
        colorFrame.resize(FRAME_W, cy + SECTION_PAD);
      }

      // ══════════════════════════════════════════════════════════
      // TYPOGRAPHY DESKTOP FRAME
      // ══════════════════════════════════════════════════════════
      var desktopTypo = [];
      var mobileTypo = [];
      for (var tti = 0; tti < tokens.typography.length; tti++) {
        if (tokens.typography[tti].name.toLowerCase().indexOf('mobile') > -1) {
          mobileTypo.push(tokens.typography[tti]);
        } else {
          desktopTypo.push(tokens.typography[tti]);
        }
      }

      function getSampleText(name) {
        var n = name.toLowerCase();
        if (n.indexOf('display') > -1) return 'The quick brown fox jumps over the lazy dog';
        if (n.indexOf('heading') > -1) return 'The quick brown fox jumps over';
        if (n.indexOf('body') > -1) return 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.';
        if (n.indexOf('caption') > -1) return 'The quick brown fox jumps over the lazy dog';
        if (n.indexOf('overline') > -1) return 'THE QUICK BROWN FOX JUMPS';
        return 'The quick brown fox jumps over the lazy dog';
      }

      function renderTypoFrame(typoList, frameName) {
        if (typoList.length === 0) return;

        // Use generous initial height — will be resized to actual content
        var estH = 3000;

        var frame = createSectionFrame(frameName, estH);
        var fy = SECTION_PAD;

        addText(frame, frameName.toUpperCase(), boldFont, 32, MARGIN, fy, DARK);
        fy += 52;

        // Column headers
        var COL_NAME = MARGIN;
        var COL_SAMPLE = MARGIN + 180;
        var COL_SPECS = MARGIN + 760;

        addText(frame, 'Token', boldFont, 12, COL_NAME, fy, MUTED);
        addText(frame, 'Sample', boldFont, 12, COL_SAMPLE, fy, MUTED);
        addText(frame, 'Specifications', boldFont, 12, COL_SPECS, fy, MUTED);
        fy += 28;

        // Divider
        var div = figma.createRectangle();
        div.resize(CONTENT_W, 1); div.x = MARGIN; div.y = fy;
        div.fills = [{ type: 'SOLID', color: { r: 0.88, g: 0.88, b: 0.88 } }];
        frame.appendChild(div);
        fy += 16;

        for (var ti = 0; ti < typoList.length; ti++) {
          var tt = typoList[ti];
          var val = tt.value;
          var fFamily = (val.fontFamily || 'Inter').split(',')[0].trim();
          var fSize = parseNumericValue(val.fontSize) || 16;
          var fWeight = val.fontWeight || '400';
          var fLH = val.lineHeight || '1.5';
          var displaySize = Math.min(fSize, 56);

          // Token name column
          var tierParts = tt.name.split('/');
          var tierName = tierParts.filter(function(p) { return p !== 'desktop' && p !== 'mobile'; }).join('.');
          addText(frame, tierName, boldFont, 13, COL_NAME, fy + 4, DARK);

          // Sample text in actual font — use fixed width so it wraps, then measure height
          var useBold = (tierName.indexOf('display') > -1 || tierName.indexOf('heading') > -1);
          var sample = figma.createText();
          sample.fontName = useBold ? sampleFontBold : sampleFont;
          sample.fontSize = displaySize;
          // Set fixed width BEFORE setting characters so text wraps properly
          sample.textAutoResize = 'HEIGHT';
          sample.resize(540, displaySize * 2);
          sample.characters = getSampleText(tt.name);
          sample.x = COL_SAMPLE; sample.y = fy;
          frame.appendChild(sample);

          // Actual sample height after text rendering
          var sampleH = sample.height;

          // Specs column — stacked chips
          var specY = fy;
          addText(frame, 'Size: ' + fSize + 'px', boldFont, 12, COL_SPECS, specY, DARK);
          specY += 18;
          addText(frame, 'Weight: ' + fWeight, labelFont, 12, COL_SPECS, specY, MUTED);
          specY += 18;
          addText(frame, 'Line Height: ' + fLH, labelFont, 12, COL_SPECS, specY, MUTED);
          specY += 18;
          addText(frame, 'Font: ' + fFamily, labelFont, 12, COL_SPECS, specY, BLUE);

          // Row height = max of (sample text height, spec labels height, minimum 40px)
          var specsH = specY - fy + 24;
          var rowH = Math.max(sampleH + 12, specsH, 40);
          fy += rowH + 8;

          // Row separator
          var sep = figma.createRectangle();
          sep.resize(CONTENT_W, 1); sep.x = MARGIN; sep.y = fy;
          sep.fills = [{ type: 'SOLID', color: { r: 0.94, g: 0.94, b: 0.94 } }];
          frame.appendChild(sep);
          fy += 12;
        }

        // Resize frame to actual content
        frame.resize(FRAME_W, fy + SECTION_PAD);
      }

      renderTypoFrame(desktopTypo, 'Typography — Desktop');
      renderTypoFrame(mobileTypo, 'Typography — Mobile');

      // ══════════════════════════════════════════════════════════
      // SPACING FRAME — Desktop & Mobile side by side, bars not squares
      // ══════════════════════════════════════════════════════════
      if (tokens.spacing.length > 0) {
        var dSpacing = [];
        var mSpacing = [];
        for (var spi = 0; spi < tokens.spacing.length; spi++) {
          if (tokens.spacing[spi].name.toLowerCase().indexOf('mobile') > -1) {
            mSpacing.push(tokens.spacing[spi]);
          } else {
            dSpacing.push(tokens.spacing[spi]);
          }
        }

        var maxItems = Math.max(dSpacing.length, mSpacing.length);
        var spFrameH = SECTION_PAD + 60 + maxItems * 48 + SECTION_PAD;

        var spFrame = createSectionFrame('Spacing', spFrameH);
        var spy = SECTION_PAD;

        addText(spFrame, 'SPACING', boldFont, 32, MARGIN, spy, DARK);
        spy += 52;

        // Render spacing column as horizontal bars (Carbon-style)
        function renderSpacingBars(list, startX, title, y0) {
          addText(spFrame, title, boldFont, 16, startX, y0, BLUE);
          var ly = y0 + 32;

          for (var si = 0; si < Math.min(list.length, 12); si++) {
            var sp = list[si];
            var spVal = parseNumericValue(sp.value);
            var barW = Math.max(spVal * 3, 8); // Scale 3x for visibility
            barW = Math.min(barW, 400); // Cap

            // Token label
            var spParts = sp.name.split('/');
            var spDisplayName = spParts.filter(function(p) { return p !== 'desktop' && p !== 'mobile'; }).join('/');
            addText(spFrame, spDisplayName, labelFont, 12, startX, ly + 4, DARK);

            // Bar
            var bar = figma.createRectangle();
            bar.resize(barW, 24);
            bar.x = startX + 120;
            bar.y = ly;
            bar.cornerRadius = 4;
            bar.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.55, b: 1 } }];
            spFrame.appendChild(bar);

            // Value label
            addText(spFrame, sp.value, labelFont, 12, startX + 120 + barW + 12, ly + 4, MUTED);

            ly += 40;
          }
          return ly;
        }

        var dEnd = renderSpacingBars(dSpacing, MARGIN, '🖥  Desktop', spy);
        var mEnd = renderSpacingBars(mSpacing, MARGIN + 560, '📱  Mobile', spy);

        spFrame.resize(FRAME_W, Math.max(dEnd, mEnd) + SECTION_PAD);
      }

      // ══════════════════════════════════════════════════════════
      // BORDER RADIUS FRAME
      // ══════════════════════════════════════════════════════════
      if (tokens.borderRadius.length > 0) {
        var radFrameH = SECTION_PAD + 60 + 120 + SECTION_PAD;
        var radFrame = createSectionFrame('Border Radius', radFrameH);
        var ry = SECTION_PAD;

        addText(radFrame, 'BORDER RADIUS', boldFont, 32, MARGIN, ry, DARK);
        ry += 52;

        var rx = MARGIN;
        for (var ri = 0; ri < tokens.borderRadius.length; ri++) {
          var rToken = tokens.borderRadius[ri];
          var rVal = parseNumericValue(rToken.value);

          var rect = figma.createRectangle();
          rect.resize(64, 64);
          rect.x = rx; rect.y = ry;
          rect.cornerRadius = Math.min(rVal, 32);
          rect.fills = [{ type: 'SOLID', color: { r: 0.93, g: 0.93, b: 0.96 } }];
          rect.strokes = [{ type: 'SOLID', color: { r: 0.75, g: 0.75, b: 0.82 } }];
          rect.strokeWeight = 2;
          radFrame.appendChild(rect);

          // Name
          addText(radFrame, rToken.name.split('/').pop(), boldFont, 11, rx, ry + 72, DARK);
          // Value
          addText(radFrame, rToken.value, labelFont, 11, rx, ry + 88, MUTED);

          rx += 90;
        }
      }

      // ══════════════════════════════════════════════════════════
      // SHADOWS FRAME — on light gray background (MD pattern)
      // ══════════════════════════════════════════════════════════
      if (tokens.shadows.length > 0) {
        var shFrameH = SECTION_PAD + 60 + 200 + SECTION_PAD;
        var shFrame = createSectionFrame('Shadows', shFrameH);
        // Light gray background for shadow visibility
        shFrame.fills = [{ type: 'SOLID', color: { r: 0.96, g: 0.96, b: 0.96 } }];

        var shy = SECTION_PAD;
        addText(shFrame, 'SHADOWS / ELEVATION', boldFont, 32, MARGIN, shy, DARK);
        shy += 52;

        var shx = MARGIN;
        for (var shi = 0; shi < tokens.shadows.length; shi++) {
          var shToken = tokens.shadows[shi];
          var sv = shToken.value;
          var oxV = parseNumericValue(sv.offsetX || sv.x || '0');
          var oyV = parseNumericValue(sv.offsetY || sv.y || '0');
          var blV = parseNumericValue(sv.blur || '0');
          var spV = parseNumericValue(sv.spread || '0');
          var shC = parseColorToRGBA(sv.color || 'rgba(0,0,0,0.25)');

          // White card with shadow
          var card = figma.createRectangle();
          card.resize(140, 140);
          card.x = shx; card.y = shy;
          card.cornerRadius = 12;
          card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
          card.effects = [{
            type: 'DROP_SHADOW',
            color: { r: shC.r, g: shC.g, b: shC.b, a: shC.a },
            offset: { x: oxV, y: oyV },
            radius: blV,
            spread: spV,
            visible: true,
            blendMode: 'NORMAL'
          }];
          shFrame.appendChild(card);

          // Level name centered on card
          addText(shFrame, shToken.name.split('/').pop(), boldFont, 14, shx + 20, shy + 30, DARK);

          // Specs on card
          addText(shFrame, 'blur: ' + blV + 'px', labelFont, 11, shx + 20, shy + 56, MUTED);
          addText(shFrame, 'y: ' + oyV + 'px', labelFont, 11, shx + 20, shy + 72, MUTED);
          addText(shFrame, 'spread: ' + spV + 'px', labelFont, 11, shx + 20, shy + 88, MUTED);

          shx += 180;
        }
      }

      // ══════════════════════════════════════════════════════════
      // POSITION ALL FRAMES — stack vertically with proper spacing
      // This runs AFTER all frames are created and resized to actual content.
      // ══════════════════════════════════════════════════════════
      var stackY = 0;
      for (var fi = 0; fi < allFrames.length; fi++) {
        allFrames[fi].y = stackY;
        stackY += allFrames[fi].height + SECTION_GAP;
      }

      figma.ui.postMessage({ type: 'spec-complete', message: 'Visual spec created with ' + allFrames.length + ' section frames!' });

    } catch (error) {
      console.error('Error creating visual spec:', error);
      figma.ui.postMessage({
        type: 'error',
        message: 'Failed to create visual spec: ' + (error && error.message ? error.message : String(error))
      });
    }
  }
};
