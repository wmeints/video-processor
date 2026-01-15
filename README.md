# Video Processor

A Python CLI tool that processes videos with AI-powered features including audio transcription using Nvidia Parakeet, automatic title/description generation, video trimming, and thumbnail overlay.

## Features

- **Audio Extraction**: Extract audio from video files for transcription
- **AI Transcription**: Transcribe audio using Nvidia Parakeet ASR model (runs locally on your MacBook)
- **Auto-Generated Metadata**: Generate titles and descriptions from transcription
- **Video Trimming**: Trim videos using start and end timestamps (mm:ss format)
- **Thumbnail Themes**: Add themed thumbnail images with title and subtitle overlay at the beginning of the video

## Requirements

- Python 3.10+
- FFmpeg installed on your system
- macOS (optimized for Apple Silicon with MPS acceleration)

### Installing FFmpeg

```bash
# macOS with Homebrew
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## Installation

1. Clone or download this project
2. Install dependencies using uv:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

## Project Structure

```
video-processor/
├── input/              # Place your input videos here
├── output/             # Processed videos are saved here
├── processing/         # Intermediate files for debugging
│   └── <timestamp>/    # Each processing run gets its own folder
├── thumbnails/         # Thumbnail theme backgrounds
│   ├── dark.jpg        # Example: dark theme
│   ├── light.jpg       # Example: light theme
│   └── corporate.jpg   # Example: corporate theme
├── src/
│   └── video_processor/
│       ├── __init__.py
│       ├── cli.py                  # Typer CLI interface
│       ├── audio_extractor.py      # Audio extraction module
│       ├── transcriber.py          # Nvidia Parakeet transcription
│       ├── content_generator.py    # Title/description generation
│       ├── video_editor.py         # Video trimming functions
│       └── thumbnail_processor.py  # Thumbnail overlay module
├── pyproject.toml
└── README.md
```

## Usage

### Basic Usage

```bash
# Process a video with a theme
uv run video-processor process my_video.mp4 --theme dark
```

### Full Options

```bash
uv run video-processor process my_video.mp4 \
    --theme corporate \
    --title "Custom Title" \
    --subtitle "Custom subtitle text" \
    --start-from 00:03 \
    --end-at 05:30 \
    --thumbnail-duration 5.0
```

### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--theme` | Theme name for thumbnail (looks for `thumbnails/<theme>.jpg`) | Required |
| `--title` | Custom title (auto-generated from transcription if not provided) | - |
| `--subtitle` | Subtitle text (uses description if not provided) | - |
| `--start-from` | Start timestamp in mm:ss format | None (video start) |
| `--end-at` | End timestamp in mm:ss format | None (video end) |
| `--thumbnail-duration` | Duration to show thumbnail in seconds | 5.0 |
| `--skip-transcription` | Skip AI transcription | False |

### Thumbnail Themes

Place your thumbnail background images in the `thumbnails/` folder:

```
thumbnails/
├── dark.jpg       # Use with --theme dark
├── light.jpg      # Use with --theme light
├── corporate.jpg  # Use with --theme corporate
└── custom.jpg     # Use with --theme custom
```

Both `.jpg` and `.png` formats are supported.

### Trimming Examples

```bash
# Trim first 3 seconds from video
uv run video-processor process my_video.mp4 --theme dark --start-from 00:03

# Keep only 00:10 to 02:30 of the video
uv run video-processor process my_video.mp4 --theme dark --start-from 00:10 --end-at 02:30

# Trim from 1 minute mark to the end
uv run video-processor process my_video.mp4 --theme dark --start-from 01:00
```

### Get Video Information

```bash
uv run video-processor info my_video.mp4
```

## Processing Pipeline

1. **Audio Extraction**: Extracts audio as 16kHz mono WAV for optimal transcription
2. **Transcription**: Uses Nvidia Parakeet TDT model for speech-to-text
3. **Metadata Generation**: Analyzes transcription to generate title and description
4. **Video Trimming**: Trims video using --start-from and --end-at timestamps (optional)
5. **Thumbnail Addition**: Creates thumbnail with text overlay and prepends to video

## Output

- Final video is saved to `output/<timestamp>_<slugified-title>.mp4`
- Intermediate files are saved to `processing/<timestamp>/` for debugging:
  - `audio.wav` - Extracted audio
  - `transcription.txt` - Full transcription
  - `metadata.json` - Generated title and description
  - `trimmed_video.mp4` - Video with trimmed start
  - `thumbnail_with_text.png` - Processed thumbnail image
  - `video_with_thumbnail.mp4` - Final video before copy to output

## Notes

### First Run

The first time you run the transcription, the Nvidia Parakeet model will be downloaded (~2.4GB). This only happens once.

### Performance

- On Apple Silicon Macs, the model uses MPS acceleration for faster inference
- On other systems, it falls back to CPU inference (slower but still functional)

### Troubleshooting

If you encounter issues:

1. Check the `processing/<timestamp>/` folder for intermediate files
2. Verify FFmpeg is installed: `ffmpeg -version`
3. Ensure your input video is in the `input/` folder
4. Make sure your theme image exists in the `thumbnails/` folder (e.g., `thumbnails/dark.jpg`)

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run the CLI directly
uv run python -m video_processor.cli --help
```

## License

MIT License
