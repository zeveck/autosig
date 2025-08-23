# Auto-Hide Signature Layer Feature Plan

## Executive Summary
Implement a `--hide-signature-layer` flag that automatically detects and hides existing signature layers in PSD files by analyzing changes in the lower-right corner when toggling layer visibility.

## Problem Statement
- Users have PSDs with existing signatures in various layer structures
- No consistent layer naming convention across files (could be "Signature", "sig", "watermark", "Layer 23", etc.)
- Current `--hide-layer` requires knowing the exact layer name/index for each file
- Need an automated solution that works across diverse PSD files

## Proposed Solution

### Core Algorithm
```
1. Load PSD file with all currently-visible layers shown
2. Capture reference snapshot of lower-right corner (where signatures typically appear)
3. For each visible layer:
   a. Temporarily hide the layer
   b. Capture new snapshot of lower-right corner
   c. Compare snapshots using image difference metric
   d. If difference exceeds threshold:
      - Mark this layer as a "signature layer"
      - Keep it hidden
   e. Otherwise, restore the layer
4. Process image normally with signature layers hidden
5. Apply new signature as usual
```

### Technical Implementation Details

#### Detection Region
- **Fixed region**: 250x150 pixels in lower-right corner
- **Rationale**: 
  - Covers typical signature sizes (most are 100-200px wide, 50-100px tall)
  - Signatures are 99% of the time in lower-right
  - Avoiding configurability keeps it simple and fast
  - If signature is elsewhere, user can still use manual `--hide-layer`

#### Difference Detection Method
```python
def calculate_difference(img1, img2):
    """Calculate normalized difference between two image regions"""
    # Convert to numpy arrays
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    
    # Calculate mean squared error
    mse = np.mean((arr1 - arr2) ** 2)
    
    # Normalize to 0-100 scale
    # Max possible MSE is 255^2 = 65025 for RGB
    normalized = (mse / 65025) * 100
    
    return normalized

def likely_has_signature(corner_region):
    """Check if corner region likely contains a signature"""
    # Convert to grayscale for analysis
    gray = corner_region.convert('L')
    pixels = np.array(gray)
    
    # Check for high contrast areas (signatures usually have text/graphics)
    std_dev = np.std(pixels)
    
    # If standard deviation > threshold, likely has content
    return std_dev > 30  # Tune based on testing
```

#### Threshold Strategy
- **Initial threshold**: 5% normalized difference
- **Reasoning**:
  - Signatures typically have high contrast with background
  - Removing them causes noticeable change in pixel values
  - 5% catches most signatures without false positives
  - May need tuning based on testing

#### Layer State Management
```python
class LayerStateManager:
    def __init__(self, psd):
        self.psd = psd
        self.originally_hidden = []  # Layers hidden before we started
        self.signature_layers = []   # Layers we hid (signatures)
        
    def detect_signature_layers(self):
        # Record initial state
        for i, layer in enumerate(self.psd):
            if not layer.is_visible():
                self.originally_hidden.append(i)
        
        # Detection logic here...
        
    def restore_non_signature_layers(self):
        # After processing, ensure only signature layers stay hidden
        for i, layer in enumerate(self.psd):
            if i not in self.signature_layers and i not in self.originally_hidden:
                layer.visible = True
```

### Integration Points

#### Command Line Argument
```python
parser.add_argument(
    "--hide-signature-layer",
    action="store_true",
    help="Automatically detect and hide existing signature layers in PSD files"
)
```

#### Processing Flow
1. Load PSD file
2. Apply manual `--hide-layer` if specified
3. Apply `--hide-signature-layer` detection if specified
4. Continue with normal processing (crop, resize, apply new signature)

#### Compatibility
- **Works with**: PSD files only
- **Combines with**: 
  - `--hide-layer` (manual hiding happens first)
  - All other flags (crop, resize, etc.)
- **Skipped for**: PNG, JPG, and other non-PSD formats (with info message)

## Edge Cases & Handling

### 1. No Signature Detected
- **Behavior**: Continue processing normally
- **User feedback**: None (silent - too noisy in batch processing)
- **Rationale**: Many files might not have signatures, avoid spam

### 2. Multiple Layers Form Signature
- **Behavior**: Hide all detected signature layers
- **Example**: Signature might be "text layer" + "logo layer"
- **Solution**: Algorithm naturally handles this by testing each layer

### 3. Signature Appears Present but Can't Be Hidden
- **Behavior**: Detect significant pixels in corner but no layer hides them
- **User feedback**: Warning: "Possible signature detected in file.psd but no hideable layer found"
- **Cause**: Signature burned into background or merged with content
- **Fallback**: User must use image editing software

### 4. False Positives
- **Risk**: Important layer in lower-right gets hidden
- **Mitigation**: 
  - Conservative threshold (5%)
  - Only check lower-right region
  - User can review output and adjust

### 5. Performance Impact
- **Issue**: Testing each layer requires multiple composite operations
- **Mitigation**:
  - Only for PSD files
  - Only when flag is used
  - Silent operation (no progress messages unless problems)

## Implementation Steps

### Phase 1: Core Detection Logic
1. Create `detect_signature_layers()` function
2. Implement image difference calculation
3. Add layer state tracking
4. Test with sample PSDs

### Phase 2: Integration
1. Add command-line argument
2. Integrate into `load_image_file()` function
3. Ensure proper layer state management
4. Add progress/status messages

### Phase 3: Testing
1. Create test PSDs with various signature configurations
2. Test with real-world PSDs
3. Tune threshold based on results
4. Add unit tests

### Phase 4: Documentation
1. Update README with new flag
2. Add examples
3. Document limitations

## Success Criteria
1. Correctly identifies signature layers in 90%+ of test cases
2. No false positives on critical content layers
3. Performance impact < 2 seconds per PSD
4. Works seamlessly with existing flags
5. Clear user feedback about what was detected/hidden

## Future Enhancements (Not in V1)
- [ ] Machine learning-based signature detection
- [ ] Configurable detection region (if users need it)
- [ ] Smart threshold adjustment based on image content
- [ ] Support for detecting signatures in flattened images
- [ ] Batch learning (detect pattern across multiple files)

## Decision Points Resolved

### Why not make region configurable?
- **Complexity**: Adds parsing, validation, documentation burden
- **Usage**: 99% of signatures are lower-right
- **Fallback**: Users can use `--hide-layer` for edge cases
- **Principle**: Start simple, add complexity only if needed

### Why 250x150 pixels?
- **Coverage**: Larger than most signatures (typically 150x75)
- **Safety**: Not so large it covers important content
- **Performance**: Small enough to compare quickly

### Why not use AI/ML?
- **Simplicity**: Pixel difference works well enough
- **Dependencies**: Avoid heavy ML libraries
- **Speed**: ML inference would be slower
- **Reliability**: Simple algorithm is predictable

## Example Usage

```bash
# Auto-detect and hide signature layers
python autosig.py psds/ newsig.png --hide-signature-layer

# Combine with manual hiding for problem files
python autosig.py psds/ newsig.png --hide-signature-layer --hide-layer "Draft"

# With other processing
python autosig.py psds/ newsig.png --hide-signature-layer --crop-portrait 4:5 --max-dimension 2000
```

## Summary
This feature provides an elegant solution to the signature layer problem by:
1. Automatically detecting signature layers through visual comparison
2. Keeping the implementation simple and focused
3. Working seamlessly with existing features
4. Providing clear feedback to users
5. Handling edge cases gracefully

The key insight is that we don't need perfect detection - we just need to catch most cases and provide fallbacks for the rest.