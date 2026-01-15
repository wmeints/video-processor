"""Video editing module for trimming and modifying videos."""

import re
from pathlib import Path
from typing import Optional

import ffmpeg
from rich.console import Console

console = Console()


def parse_timestamp(timestamp: str) -> float:
    """
    Parse a timestamp in mm:ss format to seconds.

    Args:
        timestamp: Time string in mm:ss format (e.g., "01:30" for 1 minute 30 seconds)

    Returns:
        Time in seconds as float

    Raises:
        ValueError: If timestamp format is invalid
    """
    pattern = r'^(\d{1,2}):(\d{2})$'
    match = re.match(pattern, timestamp)

    if not match:
        raise ValueError(
            f"Invalid timestamp format: '{timestamp}'. Expected mm:ss (e.g., '01:30')"
        )

    minutes = int(match.group(1))
    seconds = int(match.group(2))

    if seconds >= 60:
        raise ValueError(
            f"Invalid seconds value: {seconds}. Seconds must be 0-59."
        )

    return minutes * 60 + seconds


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as mm:ss timestamp.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string (mm:ss)
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def trim_video(
    video_path: Path,
    output_path: Path,
    start_from: Optional[str] = None,
    end_at: Optional[str] = None
) -> Path:
    """
    Trim video using start and end timestamps in mm:ss format.

    Args:
        video_path: Path to the input video file
        output_path: Directory where trimmed video will be saved
        start_from: Start timestamp in mm:ss format (e.g., "00:03" to start at 3 seconds)
        end_at: End timestamp in mm:ss format (e.g., "05:30" to end at 5:30)

    Returns:
        Path to the trimmed video file
    """
    console.print(f"[blue]Trimming video:[/blue] {video_path}")

    trimmed_output = output_path / "trimmed_video.mp4"

    try:
        # Get video duration first
        probe = ffmpeg.probe(str(video_path))
        duration = float(probe['format']['duration'])

        # Parse timestamps
        start_seconds = parse_timestamp(start_from) if start_from else 0.0
        end_seconds = parse_timestamp(end_at) if end_at else duration

        # Validate timestamps
        if start_seconds >= duration:
            raise ValueError(
                f"Start time {start_from} ({start_seconds}s) is beyond video duration "
                f"({format_timestamp(duration)})"
            )

        if end_seconds > duration:
            console.print(
                f"[yellow]Warning:[/yellow] End time {end_at} exceeds video duration. "
                f"Using video end ({format_timestamp(duration)}) instead."
            )
            end_seconds = duration

        if start_seconds >= end_seconds:
            raise ValueError(
                f"Start time ({start_from}) must be before end time ({end_at})"
            )

        # Calculate new duration
        new_duration = end_seconds - start_seconds

        console.print(
            f"[dim]Trimming from {format_timestamp(start_seconds)} to "
            f"{format_timestamp(end_seconds)} (duration: {format_timestamp(new_duration)})[/dim]"
        )

        # Build ffmpeg command
        input_stream = ffmpeg.input(str(video_path), ss=start_seconds)

        output_stream = input_stream.output(
            str(trimmed_output),
            t=new_duration,
            c='copy'  # Copy streams without re-encoding for speed
        )

        output_stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)

        console.print(f"[green]✓ Video trimmed:[/green] {trimmed_output}")
        console.print(
            f"[dim]Original duration: {format_timestamp(duration)} → "
            f"New duration: {format_timestamp(new_duration)}[/dim]"
        )

        return trimmed_output

    except ffmpeg.Error as e:
        console.print(f"[red]Error trimming video:[/red] {e.stderr.decode()}")
        raise RuntimeError(f"Failed to trim video: {e.stderr.decode()}")


def get_video_duration(video_path: Path) -> float:
    """
    Get the duration of a video file in seconds.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds
    """
    try:
        probe = ffmpeg.probe(str(video_path))
        return float(probe['format']['duration'])
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to probe video: {e.stderr.decode()}")


def get_video_dimensions(video_path: Path) -> tuple[int, int]:
    """
    Get the width and height of a video file.

    Args:
        video_path: Path to the video file

    Returns:
        Tuple of (width, height)
    """
    try:
        probe = ffmpeg.probe(str(video_path))
        video_stream = next(
            (s for s in probe['streams'] if s['codec_type'] == 'video'),
            None
        )
        if video_stream:
            return int(video_stream['width']), int(video_stream['height'])
        raise ValueError("No video stream found")
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to probe video: {e.stderr.decode()}")
