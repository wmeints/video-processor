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
2. **Transcription** (`transcriber.py`) - Uses Nvidia Parakeet TDT model via NeMo toolkit with MPS acceleration on Apple Silicon
3. **Metadata Generation** (`content_generator.py`) - Generates title/description from transcription using heuristics (no LLM)
4. **Video Trimming** (`video_editor.py`) - Trims video using mm:ss timestamps with ffmpeg stream copy
5. **Thumbnail Addition** (`thumbnail_processor.py`) - Creates PNG with text overlay using Pillow, then prepends as video segment

### Key Design Decisions

- **Intermediate files** are saved to `processing/<timestamp>/` for debugging (audio.wav, transcription.txt, metadata.json, trimmed_video.mp4, thumbnail_with_text.png)
- **Final output** goes to `output/<timestamp>_<slugified-title>.mp4`
- **Input videos** are expected in `input/` directory
- **Theme thumbnails** are loaded from `thumbnails/<theme>.jpg` or `.png`
- **Parakeet model** is cached globally in `transcriber.py` to avoid reloading (~2.4GB download on first run)
- **Video concatenation** uses ffmpeg concat demuxer with a temp file list

### Directory Structure

```
input/          # Place source videos here
output/         # Final processed videos
processing/     # Timestamped intermediate files
thumbnails/     # Theme background images (dark.jpg, light.jpg, etc.)
src/video_processor/
  cli.py        # Typer CLI entry point
  audio_extractor.py
  transcriber.py
  content_generator.py
  video_editor.py
  thumbnail_processor.py
```

## Dependencies

- Requires FFmpeg installed system-wide (`brew install ffmpeg`)
- Uses `ffmpeg-python` for video operations (not moviepy for most operations)
- NeMo toolkit for Nvidia Parakeet ASR
- Pillow for image processing
