"""Content generation module using LangChain + Claude for titles and descriptions."""

import json
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from rich.console import Console

from .settings import load_settings

console = Console()


class VideoMetadata(BaseModel):
    """Structured output for video metadata."""

    title: str = Field(description="Video title, max 140 characters")
    description: str = Field(description="Video description, 1-2 sentences")


def generate_content_metadata(transcription: str, output_path: Path) -> dict[str, str]:
    """
    Generate title and description from transcription using Claude.

    Args:
        transcription: The full transcription text
        output_path: Path where metadata will be saved

    Returns:
        Dictionary with 'title' and 'description' keys
    """
    console.print("[blue]Generating title and description with Claude...[/blue]")

    settings = load_settings()

    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        api_key=settings["api_key"],
        base_url=settings.get("api_url"),
    )

    structured_llm = llm.with_structured_output(VideoMetadata)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You generate video metadata from transcriptions."),
            (
                "user",
                """Generate a title and description for this video based on its transcription.

Guidelines:
- Title: Keep it short and engaging, maximum 140 characters
- Description: 1-2 sentences summarizing the video content

Transcription:
{transcription}""",
            ),
        ]
    )

    chain = prompt | structured_llm
    result = chain.invoke({"transcription": transcription})

    metadata = {
        "title": result.title,
        "description": result.description,
    }

    # Save metadata to JSON file
    metadata_file = output_path / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    console.print(f"[green]\u2713 Generated title:[/green] {result.title}")
    console.print(f"[green]\u2713 Generated description:[/green] {result.description}")
    console.print(f"[dim]Metadata saved to: {metadata_file}[/dim]")

    return metadata
