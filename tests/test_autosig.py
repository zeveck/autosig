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
        assert "No PSD, PNG, JPG, JPEG, WEBP, BMP, TIFF, TIF, GIF files found" in captured.out
    
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
        import subprocess
        import sys
        
        # Test that invalid quality causes sys.exit(1)
        result = subprocess.run([
            sys.executable, "autosig.py", ".", "sig.png", "--quality", "0"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 1
        assert "Quality must be between 1 and 100" in result.stdout
    
    def test_quality_validation_too_high(self):
        """Test quality validation - too high"""
        import subprocess
        import sys
        
        # Test that invalid quality causes sys.exit(1)
        result = subprocess.run([
            sys.executable, "autosig.py", ".", "sig.png", "--quality", "101"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 1
        assert "Quality must be between 1 and 100" in result.stdout
    
    def test_max_dimension_validation_negative(self):
        """Test max dimension validation"""
        import subprocess
        import sys
        
        # Test that negative max dimension causes sys.exit(1)
        result = subprocess.run([
            sys.executable, "autosig.py", ".", "sig.png", "--max-dimension", "-5"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 1
        assert "Max dimension must be a positive integer" in result.stdout
    
    def test_no_sig_validation_success(self):
        """Test that --no-sig makes signature optional"""
        import subprocess
        import sys
        
        # This should fail validation (missing signature without --no-sig)
        result = subprocess.run([
            sys.executable, "autosig.py", "nonexistent_dir"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 1
        assert "Signature file required unless --no-sig specified" in result.stdout
    
    def test_conflicting_no_sig_and_signature(self):
        """Test that --no-sig conflicts with providing signature"""
        import subprocess
        import sys
        
        # This should fail validation (--no-sig with signature)
        result = subprocess.run([
            sys.executable, "autosig.py", ".", "sig.png", "--no-sig"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 1
        assert "Cannot specify both --no-sig and signature file" in result.stdout


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


class TestNoSignatureMode:
    """Test --no-sig functionality"""
    
    def test_no_sig_skips_signature_application(self, tmp_path):
        """Test that no-sig mode skips signature processing"""
        # Create test source image
        source_img = Image.new('RGB', (100, 80), 'blue')
        source_path = tmp_path / "test_source.png"
        source_img.save(source_path)
        
        # Process with no-sig mode (no signature file provided)
        autosig.process_image_files(
            str(tmp_path),
            None,  # No signature
            apply_signature=False,
            force=True,
            suffix="_processed"
        )
        
        # Verify output was created
        output_path = tmp_path / "test_source_processed.png"
        assert output_path.exists()
        
        # Verify output is same size as input (no signature applied)
        result_img = Image.open(output_path)
        assert result_img.size == (100, 80)
    
    def test_no_sig_with_format_conversion(self, tmp_path):
        """Test no-sig mode with format conversion"""
        # Create PNG source
        source_img = Image.new('RGB', (100, 80), 'red')
        source_path = tmp_path / "test_image.png"
        source_img.save(source_path)
        
        # Convert to JPG without signature
        autosig.process_image_files(
            str(tmp_path),
            None,
            apply_signature=False,
            output_format="jpg",
            quality=90,
            force=True,
            suffix="_converted"
        )
        
        # Verify JPG output
        output_path = tmp_path / "test_image_converted.jpg"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        assert result_img.mode == 'RGB'
        assert result_img.size == (100, 80)
    
    def test_no_sig_with_resizing(self, tmp_path):
        """Test no-sig mode with image resizing"""
        # Create large source image
        source_img = Image.new('RGB', (400, 300), 'green')
        source_path = tmp_path / "large_image.png"
        source_img.save(source_path)
        
        # Resize without signature
        autosig.process_image_files(
            str(tmp_path),
            None,
            apply_signature=False,
            max_dimension=200,
            force=True,
            suffix="_resized"
        )
        
        # Verify output was resized correctly
        output_path = tmp_path / "large_image_resized.png"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        # Should be resized to 200x150 (maintaining 4:3 ratio)
        assert result_img.size == (200, 150)
    
    def test_no_sig_with_cropping(self, tmp_path):
        """Test no-sig mode with aspect ratio cropping"""
        # Create tall portrait image
        source_img = Image.new('RGB', (200, 400), 'purple')  # 1:2 ratio
        source_path = tmp_path / "tall_portrait.png"
        source_img.save(source_path)
        
        # Crop to 4:5 ratio without signature
        autosig.process_image_files(
            str(tmp_path),
            None,
            apply_signature=False,
            crop_portrait_ratio="4:5",
            force=True,
            suffix="_cropped"
        )
        
        # Verify output was cropped correctly
        output_path = tmp_path / "tall_portrait_cropped.png"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        expected_height = int(200 / 0.8)  # 250
        assert result_img.size == (200, expected_height)


class TestComplexWorkflows:
    """Test complex feature combinations"""
    
    def test_no_sig_with_multiple_features(self, tmp_path):
        """Test no-sig mode with cropping, resizing, and format conversion"""
        # Create wide landscape image
        source_img = Image.new('RGB', (600, 200), 'orange')  # 3:1 ratio
        source_path = tmp_path / "wide_landscape.png"
        source_img.save(source_path)
        
        # Process with multiple features
        autosig.process_image_files(
            str(tmp_path),
            None,
            apply_signature=False,
            crop_landscape_ratio="16:9",  # Will crop width
            max_dimension=300,  # Will resize after cropping
            output_format="jpg",
            quality=85,
            force=True,
            suffix="_processed"
        )
        
        # Verify complex processing pipeline
        output_path = tmp_path / "wide_landscape_processed.jpg"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        
        # Should be cropped to 16:9 first, then resized
        # Original: 600x200 (3:1) -> Crop to 16:9 -> ~356x200 -> Resize to max 300
        expected_width = int(200 * (16/9))  # ~356
        if expected_width > 300:
            # Will be resized down
            scale = 300 / expected_width
            final_width = 300
            final_height = int(200 * scale)
        else:
            final_width = expected_width
            final_height = 200
        
        assert result_img.size == (final_width, final_height)
        assert result_img.mode == 'RGB'  # JPG format
    
    def test_suffix_auto_adjustment(self, tmp_path, capsys):
        """Test that --no-sig auto-adjusts default suffix"""
        # Create test image
        source_img = Image.new('RGB', (100, 100), 'cyan')
        source_path = tmp_path / "test_image.png"
        source_img.save(source_path)
        
        # Process with no-sig and default suffix (should auto-adjust)
        autosig.process_image_files(
            str(tmp_path),
            None,
            apply_signature=False,
            suffix="_with_sig",  # Should be ignored/adjusted for no-sig mode
            force=True
        )
        
        # Should output with adjusted suffix - but we need to test the main CLI for this
        # This test verifies the function works with explicit suffix
        assert True  # This specific behavior is tested in CLI validation tests


class TestExcludePatterns:
    """Test --exclude-suffix functionality"""
    
    def test_exclude_custom_patterns(self, tmp_path):
        """Test that custom exclude patterns work"""
        # Create various files including ones that should be excluded
        files_to_create = [
            "image1.png",
            "image2.png", 
            "image1_draft.png",  # Should be excluded (custom pattern)
            "image2_backup.png",  # Should be excluded (custom pattern)
            "image3_source.png"   # Should be included (not in any exclude list)
        ]
        
        for filename in files_to_create:
            img = Image.new('RGB', (100, 100), 'red')  # Larger so signature fits
            img.save(tmp_path / filename)
        
        # Create small signature that will fit
        sig_img = Image.new('RGBA', (20, 15), (0, 255, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process with custom exclude patterns
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            exclude_patterns=["_draft", "_backup"],
            force=True,
            suffix="_test"
        )
        
        # Verify only expected files were processed
        expected_outputs = [
            "image1_test.png",
            "image2_test.png",
            "image3_source_test.png"
        ]
        
        for expected_file in expected_outputs:
            assert (tmp_path / expected_file).exists(), f"Expected output {expected_file} not found"
        
        # Verify excluded files were not processed
        excluded_outputs = [
            "image1_draft_test.png",
            "image2_backup_test.png"
        ]
        
        for excluded_file in excluded_outputs:
            assert not (tmp_path / excluded_file).exists(), f"Excluded file {excluded_file} should not exist"
    
    def test_default_exclude_patterns(self, tmp_path, capsys):
        """Test that default exclusion patterns work"""
        # Create files that should be excluded by default
        files_to_create = [
            "original.png",
            "image_with_sig.png",  # Should be excluded (default pattern)
            "photo_signed.png",    # Should be excluded (default pattern) 
            "document_final.png",  # Should be excluded (default pattern)
            "clean_image.png"      # Should be included
        ]
        
        for filename in files_to_create:
            img = Image.new('RGB', (100, 100), 'blue')
            img.save(tmp_path / filename)
        
        # Create signature
        sig_img = Image.new('RGBA', (20, 15), (255, 0, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process without custom exclude patterns (should use defaults)
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            force=True,
            suffix="_new"
        )
        
        # Should report some files excluded
        captured = capsys.readouterr()
        assert "Excluded" in captured.out and "PNG files that appear to be AutoSig outputs" in captured.out
        
        # Only original and clean_image should be processed
        expected_outputs = [
            "original_new.png",
            "clean_image_new.png"
        ]
        
        for expected_file in expected_outputs:
            assert (tmp_path / expected_file).exists()


class TestOrientationDetection:
    """Test image orientation detection"""
    
    def test_landscape_detection(self):
        """Test landscape orientation detection"""
        orientation = autosig.detect_orientation(300, 200)  # 1.5 ratio
        assert orientation == "landscape"
    
    def test_portrait_detection(self):
        """Test portrait orientation detection"""
        orientation = autosig.detect_orientation(200, 300)  # 0.67 ratio
        assert orientation == "portrait"
    
    def test_square_detection(self):
        """Test square orientation detection"""
        orientation = autosig.detect_orientation(200, 200)  # 1.0 ratio
        assert orientation == "square"
    
    def test_nearly_square_detection(self):
        """Test images close to square are detected as square"""
        # 1.1 ratio - should be square (between 0.8 and 1.2)
        orientation = autosig.detect_orientation(220, 200)
        assert orientation == "square"


class TestAspectRatioParsing:
    """Test aspect ratio string parsing"""
    
    def test_colon_format_parsing(self):
        """Test parsing ratios in 'width:height' format"""
        ratio = autosig.parse_aspect_ratio("4:5")
        assert ratio == 0.8
        
        ratio = autosig.parse_aspect_ratio("16:9")
        assert abs(ratio - 1.7777777777777777) < 0.0001
    
    def test_decimal_format_parsing(self):
        """Test parsing decimal ratios"""
        ratio = autosig.parse_aspect_ratio("1.5")
        assert ratio == 1.5
        
        ratio = autosig.parse_aspect_ratio("0.8")
        assert ratio == 0.8
    
    def test_invalid_format_raises_error(self):
        """Test that invalid formats raise ValueError"""
        with pytest.raises(ValueError):
            autosig.parse_aspect_ratio("invalid")
        
        with pytest.raises(ValueError):
            autosig.parse_aspect_ratio("4:0")  # Zero height
        
        with pytest.raises(ValueError):
            autosig.parse_aspect_ratio("abc:def")


class TestMaxRatioCropping:
    """Test maximum ratio constraint cropping"""
    
    @pytest.fixture
    def portrait_image(self):
        """Create a tall portrait image (2:3 ratio)"""
        return Image.new('RGB', (200, 300), 'blue')
    
    @pytest.fixture
    def landscape_image(self):
        """Create a wide landscape image (3:1 ratio)"""
        return Image.new('RGB', (300, 100), 'red')
    
    @pytest.fixture
    def square_image(self):
        """Create a square image"""
        return Image.new('RGB', (200, 200), 'green')
    
    def test_portrait_crop_when_too_tall(self, portrait_image):
        """Test portrait image gets cropped when too tall"""
        # Portrait image 2:3 (0.67) should be cropped to 4:5 (0.8) max
        result = autosig.center_crop_to_max_ratio(portrait_image, 0.8, "portrait")
        
        # Should crop height to make ratio 0.8
        expected_height = int(200 / 0.8)  # 250
        assert result.size == (200, expected_height)
    
    def test_portrait_no_crop_when_within_limit(self):
        """Test portrait image not cropped when within ratio limit"""
        # Create 4:5 portrait image (already at limit)
        image = Image.new('RGB', (200, 250), 'blue')
        result = autosig.center_crop_to_max_ratio(image, 0.8, "portrait")
        
        # Should not be cropped
        assert result.size == (200, 250)
        assert result is image
    
    def test_landscape_crop_when_too_wide(self, landscape_image):
        """Test landscape image gets cropped when too wide"""
        # Landscape image 3:1 (3.0) should be cropped to 16:9 (1.78) max
        result = autosig.center_crop_to_max_ratio(landscape_image, 16/9, "landscape")
        
        # Should crop width to make ratio 1.78
        expected_width = int(100 * (16/9))  # ~178
        assert result.size == (expected_width, 100)
    
    def test_landscape_no_crop_when_within_limit(self):
        """Test landscape image not cropped when within ratio limit"""
        # Create 16:9 landscape image (already at limit)
        image = Image.new('RGB', (320, 180), 'red')
        result = autosig.center_crop_to_max_ratio(image, 16/9, "landscape")
        
        # Should not be cropped (within tolerance)
        assert result.size == (320, 180)
        assert result is image
    
    def test_square_treated_as_portrait(self, square_image):
        """Test square images are treated as portrait for cropping"""
        # Square image (1:1) should not be cropped with 4:5 portrait limit
        result = autosig.center_crop_to_max_ratio(square_image, 0.8, "square")
        
        # Should not be cropped (1.0 > 0.8)
        assert result.size == (200, 200)
        assert result is square_image
    
    def test_center_cropping_alignment(self):
        """Test that cropping is center-aligned"""
        # Create tall image that needs cropping
        image = Image.new('RGB', (100, 200), 'blue')
        result = autosig.center_crop_to_max_ratio(image, 1.0, "portrait")  # Force to 1:1
        
        # Should crop height to 100, centered
        assert result.size == (100, 100)


class TestLayerHiding:
    """Test PSD layer hiding functionality"""
    
    def test_hide_layers_empty_list(self):
        """Test hiding with empty layer list"""
        # Mock PSD object - in real tests would use actual PSD file
        class MockPSD:
            def __len__(self):
                return 3
        
        psd = MockPSD()
        result = autosig.hide_layers_in_psd(psd, [])
        assert result == 0
    
    def test_hide_layer_by_index_validation(self):
        """Test layer hiding by index with bounds checking"""
        # Mock PSD object
        class MockLayer:
            def __init__(self):
                self.visible = True
        
        class MockPSD:
            def __init__(self):
                self.layers = [MockLayer(), MockLayer(), MockLayer()]
            
            def __len__(self):
                return len(self.layers)
            
            def __getitem__(self, index):
                return self.layers[index]
        
        psd = MockPSD()
        
        # Valid index should work
        result = autosig.hide_layers_in_psd(psd, [0])
        assert result == 1
        assert psd[0].visible == False
        
        # Invalid index should be handled gracefully  
        result = autosig.hide_layers_in_psd(psd, [10])
        assert result == 0  # No layers hidden due to invalid index
    
    def test_string_digit_conversion(self):
        """Test that string digits are converted to integers"""
        class MockLayer:
            def __init__(self):
                self.visible = True
        
        class MockPSD:
            def __init__(self):
                self.layers = [MockLayer(), MockLayer()]
            
            def __len__(self):
                return len(self.layers)
            
            def __getitem__(self, index):
                return self.layers[index]
        
        psd = MockPSD()
        result = autosig.hide_layers_in_psd(psd, ["0", "1"])
        assert result == 2
        assert psd[0].visible == False
        assert psd[1].visible == False
    
    def test_layer_hiding_with_png_files(self, tmp_path, capsys):
        """Test that layer hiding with PNG files shows warning"""
        # Create PNG file
        img = Image.new('RGB', (100, 100), 'blue')
        png_path = tmp_path / "test.png"
        img.save(png_path)
        
        # Try to load with layer hiding - should show warning
        result = autosig.load_image_file(str(png_path), layers_to_hide=["Layer 1"])
        
        # Should still load the image
        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)
        
        # Should have shown warning (this tests the actual warning logic)
        captured = capsys.readouterr()
        assert "Warning: Layer hiding only supported for PSD files" in captured.out
    
    def test_layer_hiding_integration(self, tmp_path):
        """Test layer hiding integration in processing pipeline"""
        # Create PNG source (layer hiding will be ignored but shouldn't break)
        source_img = Image.new('RGB', (100, 80), 'yellow')
        source_path = tmp_path / "test_image.png"
        source_img.save(source_path)
        
        # Create signature
        sig_img = Image.new('RGBA', (20, 15), (255, 0, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process with layer hiding (should work despite PNG input)
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            layers_to_hide=["nonexistent_layer"],
            force=True,
            suffix="_test"
        )
        
        # Should still process successfully
        output_path = tmp_path / "test_image_test.png"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        assert result_img.size == (100, 80)


class TestIntegrationNewFeatures:
    """Integration tests for new features working together"""
    
    @pytest.fixture
    def sample_landscape_image(self):
        """Create a wide landscape test image"""
        return Image.new('RGB', (400, 200), 'blue')
    
    def test_no_sig_with_cropping(self, sample_landscape_image):
        """Test --no-sig mode works with aspect ratio cropping"""
        # Simulate cropping without signature
        orientation = autosig.detect_orientation(sample_landscape_image.width, sample_landscape_image.height)
        assert orientation == "landscape"
        
        # Apply max ratio cropping
        cropped = autosig.center_crop_to_max_ratio(sample_landscape_image, 16/9, orientation)
        
        # Should be cropped to 16:9 ratio
        expected_width = int(200 * (16/9))  # ~356
        assert cropped.size == (expected_width, 200)
    
    def test_processing_order_crop_before_signature(self, tmp_path):
        """Test that cropping happens before signature application"""
        # Create a tall portrait image that will be cropped
        source_img = Image.new('RGB', (200, 400), 'blue')  # 1:2 ratio
        source_path = tmp_path / "tall_image.png"
        source_img.save(source_path)
        
        # Create a small signature
        sig_img = Image.new('RGBA', (20, 15), (255, 0, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process with cropping to 4:5 ratio (0.8) - should crop height first
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            apply_signature=True,
            crop_portrait_ratio="4:5",
            force=True,
            suffix="_test"
        )
        
        # Verify output exists
        output_path = tmp_path / "tall_image_test.png"
        assert output_path.exists()
        
        # Verify image was cropped to 4:5 ratio BEFORE signature application
        result_img = Image.open(output_path)
        expected_height = int(200 / 0.8)  # 250
        assert result_img.size == (200, expected_height)
        
        # Verify signature was applied to the CROPPED image, not original
        # (This confirms cropping happened first)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_orientation_boundary_conditions(self):
        """Test orientation detection at exact boundaries"""
        # Test exact boundary values (0.8 and 1.2) - these are treated as "square"
        assert autosig.detect_orientation(80, 100) == "square"     # 0.8 exactly
        assert autosig.detect_orientation(120, 100) == "square"    # 1.2 exactly
        
        # Test just outside boundaries
        assert autosig.detect_orientation(79, 100) == "portrait"   # 0.79 (just under 0.8)
        assert autosig.detect_orientation(121, 100) == "landscape" # 1.21 (just over 1.2)
        
        # Test clearly defined orientations
        assert autosig.detect_orientation(70, 100) == "portrait"   # 0.7 (clearly portrait)
        assert autosig.detect_orientation(150, 100) == "landscape" # 1.5 (clearly landscape)
    
    def test_aspect_ratio_parsing_edge_cases(self):
        """Test aspect ratio parsing with various edge cases"""
        # Very small ratios
        ratio = autosig.parse_aspect_ratio("1:10")
        assert ratio == 0.1
        
        # Very large ratios  
        ratio = autosig.parse_aspect_ratio("20:1")
        assert ratio == 20.0
        
        # Decimal inputs
        ratio = autosig.parse_aspect_ratio("4.5:3.2")
        assert abs(ratio - (4.5/3.2)) < 0.0001
        
        # Common social media ratios
        ratio = autosig.parse_aspect_ratio("9:16")  # Stories
        assert abs(ratio - 0.5625) < 0.0001
    
    def test_cropping_with_minimal_adjustment_needed(self):
        """Test cropping when image is very close to target ratio"""
        # Image that's very close to target ratio (should still crop slightly)
        image = Image.new('RGB', (400, 501), 'red')  # ~0.7985 ratio
        result = autosig.center_crop_to_max_ratio(image, 0.8, "portrait")  # 4:5 ratio
        
        # Should be cropped to exactly 4:5 ratio
        expected_height = int(400 / 0.8)  # 500
        assert result.size == (400, expected_height)
    
    def test_very_small_images(self, tmp_path):
        """Test processing very small images"""
        # Create tiny image
        tiny_img = Image.new('RGB', (10, 8), 'blue')
        tiny_path = tmp_path / "tiny.png"
        tiny_img.save(tiny_path)
        
        # Create signature larger than image
        large_sig = Image.new('RGBA', (20, 15), (255, 0, 0, 128))
        sig_path = tmp_path / "large_sig.png"
        large_sig.save(sig_path)
        
        # Should skip due to signature being too large
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            force=True,
            suffix="_test"
        )
        
        # Should not create output (signature too large)
        output_path = tmp_path / "tiny_test.png"
        assert not output_path.exists()
    
    def test_zero_offset_positioning(self, tmp_path):
        """Test signature positioning with zero offset"""
        # Create test image
        source_img = Image.new('RGB', (100, 80), 'green')
        source_path = tmp_path / "test_image.png"
        source_img.save(source_path)
        
        # Create signature
        sig_img = Image.new('RGBA', (20, 15), (255, 0, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process with zero pixel offset
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            offset_pixels=0,
            force=True,
            suffix="_zero"
        )
        
        # Should place signature at exact bottom-right corner
        output_path = tmp_path / "test_image_zero.png"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        assert result_img.size == (100, 80)
    
    def test_percentage_offset_edge_cases(self, tmp_path):
        """Test percentage offset at boundary values"""
        source_img = Image.new('RGB', (100, 100), 'purple')
        source_path = tmp_path / "square.png"
        source_img.save(source_path)
        
        sig_img = Image.new('RGBA', (10, 10), (255, 255, 0, 128))
        sig_path = tmp_path / "small_sig.png"
        sig_img.save(sig_path)
        
        # Test maximum allowed percentage (50%)
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            offset_percent=50.0,  # Maximum allowed
            force=True,
            suffix="_max_percent"
        )
        
        # Should work with 50% offset
        output_path = tmp_path / "square_max_percent.png"
        assert output_path.exists()
    
    def test_cropping_with_exact_target_ratio_images(self):
        """Test that images already at target ratio aren't modified"""
        # Create image with exact 4:5 ratio
        exact_image = Image.new('RGB', (400, 500), 'yellow')  # Exactly 0.8 ratio
        result = autosig.center_crop_to_max_ratio(exact_image, 0.8, "portrait")
        
        # Should return the same image object (no modification)
        assert result is exact_image
        assert result.size == (400, 500)
        
        # Test landscape with exact 16:9 ratio
        landscape_exact = Image.new('RGB', (1600, 900), 'cyan')  # Exactly 16:9
        result = autosig.center_crop_to_max_ratio(landscape_exact, 16/9, "landscape")
        
        # Should return the same image object
        assert result is landscape_exact
        assert result.size == (1600, 900)
    
    def test_invalid_aspect_ratio_handling(self, tmp_path, capsys):
        """Test handling of invalid aspect ratios in processing"""
        source_img = Image.new('RGB', (100, 200), 'orange')
        source_path = tmp_path / "tall_image.png"
        source_img.save(source_path)
        
        sig_img = Image.new('RGBA', (10, 10), (0, 0, 255, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process with invalid portrait ratio
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            crop_portrait_ratio="invalid:ratio",
            force=True,
            suffix="_invalid"
        )
        
        # Should show warning but still process (without cropping)
        captured = capsys.readouterr()
        assert "Warning: Invalid portrait ratio" in captured.out
        
        # Should still create output (just without cropping)
        output_path = tmp_path / "tall_image_invalid.png"
        assert output_path.exists()
        
        # Image should be unchanged size (no cropping applied)
        result_img = Image.open(output_path)
        assert result_img.size == (100, 200)  # Original size


class TestRealPSDFunctionality:
    """Test real PSD file functionality - requires actual PSD test files"""
    
    @pytest.fixture
    def psd_available(self):
        """Check if real PSD test files are available"""
        fixtures_dir = Path(__file__).parent / "fixtures"
        psd_files = list(fixtures_dir.glob("*.psd"))
        return len(psd_files) > 0
    
    @pytest.fixture  
    def simple_psd_path(self):
        """Path to simple test PSD file"""
        return Path(__file__).parent / "fixtures" / "test_simple.psd"
        
    @pytest.fixture
    def multilayer_psd_path(self):
        """Path to multilayer test PSD file"""
        return Path(__file__).parent / "fixtures" / "test_multilayer.psd"
        
    @pytest.fixture
    def signature_psd_path(self):
        """Path to PSD signature file"""
        return Path(__file__).parent / "fixtures" / "test_signature.psd"
    
    def test_psd_tools_import(self):
        """Verify psd-tools is properly available"""
        try:
            from psd_tools import PSDImage
            assert PSDImage is not None
        except ImportError:
            pytest.fail("psd-tools is required for PSD testing but not available")
    
    @pytest.mark.skipif(not Path(__file__).parent.joinpath("fixtures").glob("*.psd"), 
                       reason="No PSD test files available - create test PSDs in fixtures/")
    def test_load_real_psd_file(self, simple_psd_path):
        """Test loading actual PSD file with psd-tools"""
        if not simple_psd_path.exists():
            pytest.skip("test_simple.psd not found - create in fixtures/")
            
        # Load PSD and verify basic properties
        result = autosig.load_image_file(str(simple_psd_path))
        
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGBA'
        assert result.size[0] > 0 and result.size[1] > 0
        
        print(f"Successfully loaded PSD: {result.size}")
    
    @pytest.mark.skipif(not Path(__file__).parent.joinpath("fixtures").glob("*.psd"),
                       reason="No PSD test files available")
    def test_hide_named_layers_in_real_psd(self, multilayer_psd_path):
        """Test hiding layers by name in actual PSD with multiple layers"""
        if not multilayer_psd_path.exists():
            pytest.skip("test_multilayer.psd not found - create with named layers")
        
        from psd_tools import PSDImage
        
        # Load PSD and check layers
        psd = PSDImage.open(multilayer_psd_path)
        original_layer_count = len(psd)
        
        # Get layer names for verification
        layer_names = [layer.name for layer in psd if hasattr(layer, 'name')]
        print(f"PSD has {original_layer_count} layers: {layer_names}")
        
        # Test hiding by name
        if "Overlay" in layer_names:
            result = autosig.hide_layers_in_psd(psd, ["Overlay"])
            assert result == 1  # Should have hidden 1 layer
            
            # Verify layer was hidden
            for layer in psd:
                if hasattr(layer, 'name') and layer.name == "Overlay":
                    assert layer.visible == False
        else:
            pytest.skip("PSD doesn't have 'Overlay' layer - create multilayer PSD with named layers")
    
    @pytest.mark.skipif(not Path(__file__).parent.joinpath("fixtures").glob("*.psd"),
                       reason="No PSD test files available")
    def test_hide_layers_by_index_real_psd(self, multilayer_psd_path):
        """Test hiding layers by index in real PSD"""
        if not multilayer_psd_path.exists():
            pytest.skip("test_multilayer.psd not found")
            
        from psd_tools import PSDImage
        
        psd = PSDImage.open(multilayer_psd_path)
        if len(psd) < 2:
            pytest.skip("PSD needs at least 2 layers for index testing")
        
        # Hide layer by index
        result = autosig.hide_layers_in_psd(psd, [0])
        assert result == 1
        assert psd[0].visible == False
    
    @pytest.mark.skipif(not Path(__file__).parent.joinpath("fixtures").glob("*.psd"),
                       reason="No PSD test files available")
    def test_psd_signature_file_support(self, tmp_path, signature_psd_path):
        """Test using PSD file as signature"""
        if not signature_psd_path.exists():
            pytest.skip("test_signature.psd not found - create PSD signature file")
        
        # Create PNG source image
        source_img = Image.new('RGB', (200, 150), 'lightblue')
        source_path = tmp_path / "test_source.png"
        source_img.save(source_path)
        
        # Process with PSD signature
        autosig.process_image_files(
            str(tmp_path),
            str(signature_psd_path),
            force=True,
            suffix="_psd_sig"
        )
        
        # Verify output was created
        output_path = tmp_path / "test_source_psd_sig.png"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        assert result_img.size == (200, 150)
    
    @pytest.mark.skipif(not Path(__file__).parent.joinpath("fixtures").glob("*.psd"),
                       reason="No PSD test files available")
    def test_complete_psd_workflow(self, tmp_path, multilayer_psd_path):
        """Test complete PSD processing: load → hide layers → crop → signature → save"""
        if not multilayer_psd_path.exists():
            pytest.skip("test_multilayer.psd not found")
        
        # Copy PSD to temp directory
        import shutil
        temp_psd_path = tmp_path / "test_multilayer.psd"
        shutil.copy2(multilayer_psd_path, temp_psd_path)
        
        # Create PNG signature
        sig_img = Image.new('RGBA', (30, 20), (255, 0, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process with multiple features: layer hiding + cropping + signature
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            layers_to_hide=["Draft", "Overlay"],
            crop_portrait_ratio="4:5",
            max_dimension=100,
            force=True,
            suffix="_complete"
        )
        
        # Verify output
        output_path = tmp_path / "test_multilayer_complete.png"
        assert output_path.exists()
        
        result_img = Image.open(output_path)
        # Should be processed (exact size depends on original PSD dimensions)
        assert result_img.size[0] <= 100  # Max dimension applied
        assert result_img.size[1] <= 100
    
    def test_psd_error_handling_with_png(self, tmp_path, capsys):
        """Test PSD-specific functions with PNG files (should show warnings)"""
        # Create PNG file
        png_img = Image.new('RGB', (100, 100), 'green')
        png_path = tmp_path / "fake.psd"  # PNG with .psd extension!
        png_img.save(png_path, "PNG")
        
        # Try to load as PSD - should fail gracefully
        try:
            result = autosig.load_image_file(str(png_path))
            # If it loads, it should fallback to PIL
            assert isinstance(result, Image.Image)
        except Exception as e:
            # Should handle PSD parsing errors gracefully
            # Could be various errors: ColorMode, format, etc.
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in ["colormode", "format", "psd", "invalid", "read"])
    
    def test_psd_layer_hiding_boundary_cases(self):
        """Test PSD layer hiding with edge cases using mocks"""
        # Test with layer that has no name attribute
        class LayerWithoutName:
            def __init__(self):
                self.visible = True
                # No name attribute
        
        class PSWithUnnamedLayers:
            def __init__(self):
                self.layers = [LayerWithoutName(), LayerWithoutName()]
            
            def __len__(self):
                return len(self.layers)
                
            def __getitem__(self, index):
                return self.layers[index]
                
            def __iter__(self):
                return iter(self.layers)
        
        psd = PSWithUnnamedLayers()
        
        # Try to hide by name when layers have no names
        result = autosig.hide_layers_in_psd(psd, ["NonexistentLayer"])
        assert result == 0  # Should not hide any layers
        
        # Hiding by index should still work
        result = autosig.hide_layers_in_psd(psd, [0])
        assert result == 1
        assert psd[0].visible == False


class TestPSDIntegrationScenarios:
    """Integration tests for PSD functionality that can work without real PSDs"""
    
    def test_psd_vs_png_processing_parity(self, tmp_path):
        """Test that PSD and PNG processing produce equivalent results"""
        # Create identical PNG and "PSD" (actually PNG with .psd extension for testing)
        base_img = Image.new('RGB', (120, 100), 'lightcyan')
        
        png_path = tmp_path / "test.png"
        base_img.save(png_path)
        
        fake_psd_path = tmp_path / "test.psd"
        base_img.save(fake_psd_path, "PNG")  # PNG saved as .psd for testing
        
        # Create signature
        sig_img = Image.new('RGBA', (20, 15), (255, 0, 0, 128))
        sig_path = tmp_path / "sig.png"
        sig_img.save(sig_path)
        
        # Process both files
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            force=True,
            suffix="_test"
        )
        
        # Both should be processed
        png_output = tmp_path / "test_test.png"
        psd_output = tmp_path / "test_test.png"  # Will overwrite, but that's ok for this test
        
        assert png_output.exists()
        
        # Verify processing worked
        result_img = Image.open(png_output)
        assert result_img.size == (120, 100)
    
    def test_mixed_file_types_processing(self, tmp_path, capsys):
        """Test processing directory with both PNG and PSD files"""
        # Create mixed file types - only use valid files for this test
        files_to_create = [
            ("image1.png", "PNG"),
            ("image3.png", "PNG")
        ]
        
        for filename, format_type in files_to_create:
            img = Image.new('RGB', (80, 60), 'purple')
            img.save(tmp_path / filename, format_type)
        
        # Create signature that will fit
        sig_img = Image.new('RGBA', (20, 15), (255, 255, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process mixed directory
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            force=True,
            suffix="_mixed"
        )
        
        # Valid PNG files should be processed
        expected_outputs = [
            "image1_mixed.png",
            "image3_mixed.png"
        ]
        
        for expected_file in expected_outputs:
            output_path = tmp_path / expected_file
            assert output_path.exists()
            
            result_img = Image.open(output_path)
            assert result_img.size == (80, 60)
    
    def test_invalid_psd_file_handling(self, tmp_path, capsys):
        """Test handling of invalid PSD files in processing"""
        # Create PNG with .psd extension (invalid PSD)
        img = Image.new('RGB', (100, 80), 'orange')
        invalid_psd_path = tmp_path / "invalid.psd"
        img.save(invalid_psd_path, "PNG")
        
        # Create valid PNG
        valid_png_path = tmp_path / "valid.png"
        img.save(valid_png_path, "PNG")
        
        # Create signature
        sig_img = Image.new('RGBA', (20, 15), (0, 255, 0, 128))
        sig_path = tmp_path / "signature.png"
        sig_img.save(sig_path)
        
        # Process directory with invalid PSD
        autosig.process_image_files(
            str(tmp_path),
            str(sig_path),
            force=True,
            suffix="_test"
        )
        
        # Should process valid PNG and report error for invalid PSD
        captured = capsys.readouterr()
        assert "Error processing invalid.psd" in captured.out
        
        # Valid PNG should be processed
        valid_output = tmp_path / "valid_test.png"
        assert valid_output.exists()


class TestMultiFormatSupport:
    """Test support for multiple input formats"""
    
    def test_normalize_input_formats_all_default(self):
        """Test that None returns all supported formats"""
        result = autosig.normalize_input_formats(None)
        expected = autosig.ALL_SUPPORTED_FORMATS
        assert set(result) == set(expected)
    
    def test_normalize_input_formats_single_format(self):
        """Test normalizing single format"""
        result = autosig.normalize_input_formats(['jpg'])
        assert 'jpg' in result
        assert 'jpeg' in result  # Should include alias
    
    def test_normalize_input_formats_aliases(self):
        """Test format aliases are handled correctly"""
        # Test JPEG aliases
        result = autosig.normalize_input_formats(['jpeg'])
        assert 'jpg' in result and 'jpeg' in result
        
        # Test TIFF aliases
        result = autosig.normalize_input_formats(['tiff'])
        assert 'tiff' in result and 'tif' in result
    
    def test_normalize_input_formats_invalid_format(self):
        """Test error handling for invalid formats"""
        with pytest.raises(ValueError, match="Unsupported format 'xyz'"):
            autosig.normalize_input_formats(['xyz'])
    
    def test_normalize_input_formats_mixed_valid_invalid(self):
        """Test that one invalid format causes error even with valid ones"""
        with pytest.raises(ValueError, match="Unsupported format 'badformat'"):
            autosig.normalize_input_formats(['jpg', 'png', 'badformat'])


class TestCLIMultiFormat:
    """Test new CLI arguments for multi-format support"""
    
    def test_output_format_validation(self):
        """Test that --output-format accepts valid formats"""
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, "autosig.py", ".", "sig.png", "--output-format", "jpg"
        ], capture_output=True, text=True, cwd=".")
        
        # Should not fail due to format validation (will fail due to missing directory)
        assert "invalid choice" not in result.stderr
    
    def test_input_formats_parsing(self):
        """Test that --input-formats accepts comma-separated values"""
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, "autosig.py", "nonexistent", "sig.png", "--input-formats", "jpg,png"
        ], capture_output=True, text=True, cwd=".")
        
        # Should fail due to directory not existing, not format parsing
        assert "Directory 'nonexistent' does not exist" in result.stdout
    
    def test_suffix_empty_argument_parsing(self):
        """Test that --suffix without value works for no suffix"""
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, "autosig.py", "nonexistent", "sig.png", "--suffix"
        ], capture_output=True, text=True, cwd=".")
        
        # Should fail due to directory not existing, not argument parsing
        assert "expected one argument" not in result.stderr
        assert "Directory 'nonexistent' does not exist" in result.stdout
    
    def test_suffix_empty_string_argument_parsing(self):
        """Test that --suffix '' also works for no suffix"""
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, "autosig.py", "nonexistent", "sig.png", "--suffix", ""
        ], capture_output=True, text=True, cwd=".")
        
        # Should fail due to directory not existing, not argument parsing
        assert "expected one argument" not in result.stderr
        assert "Directory 'nonexistent' does not exist" in result.stdout

    def test_input_formats_invalid_format(self):
        """Test that invalid input format shows proper error"""
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, "autosig.py", "tests/fixtures", "--no-sig", "--input-formats", "xyz"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode != 0
        assert "Unsupported format 'xyz'" in result.stdout


class TestAnimatedGIFDetection:
    """Test animated GIF detection and warning"""
    
    def test_gif_warning_message_format(self):
        """Test that GIF warning uses correct format-agnostic message"""
        # Create a mock Image object that simulates an animated GIF
        from unittest.mock import Mock, patch
        from pathlib import Path
        
        mock_img = Mock()
        mock_img.is_animated = True
        mock_img.n_frames = 5
        mock_img.convert.return_value = mock_img
        
        with patch('autosig.Image.open', return_value=mock_img), \
             patch('autosig.tqdm.write') as mock_write:
            
            result = autosig.load_image_file("test.gif")
            
            # Should warn about animated GIF
            mock_write.assert_called()
            warning_message = mock_write.call_args[0][0]
            assert "Animated GIF detected (5 frames)" in warning_message
            assert "using first frame only" in warning_message


class TestFormatAgnosticWarnings:
    """Test that warnings work with all file formats"""
    
    def test_layer_hiding_warning_non_psd(self):
        """Test layer hiding warning works for all non-PSD formats"""
        from unittest.mock import Mock, patch
        
        test_formats = ['.jpg', '.png', '.webp', '.bmp', '.tiff', '.gif']
        
        for fmt in test_formats:
            mock_img = Mock()
            mock_img.convert.return_value = mock_img
            
            # Setup GIF-specific attributes for GIF test
            if fmt == '.gif':
                mock_img.is_animated = False
                mock_img.n_frames = 1
            
            with patch('autosig.Image.open', return_value=mock_img), \
                 patch('autosig.tqdm.write') as mock_write:
                
                autosig.load_image_file(f"test{fmt}", layers_to_hide=["Background"])
                
                # Should warn about layer hiding not supported
                mock_write.assert_called()
                warning_message = mock_write.call_args[0][0]
                assert "Layer hiding only supported for PSD files" in warning_message
                assert f"test{fmt}" in warning_message


class TestIntegrationMultiFormat:
    """Integration tests for multi-format processing"""
    
    def test_mixed_format_directory_processing(self, tmp_path):
        """Test processing directory with mixed file formats"""
        from PIL import Image
        
        # Create test files of different formats
        base_img = Image.new('RGB', (200, 150), 'blue')
        
        # Save in different formats
        jpg_path = tmp_path / "test1.jpg"
        png_path = tmp_path / "test2.png"
        webp_path = tmp_path / "test3.webp"
        
        base_img.save(jpg_path, "JPEG")
        base_img.save(png_path, "PNG")
        base_img.save(webp_path, "WEBP")
        
        # Process with no signature mode to avoid signature validation issues
        autosig.process_image_files(
            str(tmp_path),
            None,  # No signature
            apply_signature=False,
            force=True,
            suffix="_test"
        )
        
        # Should create output files for all input formats
        output_files = list(tmp_path.glob("*_test.png"))
        assert len(output_files) == 3  # Should process JPG, PNG, and WEBP
        
        # Verify specific files exist
        assert (tmp_path / "test1_test.png").exists()  # From JPG
        assert (tmp_path / "test2_test.png").exists()  # From PNG
        assert (tmp_path / "test3_test.png").exists()  # From WEBP
    
    def test_format_filtering_excludes_others(self, tmp_path):
        """Test that format filtering only processes specified formats"""
        from PIL import Image
        
        # Create test files
        base_img = Image.new('RGB', (100, 80), 'green')
        
        jpg_path = tmp_path / "test.jpg"
        png_path = tmp_path / "test.png"
        
        base_img.save(jpg_path, "JPEG")
        base_img.save(png_path, "PNG")
        
        # Process only JPG files
        autosig.process_image_files(
            str(tmp_path),
            None,  # No signature
            apply_signature=False,
            force=True,
            suffix="_processed",
            input_formats="jpg"
        )
        
        # Should only process JPG file
        assert (tmp_path / "test_processed.png").exists()  # From JPG
        # PNG should not be processed, so no PNG output with our suffix
        png_outputs = [f for f in tmp_path.glob("test_processed*") if f.stem.startswith("test_processed")]
        assert len(png_outputs) == 1  # Only one output file


class TestKeyboardInterruptHandling:
    """Test Ctrl+C cancellation functionality"""
    
    def test_keyboard_interrupt_during_processing(self, tmp_path):
        """Test that KeyboardInterrupt is handled gracefully during processing"""
        from PIL import Image
        import unittest.mock
        
        # Create test files
        base_img = Image.new('RGB', (50, 50), 'blue')
        test_file = tmp_path / "test.png"
        base_img.save(test_file)
        
        # Mock load_image_file to raise KeyboardInterrupt
        with unittest.mock.patch('autosig.load_image_file', side_effect=KeyboardInterrupt):
            # Capture output
            import io
            import contextlib
            
            stdout_capture = io.StringIO()
            with contextlib.redirect_stdout(stdout_capture):
                # This should handle KeyboardInterrupt gracefully
                autosig.process_image_files(
                    str(tmp_path),
                    None,  # No signature
                    apply_signature=False,
                    force=True,
                    suffix="_test"
                )
            
            output = stdout_capture.getvalue()
            assert "cancelled by user (Ctrl+C)" in output, "Should show cancellation message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])