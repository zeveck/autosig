#!/usr/bin/env python3
"""
Create real PSD files for testing using Aspose.PSD
"""

import os
from pathlib import Path

def create_real_psd_files():
    """Create actual PSD files using Aspose.PSD library"""
    try:
        from aspose.psd import Color, Graphics, Pen, Rectangle
        from aspose.psd.brushes import SolidBrush
        from aspose.psd.fileformats.psd import PsdImage
        
        fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
        fixtures_dir.mkdir(exist_ok=True)
        
        print("Creating real PSD files using Aspose.PSD...")
        
        # 1. Create test_simple.psd (50x40 pixels)
        print("Creating test_simple.psd...")
        simple_path = fixtures_dir / "test_simple.psd"
        
        with PsdImage(50, 40) as psd_simple:
            # Add a regular layer called "Background"
            background_layer = psd_simple.add_regular_layer()
            graphics = Graphics(background_layer)
            
            # Add some simple content
            graphics.clear(Color.light_blue)
            pen = Pen(Color.dark_blue, 2)
            graphics.draw_rectangle(pen, Rectangle(5, 5, 35, 25))
            
            psd_simple.save(str(simple_path))
        print(f"Created {simple_path}")
        
        # 2. Create test_multilayer.psd (150x120 pixels) with named layers
        print("Creating test_multilayer.psd...")
        multilayer_path = fixtures_dir / "test_multilayer.psd"
        
        with PsdImage(150, 120) as psd_multi:
            # Background layer
            background_layer = psd_multi.add_regular_layer()
            background_layer.display_name = "Background"
            graphics = Graphics(background_layer)
            graphics.clear(Color.light_gray)
            graphics.fill_rectangle(SolidBrush(Color.light_blue), Rectangle(0, 0, 150, 120))
            
            # Overlay layer
            overlay_layer = psd_multi.add_regular_layer()
            overlay_layer.display_name = "Overlay"
            graphics = Graphics(overlay_layer)
            graphics.fill_rectangle(SolidBrush(Color.from_argb(128, 255, 100, 100)), Rectangle(20, 20, 110, 80))
            
            # Draft layer
            draft_layer = psd_multi.add_regular_layer()
            draft_layer.display_name = "Draft"
            graphics = Graphics(draft_layer)
            graphics.fill_rectangle(SolidBrush(Color.from_argb(100, 100, 255, 100)), Rectangle(10, 90, 80, 20))
            
            # Signature layer
            signature_layer = psd_multi.add_regular_layer()
            signature_layer.display_name = "Signature"
            graphics = Graphics(signature_layer)
            graphics.fill_rectangle(SolidBrush(Color.from_argb(150, 255, 0, 0)), Rectangle(100, 100, 40, 15))
            
            psd_multi.save(str(multilayer_path))
        print(f"Created {multilayer_path}")
        
        # 3. Create test_signature.psd (30x20 pixels)
        print("Creating test_signature.psd...")
        signature_path = fixtures_dir / "test_signature.psd"
        
        with PsdImage(30, 20) as psd_sig:
            sig_layer = psd_sig.add_regular_layer()
            graphics = Graphics(sig_layer)
            
            # Semi-transparent red signature
            graphics.fill_rectangle(SolidBrush(Color.from_argb(128, 255, 0, 0)), Rectangle(2, 2, 26, 16))
            
            psd_sig.save(str(signature_path))
        print(f"Created {signature_path}")
        
        # 4. Create test_complex.psd (200x150 pixels)
        print("Creating test_complex.psd...")
        complex_path = fixtures_dir / "test_complex.psd"
        
        with PsdImage(200, 150) as psd_complex:
            # Create multiple layers with different content
            for i in range(5):
                layer = psd_complex.add_regular_layer()
                layer.display_name = f"Layer_{i+1}"
                graphics = Graphics(layer)
                
                # Different colors and positions for each layer
                colors = [Color.red, Color.green, Color.blue, Color.yellow, Color.magenta]
                x = 20 + (i * 30)
                y = 20 + (i * 20)
                graphics.fill_rectangle(SolidBrush(Color.from_argb(100, colors[i].r, colors[i].g, colors[i].b)), 
                                      Rectangle(x, y, 40, 30))
            
            psd_complex.save(str(complex_path))
        print(f"Created {complex_path}")
        
        print("\nAll PSD files created successfully!")
        return True
        
    except ImportError as e:
        print(f"Aspose.PSD not available: {e}")
        return False
    except Exception as e:
        print(f"Failed to create PSD files: {e}")
        return False

def test_created_psds():
    """Test that the created PSDs can be loaded by psd-tools"""
    try:
        from psd_tools import PSDImage
        
        fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
        psd_files = ["test_simple.psd", "test_multilayer.psd", "test_signature.psd", "test_complex.psd"]
        
        print("\nTesting created PSD files with psd-tools...")
        for psd_file in psd_files:
            psd_path = fixtures_dir / psd_file
            if psd_path.exists():
                try:
                    psd = PSDImage.open(psd_path)
                    print(f"SUCCESS {psd_file}: {psd.width}x{psd.height}, {len(psd)} layers")
                except Exception as e:
                    print(f"FAILED {psd_file}: Failed to load - {e}")
            else:
                print(f"MISSING {psd_file}: File not found")
        
        return True
        
    except ImportError:
        print("psd-tools not available for testing")
        return False

if __name__ == "__main__":
    success = create_real_psd_files()
    if success:
        test_created_psds()
    else:
        print("\nFailed to create PSD files. You'll need to create them manually.")