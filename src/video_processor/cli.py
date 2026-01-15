"""Command-line interface for the video processor using Typer."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from slugify import slugify

from .audio_extractor import extract_audio
from .content_generator import generate_content_metadata
from .thumbnail_processor import add_thumbnail_to_video, create_thumbnail_with_text
from .transcriber import transcribe_audio
from .video_editor import get_video_dimensions, trim_video

app = typer.Typer(
    name="video-processor",
    help="Process videos: extract audio, transcribe, generate metadata, trim, and add thumbnails.",
    add_completion=False,
)
console = Console()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path.cwd()


def ensure_directories(project_root: Path) -> tuple[Path, Path, Path]:
    """
    Ensure input, output, and processing directories exist.

    Returns:
        Tuple of (input_dir, output_dir, processing_dir)
    """
    input_dir = project_root / "input"
    output_dir = project_root / "output"
    processing_dir = project_root / "processing"

    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    processing_dir.mkdir(exist_ok=True)

    return input_dir, output_dir, processing_dir


def get_thumbnail_path(project_root: Path, theme: str) -> Path:
    """
    Get the thumbnail path for a given theme.

    Args:
        project_root: Project root directory
        theme: Theme name (e.g., 'dark', 'light', 'corporate')

    Returns:
        Path to the thumbnail image

    Raises:
        FileNotFoundError: If the theme thumbnail doesn't exist
    """
    thumbnails_dir = project_root / "thumbnails"
    thumbnail_path = thumbnails_dir / f"{theme}.jpg"

    if not thumbnail_path.exists():
        # Also try .png extension
        thumbnail_path = thumbnails_dir / f"{theme}.png"

    if not thumbnail_path.exists():
        available = list(thumbnails_dir.glob("*.jpg")) + list(thumbnails_dir.glob("*.png"))
        available_names = [p.stem for p in available]
        raise FileNotFoundError(
            f"Theme '{theme}' not found. Looking for: thumbnails/{theme}.jpg or .png\n"
            f"Available themes: {', '.join(available_names) if available_names else 'none'}"
        )

    return thumbnail_path


@app.command()
def process(
    video_name: str = typer.Argument(
        ...,
        help="Name of the video file in the input folder (e.g., 'my_video.mp4')"
    ),
    theme: str = typer.Option(
        "raise",
        "--theme",
        help="Theme name for thumbnail background (looks for thumbnails/<theme>.jpg or .png)"
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        help="Custom title for the thumbnail (auto-generated from transcription if not provided)"
    ),
    subtitle: Optional[str] = typer.Option(
        None,
        "--subtitle",
        help="Subtitle for the thumbnail (uses description if not provided)"
    ),
    start_from: Optional[str] = typer.Option(
        None,
        "--start-from",
        help="Start timestamp in mm:ss format (e.g., '00:03' to start at 3 seconds)"
    ),
    end_at: Optional[str] = typer.Option(
        None,
        "--end-at",
        help="End timestamp in mm:ss format (e.g., '05:30' to end at 5 minutes 30 seconds)"
    ),
    thumbnail_duration: float = typer.Option(
        5.0,
        "--thumbnail-duration",
        help="Duration to show the thumbnail at the start (seconds)"
    ),
    skip_transcription: bool = typer.Option(
        False,
        "--skip-transcription",
        help="Skip transcription and use provided title/subtitle instead"
    ),
    lang: str = typer.Option(
        "nl",
        "--lang",
        help="Language for generated title/description ('nl' for Dutch, 'en' for English)"
    ),
    author: Optional[str] = typer.Option(
        None,
        "--author",
        help="Author name to display as subtitle on the thumbnail"
    ),
):
    """
    Process a video file with full pipeline:

    1. Extract audio from video
    2. Transcribe audio using Nvidia Parakeet
    3. Generate title and description from transcription
    4. Trim video (optionally using --start-from and --end-at timestamps)
    5. Add thumbnail with title/subtitle overlay

    The output is saved to the output folder with timestamp and slugified title.
    Intermediate files are saved to processing/<timestamp> for debugging.

    Timestamp format for trimming: mm:ss (e.g., '01:30' for 1 minute 30 seconds)
    """
    console.print(Panel(
        "[bold blue]Video Processor[/bold blue]\n"
        "Processing your video with AI-powered features",
        expand=False
    ))

    # Setup directories
    project_root = get_project_root()
    input_dir, output_dir, processing_base = ensure_directories(project_root)

    # Create timestamped processing directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processing_dir = processing_base / timestamp
    processing_dir.mkdir(parents=True, exist_ok=True)

    # Validate input video
    video_path = input_dir / video_name
    if not video_path.exists():
        console.print(f"[red]Error:[/red] Video file not found: {video_path}")
        console.print(f"[dim]Please place your video in the input folder: {input_dir}[/dim]")
        raise typer.Exit(code=1)

    # Get thumbnail path from theme
    try:
        thumbnail_path = get_thumbnail_path(project_root, theme)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print(f"[dim]Create a thumbnails folder and add your theme images (e.g., thumbnails/dark.jpg or dark.png)[/dim]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold]Input video:[/bold] {video_path}")
    console.print(f"[bold]Processing directory:[/bold] {processing_dir}")
    console.print(f"[bold]Theme:[/bold] {theme} ({thumbnail_path})\n")

    try:
        # Step 1: Extract audio
        console.print(Panel("[bold]Step 1/5: Extracting Audio[/bold]"))
        audio_path = extract_audio(video_path, processing_dir)

        # Step 2: Transcribe (unless skipped)
        if not skip_transcription:
            console.print(Panel("[bold]Step 2/5: Transcribing Audio[/bold]"))
            transcription = transcribe_audio(audio_path, processing_dir)
        else:
            console.print(Panel("[bold]Step 2/5: Skipping Transcription[/bold]"))
            transcription = title or "Video Content"

        # Step 3: Generate metadata
        console.print(Panel("[bold]Step 3/5: Generating Metadata[/bold]"))
        if skip_transcription and title:
            metadata = {
                "title": title,
                "description": subtitle or "Video content"
            }
        else:
            metadata = generate_content_metadata(transcription, processing_dir, lang=lang)

        # Use provided title/subtitle or generated ones
        final_title = title or metadata["title"]
        final_description = subtitle or metadata["description"]
        thumbnail_subtitle = author or final_description

        # Step 4: Trim video (if timestamps provided)
        if start_from or end_at:
            console.print(Panel("[bold]Step 4/5: Trimming Video[/bold]"))
            trimmed_video = trim_video(
                video_path, processing_dir,
                start_from=start_from,
                end_at=end_at
            )
        else:
            console.print(Panel("[bold]Step 4/5: Skipping Trim (no timestamps provided)[/bold]"))
            # Copy video to processing dir for consistency
            import shutil as sh
            trimmed_video = processing_dir / "trimmed_video.mp4"
            sh.copy2(video_path, trimmed_video)

        # Step 5: Add thumbnail
        console.print(Panel("[bold]Step 5/5: Adding Thumbnail[/bold]"))

        # Get video dimensions for thumbnail
        width, height = get_video_dimensions(trimmed_video)

        # Create thumbnail with text
        processed_thumbnail = create_thumbnail_with_text(
            thumbnail_path=thumbnail_path,
            title=final_title,
            subtitle=thumbnail_subtitle,
            output_path=processing_dir,
            video_width=width,
            video_height=height,
            duration=thumbnail_duration
        )

        # Add thumbnail to video
        final_video = add_thumbnail_to_video(
            video_path=trimmed_video,
            thumbnail_path=processed_thumbnail,
            output_path=processing_dir,
            thumbnail_duration=thumbnail_duration
        )

        # Generate output filename with timestamp and slugified title
        slugified_title = slugify(final_title, max_length=50)
        output_filename = f"{timestamp}_{slugified_title}.mp4"
        output_path = output_dir / output_filename

        # Copy final video to output directory
        shutil.copy2(final_video, output_path)

        # Save metadata to output directory
        output_metadata = {
            "title": final_title,
            "description": final_description,
            "author": author,
        }
        output_metadata_path = output_dir / f"{timestamp}_{slugified_title}_metadata.json"
        output_metadata_path.write_text(json.dumps(output_metadata, indent=2), encoding="utf-8")

        # Success summary
        console.print("\n" + "=" * 60)
        console.print(Panel(
            f"[bold green]✓ Processing Complete![/bold green]\n\n"
            f"[bold]Title:[/bold] {final_title}\n"
            f"[bold]Description:[/bold] {final_description}\n\n"
            f"[bold]Output file:[/bold] {output_path}\n"
            f"[bold]Processing files:[/bold] {processing_dir}",
            expand=False
        ))

    except Exception as e:
        console.print(f"\n[red bold]Error during processing:[/red bold] {e}")
        console.print(f"[dim]Check processing directory for intermediate files: {processing_dir}[/dim]")
        raise typer.Exit(code=1)


@app.command()
def info(
    video_name: str = typer.Argument(
        ...,
        help="Name of the video file in the input folder"
    ),
):
    """Display information about a video file."""
    import ffmpeg

    project_root = get_project_root()
    input_dir = project_root / "input"
    video_path = input_dir / video_name

    if not video_path.exists():
        console.print(f"[red]Error:[/red] Video file not found: {video_path}")
        raise typer.Exit(code=1)

    try:
        probe = ffmpeg.probe(str(video_path))

        console.print(Panel(f"[bold]Video Information: {video_name}[/bold]"))

        # Format info
        format_info = probe.get('format', {})
        console.print(f"\n[bold]Format:[/bold] {format_info.get('format_name', 'Unknown')}")
        console.print(f"[bold]Duration:[/bold] {float(format_info.get('duration', 0)):.2f} seconds")
        console.print(f"[bold]Size:[/bold] {int(format_info.get('size', 0)) / (1024*1024):.2f} MB")

        # Stream info
        for stream in probe.get('streams', []):
            if stream['codec_type'] == 'video':
                console.print(f"\n[bold]Video Stream:[/bold]")
                console.print(f"  Codec: {stream.get('codec_name', 'Unknown')}")
                console.print(f"  Resolution: {stream.get('width')}x{stream.get('height')}")
                console.print(f"  Frame rate: {stream.get('r_frame_rate', 'Unknown')}")
            elif stream['codec_type'] == 'audio':
                console.print(f"\n[bold]Audio Stream:[/bold]")
                console.print(f"  Codec: {stream.get('codec_name', 'Unknown')}")
                console.print(f"  Sample rate: {stream.get('sample_rate', 'Unknown')} Hz")
                console.print(f"  Channels: {stream.get('channels', 'Unknown')}")

    except Exception as e:
        console.print(f"[red]Error reading video info:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
