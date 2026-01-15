"""Tests for the transcriber module."""

import pytest

from video_processor.audio_extractor import extract_audio
from video_processor.transcriber import transcribe_audio


@pytest.fixture
def test_audio_path(test_video_path, processing_dir):
    """Extract audio from test video for transcription tests."""
    return extract_audio(test_video_path, processing_dir)


@pytest.mark.slow
def test_transcribe_audio_english_returns_text(test_audio_path, processing_dir):
    # Act
    result = transcribe_audio(test_audio_path, processing_dir, lang="en")

    # Assert
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.slow
def test_transcribe_audio_creates_transcription_file(test_audio_path, processing_dir):
    # Act
    transcribe_audio(test_audio_path, processing_dir, lang="en")

    # Assert
    transcription_file = processing_dir / "transcription.txt"
    assert transcription_file.exists()
    assert transcription_file.read_text().strip() != ""


@pytest.mark.slow
def test_transcribe_audio_dutch_returns_text(test_audio_path, processing_dir):
    # Act
    result = transcribe_audio(test_audio_path, processing_dir, lang="nl")

    # Assert
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.slow
def test_transcribe_audio_content_makes_sense(test_audio_path, processing_dir):
    """Test that transcription contains expected words from the test video about Copilot skills."""
    # Act
    result = transcribe_audio(test_audio_path, processing_dir, lang="en")

    # Assert - video is about Copilot skills, so should contain relevant words
    result_lower = result.lower()
    # Check for at least some expected terms
    expected_terms = ["copilot", "skill", "code", "github"]
    found_terms = [term for term in expected_terms if term in result_lower]
    assert len(found_terms) >= 1, (
        f"Expected at least one of {expected_terms} in transcription"
    )
