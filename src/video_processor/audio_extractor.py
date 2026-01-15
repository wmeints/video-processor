"""Audio extraction module for extracting audio tracks from video files."""

from pathlib import Path

import ffmpeg
from rich.console import Console

console = Console()


def extract_audio(
    video_path: Path, output_path: Path, sample_rate: int = 16000
) -> Path:
    """
    Extract audio from a video file and save as WAV.

    Parameters
    ----------
    video_path : Path
        Path to the input video file.
    output_path : Path
        Path where the audio file will be saved.
    sample_rate : int, optional
        Sample rate for the output audio (default is 16000 for Parakeet).

    Returns
    -------
    Path
        Path to the extracted audio file.
    """
    console.print(f"[blue]Extracting audio from:[/blue] {video_path}")

    audio_output = output_path / "audio.wav"

    try:
        # Use ffmpeg to extract audio with proper sample rate for speech recognition
        (
            ffmpeg.input(str(video_path))
            .output(
                str(audio_output),
                acodec="pcm_s16le",
                ac=1,  # Mono channel
                ar=sample_rate,  # Sample rate for Parakeet
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        console.print(f"[green]✓ Audio extracted to:[/green] {audio_output}")
        return audio_output

    except ffmpeg.Error as e:
        console.print(f"[red]Error extracting audio:[/red] {e.stderr.decode()}")
        raise RuntimeError(f"Failed to extract audio: {e.stderr.decode()}")
