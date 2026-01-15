# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run video-processor process <video_name> --theme <theme>

# Run with all options
uv run video-processor process my_video.mp4 --theme dark --title "Title" --subtitle "Subtitle" --start-from 00:03 --end-at 05:30

# Get video info
uv run video-processor info my_video.mp4

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_function -v
```

## Architecture

This is a video processing CLI tool that orchestrates a 5-step pipeline:

1. **Audio Extraction** (`audio_extractor.py`) - Extracts 16kHz mono WAV using ffmpeg-python
2. **Transcription** (`transcriber.py`) - Uses Nvidia Parakeet TDT model via NeMo toolkit with CUDA/MPS acceleration
3. **Metadata Generation** (`content_generator.py`) - Generates title/description from transcription using heuristics (no LLM)
4. **Video Trimming** (`video_editor.py`) - Trims video using mm:ss timestamps with ffmpeg stream copy
5. **Thumbnail Addition** (`thumbnail_processor.py`) - Creates PNG with text overlay using Pillow, then prepends as video segment

### Module Structure

- **`cli.py`** - Typer CLI entry point, handles argument parsing, validation, and user output
- **`pipeline.py`** - Pipeline orchestration with `ProcessingContext` dataclass and step functions (`run_pipeline`, `step_extract_audio`, `step_transcribe`, etc.)

### Key Design Decisions

- **Intermediate files** are saved to `processing/<timestamp>/` for debugging (audio.wav, transcription.txt, metadata.json, trimmed_video.mp4, thumbnail_with_text.png)
- **Final output** goes to `output/<timestamp>_<slugified-title>.mp4`
- **Input videos** are expected in `input/` directory
- **Theme thumbnails** are loaded from `thumbnails/<theme>.jpg` or `.png`
- **Parakeet model** is cached globally in `transcriber.py` to avoid reloading (~2.4GB download on first run)
- **Video concatenation** uses ffmpeg concat demuxer with a temp file list
- **GPU acceleration** prefers CUDA, falls back to MPS (Apple Silicon), then CPU

### Directory Structure

```
input/          # Place source videos here
output/         # Final processed videos
processing/     # Timestamped intermediate files
thumbnails/     # Theme background images (dark.jpg, light.jpg, etc.)
src/video_processor/
  cli.py        # Typer CLI entry point
  pipeline.py   # Pipeline orchestration and step functions
  audio_extractor.py
  transcriber.py
  content_generator.py
  video_editor.py
  thumbnail_processor.py
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=video_processor

# Run a specific test file
uv run pytest tests/test_audio_extractor.py -v

# Run a specific test function
uv run pytest tests/test_audio_extractor.py::test_extract_audio_creates_wav_file -v
```

### Test Structure

Tests mirror the module structure in `src/video_processor/`:

```
tests/
  conftest.py              # Shared fixtures
  test_audio_extractor.py
  test_video_editor.py
  test_content_generator.py
  test_thumbnail_processor.py
  test_transcriber.py
  test_cli.py
```

### Writing Tests

- Use **fixtures** for setting up mocks and test data (defined in `conftest.py`)
- Use **arrange-act-assert** pattern in all tests
- Use **test functions only**, no test classes
- Use **plain `assert` statements** for assertions

Example test structure:

```python
def test_something_does_expected_behavior(mock_dependency, sample_data):
    # Arrange
    expected = "expected result"

    # Act
    result = function_under_test(sample_data)

    # Assert
    assert result == expected
```

### Available Fixtures

Common fixtures are defined in `tests/conftest.py`:

- `sample_video_path` - Creates a fake video file path
- `processing_dir` - Creates a processing directory for intermediate files
- `sample_transcription` - Sample transcription text
- `sample_metadata` - Sample metadata dictionary
- `mock_ffmpeg` - Mocks ffmpeg for audio_extractor tests
- `mock_ffmpeg_editor` - Mocks ffmpeg for video_editor tests
- `mock_settings` - Mocks settings/config loading
- `sample_thumbnail_path` - Creates a sample thumbnail file

## Code Style

### Linting

This project uses **ruff** for linting:

```bash
# Run linter
uv run ruff check

# Run linter with auto-fix
uv run ruff check --fix
```

### Docstrings

Use **NumPy-style docstrings** for all functions and classes:

```python
def function_name(param1: str, param2: int = 10) -> bool:
    """
    Short description of the function.

    Longer description if needed, explaining the function's behavior
    in more detail.

    Parameters
    ----------
    param1 : str
        Description of param1.
    param2 : int, optional
        Description of param2 (default is 10).

    Returns
    -------
    bool
        Description of return value.

    Raises
    ------
    ValueError
        When param1 is invalid.
    """
```

## Dependencies

- Requires FFmpeg installed system-wide (`brew install ffmpeg`)
- Uses `ffmpeg-python` for video operations (not moviepy for most operations)
- NeMo toolkit for Nvidia Parakeet ASR
- Pillow for image processing
