# Changelog

All notable changes to AutoSig will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2025-08-04

### Added
- **🛑 Ctrl+C cancellation** with graceful exit and progress reporting:
  - **Reliable cancellation** - Standard KeyboardInterrupt handling
  - **Immediate response** - No complex key detection required
  - **Comprehensive reporting** - Shows processed files, remaining files, and skipped files
  - **Clean error handling** - Proper cleanup without terminal corruption

- **Enhanced progress feedback**:
  - Progress bar shows "Processing images (Ctrl+C to cancel)"
  - Initial instruction: "Press Ctrl+C to cancel processing at any time"
  - Detailed cancellation report with processing statistics
  - Standard and reliable cancellation mechanism

### Technical Improvements
- **🧪 Simplified cancellation system** with reliable KeyboardInterrupt handling
- **🧪 Updated test coverage**: 95 tests with 88% coverage
  - **Cancellation testing** for KeyboardInterrupt handling
  - **Graceful exit testing** with proper cleanup
  - **Removed complex ESC key detection** for better reliability
- **🛡️ Robust error handling** for interrupted processing

### Use Cases Enabled
- **⏹️ Long batch processing** - Cancel lengthy operations without losing progress
- **🚫 Accidental runs** - Stop processing immediately if wrong parameters used
- **📈 Progress monitoring** - Get detailed reports of what was completed before cancellation
- **💻 Professional workflows** - Clean cancellation using standard Ctrl+C

## [0.3.1] - 2025-08-04

### Added
- **🌍 Universal format support** for input files:
  - Process **all common image formats**: PSD, PNG, JPG, JPEG, WEBP, BMP, TIFF, TIF, GIF
  - **Automatic format detection** - no configuration needed
  - **Animated GIF support** - extracts first frame with user warnings
  - **Format aliases** - handles both .jpg/.jpeg and .tiff/.tif automatically

- **🎛️ Advanced format filtering** via `--input-formats` / `-if`:
  - Process only specific formats: `--input-formats jpg,png`
  - **Comma-separated format lists** with validation
  - **Professional workflows** - filter legacy formats, specific file types, etc.
  - **Error handling** - clear messages for unsupported formats

### Changed
- **🚫 BREAKING**: Replaced `--format` with `--output-format` / `-of` for clarity
  - **No backward compatibility** - clean CLI design
  - **Unambiguous naming** - clear separation of input vs output format control
  - **Updated help text** and examples throughout

- **📊 Enhanced test coverage**: 94 tests with 88% coverage (was 82 tests, 85%)
  - **12 new test classes** covering multi-format functionality
  - **Format validation tests** - CLI argument validation with subprocess
  - **Animated GIF detection tests** - mock-based warning verification
  - **Integration tests** - mixed format directory processing
  - **Real format testing** - actual file format processing validation

- **⚠️ Improved warning messages**:
  - **Format-agnostic layer hiding** warnings: "Layer hiding only supported for PSD files"
  - **Animated GIF detection** warnings: "Animated GIF detected (X frames), using first frame only"
  - **Enhanced error messages** with proper exit codes

### Technical Improvements
- **🏗️ Robust format normalization** with alias handling
- **🔍 Dynamic file discovery** supporting all formats with filtering
- **🛡️ Comprehensive input validation** with meaningful error messages
- **🧪 Mock-based testing** for format-specific behavior verification
- **📈 Improved code organization** with helper functions for format handling

### Use Cases Enabled
- **📁 Legacy format modernization**: Convert BMP/TIFF archives to PNG/WEBP
- **🎬 Animated GIF processing**: Extract static frames for further processing
- **🔄 Selective batch processing**: Process only photos (skip PSDs), only graphics, etc.
- **⚡ Professional workflows**: Format-specific processing pipelines
- **🌐 Modern format adoption**: Batch convert to WEBP for web optimization

## [0.3.0] - 2025-08-04

### Added
- **🎯 No-signature mode** via `--no-sig` flag:
  - Process images without applying signatures
  - Perfect for format conversion, resizing, and cropping workflows
  - Auto-adjusts output suffix to `_processed` when no custom suffix provided
  - Signature argument becomes optional when this flag is used

- **🎨 PSD layer hiding** via `--hide-layer` argument:
  - Hide specific layers in PSD files by name (case-insensitive)
  - Hide layers by index (0-based)
  - Support for multiple layers with repeated `--hide-layer` arguments
  - Graceful handling of missing layers with warning messages
  - Only affects PSD files - PNG files show warnings if layer hiding attempted

- **📐 Smart aspect ratio cropping** with maximum constraints:
  - `--crop-portrait` for portrait and square images (e.g., `4:5`)
  - `--crop-landscape` for landscape images (e.g., `16:9`)
  - **Maximum ratio enforcement**: Only crops images that exceed specified ratios
  - **Orientation detection**: Automatically classifies images as portrait/landscape/square
  - **Center-aligned cropping**: Preserves important content in center of images
  - **Aspect ratio parsing**: Supports both `width:height` format and decimal ratios

