# AutoSig Advanced Features Implementation Plan

## Overview

This document outlines the implementation plan for three major new features that will transform AutoSig from a signature application tool into a comprehensive image processing utility.

## Feature Requirements

### 1. No-Signature Mode (`--no-sig`)
**Purpose**: Allow AutoSig to be used purely for image processing without signature application.

**Use Cases**:
- Batch resizing images
- Format conversion (PSD → PNG/JPG/WEBP)
- Layer manipulation without adding signatures
- Aspect ratio cropping workflows

### 2. PSD Layer Hiding (`--hide-layer`)
**Purpose**: Hide specific layers in PSD files before processing.

**Use Cases**:
- Remove existing signatures or watermarks
- Hide draft/review layers
- Process different layer combinations
- Clean up images for final output

### 3. Smart Aspect Ratio Cropping
**Purpose**: Apply maximum aspect ratio constraints to crop images that exceed specified ratios, preserving images already within limits.

**Use Cases**:
- Social media formatting (Instagram 4:5 max for portraits, 16:9 max for landscapes)
- Print formatting (enforce maximum elongation ratios)
- Prevent extremely tall or wide images while preserving well-proportioned ones
- Orientation-specific ratio constraints

## Technical Implementation Plan

### Phase 1: No-Signature Mode (Low Complexity)

#### Implementation Details
```python
# New parameter in process_image_files()
def process_image_files(..., apply_signature=True):
    # Skip signature application if apply_signature=False
    if apply_signature and signature_path:
        # Existing signature logic
    else:
        # Skip signature application
```

#### Command Line Interface
```bash
# Process images without signature
python autosig.py images/ --no-sig --format jpg --max-dimension 2000

# Convert PSD to PNG without signature
python autosig.py psds/ --no-sig --format png
```

#### Validation Rules
- `--no-sig` makes signature argument optional
- Error if no processing operations specified (no resize, no format change, etc.)
- All other existing features remain compatible

### Phase 2: PSD Layer Hiding (Medium Complexity)

#### Technical Approach
```python
def hide_layers_in_psd(psd, layers_to_hide):
    """
    Hide specified layers in PSD before composite
    
    Args:
        psd: PSDImage object
        layers_to_hide: List of layer names or indices
    """
    for layer_spec in layers_to_hide:
        if isinstance(layer_spec, int):
            # Hide by index
            if 0 <= layer_spec < len(psd):
                psd[layer_spec].visible = False
        else:
            # Hide by name (case-insensitive)
            for layer in psd:
                if layer.name.lower() == layer_spec.lower():
                    layer.visible = False
                    break
```

#### Command Line Interface
```bash
# Hide specific layers by name
python autosig.py images/ sig.png --hide-layer "Signature" --hide-layer "Watermark"

# Hide layers by index (0-based)
python autosig.py images/ --no-sig --hide-layer 0 --hide-layer 3

# Multiple layers, mixed names and indices
python autosig.py images/ sig.png --hide-layer "Layer 1" --hide-layer 5
```

