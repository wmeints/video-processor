"""Tests for the CLI module."""

import shutil

import pytest
from typer.testing import CliRunner

from video_processor.cli import app, get_thumbnail_path


runner = CliRunner()


@pytest.fixture
def project_setup(tmp_path, test_video_path, test_thumbnail_path):
    """Setup a project directory structure for CLI tests."""
    # Create directory structure
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    thumbnails_dir = tmp_path / "thumbnails"

    input_dir.mkdir()
    output_dir.mkdir()
    thumbnails_dir.mkdir()

    # Copy test video to input
    shutil.copy(test_video_path, input_dir / "test_video.mov")

    # Copy thumbnail
    shutil.copy(test_thumbnail_path, thumbnails_dir / "raise.png")

    return tmp_path


@pytest.mark.parametrize("theme,extension", [
    ("dark", "png"),
    ("light", "jpg"),
])
def test_get_thumbnail_path_finds_image(tmp_path, theme, extension):
    # Arrange
    thumbnails_dir = tmp_path / "thumbnails"
    thumbnails_dir.mkdir()
    thumbnail = thumbnails_dir / f"{theme}.{extension}"
    thumbnail.touch()

    # Act
    result = get_thumbnail_path(tmp_path, theme)

    # Assert
    assert result == thumbnail


def test_get_thumbnail_path_prefers_jpg_over_png(tmp_path):
    # Arrange
    thumbnails_dir = tmp_path / "thumbnails"
    thumbnails_dir.mkdir()
    jpg_thumbnail = thumbnails_dir / "theme.jpg"
    png_thumbnail = thumbnails_dir / "theme.png"
    jpg_thumbnail.touch()
    png_thumbnail.touch()

    # Act
    result = get_thumbnail_path(tmp_path, "theme")

    # Assert - jpg is checked first
    assert result == jpg_thumbnail


def test_get_thumbnail_path_not_found_raises_error(tmp_path):
    # Arrange
    thumbnails_dir = tmp_path / "thumbnails"
    thumbnails_dir.mkdir()

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="Theme 'nonexistent' not found"):
        get_thumbnail_path(tmp_path, "nonexistent")


def test_info_command_shows_video_info(project_setup, monkeypatch):
    # Arrange
    monkeypatch.chdir(project_setup)

    # Act
    result = runner.invoke(app, ["info", "test_video.mov"])

    # Assert
    assert result.exit_code == 0
    assert "Video Information" in result.output
    assert "Duration" in result.output


def test_info_command_video_not_found(project_setup, monkeypatch):
    # Arrange
    monkeypatch.chdir(project_setup)

    # Act
    result = runner.invoke(app, ["info", "nonexistent.mp4"])

    # Assert
    assert result.exit_code == 1
    assert "not found" in result.output


@pytest.mark.slow
def test_process_command_full_pipeline(project_setup, monkeypatch):
    """Integration test for the full processing pipeline (skips transcription)."""
    # Arrange
    monkeypatch.chdir(project_setup)

    # Act - use skip-transcription to avoid needing ML models
    result = runner.invoke(app, [
        "process", "test_video.mov",
        "--theme", "raise",
        "--title", "Test Video",
        "--subtitle", "Test Author",
        "--skip-transcription",
        "--start-from", "00:00",
        "--end-at", "00:05",
        "--thumbnail-duration", "2",
    ])

    # Assert
    assert result.exit_code == 0
    assert "Processing Complete" in result.output

    # Check output file was created
    output_dir = project_setup / "output"
    output_files = list(output_dir.glob("*.mp4"))
    assert len(output_files) == 1


@pytest.mark.slow
def test_process_command_creates_metadata_file(project_setup, monkeypatch):
    """Test that metadata JSON is created."""
    # Arrange
    monkeypatch.chdir(project_setup)

    # Act
    result = runner.invoke(app, [
        "process", "test_video.mov",
        "--theme", "raise",
        "--title", "Metadata Test",
        "--subtitle", "Author Name",
        "--skip-transcription",
        "--end-at", "00:03",
    ])

    # Assert
    assert result.exit_code == 0
    output_dir = project_setup / "output"
    metadata_files = list(output_dir.glob("*_metadata.json"))
    assert len(metadata_files) == 1


def test_process_command_video_not_found(project_setup, monkeypatch):
    # Arrange
    monkeypatch.chdir(project_setup)

    # Act
    result = runner.invoke(app, [
        "process", "nonexistent.mp4",
        "--theme", "raise",
    ])

    # Assert
    assert result.exit_code == 1
    assert "not found" in result.output


def test_process_command_theme_not_found(project_setup, monkeypatch):
    # Arrange
    monkeypatch.chdir(project_setup)

    # Act
    result = runner.invoke(app, [
        "process", "test_video.mov",
        "--theme", "nonexistent",
    ])

    # Assert
    assert result.exit_code == 1
    assert "not found" in result.output