### Enhanced Features
- **🔄 Processing order optimization**:
  - Layer hiding → Aspect ratio cropping → Signature application → Resizing
  - Ensures optimal quality and correct proportions at each step
- **📊 Comprehensive test coverage**: 82 tests covering all functionality with 85% code coverage
- **🧪 Real PSD testing**: Complete test suite with actual PSD files including multi-layer scenarios
- **🛡️ Advanced validation**: Proper error handling for invalid aspect ratios and layer specifications
- **📝 Enhanced help text**: Updated examples demonstrating complex workflows

### Breaking Changes
- **Command line interface**: Signature argument is now optional (but required unless `--no-sig` specified)
- **Processing pipeline**: Aspect ratio cropping now occurs before signature application

### Use Cases Enabled
- **Format conversion workflows**: Convert PSD to JPG/PNG/WEBP without signatures
- **Social media batch processing**: Apply different aspect ratio constraints for portrait vs landscape
- **Layer management**: Hide watermarks, draft layers, or signatures before processing
- **Complex processing pipelines**: Combine layer hiding, cropping, signatures, and format conversion

### Technical Improvements
- **Orientation detection algorithm**: Robust classification of image orientations
- **Aspect ratio constraint system**: Smart cropping that preserves well-proportioned images
- **Real PSD testing infrastructure**: Programmatically created PSD test files with proper layer structures
- **Subprocess CLI testing**: Authentic command-line validation that captures actual exit codes and error messages  
- **Comprehensive test suite**: 82 tests with 85% coverage, zero skipped tests
- **Error resilience**: Graceful handling of invalid layer names, indices, and aspect ratios

## [0.2.0] - 2025-08-02

### Added
- **Custom output suffixes** via `--suffix` / `-s` argument (default: `_with_sig`)
- **Image resizing** via `--max-dimension` / `-md` argument to limit larger dimension while maintaining aspect ratio
- **File conflict handling** with multiple modes:
  - Interactive prompts with y/n/a/s options (default behavior)
  - `--force` / `-f` flag to overwrite all existing files without prompting
  - `--skip-existing` / `-se` flag to skip existing files without prompting
- **Enhanced progress tracking** showing processed and skipped file counts
- **Comprehensive reporting** with summary of processing results and list of skipped files
- **Flexible positioning options**:
  - Pixel-based positioning via `--pixels` / `-p` (default: 20px)
  - Percentage-based positioning via `--percent` / `-pc` 
- **Multiple output formats** via `--format` / `-fmt` argument:
  - PNG (default) - lossless with transparency
  - JPG - smaller files, composited on white background
  - WEBP - modern format with transparency and compression
  - TIFF - professional quality with transparency
- **Quality control** via `--quality` / `-q` argument for lossy formats (1-100, default: 85)
- **Smart transparency handling** - JPG auto-composites on white background, others preserve transparency
- **Smart input filtering** to prevent processing AutoSig output files:
  - Auto-detection of common AutoSig suffixes (`_with_sig`, `_signed`, `_test`, etc.)
  - Prevents exponential file growth when running multiple times on same directory
  - `--exclude-suffix` / `-ex` argument for custom exclusion patterns
  - Transparent reporting of excluded file counts
- **Version information** via `--version` argument
- **Improved error handling** with validation for all input parameters

### Changed
- **Enhanced output filename control** - files now use customizable suffixes and multiple format options
- **Improved signature application order** - signature applied before resizing for better proportional results
- **Improved user experience** with better progress visualization using tqdm progress bars
- **Safer file operations** - no more silent overwrites, user has full control over file conflicts
- **Better error reporting** with detailed summaries of processing results

### Technical Improvements
- **Suppressed harmless PSD library warnings** for cleaner output
- **High-quality image resizing** using LANCZOS resampling
- **Robust file handling** with proper conflict detection and resolution
- **Comprehensive input validation** for all command line arguments

## [0.1.0] - 2025-08-01

### Added
- **Multi-format support** for both source files and signatures:
  - Process PSD and PNG source files
  - Support PSD and PNG signature files
- **Automatic signature placement** with fixed 20px offset from right and bottom edges
- **Batch processing** of entire directories
- **High-quality output** with proper alpha channel handling and transparency support
- **Progress indication** during processing
- **Basic error handling** for unsupported files and processing errors
- **Command line interface** with directory and signature file arguments

### Features
- Converts PSD files to PNG format while preserving image quality
- Maintains signature transparency and alpha blending
- Processes all PSD and PNG files in specified directory
- Exports results as PNG files with same base filenames
- Provides basic progress feedback during processing

### Dependencies
- Pillow (PIL) for image processing
- psd-tools for PSD file support
- tqdm for progress visualization