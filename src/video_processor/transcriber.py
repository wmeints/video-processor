"""Transcription module using Nvidia Parakeet ASR model."""

from pathlib import Path

import torch
from rich.console import Console

console = Console()

# Global model cache to avoid reloading
_model = None


def get_parakeet_model():
    """
    Load and cache the Nvidia Parakeet ASR model.

    Returns:
        The loaded Parakeet model
    """
    global _model

    if _model is None:
        console.print("[blue]Loading Nvidia Parakeet model...[/blue]")

        try:
            import nemo.collections.asr as nemo_asr

            # Use Parakeet TDT model - optimized for transcription
            # This model works well on CPU/MPS for MacBook
            model_name = "nvidia/parakeet-tdt-0.6b-v2"

            # Determine device - prefer MPS on Mac, fallback to CPU
            if torch.backends.mps.is_available():
                device = "mps"
                console.print("[green]Using Apple Silicon (MPS) acceleration[/green]")
            else:
                device = "cpu"
                console.print("[yellow]Using CPU for inference[/yellow]")

            _model = nemo_asr.models.ASRModel.from_pretrained(model_name)

            # Move model to appropriate device
            if device == "cpu":
                _model = _model.cpu()

            _model.eval()
            console.print("[green]✓ Parakeet model loaded successfully[/green]")

        except Exception as e:
            console.print(f"[red]Error loading Parakeet model:[/red] {e}")
            raise RuntimeError(f"Failed to load Parakeet model: {e}")

    return _model


def transcribe_audio(audio_path: Path, output_path: Path) -> str:
    """
    Transcribe audio file using Nvidia Parakeet.

    Args:
        audio_path: Path to the audio file (WAV format, 16kHz)
        output_path: Path where transcription will be saved

    Returns:
        The transcription text
    """
    console.print(f"[blue]Transcribing audio:[/blue] {audio_path}")

    model = get_parakeet_model()

    try:
        # Transcribe the audio file
        transcriptions = model.transcribe([str(audio_path)])

        if isinstance(transcriptions, list) and len(transcriptions) > 0:
            # Handle different return formats
            if hasattr(transcriptions[0], 'text'):
                transcription = transcriptions[0].text
            else:
                transcription = transcriptions[0]
        else:
            transcription = str(transcriptions)

        # Save transcription to file
        transcription_file = output_path / "transcription.txt"
        transcription_file.write_text(transcription, encoding="utf-8")

        console.print(f"[green]✓ Transcription saved to:[/green] {transcription_file}")
        console.print(f"[dim]Transcription preview: {transcription[:200]}...[/dim]")

        return transcription

    except Exception as e:
        console.print(f"[red]Error during transcription:[/red] {e}")
        raise RuntimeError(f"Failed to transcribe audio: {e}")
