"""Video processing pipeline with step functions."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from slugify import slugify

from .audio_extractor import extract_audio
from .content_generator import generate_content_metadata
from .thumbnail_processor import add_thumbnail_to_video, create_thumbnail_with_text
from .transcriber import transcribe_audio
from .video_editor import get_video_dimensions, trim_video

console = Console()


@dataclass
class ProcessingContext:
    """Context object holding all paths and settings for video processing."""

    video_path: Path
    processing_dir: Path
    output_dir: Path
    thumbnail_path: Path
    timestamp: str
    title: str | None
    subtitle: str | None
    author: str | None
    start_from: str | None
    end_at: str | None
    thumbnail_duration: float
    skip_transcription: bool
    lang: str


@dataclass
class VideoMetadata:
    """Metadata generated or provided for the video."""

    title: str
    description: str
    author: str | None


def step_extract_audio(ctx: ProcessingContext) -> Path:
    """Extract audio from video file."""
    console.print(Panel("[bold]Step 1/5: Extracting Audio[/bold]"))
    return extract_audio(ctx.video_path, ctx.processing_dir)


def step_transcribe(ctx: ProcessingContext, audio_path: Path) -> str:
    """Transcribe audio to text."""
    if ctx.skip_transcription:
        console.print(Panel("[bold]Step 2/5: Skipping Transcription[/bold]"))
        return ctx.title or "Video Content"

    console.print(Panel("[bold]Step 2/5: Transcribing Audio[/bold]"))
    return transcribe_audio(audio_path, ctx.processing_dir, lang=ctx.lang)


def step_generate_metadata(ctx: ProcessingContext, transcription: str) -> VideoMetadata:
    """Generate or use provided metadata."""
    console.print(Panel("[bold]Step 3/5: Generating Metadata[/bold]"))

    if ctx.skip_transcription and ctx.title:
        generated = {"title": ctx.title, "description": ctx.subtitle or "Video content"}
    else:
        generated = generate_content_metadata(transcription, ctx.processing_dir, lang=ctx.lang)

    return VideoMetadata(
        title=ctx.title or generated["title"],
        description=ctx.subtitle or generated["description"],
        author=ctx.author,
    )


def step_trim_video(ctx: ProcessingContext) -> Path:
    """Trim video or copy if no timestamps provided."""
    if ctx.start_from or ctx.end_at:
        console.print(Panel("[bold]Step 4/5: Trimming Video[/bold]"))
        return trim_video(
            ctx.video_path,
            ctx.processing_dir,
            start_from=ctx.start_from,
            end_at=ctx.end_at,
        )

    console.print(Panel("[bold]Step 4/5: Skipping Trim (no timestamps provided)[/bold]"))
    trimmed_video = ctx.processing_dir / "trimmed_video.mp4"
    shutil.copy2(ctx.video_path, trimmed_video)
    return trimmed_video


def step_add_thumbnail(ctx: ProcessingContext, video_path: Path, metadata: VideoMetadata) -> Path:
    """Create and add thumbnail to video."""
    console.print(Panel("[bold]Step 5/5: Adding Thumbnail[/bold]"))

    width, height = get_video_dimensions(video_path)
    thumbnail_subtitle = metadata.author or metadata.description

    processed_thumbnail = create_thumbnail_with_text(
        thumbnail_path=ctx.thumbnail_path,
        title=metadata.title,
        subtitle=thumbnail_subtitle,
        output_path=ctx.processing_dir,
        video_width=width,
        video_height=height,
        duration=ctx.thumbnail_duration,
    )

    return add_thumbnail_to_video(
        video_path=video_path,
        thumbnail_path=processed_thumbnail,
        output_path=ctx.processing_dir,
        thumbnail_duration=ctx.thumbnail_duration,
    )


def save_output(ctx: ProcessingContext, final_video: Path, metadata: VideoMetadata) -> Path:
    """Copy final video and metadata to output directory."""
    slugified_title = slugify(metadata.title, max_length=50)
    output_filename = f"{ctx.timestamp}_{slugified_title}.mp4"
    output_path = ctx.output_dir / output_filename

    shutil.copy2(final_video, output_path)

    output_metadata = {
        "title": metadata.title,
        "description": metadata.description,
        "author": metadata.author,
    }
    metadata_path = ctx.output_dir / f"{ctx.timestamp}_{slugified_title}_metadata.json"
    metadata_path.write_text(json.dumps(output_metadata, indent=2), encoding="utf-8")

    return output_path


def run_pipeline(ctx: ProcessingContext) -> tuple[Path, VideoMetadata]:
    """
    Run the full video processing pipeline.

    Returns
    -------
    tuple[Path, VideoMetadata]
        The output path and final metadata.
    """
    audio_path = step_extract_audio(ctx)
    transcription = step_transcribe(ctx, audio_path)
    metadata = step_generate_metadata(ctx, transcription)
    trimmed_video = step_trim_video(ctx)
    final_video = step_add_thumbnail(ctx, trimmed_video, metadata)
    output_path = save_output(ctx, final_video, metadata)

    return output_path, metadata
