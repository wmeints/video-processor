"""Tests for the content_generator module."""

from unittest.mock import MagicMock, patch

import pytest

from video_processor.content_generator import VideoMetadata, generate_content_metadata


@pytest.fixture
def mock_claude_chain():
    """Mock the entire LangChain chain for content generation."""
    with (
        patch("video_processor.content_generator.ChatAnthropic") as mock_anthropic,
        patch("video_processor.content_generator.ChatPromptTemplate") as mock_prompt,
    ):
        # Create mock chain that returns VideoMetadata
        mock_llm = MagicMock()
        mock_anthropic.return_value = mock_llm

        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_prompt_instance = MagicMock()
        mock_prompt.from_messages.return_value = mock_prompt_instance

        # Setup the chain to return proper VideoMetadata
        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain

        yield mock_chain


def test_generate_content_metadata_returns_dict(
    mock_settings, mock_claude_chain, processing_dir
):
    # Arrange
    transcription = "This video explains how to use GitHub Copilot skills to enhance your coding workflow."
    mock_claude_chain.invoke.return_value = VideoMetadata(
        title="Using GitHub Copilot Skills",
        description="Learn how to enhance your coding workflow with Copilot skills.",
    )

    # Act
    result = generate_content_metadata(transcription, processing_dir, lang="en")

    # Assert
    assert isinstance(result, dict)
    assert "title" in result
    assert "description" in result
    assert result["title"] == "Using GitHub Copilot Skills"


def test_generate_content_metadata_saves_json_file(
    mock_settings, mock_claude_chain, processing_dir
):
    # Arrange
    transcription = "This is a test transcription about video processing."
    mock_claude_chain.invoke.return_value = VideoMetadata(
        title="Video Processing Guide",
        description="A comprehensive guide to video processing techniques.",
    )

    # Act
    generate_content_metadata(transcription, processing_dir, lang="en")

    # Assert
    metadata_file = processing_dir / "metadata.json"
    assert metadata_file.exists()

    import json

    content = json.loads(metadata_file.read_text())
    assert content["title"] == "Video Processing Guide"


def test_generate_content_metadata_dutch_language(
    mock_settings, mock_claude_chain, processing_dir
):
    # Arrange
    transcription = "Dit is een test transcriptie over video verwerking."
    mock_claude_chain.invoke.return_value = VideoMetadata(
        title="Video Verwerking Handleiding",
        description="Een complete handleiding voor video verwerking technieken.",
    )

    # Act
    result = generate_content_metadata(transcription, processing_dir, lang="nl")

    # Assert
    assert result["title"] == "Video Verwerking Handleiding"


def test_generate_content_metadata_with_realistic_transcription(
    mock_settings, mock_claude_chain, processing_dir
):
    # Arrange - use a realistic transcription snippet
    transcription = """
    Welcome to this video about GitHub Copilot skills. Today I'm going to show you
    how to create custom skills that can help you be more productive. We'll cover
    the basics of skill creation, how to test your skills, and best practices for
    sharing them with your team. Let's get started.
    """
    mock_claude_chain.invoke.return_value = VideoMetadata(
        title="Creating Custom GitHub Copilot Skills",
        description="Learn how to create and share custom Copilot skills for improved productivity.",
    )

    # Act
    result = generate_content_metadata(transcription, processing_dir, lang="en")

    # Assert
    assert len(result["title"]) <= 140
    assert len(result["description"]) > 0
    mock_claude_chain.invoke.assert_called_once()
