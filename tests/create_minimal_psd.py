#!/usr/bin/env python3
"""
Create minimal PSD files for testing by generating them programmatically
"""

import struct
import os
from pathlib import Path

def create_minimal_psd():
    """
    Create a minimal PSD file with basic layers for testing
    This creates a very basic PSD structure that psd-tools can read
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    psd_path = fixtures_dir / "test_minimal.psd"
    
    # PSD File Header (26 bytes)
    header = bytearray()
    header.extend(b'8BPS')  # Signature
    header.extend(struct.pack('>H', 1))  # Version
    header.extend(b'\x00' * 6)  # Reserved
    header.extend(struct.pack('>H', 3))  # Channels (RGB)
    header.extend(struct.pack('>I', 100))  # Height
    header.extend(struct.pack('>I', 100))  # Width
    header.extend(struct.pack('>H', 8))  # Depth
    header.extend(struct.pack('>H', 3))  # Color mode (RGB)
    
    # Color Mode Data Length (4 bytes) - no color mode data
    color_mode_data = struct.pack('>I', 0)
    
    # Image Resources Length (4 bytes) - no image resources
    image_resources = struct.pack('>I', 0)
    
    # Layer and Mask Information
    layer_info = bytearray()
    
    # Layer info section length (we'll update this later)
    layer_info_start = len(layer_info)
    layer_info.extend(struct.pack('>I', 0))  # Placeholder for length
    
    # Layer count (2 layers)
    layer_info.extend(struct.pack('>h', 2))  # Negative for first alpha channel
    
    # Layer 1: "Background"
    # Layer records
    layer_info.extend(struct.pack('>i', 0))    # Top
    layer_info.extend(struct.pack('>i', 0))    # Left  
    layer_info.extend(struct.pack('>i', 100))  # Bottom
    layer_info.extend(struct.pack('>i', 100))  # Right
    layer_info.extend(struct.pack('>H', 3))    # Number of channels
    
    # Channel info
    for i in range(3):  # RGB channels
        layer_info.extend(struct.pack('>h', i))  # Channel ID
        layer_info.extend(struct.pack('>I', 10000))  # Channel data length
    
    # Blend mode signature
    layer_info.extend(b'8BIM')
    layer_info.extend(b'norm')  # Normal blend mode
    layer_info.extend(struct.pack('B', 255))  # Opacity
    layer_info.extend(struct.pack('B', 0))    # Clipping
    layer_info.extend(struct.pack('B', 0))    # Flags
    layer_info.extend(struct.pack('B', 0))    # Filler
    
    # Extra data length
    extra_data_start = len(layer_info)
    layer_info.extend(struct.pack('>I', 0))  # Placeholder
    
    # Layer name (Pascal string)
    layer_name = b'Background'
    layer_info.extend(struct.pack('B', len(layer_name)))
    layer_info.extend(layer_name)
    # Pad to even boundary
    if len(layer_name) % 2 == 0:
        layer_info.extend(b'\x00')
    
    # Update extra data length
    extra_data_length = len(layer_info) - extra_data_start - 4
    struct.pack_into('>I', layer_info, extra_data_start, extra_data_length)
    
    # Layer 2: "Overlay" 
    layer_info.extend(struct.pack('>i', 10))   # Top
    layer_info.extend(struct.pack('>i', 10))   # Left
    layer_info.extend(struct.pack('>i', 90))   # Bottom
    layer_info.extend(struct.pack('>i', 90))   # Right
    layer_info.extend(struct.pack('>H', 3))    # Number of channels
    
    # Channel info  
    for i in range(3):
        layer_info.extend(struct.pack('>h', i))
        layer_info.extend(struct.pack('>I', 6400))  # 80x80 channel data
    
    # Blend mode
    layer_info.extend(b'8BIM')
    layer_info.extend(b'norm')
    layer_info.extend(struct.pack('B', 255))
    layer_info.extend(struct.pack('B', 0))
    layer_info.extend(struct.pack('B', 0))
    layer_info.extend(struct.pack('B', 0))
    
    # Extra data
    extra_data_start = len(layer_info)
    layer_info.extend(struct.pack('>I', 0))
    
    layer_name = b'Overlay'
    layer_info.extend(struct.pack('B', len(layer_name)))
    layer_info.extend(layer_name)
    if len(layer_name) % 2 == 1:
        layer_info.extend(b'\x00')
    
    extra_data_length = len(layer_info) - extra_data_start - 4
    struct.pack_into('>I', layer_info, extra_data_start, extra_data_length)
    
    # Layer channel data (simplified - just zeros for now)
    # This would normally contain the actual pixel data
    channel_data = b'\x00' * 20000  # Simplified channel data
    layer_info.extend(channel_data)
    
    # Update layer info length
    layer_info_length = len(layer_info) - 4
    struct.pack_into('>I', layer_info, layer_info_start, layer_info_length)
    
    # Global layer mask info (empty)
    layer_mask_info = struct.pack('>I', 0)
    
    # Layer and mask info length
    layer_and_mask_length = len(layer_info) + len(layer_mask_info)
    layer_and_mask_header = struct.pack('>I', layer_and_mask_length)
    
    # Image data (compressed)
    # Compression method (0 = raw data)
    image_data = struct.pack('>H', 1)  # RLE compression
    # Add some basic image data (this is very simplified)
    image_data += b'\x00' * 30000  # Placeholder image data
    
    # Write the complete PSD file
    with open(psd_path, 'wb') as f:
        f.write(header)
        f.write(color_mode_data)
        f.write(image_resources)
        f.write(layer_and_mask_header)
        f.write(layer_info)
        f.write(layer_mask_info)
        f.write(image_data)
    
    print(f"Created minimal PSD file: {psd_path}")
    return psd_path

def test_psd_creation():
    """Test if the created PSD can be loaded by psd-tools"""
    try:
        from psd_tools import PSDImage
        
        psd_path = create_minimal_psd()
        
        # Try to load it
        try:
            psd = PSDImage.open(psd_path)
            print(f"Successfully loaded PSD: {psd.width}x{psd.height}")
            print(f"Layers: {len(psd)}")
            for i, layer in enumerate(psd):
                print(f"  Layer {i}: {layer.name if hasattr(layer, 'name') else 'Unnamed'}")
            return True
        except Exception as e:
            print(f"Failed to load created PSD: {e}")
            return False
            
    except ImportError:
        print("psd-tools not available for testing")
        return False

if __name__ == "__main__":
    test_psd_creation()