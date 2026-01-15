"""Command-line interface for the video processor using Typer."""

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .pipeline import ProcessingContext, run_pipeline

app = typer.Typer(
    name="video-processor",
    help="Process videos: extract audio, transcribe, generate metadata, trim, and add thumbnails.",
    add_completion=False,
)
console = Console()


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns
    -------
    Path
        The current working directory as project root.
    """
    return Path.cwd()


def ensure_directories(project_root: Path) -> tuple[Path, Path, Path]:
    """
    Ensure input, output, and processing directories exist.

    Parameters
    ----------
    project_root : Path
        The project root directory.

    Returns
    -------
    tuple[Path, Path, Path]
        Tuple of (input_dir, output_dir, processing_dir).
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

    Parameters
    ----------
    project_root : Path
        Project root directory.
    theme : str
        Theme name (e.g., 'dark', 'light', 'corporate').

    Returns
    -------
    Path
        Path to the thumbnail image.

    Raises
    ------
    FileNotFoundError
        If the theme thumbnail doesn't exist.
    """
    thumbnails_dir = project_root / "thumbnails"
    thumbnail_path = thumbnails_dir / f"{theme}.jpg"

    if not thumbnail_path.exists():
        thumbnail_path = thumbnails_dir / f"{theme}.png"

    if not thumbnail_path.exists():
        available = list(thumbnails_dir.glob("*.jpg")) + list(
            thumbnails_dir.glob("*.png")
        )
        available_names = [p.stem for p in available]
        raise FileNotFoundError(
            f"Theme '{theme}' not found. Looking for: thumbnails/{theme}.jpg or .png\n"
            f"Available themes: {', '.join(available_names) if available_names else 'none'}"
        )

    return thumbnail_path


@app.command()
def process(
    video_name: str = typer.Argument(
        ..., help="Name of the video file in the input folder (e.g., 'my_video.mp4')"
    ),
    theme: str = typer.Option(
        ...,
        "--theme",
        help="Theme name for thumbnail background (looks for thumbnails/<theme>.jpg or .png)",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Custom title for the thumbnail (auto-generated from transcription if not provided)",
    ),
    subtitle: str | None = typer.Option(
        None,
        "--subtitle",
        help="Subtitle for the thumbnail (uses description if not provided)",
    ),
    start_from: str | None = typer.Option(
        None,
        "--start-from",
        help="Start timestamp in mm:ss format (e.g., '00:03' to start at 3 seconds)",
    ),
    end_at: str | None = typer.Option(
        None,
        "--end-at",
        help="End timestamp in mm:ss format (e.g., '05:30' to end at 5 minutes 30 seconds)",
    ),
    thumbnail_duration: float = typer.Option(
        1.5,
        "--thumbnail-duration",
        help="Duration to show the thumbnail at the start (seconds)",
    ),
    skip_transcription: bool = typer.Option(
        False,
        "--skip-transcription",
        help="Skip transcription and use provided title/subtitle instead",
    ),
    lang: str = typer.Option(
        "nl",
        "--lang",
        help="Language for transcription and metadata ('nl' for Dutch, 'en' for English)",
    ),
    author: str | None = typer.Option(
        None, "--author", help="Author name to display as subtitle on the thumbnail"
    ),
):
    """
    Process a video file with full pipeline.

    Steps:
    1. Extract audio from video
    2. Transcribe audio using Nvidia Parakeet
    3. Generate title and description from transcription
    4. Trim video (optionally using --start-from and --end-at timestamps)
    5. Add thumbnail with title/subtitle overlay

    The output is saved to the output folder with timestamp and slugified title.
    Intermediate files are saved to processing/<timestamp> for debugging.
    """
    console.print(
        Panel(
            "[bold blue]Video Processor[/bold blue]\n"
            "Processing your video with AI-powered features",
            expand=False,
        )
    )

    project_root = get_project_root()
    input_dir, output_dir, processing_base = ensure_directories(project_root)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processing_dir = processing_base / timestamp
    processing_dir.mkdir(parents=True, exist_ok=True)

    video_path = input_dir / video_name
    if not video_path.exists():
        console.print(f"[red]Error:[/red] Video file not found: {video_path}")
        console.print(
            f"[dim]Please place your video in the input folder: {input_dir}[/dim]"
        )
        raise typer.Exit(code=1)

    try:
        thumbnail_path = get_thumbnail_path(project_root, theme)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print(
            "[dim]Create a thumbnails folder and add theme images (e.g., thumbnails/dark.jpg)[/dim]"
        )
        raise typer.Exit(code=1)

    console.print(f"\n[bold]Input video:[/bold] {video_path}")
    console.print(f"[bold]Processing directory:[/bold] {processing_dir}")
    console.print(f"[bold]Theme:[/bold] {theme} ({thumbnail_path})\n")

    ctx = ProcessingContext(
        video_path=video_path,
        processing_dir=processing_dir,
        output_dir=output_dir,
        thumbnail_path=thumbnail_path,
        timestamp=timestamp,
        title=title,
        subtitle=subtitle,
        author=author,
        start_from=start_from,
        end_at=end_at,
        thumbnail_duration=thumbnail_duration,
        skip_transcription=skip_transcription,
        lang=lang,
    )

    try:
        output_path, metadata = run_pipeline(ctx)

        console.print("\n" + "=" * 60)
        console.print(
            Panel(
                f"[bold green]Processing Complete![/bold green]\n\n"
                f"[bold]Title:[/bold] {metadata.title}\n"
                f"[bold]Description:[/bold] {metadata.description}\n\n"
                f"[bold]Output file:[/bold] {output_path}\n"
                f"[bold]Processing files:[/bold] {processing_dir}",
                expand=False,
            )
        )
    except (OSError, RuntimeError) as e:
        console.print(f"\n[red bold]Error during processing:[/red bold] {e}")
        console.print(
            f"[dim]Check processing directory for intermediate files: {processing_dir}[/dim]"
        )
        raise typer.Exit(code=1)


@app.command()
def info(
    video_name: str = typer.Argument(
        ..., help="Name of the video file in the input folder"
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

        format_info = probe.get("format", {})
        console.print(
            f"\n[bold]Format:[/bold] {format_info.get('format_name', 'Unknown')}"
        )
        console.print(
            f"[bold]Duration:[/bold] {float(format_info.get('duration', 0)):.2f} seconds"
        )
        console.print(
            f"[bold]Size:[/bold] {int(format_info.get('size', 0)) / (1024 * 1024):.2f} MB"
        )

        for stream in probe.get("streams", []):
            if stream["codec_type"] == "video":
                console.print("\n[bold]Video Stream:[/bold]")
                console.print(f"  Codec: {stream.get('codec_name', 'Unknown')}")
                console.print(
                    f"  Resolution: {stream.get('width')}x{stream.get('height')}"
                )
                console.print(f"  Frame rate: {stream.get('r_frame_rate', 'Unknown')}")
            elif stream["codec_type"] == "audio":
                console.print("\n[bold]Audio Stream:[/bold]")
                console.print(f"  Codec: {stream.get('codec_name', 'Unknown')}")
                console.print(
                    f"  Sample rate: {stream.get('sample_rate', 'Unknown')} Hz"
                )
                console.print(f"  Channels: {stream.get('channels', 'Unknown')}")

    except ffmpeg.Error as e:
        console.print(f"[red]Error reading video info:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
