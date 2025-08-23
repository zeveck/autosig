#!/usr/bin/env python3
"""
Create test fixture files for AutoSig tests
"""

from PIL import Image, ImageDraw
import os

def create_test_fixtures():
    """Create simple test images for testing"""
    fixtures_dir = os.path.dirname(__file__) + "/fixtures"
    
    # Create a simple test source image (200x150 blue rectangle)
    source_img = Image.new('RGB', (200, 150), 'lightblue')
    draw = ImageDraw.Draw(source_img)
    draw.rectangle([10, 10, 190, 140], fill='darkblue', outline='navy')
    draw.text((20, 30), "TEST", fill='white')
    source_img.save(f"{fixtures_dir}/test_source.png", "PNG")
    
    # Create a simple signature (20x15 red rectangle with transparency)
    sig_img = Image.new('RGBA', (20, 15), (255, 0, 0, 128))  # Semi-transparent red
    draw = ImageDraw.Draw(sig_img)
    draw.text((2, 2), "SIG", fill='white')
    sig_img.save(f"{fixtures_dir}/test_signature.png", "PNG")
    
    # Create a larger test image (300x200)
    large_img = Image.new('RGB', (300, 200), 'lightgreen')
    draw = ImageDraw.Draw(large_img)
    draw.ellipse([50, 50, 250, 150], fill='darkgreen', outline='black')
    draw.text((120, 90), "LARGE TEST", fill='white')
    large_img.save(f"{fixtures_dir}/test_large.png", "PNG")
    
    print("Test fixtures created successfully!")

def create_minimal_psd_files():
    """Create minimal PSD files for testing PSD functionality"""
    try:
        from psd_tools import PSDImage
        from psd_tools.api.layers import PixelLayer
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        
        # Note: psd-tools doesn't have direct PSD creation capabilities
        # We'll create some basic test data and minimal PSD structures
        print("Warning: Cannot create real PSD files programmatically with psd-tools")
        print("PSD fixtures need to be created manually or with external tools")
        print("For now, creating PNG equivalents and documenting the need for real PSDs")
        
        # Create PNG files that simulate PSD structures for initial testing
        # These will be replaced with real PSD files when available
        
        # Simulated "multi-layer" image (will need real PSD)
        multilayer_img = Image.new('RGBA', (150, 120), (255, 255, 255, 255))
        draw = ImageDraw.Draw(multilayer_img)
        draw.rectangle([10, 10, 140, 50], fill='red', outline='darkred')
        draw.text((15, 20), "Background Layer", fill='white')
        draw.rectangle([20, 60, 130, 100], fill='blue', outline='darkblue')
        draw.text((25, 75), "Overlay Layer", fill='white')
        multilayer_img.save(f"{fixtures_dir}/test_multilayer_simulation.png", "PNG")
        
        # Create a note file explaining what's needed
        with open(f"{fixtures_dir}/PSD_FIXTURES_NEEDED.txt", "w") as f:
            f.write("""
CRITICAL: Real PSD Test Fixtures Needed

Current Status: Using PNG simulations - NOT SUFFICIENT FOR REAL TESTING

Required PSD Files:
1. test_multilayer.psd - PSD with multiple named layers:
   - "Background" layer (base image)
   - "Overlay" layer (can be hidden)
   - "Signature" layer (can be hidden)
   - "Draft" layer (can be hidden)

2. test_signature.psd - PSD file to use as signature

3. test_simple.psd - Basic PSD with 1-2 layers

4. test_complex.psd - PSD with many layers, groups, effects

How to Create:
- Use Photoshop, GIMP, or other PSD-capable editor
- Create layers with specific names for testing layer hiding
- Save as PSD format
- Place in tests/fixtures/ directory

Without real PSD files, our PSD testing is essentially mocked and unreliable.
""")
        
        print("Created placeholder files and documentation for needed PSD fixtures")
        return False  # Indicates real PSDs not available
        
    except ImportError:
        print("psd-tools not available for PSD creation")
        return False

if __name__ == "__main__":
    create_test_fixtures()
    create_minimal_psd_files()