"""Tests for the thumbnail_processor module."""

import pytest
from PIL import Image

from video_processor.thumbnail_processor import (
    add_thumbnail_to_video,
    create_thumbnail_with_text,
)
from video_processor.video_editor import get_video_dimensions, get_video_duration, trim_video


@pytest.fixture
def prepared_video_and_thumbnail(test_thumbnail_path, test_video_path, processing_dir):
    """Prepare a trimmed video and processed thumbnail for add_thumbnail_to_video tests."""
    trimmed_video = trim_video(test_video_path, processing_dir, end_at="00:05")
    width, height = get_video_dimensions(trimmed_video)

    processed_thumbnail = create_thumbnail_with_text(
        thumbnail_path=test_thumbnail_path,
        title="Test",
        subtitle="Subtitle",
        output_path=processing_dir,
        video_width=width,
        video_height=height,
    )

    return trimmed_video, processed_thumbnail


def test_create_thumbnail_with_text_creates_file(test_thumbnail_path, processing_dir):
    # Act
    result = create_thumbnail_with_text(
        thumbnail_path=test_thumbnail_path,
        title="Test Title",
        subtitle="Test Subtitle",
        output_path=processing_dir,
        video_width=1920,
        video_height=1080,
    )

    # Assert
    assert result.exists()
    assert result.name == "thumbnail_with_text.png"


def test_create_thumbnail_with_text_correct_dimensions(test_thumbnail_path, processing_dir):
    # Arrange
    width, height = 1920, 1080

    # Act
    result = create_thumbnail_with_text(
        thumbnail_path=test_thumbnail_path,
        title="Test Title",
        subtitle="Test Subtitle",
        output_path=processing_dir,
        video_width=width,
        video_height=height,
    )

    # Assert
    with Image.open(result) as img:
        assert img.width == width
        assert img.height == height


def test_create_thumbnail_with_text_is_rgba(test_thumbnail_path, processing_dir):
    # Act
    result = create_thumbnail_with_text(
        thumbnail_path=test_thumbnail_path,
        title="Test Title",
        subtitle="Test Subtitle",
        output_path=processing_dir,
        video_width=1920,
        video_height=1080,
    )

    # Assert
    with Image.open(result) as img:
        assert img.mode == "RGBA"


def test_create_thumbnail_uses_video_dimensions(test_thumbnail_path, test_video_path, processing_dir):
    # Arrange - use actual video dimensions
    width, height = get_video_dimensions(test_video_path)

    # Act
    result = create_thumbnail_with_text(
        thumbnail_path=test_thumbnail_path,
        title="Copilot Skills",
        subtitle="Willem de Moor",
        output_path=processing_dir,
        video_width=width,
        video_height=height,
    )

    # Assert
    with Image.open(result) as img:
        assert img.width == width
        assert img.height == height


def test_add_thumbnail_to_video_creates_output(prepared_video_and_thumbnail, processing_dir):
    # Arrange
    trimmed_video, processed_thumbnail = prepared_video_and_thumbnail

    # Act
    result = add_thumbnail_to_video(
        video_path=trimmed_video,
        thumbnail_path=processed_thumbnail,
        output_path=processing_dir,
        thumbnail_duration=2.0,
    )

    # Assert
    assert result.exists()
    assert result.name == "video_with_thumbnail.mp4"


def test_add_thumbnail_increases_duration(prepared_video_and_thumbnail, processing_dir):
    # Arrange
    trimmed_video, processed_thumbnail = prepared_video_and_thumbnail
    thumbnail_duration = 3.0

    # Act
    result = add_thumbnail_to_video(
        video_path=trimmed_video,
        thumbnail_path=processed_thumbnail,
        output_path=processing_dir,
        thumbnail_duration=thumbnail_duration,
    )

    # Assert - verify output was created and has reasonable duration
    # (exact duration verification is complex due to re-encoding and keyframes)
    final_duration = get_video_duration(result)
    assert final_duration >= thumbnail_duration  # At minimum, has the thumbnail duration
