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
  // VISUAL SPEC GENERATOR
  // Creates a visual reference page showing all tokens
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

      // Use current page instead of creating new page (Figma Starter plan has 3-page limit)
      var specPage = figma.currentPage;
      specPage.name = '🎨 Design System Spec';

      // Clear existing children on the page so spec starts fresh
      while (specPage.children.length > 0) {
        specPage.children[0].remove();
      }

      var yOffset = 0;
      var xOffset = 0;
      var sectionGap = 80;
      var itemGap = 16;

      // Load Inter font for labels (with fallbacks for environments missing styles)
      var headingStyle = 'Regular';
      await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
      try {
        await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
        headingStyle = 'Bold';
      } catch (e) {
        console.warn('Inter Bold not available, using Regular for headings');
      }

      // === COLORS SECTION ===
      if (tokens.colors.length > 0) {
        // Section title
        var colorTitle = figma.createText();
        colorTitle.characters = 'COLORS';
        colorTitle.fontName = { family: 'Inter', style: headingStyle };
        colorTitle.fontSize = 24;
        colorTitle.x = xOffset;
        colorTitle.y = yOffset;
        specPage.appendChild(colorTitle);
        yOffset += 50;

        var colorX = xOffset;
        var colorY = yOffset;
        var swatchSize = 60;
        var swatchGap = 16;
        var colsPerRow = 6;

        for (var ci = 0; ci < tokens.colors.length; ci++) {
          var colorToken = tokens.colors[ci];
          var col = ci % colsPerRow;
          var row = Math.floor(ci / colsPerRow);

          // Color swatch
          var swatch = figma.createRectangle();
          swatch.resize(swatchSize, swatchSize);
          swatch.x = colorX + col * (swatchSize + swatchGap);
          swatch.y = colorY + row * (swatchSize + swatchGap + 30);
          swatch.cornerRadius = 8;

          var rgb = hexToRgb(colorToken.value);
          swatch.fills = [{ type: 'SOLID', color: rgb }];
          swatch.strokes = [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }];
          swatch.strokeWeight = 1;
          specPage.appendChild(swatch);

          // Color name label
          var colorLabel = figma.createText();
          colorLabel.characters = colorToken.name.split('/').pop() || colorToken.name;
          colorLabel.fontName = { family: 'Inter', style: 'Regular' };
          colorLabel.fontSize = 10;
          colorLabel.x = swatch.x;
          colorLabel.y = swatch.y + swatchSize + 4;
          specPage.appendChild(colorLabel);

          // Color value label
          var valueLabel = figma.createText();
          valueLabel.characters = colorToken.value.toUpperCase();
          valueLabel.fontName = { family: 'Inter', style: 'Regular' };
          valueLabel.fontSize = 9;
          valueLabel.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
          valueLabel.x = swatch.x;
          valueLabel.y = swatch.y + swatchSize + 16;
          specPage.appendChild(valueLabel);
        }

        var colorRows = Math.ceil(tokens.colors.length / colsPerRow);
        yOffset = colorY + colorRows * (swatchSize + swatchGap + 30) + sectionGap;
      }

      // === TYPOGRAPHY SECTION ===
      // IMPORTANT: Only use already-loaded Inter Regular/Bold for ALL text in the spec.
      // Never attempt to load custom fonts — they may not exist in the Figma environment
      // and would crash the entire spec generation. Font details are shown as labels.
      if (tokens.typography.length > 0) {
        var typoTitle = figma.createText();
        typoTitle.characters = 'TYPOGRAPHY';
        typoTitle.fontName = { family: 'Inter', style: headingStyle };
        typoTitle.fontSize = 24;
        typoTitle.x = xOffset;
        typoTitle.y = yOffset;
        specPage.appendChild(typoTitle);
        yOffset += 50;

        for (var ti = 0; ti < tokens.typography.length; ti++) {
          var typoToken = tokens.typography[ti];
          var value = typoToken.value;

          var fontFamily = value.fontFamily || 'Inter';
          if (fontFamily.indexOf(',') > -1) {
            fontFamily = fontFamily.split(',')[0].trim();
          }
          var fontSize = parseNumericValue(value.fontSize) || 16;
          var fontWeight = value.fontWeight || '400';
          var displaySize = Math.min(fontSize, 48); // Cap display size

          // Sample text — always use Inter (safe), size shows relative scale
          var sampleText = figma.createText();
          sampleText.fontName = { family: 'Inter', style: headingStyle };
          sampleText.fontSize = displaySize;
          sampleText.characters = typoToken.name.split('/').pop() || 'Sample Text';
          sampleText.x = xOffset;
          sampleText.y = yOffset;
          specPage.appendChild(sampleText);

          // Specs label — show the ACTUAL font specs as readable text
          var specsLabel = figma.createText();
          specsLabel.fontName = { family: 'Inter', style: 'Regular' };
          specsLabel.fontSize = 11;
          specsLabel.characters = fontFamily + '  ·  ' + fontSize + 'px  ·  wt ' + fontWeight;
          specsLabel.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
          specsLabel.x = xOffset + 300;
          specsLabel.y = yOffset + 4;
          specPage.appendChild(specsLabel);

          yOffset += Math.max(displaySize, 24) + itemGap;
        }

        yOffset += sectionGap;
      }

      // === SPACING SECTION ===
      if (tokens.spacing.length > 0) {
        var spacingTitle = figma.createText();
        spacingTitle.characters = 'SPACING';
        spacingTitle.fontName = { family: 'Inter', style: headingStyle };
        spacingTitle.fontSize = 24;
        spacingTitle.x = xOffset;
        spacingTitle.y = yOffset;
        specPage.appendChild(spacingTitle);
        yOffset += 50;

        var spacingX = xOffset;
        for (var si = 0; si < Math.min(tokens.spacing.length, 12); si++) {
          var spacingToken = tokens.spacing[si];
          var spacingValue = parseNumericValue(spacingToken.value);

          // Spacing bar
          var bar = figma.createRectangle();
          bar.resize(Math.max(spacingValue, 4), 24);
          bar.x = spacingX;
          bar.y = yOffset;
          bar.cornerRadius = 4;
          bar.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.6, b: 1 } }];
          specPage.appendChild(bar);

          // Label
          var spLabel = figma.createText();
          spLabel.characters = spacingToken.name.split('/').pop() + ' = ' + spacingToken.value;
          spLabel.fontName = { family: 'Inter', style: 'Regular' };
          spLabel.fontSize = 11;
          spLabel.x = spacingX;
          spLabel.y = yOffset + 30;
          specPage.appendChild(spLabel);

          spacingX += Math.max(spacingValue, 40) + 24;
        }

        yOffset += 80 + sectionGap;
      }

      // === BORDER RADIUS SECTION ===
      if (tokens.borderRadius.length > 0) {
        var radiusTitle = figma.createText();
        radiusTitle.characters = 'BORDER RADIUS';
        radiusTitle.fontName = { family: 'Inter', style: headingStyle };
        radiusTitle.fontSize = 24;
        radiusTitle.x = xOffset;
        radiusTitle.y = yOffset;
        specPage.appendChild(radiusTitle);
        yOffset += 50;

        var radiusX = xOffset;
        for (var ri = 0; ri < tokens.borderRadius.length; ri++) {
          var radiusToken = tokens.borderRadius[ri];
          var radiusValue = parseNumericValue(radiusToken.value);

          // Rounded rectangle
          var rect = figma.createRectangle();
          rect.resize(50, 50);
          rect.x = radiusX;
          rect.y = yOffset;
          rect.cornerRadius = Math.min(radiusValue, 25);
          rect.fills = [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.95 } }];
          rect.strokes = [{ type: 'SOLID', color: { r: 0.8, g: 0.8, b: 0.8 } }];
          rect.strokeWeight = 2;
          specPage.appendChild(rect);

          // Label
          var rLabel = figma.createText();
          rLabel.characters = radiusToken.name.split('/').pop() + '\n' + radiusToken.value;
          rLabel.fontName = { family: 'Inter', style: 'Regular' };
          rLabel.fontSize = 10;
          rLabel.textAlignHorizontal = 'CENTER';
          rLabel.x = radiusX;
          rLabel.y = yOffset + 56;
          specPage.appendChild(rLabel);

          radiusX += 70;
        }

        yOffset += 100 + sectionGap;
      }

      // === SHADOWS SECTION ===
      if (tokens.shadows.length > 0) {
        var shadowTitle = figma.createText();
        shadowTitle.characters = 'SHADOWS';
        shadowTitle.fontName = { family: 'Inter', style: headingStyle };
        shadowTitle.fontSize = 24;
        shadowTitle.x = xOffset;
        shadowTitle.y = yOffset;
        specPage.appendChild(shadowTitle);
        yOffset += 50;

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
          card.resize(80, 80);
          card.x = shadowX;
          card.y = yOffset;
          card.cornerRadius = 8;
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

          // Label
          var shLabel = figma.createText();
          shLabel.characters = shadowToken.name.split('/').pop();
          shLabel.fontName = { family: 'Inter', style: 'Regular' };
          shLabel.fontSize = 11;
          shLabel.x = shadowX;
          shLabel.y = yOffset + 90;
          specPage.appendChild(shLabel);

          shadowX += 110;
        }
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