#### Error Handling
- Warning if layer name not found (don't fail)
- Warning if layer index out of range
- Graceful handling of nested layer groups
- PSD-only feature (ignored for PNG inputs)

### Phase 3: Smart Aspect Ratio Cropping (High Complexity)

#### Core Logic
```python
def detect_orientation(width, height):
    """Classify image orientation"""
    ratio = width / height
    if ratio > 1.2:
        return "landscape"
    elif ratio < 0.8:
        return "portrait"
    else:
        return "square"

def parse_aspect_ratio(ratio_str):
    """Parse "4:5" or "16:9" format"""
    if ":" in ratio_str:
        w, h = map(int, ratio_str.split(":"))
        return w / h
    else:
        return float(ratio_str)

def center_crop_to_max_ratio(image, max_ratio, orientation):
    """
    Center crop image only if it exceeds the maximum aspect ratio for its orientation
    
    Args:
        image: PIL Image object
        max_ratio: Maximum allowed aspect ratio (width/height)
        orientation: "portrait", "landscape", or "square"
    
    Returns:
        PIL Image object (cropped only if needed)
    """
    current_ratio = image.width / image.height
    
    # Only crop if image exceeds the maximum ratio for its orientation
    if orientation == "portrait" and current_ratio < max_ratio:
        # Portrait image too tall (ratio too small) - crop height
        new_height = int(image.width / max_ratio)
        top = (image.height - new_height) // 2
        return image.crop((0, top, image.width, top + new_height))
    elif orientation == "landscape" and current_ratio > max_ratio:
        # Landscape image too wide (ratio too large) - crop width
        new_width = int(image.height * max_ratio)
        left = (image.width - new_width) // 2
        return image.crop((left, 0, left + new_width, image.height))
    else:
        # Image is within acceptable ratio limits, no cropping needed
        return image
```

#### Command Line Interface Design

**Orientation-Specific Cropping (Clean & Intuitive)**
```bash
# Different ratios for portrait vs landscape
python autosig.py images/ sig.png --crop-portrait 4:5 --crop-landscape 16:9

# Only crop portrait images (leave landscape unchanged)
python autosig.py images/ sig.png --crop-portrait 4:5

# Only crop landscape images (leave portrait unchanged)  
python autosig.py images/ sig.png --crop-landscape 16:9

# Same ratio for both orientations
python autosig.py images/ sig.png --crop-portrait 1:1 --crop-landscape 1:1
```

**Behavior Rules (Maximum Ratio Constraints)**:
- `--crop-portrait 4:5`: Only crop portrait images that are taller than 4:5 ratio (too tall)
- `--crop-landscape 16:9`: Only crop landscape images wider than 16:9 ratio (too wide)
- Images already within the specified maximum ratios remain unchanged
- Square images are treated as portrait for cropping purposes

#### Advanced Cropping Features
```python
# Future enhancements (v0.3.0+)
def smart_crop_with_focus(image, target_ratio, focus_area="center"):
    """
    Smart cropping with focus area detection
    
    focus_area options:
    - "center": Traditional center crop
    - "top": Preserve top portion (good for portraits)
    - "bottom": Preserve bottom portion
    - "auto": Use ML/algorithm to detect important areas
    """
```

### Phase 4: Integration & Command Line Design

#### Argument Precedence Rules
1. **Signature Processing**: 
   - If `--no-sig` specified: Skip signature entirely
   - Otherwise: Apply signature using provided signature file

2. **Layer Hiding**: 
   - Applied before signature processing
   - Only affects PSD files
   - Multiple layers can be hidden

3. **Processing Order**:
   1. Load source image
   2. Hide specified layers (PSD only)
   3. Apply aspect ratio cropping
   4. Apply signature (unless `--no-sig`)
   5. Resize to max dimension
   6. Save in specified format

#### Complete CLI Examples
```bash
# Complex workflow: Hide layers, apply max ratio constraints, add signature, resize
python autosig.py psds/ sig.png \
    --hide-layer "Draft" --hide-layer "Notes" \
    --crop-portrait 4:5 --crop-landscape 16:9 \
    --max-dimension 2000 \
    --format jpg --quality 90

# Pure image processing: No signature, hide layers, constrain ratios, convert format  
python autosig.py psds/ --no-sig \
    --hide-layer "Watermark" \
    --crop-landscape 16:9 \
    --format webp --quality 85

# Social media batch processing with ratio constraints
python autosig.py photos/ sig.png \
    --crop-portrait 4:5 --crop-landscape 16:9 \
    --max-dimension 1080 \
    --suffix "_insta" --format jpg
```

#### New Command Line Arguments Summary

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--no-sig` | flag | Skip signature application | `--no-sig` |
| `--hide-layer` | string (multi) | Hide PSD layer by name or index | `--hide-layer "Signature"` |
| `--crop-portrait` | string | Crop portrait/square images to ratio | `--crop-portrait 4:5` |
| `--crop-landscape` | string | Crop landscape images to ratio | `--crop-landscape 16:9` |

## Implementation Strategy

### Development Phases

#### Phase 1: Foundation (1-2 days)
- [ ] Implement `--no-sig` flag
- [ ] Update validation logic for optional signature
- [ ] Add tests for no-signature mode
- [ ] Update documentation

#### Phase 2: Layer Management (2-3 days)
- [ ] Research psd-tools layer manipulation
- [ ] Implement `hide_layers_in_psd()` function
- [ ] Add `--hide-layer` command line argument
- [ ] Handle layer names vs indices
- [ ] Add comprehensive error handling
- [ ] Create tests with sample PSD files
- [ ] Update documentation

#### Phase 3: Aspect Ratio Cropping (3-4 days)
- [ ] Implement orientation detection
- [ ] Create aspect ratio parsing
- [ ] Develop center crop algorithm
- [ ] Add crop command line arguments
- [ ] Handle edge cases (already correct ratio, etc.)
- [ ] Extensive testing with various image sizes
- [ ] Performance optimization
- [ ] Update documentation

#### Phase 4: Integration & Polish (1-2 days)
- [ ] Integrate all features into main processing flow
- [ ] Comprehensive integration testing
- [ ] Update help text and examples
- [ ] Update README with new features
- [ ] Add to CHANGELOG
- [ ] Version bump to 0.3.0

### Testing Strategy

#### Unit Tests
```python
# New test categories needed
class TestNoSignatureMode:
    def test_no_sig_flag_skips_signature()
    def test_no_sig_with_processing_operations()
    def test_no_sig_validation_rules()

class TestLayerHiding:
    def test_hide_layer_by_name()
    def test_hide_layer_by_index()
    def test_hide_multiple_layers()
    def test_layer_not_found_warning()
    def test_layer_hiding_psd_only()

class TestAspectRatioCropping:
    def test_orientation_detection()
    def test_aspect_ratio_parsing()
    def test_center_crop_algorithm()
    def test_portrait_landscape_specific_crops()
    def test_already_correct_ratio()
```

#### Integration Tests
- Test all features working together
- Performance testing with large batches
- Memory usage with large PSD files
- Error handling with malformed inputs

## Backwards Compatibility

### Guaranteed Compatibility
- All existing command line arguments work unchanged
- Existing workflows continue to function
- No breaking changes to core functionality

### New Defaults
- Signature file remains required unless `--no-sig` specified
- No cropping applied unless explicitly requested
- Layer hiding only applies when `--hide-layer` specified

## Risk Assessment

### Low Risk
- `--no-sig` implementation (simple flag)
- Basic layer hiding by name

### Medium Risk
- Layer hiding by index (bounds checking)
- Aspect ratio parsing and validation

### High Risk
- Center crop algorithm correctness
- Performance with large PSD files
- Memory usage with multiple large images

### Mitigation Strategies
- Extensive testing with edge cases
- Performance benchmarking
- Memory profiling
- Progressive rollout of features

## Future Enhancements (v0.4.0+)

### Smart Cropping
- ML-based important area detection
- Face detection for portrait cropping
- Rule of thirds alignment

### Advanced Layer Management
- Layer group manipulation
- Blend mode changes
- Layer effects processing

### Batch Processing Improvements
- Progress estimation
- Parallel processing
- Resume interrupted operations

## Success Metrics

### Feature Completeness
- [ ] All three major features implemented
- [ ] Comprehensive test coverage (>80%)
- [ ] Documentation updated
- [ ] Performance benchmarks established

### User Experience
- [ ] Intuitive command line interface
- [ ] Clear error messages
- [ ] Helpful examples and documentation
- [ ] Backwards compatibility maintained

### Code Quality
- [ ] Clean, maintainable code
- [ ] Proper error handling
- [ ] Performance optimized
- [ ] Well-documented functions

---

**Target Completion**: Version 0.3.0
**Estimated Development Time**: 7-11 days
**Testing Phase**: 2-3 additional days