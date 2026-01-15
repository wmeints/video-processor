"""Transcription module using Nvidia Parakeet ASR model (English) and Whisper (Dutch)."""

from pathlib import Path

import torch
from rich.console import Console

console = Console()

# Global model cache to avoid reloading
_parakeet_model = None
_whisper_model = None


def get_parakeet_model():
    """
    Load and cache the Nvidia Parakeet ASR model.

    Returns
    -------
    nemo_asr.models.ASRModel
        The loaded Parakeet model.
    """
    global _parakeet_model

    if _parakeet_model is None:
        console.print("[blue]Loading Nvidia Parakeet model...[/blue]")

        try:
            import nemo.collections.asr as nemo_asr  # type: ignore[import-not-found]

            # Use Parakeet TDT model - optimized for transcription
            # This model works well on CPU/MPS for MacBook
            model_name = "nvidia/parakeet-tdt-0.6b-v2"

            # Determine device - prefer CUDA, then MPS on Mac, fallback to CPU
            if torch.cuda.is_available():
                device = "cuda"
                console.print("[green]Using CUDA GPU acceleration[/green]")
            elif torch.backends.mps.is_available():
                device = "mps"
                console.print("[green]Using Apple Silicon (MPS) acceleration[/green]")
            else:
                device = "cpu"
                console.print("[yellow]Using CPU for inference[/yellow]")

            _parakeet_model = nemo_asr.models.ASRModel.from_pretrained(model_name)

            # Move model to appropriate device
            if device == "cuda":
                _parakeet_model = _parakeet_model.cuda()  # type: ignore[union-attr]
            elif device == "cpu":
                _parakeet_model = _parakeet_model.cpu()  # type: ignore[union-attr]

            _parakeet_model.eval()  # type: ignore[union-attr]
            console.print("[green]✓ Parakeet model loaded successfully[/green]")

        except Exception as e:
            console.print(f"[red]Error loading Parakeet model:[/red] {e}")
            raise RuntimeError(f"Failed to load Parakeet model: {e}")

    return _parakeet_model


def get_whisper_model():
    """
    Load and cache the Whisper model for multilingual transcription.

    Returns
    -------
    whisper.Whisper
        The loaded Whisper model.
    """
    global _whisper_model

    if _whisper_model is None:
        console.print("[blue]Loading Whisper model...[/blue]")

        try:
            import whisper

            # Determine device - prefer CUDA, then MPS on Mac, fallback to CPU
            if torch.cuda.is_available():
                device = "cuda"
                console.print("[green]Using CUDA GPU acceleration[/green]")
            elif torch.backends.mps.is_available():
                device = "mps"
                console.print("[green]Using Apple Silicon (MPS) acceleration[/green]")
            else:
                device = "cpu"
                console.print("[yellow]Using CPU for inference[/yellow]")

            # Use medium model for good balance of speed and accuracy
            _whisper_model = whisper.load_model("medium", device=device)
            console.print("[green]✓ Whisper model loaded successfully[/green]")

        except Exception as e:
            console.print(f"[red]Error loading Whisper model:[/red] {e}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")

    return _whisper_model


def transcribe_audio(audio_path: Path, output_path: Path, lang: str = "en") -> str:
    """
    Transcribe audio file using Nvidia Parakeet (English) or Whisper (Dutch/other).

    Parameters
    ----------
    audio_path : Path
        Path to the audio file (WAV format, 16kHz).
    output_path : Path
        Path where transcription will be saved.
    lang : str, optional
        Language code ('en' for English, 'nl' for Dutch). Default is 'en'.

    Returns
    -------
    str
        The transcription text.
    """
    console.print(f"[blue]Transcribing audio ({lang}):[/blue] {audio_path}")

    try:
        if lang == "en":
            # Use Parakeet for English
            model = get_parakeet_model()
            transcriptions = model.transcribe([str(audio_path)])  # type: ignore[union-attr]

            if isinstance(transcriptions, list) and len(transcriptions) > 0:
                if hasattr(transcriptions[0], "text"):
                    transcription = transcriptions[0].text
                else:
                    transcription = transcriptions[0]
            else:
                transcription = str(transcriptions)
        else:
            # Use Whisper for Dutch and other languages
            model = get_whisper_model()
            result = model.transcribe(str(audio_path), language=lang)
            transcription = result["text"]

        # Save transcription to file
        transcription_file = output_path / "transcription.txt"
        transcription_file.write_text(transcription, encoding="utf-8")  # type: ignore[arg-type]

        console.print(f"[green]✓ Transcription saved to:[/green] {transcription_file}")
        preview = (
            transcription[:200] + "..." if len(transcription) > 200 else transcription  # type: ignore[operator]
        )
        console.print(f"[dim]Transcription preview: {preview}[/dim]")

        return transcription  # type: ignore[return-value]

    except Exception as e:
        console.print(f"[red]Error during transcription:[/red] {e}")
        raise RuntimeError(f"Failed to transcribe audio: {e}")
