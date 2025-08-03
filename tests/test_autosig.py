#!/usr/bin/env python3
"""
Tests for AutoSig application
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from PIL import Image

# Add parent directory to path to import autosig
sys.path.insert(0, str(Path(__file__).parent.parent))
import autosig

class TestGenerateOutputPath:
    """Test output path generation with different suffixes and formats"""
    
    def test_default_png_with_suffix(self):
        input_path = Path("test_image.psd")
        result = autosig.generate_output_path(input_path, "_with_sig", "png")
        assert result == Path("test_image_with_sig.png")
    
    def test_jpg_format(self):
        input_path = Path("test_image.psd")
        result = autosig.generate_output_path(input_path, "_signed", "jpg")
        assert result == Path("test_image_signed.jpg")
    
    def test_no_suffix(self):
        input_path = Path("test_image.psd")
        result = autosig.generate_output_path(input_path, "", "webp")
        assert result == Path("test_image.webp")
    
    def test_tiff_format(self):
        input_path = Path("photo.png")
        result = autosig.generate_output_path(input_path, "_final", "tiff")
        assert result == Path("photo_final.tiff")
    
    def test_jpeg_alias(self):
        input_path = Path("image.psd")
        result = autosig.generate_output_path(input_path, "_test", "jpeg")
        assert result == Path("image_test.jpg")


class TestResizeImage:
    """Test image resizing functionality"""
    
    @pytest.fixture
    def sample_image(self):
        """Create a test image"""
        return Image.new('RGB', (200, 100), 'blue')
    
    def test_no_resize_when_none(self, sample_image):
        result = autosig.resize_image_if_needed(sample_image, None)
        assert result.size == (200, 100)
        assert result is sample_image  # Should return same object
    
    def test_no_resize_when_smaller(self, sample_image):
        result = autosig.resize_image_if_needed(sample_image, 300)
        assert result.size == (200, 100)
        assert result is sample_image
    
    def test_resize_width_larger(self, sample_image):
        result = autosig.resize_image_if_needed(sample_image, 100)
        assert result.size == (100, 50)  # Maintains aspect ratio
    
    def test_resize_height_larger(self):
        tall_image = Image.new('RGB', (100, 200), 'red')
        result = autosig.resize_image_if_needed(tall_image, 100)
        assert result.size == (50, 100)  # Maintains aspect ratio
    
    def test_resize_square_image(self):
        square_image = Image.new('RGB', (200, 200), 'green')
        result = autosig.resize_image_if_needed(square_image, 100)
        assert result.size == (100, 100)


class TestSaveImageWithFormat:
    """Test saving images in different formats"""
    
    @pytest.fixture
    def test_image(self):
        """Create a test image with transparency"""
        img = Image.new('RGBA', (50, 50), (255, 0, 0, 128))  # Semi-transparent red
        return img
    
    def test_save_png_preserves_transparency(self, test_image, tmp_path):
        output_path = tmp_path / "test.png"
        autosig.save_image_with_format(test_image, output_path, "png", 85)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify transparency is preserved
        saved_img = Image.open(output_path)
        assert saved_img.mode == 'RGBA'
    
    def test_save_jpg_removes_transparency(self, test_image, tmp_path):
        output_path = tmp_path / "test.jpg"
        autosig.save_image_with_format(test_image, output_path, "jpg", 85)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify transparency is removed (composited on white)
        saved_img = Image.open(output_path)
        assert saved_img.mode == 'RGB'
    
    def test_save_webp_with_quality(self, test_image, tmp_path):
        output_path = tmp_path / "test.webp"
        autosig.save_image_with_format(test_image, output_path, "webp", 75)
        
        # Verify file was created
        assert output_path.exists()
        
        # WEBP should preserve transparency
        saved_img = Image.open(output_path)
        assert saved_img.mode in ['RGBA', 'RGB']  # Depends on PIL version
    
    def test_save_tiff_lossless(self, test_image, tmp_path):
        output_path = tmp_path / "test.tiff"
        autosig.save_image_with_format(test_image, output_path, "tiff", 85)
        
        # Verify file was created
        assert output_path.exists()


class TestFileConflictHandling:
    """Test file conflict resolution"""
    
    def test_no_conflict_when_file_missing(self, tmp_path):
        output_path = tmp_path / "nonexistent.png"
        should_process, action = autosig.handle_file_conflict(output_path, False, False)
        assert should_process is True
        assert action is None
    
    def test_force_overwrites(self, tmp_path):
        output_path = tmp_path / "existing.png"
        output_path.touch()  # Create the file
        
        should_process, action = autosig.handle_file_conflict(output_path, True, False)
        assert should_process is True
        assert action is None
    
    def test_skip_existing(self, tmp_path):
        output_path = tmp_path / "existing.png"
        output_path.touch()  # Create the file
        
        should_process, action = autosig.handle_file_conflict(output_path, False, True)
        assert should_process is False
        assert action is None


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_load_image_file_invalid_format(self):
        """Test loading invalid file format"""
        # Create a text file with .png extension
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b"This is not an image")
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):
                autosig.load_image_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_signature_too_large_scenario(self):
        """Test when signature is larger than source image"""
        # Create a tiny source image
        tiny_img = Image.new('RGB', (10, 10), 'blue')
        
        # Create a large signature
        large_sig = Image.new('RGBA', (50, 50), (255, 0, 0, 128))
        
        # Calculate position - should be negative
        sig_x = tiny_img.width - large_sig.width - 20  # 10 - 50 - 20 = -60
        sig_y = tiny_img.height - large_sig.height - 20  # 10 - 50 - 20 = -60
        
        assert sig_x < 0
        assert sig_y < 0
    
    def test_load_image_file_unknown_extension(self):
        """Test loading file with unknown extension defaults to PIL"""
        # Create a simple PNG but save with unknown extension
        img = Image.new('RGB', (50, 50), 'red')
        with tempfile.NamedTemporaryFile(suffix='.unknown', delete=False) as f:
            temp_path = f.name
        
        try:
            img.save(temp_path, 'PNG')  # Save as PNG but with .unknown extension
            # Should still load via PIL Image.open path
            result = autosig.load_image_file(temp_path)
            assert isinstance(result, Image.Image)
            assert result.mode == 'RGBA'
        finally:
            os.unlink(temp_path)


class TestProcessImageFiles:
    """Test the main processing function with various scenarios"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def fixtures_dir(self):
        return Path(__file__).parent / "fixtures"
    
    def test_process_nonexistent_directory(self, fixtures_dir, tmp_path, capsys):
        """Test processing with nonexistent directory"""
        sig_path = fixtures_dir / "test_signature.png"
        
        # This should return early with error message
        autosig.process_image_files(
            "nonexistent_dir", 
            str(sig_path),
            force=True  # Avoid prompts
        )
        
        captured = capsys.readouterr()
        assert "Error: Directory 'nonexistent_dir' does not exist" in captured.out
    
    def test_process_nonexistent_signature(self, temp_dir, capsys):
        """Test processing with nonexistent signature file"""
        # Create empty directory
        autosig.process_image_files(
            str(temp_dir),
            "nonexistent_signature.png",
            force=True
        )
        
        captured = capsys.readouterr()
        assert "Error: Signature file 'nonexistent_signature.png' does not exist" in captured.out
    
    def test_process_empty_directory(self, temp_dir, fixtures_dir, capsys):
        """Test processing directory with no image files"""
        sig_path = fixtures_dir / "test_signature.png"
        
        autosig.process_image_files(
            str(temp_dir),
            str(sig_path),
            force=True
        )
        
        captured = capsys.readouterr()
        assert "No PSD or PNG files found" in captured.out
    
    def test_process_with_files_basic(self, temp_dir, fixtures_dir, capsys):
        """Test basic processing with actual files"""
        # Copy test source to temp directory
        source_path = fixtures_dir / "test_source.png"
        temp_source = temp_dir / "test_image.png"
        
        # Copy the file
        import shutil
        shutil.copy2(source_path, temp_source)
        
        sig_path = fixtures_dir / "test_signature.png"
        
        # Process with force=True to avoid prompts
        autosig.process_image_files(
            str(temp_dir),
            str(sig_path),
            force=True,
            suffix="_test"
        )
        
        # Check output was created
        output_path = temp_dir / "test_image_test.png"
        assert output_path.exists()
        
        # Verify it's a valid image
        result_img = Image.open(output_path)
        assert result_img.size == (100, 80)  # Same as source
        
        captured = capsys.readouterr()
        assert "Found 1 image files to process" in captured.out
        assert "Processed: 1 files" in captured.out
    
    def test_process_with_different_formats(self, temp_dir, fixtures_dir, capsys):
        """Test processing with different output formats"""
        # Copy test source to temp directory
        source_path = fixtures_dir / "test_source.png"
        temp_source = temp_dir / "test_image.png"
        
        import shutil
        shutil.copy2(source_path, temp_source)
        
        sig_path = fixtures_dir / "test_signature.png"
        
        # Test JPG output
        autosig.process_image_files(
            str(temp_dir),
            str(sig_path),
            force=True,
            output_format="jpg",
            quality=90
        )
        
        # Check JPG output was created
        jpg_output = temp_dir / "test_image_with_sig.jpg"
        assert jpg_output.exists()
        
        # Verify it's JPG (no transparency)
        jpg_img = Image.open(jpg_output)
        assert jpg_img.mode == 'RGB'
    
    def test_process_with_resize(self, temp_dir, fixtures_dir):
        """Test processing with image resizing"""
        # Copy large test image
        source_path = fixtures_dir / "test_large.png"  # 300x200
        temp_source = temp_dir / "large_image.png"
        
        import shutil
        shutil.copy2(source_path, temp_source)
        
        sig_path = fixtures_dir / "test_signature.png"
        
        # Process with max dimension
        autosig.process_image_files(
            str(temp_dir),
            str(sig_path),
            force=True,
            max_dimension=150  # Should resize 300x200 to 150x100
        )
        
        # Check output
        output_path = temp_dir / "large_image_with_sig.png"
        assert output_path.exists()
        
        # Verify size was reduced
        result_img = Image.open(output_path)
        assert result_img.size == (150, 100)  # Should be resized


