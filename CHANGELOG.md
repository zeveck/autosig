# Changelog

All notable changes to AutoSig will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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