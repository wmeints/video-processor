# Video Processor - Architecture Documentation

This documentation follows the [arc42](https://arc42.org/) template for architecture documentation.

## About

Video Processor is a CLI tool that automates video processing workflows. It extracts audio, generates transcriptions, creates metadata using AI, trims videos, and adds branded thumbnail overlays.

## Table of Contents

1. [Introduction and Goals](01-introduction-goals.md) - Purpose, stakeholders, and quality objectives
2. [Context and Scope](03-context-scope.md) - System boundaries and external interfaces
3. [Building Block View](05-building-block-view.md) - Component structure and responsibilities
4. [Runtime View](06-runtime-view.md) - Pipeline execution flow and data transformations
5. [Deployment View](07-deployment-view.md) - Installation and environment requirements

## Quick Reference

```bash
# Run the processor
uv run video-processor process <video_name> --theme <theme>

# Get video info
uv run video-processor info <video_name>
```

## Key Technologies

| Component | Technology |
|-----------|------------|
| CLI Framework | Typer |
| Video Processing | FFmpeg (via ffmpeg-python) |
| Transcription | Nvidia Parakeet TDT, OpenAI Whisper |
| Metadata Generation | LangChain + Claude |
| Image Processing | Pillow |
