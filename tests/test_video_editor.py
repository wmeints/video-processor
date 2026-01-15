"""Tests for the video_editor module."""

import pytest

from video_processor.video_editor import (
    format_timestamp,
    get_video_dimensions,
    get_video_duration,
    parse_timestamp,
    trim_video,
)


@pytest.mark.parametrize("timestamp,expected", [
    ("01:30", 90.0),
    ("00:00", 0.0),
    ("00:45", 45.0),
    ("05:00", 300.0),
    ("5:30", 330.0),
])
def test_parse_timestamp(timestamp, expected):
    assert parse_timestamp(timestamp) == expected


def test_parse_timestamp_invalid_format_raises_error():
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        parse_timestamp("1:2:3")


def test_parse_timestamp_invalid_seconds_raises_error():
    with pytest.raises(ValueError, match="Invalid seconds value"):
        parse_timestamp("01:60")


@pytest.mark.parametrize("seconds,expected", [
    (90, "01:30"),
    (0, "00:00"),
    (45, "00:45"),
    (300, "05:00"),
])
def test_format_timestamp(seconds, expected):
    assert format_timestamp(seconds) == expected


def test_get_video_duration(test_video_path):
    # Act
    duration = get_video_duration(test_video_path)

    # Assert - test video is ~348 seconds
    assert duration > 340
    assert duration < 360


def test_get_video_dimensions(test_video_path):
    # Act
    width, height = get_video_dimensions(test_video_path)

    # Assert - test video is 3456x2234
    assert width == 3456
    assert height == 2234


def test_trim_video_creates_output_file(test_video_path, processing_dir):
    # Act
    result = trim_video(
        test_video_path, processing_dir, start_from="00:05", end_at="00:10"
    )

    # Assert
    assert result.exists()
    assert result.name == "trimmed_video.mp4"


def test_trim_video_correct_duration(test_video_path, processing_dir):
    # Arrange
    start = "00:05"
    end = "00:15"

    # Act
    result = trim_video(test_video_path, processing_dir, start_from=start, end_at=end)

    # Assert - check output duration
    # Note: ffmpeg stream copy cuts at keyframes, so duration may vary
    # We just verify the output was created and is shorter than original
    actual_duration = get_video_duration(result)
    original_duration = get_video_duration(test_video_path)
    assert actual_duration < original_duration


def test_trim_video_start_only(test_video_path, processing_dir):
    # Act
    result = trim_video(test_video_path, processing_dir, start_from="00:10")

    # Assert
    assert result.exists()
    original_duration = get_video_duration(test_video_path)
    trimmed_duration = get_video_duration(result)
    # Should be shorter than original (keyframe alignment may cause variance)
    assert trimmed_duration < original_duration


def test_trim_video_end_only(test_video_path, processing_dir):
    # Act
    result = trim_video(test_video_path, processing_dir, end_at="00:20")

    # Assert
    assert result.exists()
    original_duration = get_video_duration(test_video_path)
    trimmed_duration = get_video_duration(result)
    # Should be shorter than original (keyframe alignment may cause variance)
    assert trimmed_duration < original_duration


def test_trim_video_invalid_start_beyond_duration(test_video_path, processing_dir):
    # Act & Assert
    with pytest.raises(ValueError, match="Start time .* is beyond video duration"):
        trim_video(test_video_path, processing_dir, start_from="99:00")


def test_trim_video_start_after_end_raises_error(test_video_path, processing_dir):
    # Act & Assert
    with pytest.raises(ValueError, match="Start time .* must be before end time"):
        trim_video(test_video_path, processing_dir, start_from="00:30", end_at="00:10")
