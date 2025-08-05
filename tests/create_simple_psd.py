#!/usr/bin/env python3
"""
Create simple PSD files for testing using alternative approach
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw

def create_psd_from_images():
    """
    Create basic PSD files by converting from PIL images
    This uses a workaround since we can't create PSDs directly
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    # Create base images that represent what PSD layers would contain
    
    # 1. Create a multi-layer composition as PNG (temporary)
    base_img = Image.new('RGBA', (150, 120), (255, 255, 255, 255))
    draw = ImageDraw.Draw(base_img)
    
    # Background layer content
    draw.rectangle([0, 0, 150, 120], fill=(200, 220, 255, 255))
    draw.text((10, 10), "Background Layer", fill='black')
    
    # Overlay layer content
    draw.rectangle([30, 40, 120, 80], fill=(255, 100, 100, 200))
    draw.text((35, 55), "Overlay", fill='white')
    
    # Draft layer content (should be hideable)
    draw.rectangle([10, 90, 80, 110], fill=(100, 255, 100, 150))
    draw.text((15, 95), "Draft", fill='black')
    
    base_img.save(fixtures_dir / "test_multilayer_reference.png")
    
    # Since we can't create real PSDs programmatically, create a note
    # about what we need and create minimal test infrastructure
    
    with open(fixtures_dir / "MINIMAL_PSD_SPEC.txt", "w") as f:
        f.write("""
MINIMAL PSD TEST FILES SPECIFICATION

For comprehensive PSD testing, we need these files:

1. test_simple.psd (50x40 pixels):
   - Single layer named "Background"
   - Basic RGB content
   
2. test_multilayer.psd (150x120 pixels):
   - Layer 0: "Background" (base content)  
   - Layer 1: "Overlay" (can be hidden)
   - Layer 2: "Draft" (can be hidden)
   - Layer 3: "Signature" (can be hidden)

3. test_signature.psd (30x20 pixels):
   - Semi-transparent signature content
   - Single layer for use as signature

4. test_complex.psd (200x150 pixels):
   - Multiple layers (5+)
   - Layer groups (if supported)
   - Various blend modes

CURRENT WORKAROUND:
Since we cannot create PSDs programmatically, we'll:
1. Create comprehensive tests that work with PNG files
2. Add conditional PSD tests that skip when real PSDs unavailable
3. Document exactly what PSD features need manual testing

MANUAL CREATION NEEDED:
Use Photoshop, GIMP, or similar to create the above PSD files
and place them in tests/fixtures/ directory.
""")
    
    print("Created PSD specification and reference images")
    return True

def test_psd_tools_availability():
    """Test if psd-tools can handle basic operations"""
    try:
        from psd_tools import PSDImage
        
        # Try to create a minimal test
        print("psd-tools is available")
        print("psd-tools version:", getattr(PSDImage, '__version__', 'unknown'))
        return True
        
    except ImportError as e:
        print(f"psd-tools not available: {e}")
        return False

if __name__ == "__main__":
    test_psd_tools_availability()
    create_psd_from_images()