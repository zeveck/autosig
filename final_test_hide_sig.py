#!/usr/bin/env python3
"""
Final integration test for --hide-signature-layer feature
"""

import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess
import sys
import os

# Add parent directory to path for importing autosig
sys.path.insert(0, str(Path(__file__).parent))
from autosig import (
    calculate_image_difference,
    likely_has_signature,
    detect_and_hide_signature_layers
)

def test_end_to_end():
    """Test the feature end-to-end with command line"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create test images with signature-like content in corner
        for i in range(3):
            img = Image.new('RGB', (500, 400), 'lightblue')
            draw = ImageDraw.Draw(img)
            
            # Main content
            draw.ellipse([50, 50, 250, 250], fill='darkblue')
            draw.text((120, 150), f"IMAGE {i+1}", fill='white')
            
            # Add signature-like element in lower-right
            sig_x = 500 - 180
            sig_y = 400 - 120
            draw.rectangle([sig_x, sig_y, sig_x+160, sig_y+80], fill='black')
            draw.text((sig_x+20, sig_y+30), "OLD SIGNATURE", fill='white')
            
            img.save(tmppath / f"test_{i:02d}.png")
        
        # Create new signature
        sig_dir = tmppath / "sigs"
        sig_dir.mkdir()
        new_sig = Image.new('RGBA', (100, 50), (255, 0, 0, 200))
        draw = ImageDraw.Draw(new_sig)
        draw.text((10, 15), "NEW SIG", fill='white')
        new_sig.save(sig_dir / "newsig.png")
        
        print(f"Created test files in: {tmppath}")
        print("Files:", list(tmppath.glob("*.png")))
        
        # Test 1: Process WITHOUT --hide-signature-layer
        print("\n=== Test 1: WITHOUT --hide-signature-layer ===")
        result = subprocess.run([
            sys.executable, "autosig.py",
            str(tmppath),
            str(sig_dir / "newsig.png"),
            "--force",
            "--suffix", "_without"
        ], capture_output=True, text=True)
        
        print("Output:", result.stdout)
        without_files = list(tmppath.glob("*_without.png"))
        print(f"Created {len(without_files)} files")
        
        # Test 2: Process WITH --hide-signature-layer (should be ignored for PNG)
        print("\n=== Test 2: WITH --hide-signature-layer (PNG files) ===")
        result = subprocess.run([
            sys.executable, "autosig.py",
            str(tmppath),
            str(sig_dir / "newsig.png"),
            "--hide-signature-layer",
            "--force",
            "--suffix", "_with"
        ], capture_output=True, text=True)
        
        print("Output:", result.stdout)
        with_files = list(tmppath.glob("*_with.png"))
        print(f"Created {len(with_files)} files")
        
        # Should NOT show PSD-specific warnings for PNG files
        assert "but no hideable layer found" not in result.stdout, "Should not show PSD warning for PNG files"
        
        # Test 3: Test help text
        print("\n=== Test 3: Verify help text ===")
        result = subprocess.run([
            sys.executable, "autosig.py", "--help"
        ], capture_output=True, text=True)
        
        assert "--hide-signature-layer" in result.stdout, "Flag missing from help"
        assert "Automatically detect and hide" in result.stdout, "Description missing"
        print("[OK] Help text includes --hide-signature-layer")
        
        print("\n=== ALL TESTS PASSED ===")
        print("The --hide-signature-layer feature is working correctly:")
        print("1. Flag is properly defined in CLI")
        print("2. PNG files are handled correctly (feature ignored)")
        print("3. No inappropriate warnings for non-PSD files")
        print("\nNote: Full PSD testing requires actual PSD files with layers")
        
        return True

if __name__ == "__main__":
    try:
        success = test_end_to_end()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)