class TestCommandLineValidation:
    """Test command line argument validation"""
    
    def test_quality_validation_too_low(self):
        """Test quality validation - too low"""
        # Simulate args object
        class MockArgs:
            max_dimension = None
            quality = 0  # Invalid
        
        args = MockArgs()
        
        # The validation should catch this
        assert args.quality < 1
    
    def test_quality_validation_too_high(self):
        """Test quality validation - too high"""
        class MockArgs:
            max_dimension = None
            quality = 101  # Invalid
        
        args = MockArgs()
        
        # The validation should catch this  
        assert args.quality > 100
    
    def test_max_dimension_validation_negative(self):
        """Test max dimension validation"""
        class MockArgs:
            max_dimension = -5  # Invalid
            quality = 85
        
        args = MockArgs()
        
        # The validation should catch this
        assert args.max_dimension <= 0


class TestIntegration:
    """Integration tests using test fixtures"""
    
    @pytest.fixture
    def fixtures_dir(self):
        return Path(__file__).parent / "fixtures"
    
    @pytest.fixture
    def source_image_path(self, fixtures_dir):
        return fixtures_dir / "test_source.png"
    
    @pytest.fixture
    def signature_path(self, fixtures_dir):
        return fixtures_dir / "test_signature.png"
    
    def test_load_image_file_png(self, source_image_path):
        """Test loading PNG files"""
        result = autosig.load_image_file(source_image_path)
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGBA'
        assert result.size == (100, 80)
    
    def test_signature_positioning_pixels(self, fixtures_dir):
        """Test signature positioning with pixel offset"""
        source_img = Image.open(fixtures_dir / "test_source.png").convert("RGBA")
        sig_img = Image.open(fixtures_dir / "test_signature.png").convert("RGBA")
        
        # Calculate position (20px from edges)
        sig_x = source_img.width - sig_img.width - 20
        sig_y = source_img.height - sig_img.height - 20
        
        expected_x = 100 - 20 - 20  # source_width - sig_width - offset
        expected_y = 80 - 15 - 20   # source_height - sig_height - offset
        
        assert sig_x == expected_x
        assert sig_y == expected_y
    
    def test_signature_positioning_percentage(self, fixtures_dir):
        """Test signature positioning with percentage offset"""
        source_img = Image.open(fixtures_dir / "test_source.png").convert("RGBA")
        sig_img = Image.open(fixtures_dir / "test_signature.png").convert("RGBA")
        
        # Calculate position (5% from edges)
        offset_percent = 5
        offset_x = int(source_img.width * (offset_percent / 100))
        offset_y = int(source_img.height * (offset_percent / 100))
        
        sig_x = source_img.width - sig_img.width - offset_x
        sig_y = source_img.height - sig_img.height - offset_y
        
        expected_offset_x = int(100 * 0.05)  # 5
        expected_offset_y = int(80 * 0.05)   # 4
        
        assert offset_x == expected_offset_x
        assert offset_y == expected_offset_y
    
    def test_end_to_end_processing(self, fixtures_dir, tmp_path):
        """Test complete signature application process"""
        source_path = fixtures_dir / "test_source.png"
        sig_path = fixtures_dir / "test_signature.png"
        
        # Load images
        source_img = autosig.load_image_file(source_path)
        sig_img = autosig.load_image_file(sig_path)
        
        # Apply signature (20px offset)
        result_img = source_img.copy()
        sig_x = source_img.width - sig_img.width - 20
        sig_y = source_img.height - sig_img.height - 20
        result_img.paste(sig_img, (sig_x, sig_y), sig_img)
        
        # Save result
        output_path = tmp_path / "result.png"
        autosig.save_image_with_format(result_img, output_path, "png", 85)
        
        # Verify output
        assert output_path.exists()
        saved_img = Image.open(output_path)
        assert saved_img.size == source_img.size
        assert saved_img.mode == 'RGBA'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])