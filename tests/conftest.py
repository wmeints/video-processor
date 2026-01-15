"""Pytest fixtures for video-processor tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_VIDEO_PATH = TEST_DATA_DIR / "tip-willem-copilot-skills.mov"


@pytest.fixture
def test_video_path():
    """Return path to the real test video file."""
    if not TEST_VIDEO_PATH.exists():
        pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
    return TEST_VIDEO_PATH


@pytest.fixture
def test_thumbnail_path():
    """Return path to a real thumbnail file."""
    project_root = Path(__file__).parent.parent
    thumbnail_path = project_root / "thumbnails" / "raise.png"
    if not thumbnail_path.exists():
        pytest.skip(f"Thumbnail not found: {thumbnail_path}")
    return thumbnail_path


@pytest.fixture
def sample_video_path(tmp_path):
    """Create a fake video file path for testing."""
    video_file = tmp_path / "input" / "test_video.mp4"
    video_file.parent.mkdir(parents=True, exist_ok=True)
    video_file.touch()
    return video_file


@pytest.fixture
def processing_dir(tmp_path):
    """Create a processing directory for intermediate files."""
    proc_dir = tmp_path / "processing" / "20240101_120000"
    proc_dir.mkdir(parents=True, exist_ok=True)
    return proc_dir


@pytest.fixture
def sample_transcription():
    """Sample transcription text for testing content generation."""
    return "This is a sample transcription about video processing techniques."


@pytest.fixture
def sample_metadata():
    """Sample metadata dictionary."""
    return {
        "title": "Video Processing Techniques",
        "description": "A guide to modern video processing.",
    }


@pytest.fixture
def mock_ffmpeg():
    """Mock ffmpeg module for testing without actual video processing."""
    with patch("video_processor.audio_extractor.ffmpeg") as mock:
        mock_stream = MagicMock()
        mock.input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run.return_value = (b"", b"")
        yield mock


@pytest.fixture
def mock_ffmpeg_editor():
    """Mock ffmpeg module for video_editor tests."""
    with patch("video_processor.video_editor.ffmpeg") as mock:
        mock.probe.return_value = {"format": {"duration": "120.5"}}
        mock_stream = MagicMock()
        mock.input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run.return_value = (b"", b"")
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("video_processor.content_generator.load_settings") as mock:
        mock.return_value = {
            "api_key": "test-api-key",
            "api_url": None,
        }
        yield mock


@pytest.fixture
def sample_thumbnail_path(tmp_path):
    """Create a sample thumbnail file for testing."""
    thumbnails_dir = tmp_path / "thumbnails"
    thumbnails_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_file = thumbnails_dir / "dark.png"
    thumbnail_file.touch()
    return thumbnail_file
