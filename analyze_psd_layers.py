#!/usr/bin/env python3
"""
Analyze PSD layers to understand what each contains
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np
from psd_tools import PSDImage

def analyze_psd_layers(psd_path):
    """Analyze each layer in a PSD file"""
    print(f"\n=== Analyzing PSD: {psd_path} ===\n")
    
    psd = PSDImage.open(psd_path)
    width, height = psd.width, psd.height
    
    print(f"Document size: {width}x{height}")
    print(f"Total layers: {len(psd)}\n")
    
    # Define signature region (lower-right corner)
    sig_region = (width - 250, height - 150, width, height)
    print(f"Signature detection region: 250x150 pixels at ({sig_region[0]}, {sig_region[1]})\n")
    
    # Get composite with all layers
    full_composite = psd.composite(force=True)
    full_sig_region = full_composite.crop(sig_region)
    full_sig_region.save("analysis_full_composite.png")
    print("Saved full composite signature region to analysis_full_composite.png\n")
    
    # Analyze each layer individually
    print("=== Layer Analysis ===\n")
    
    for i, layer in enumerate(psd):
        print(f"Layer {i}: {layer.name}")
        print(f"  Visible: {layer.visible}")
        print(f"  Bounds: {layer.bbox}")
        
        # Check if layer overlaps with signature region
        if layer.bbox:
            x1, y1, x2, y2 = layer.bbox
            overlaps = not (x2 <= sig_region[0] or x1 >= sig_region[2] or 
                          y2 <= sig_region[1] or y1 >= sig_region[3])
            print(f"  Overlaps signature region: {overlaps}")
            
            if overlaps:
                # Calculate how much it overlaps
                overlap_x1 = max(x1, sig_region[0])
                overlap_y1 = max(y1, sig_region[1])
                overlap_x2 = min(x2, sig_region[2])
                overlap_y2 = min(y2, sig_region[3])
                
                overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                layer_area = (x2 - x1) * (y2 - y1)
                sig_area = 250 * 150
                
                print(f"  Overlap area: {overlap_area:,} pixels")
                print(f"  % of layer in sig region: {(overlap_area/layer_area)*100:.1f}%")
                print(f"  % of sig region covered: {(overlap_area/sig_area)*100:.1f}%")
        
        # Hide all layers except this one to see what it contains
        original_states = []
        for j, other_layer in enumerate(psd):
            original_states.append(other_layer.visible)
            other_layer.visible = (i == j)  # Only keep current layer visible
        
        # Composite with only this layer
        solo_composite = psd.composite(force=True)
        solo_sig_region = solo_composite.crop(sig_region)
        
        # Check if this layer has any content in signature region
        solo_array = np.array(solo_sig_region)
        has_content = np.any(solo_array[:,:,3] > 0) if solo_array.shape[2] == 4 else np.any(solo_array != 0)
        print(f"  Has content in sig region: {has_content}")
        
        if has_content:
            # Save this layer's contribution to signature region
            solo_sig_region.save(f"analysis_layer_{i}_solo.png")
            print(f"  Saved layer's sig region to analysis_layer_{i}_solo.png")
            
            # Calculate how much this layer changes the signature region
            # when removed
            for j, other_layer in enumerate(psd):
                other_layer.visible = original_states[j]
            
            # Now hide just this layer
            layer.visible = False
            without_this = psd.composite(force=True)
            without_sig_region = without_this.crop(sig_region)
            
            # Calculate difference
            full_array = np.array(full_sig_region)
            without_array = np.array(without_sig_region)
            
            if full_array.shape == without_array.shape:
                diff = np.mean(np.abs(full_array.astype(float) - without_array.astype(float)))
                print(f"  Mean change when removed: {diff:.2f}")
                
                # Save the "without" version
                without_sig_region.save(f"analysis_without_layer_{i}.png")
                print(f"  Saved 'without layer {i}' to analysis_without_layer_{i}.png")
        
        # Restore original states
        for j, other_layer in enumerate(psd):
            other_layer.visible = original_states[j]
        
        print()
    
    print("\n=== Recommendations ===")
    print("1. Check the generated images to see which layer(s) contain the actual signature")
    print("2. The signature is likely in a layer that:")
    print("   - Has a small overlap area with the signature region")
    print("   - Shows text/graphics in the solo image")
    print("   - When removed, causes a noticeable but localized change")
    print("\n3. You may want to manually hide specific layers using --hide-layer")
    print("   instead of --hide-signature-layer if the auto-detection is too aggressive")

if __name__ == "__main__":
    psd_file = r"E:\Autumn Art (Unique)\PSD\foo\collisions.psd"
    analyze_psd_layers(psd_file)