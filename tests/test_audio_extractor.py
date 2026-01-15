"""Tests for the audio_extractor module."""

import wave

from video_processor.audio_extractor import extract_audio


def test_extract_audio_creates_wav_file(test_video_path, processing_dir):
    # Act
    result = extract_audio(test_video_path, processing_dir)

    # Assert
    assert result.exists()
    assert result.suffix == ".wav"
    assert result.name == "audio.wav"


def test_extract_audio_creates_valid_wav(test_video_path, processing_dir):
    # Act
    result = extract_audio(test_video_path, processing_dir)

    # Assert - verify it's a valid WAV file
    with wave.open(str(result), "rb") as wav_file:
        assert wav_file.getnchannels() == 1  # Mono
        assert wav_file.getframerate() == 16000  # Default sample rate
        assert wav_file.getnframes() > 0  # Has audio data


def test_extract_audio_uses_custom_sample_rate(test_video_path, processing_dir):
    # Arrange
    custom_sample_rate = 22050

    # Act
    result = extract_audio(
        test_video_path, processing_dir, sample_rate=custom_sample_rate
    )

    # Assert
    with wave.open(str(result), "rb") as wav_file:
        assert wav_file.getframerate() == custom_sample_rate
