#!/usr/bin/env python3
"""
Create test fixture files for AutoSig tests
"""

from PIL import Image, ImageDraw
import os

def create_test_fixtures():
    """Create simple test images for testing"""
    fixtures_dir = os.path.dirname(__file__) + "/fixtures"
    
    # Create a simple test source image (100x80 blue rectangle)
    source_img = Image.new('RGB', (100, 80), 'lightblue')
    draw = ImageDraw.Draw(source_img)
    draw.rectangle([10, 10, 90, 70], fill='darkblue', outline='navy')
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

if __name__ == "__main__":
    create_test_fixtures()