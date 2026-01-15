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


PROMPTS = {
    "nl": {
        "system": "Je genereert video metadata van transcripties. Schrijf altijd in het Nederlands.",
        "user": """Genereer een titel en beschrijving voor deze video op basis van de transcriptie.

Richtlijnen:
- Titel: Houd het kort en pakkend, maximaal 140 karakters
- Beschrijving: 1-2 zinnen die de inhoud van de video samenvatten
- Schrijf in het Nederlands

Transcriptie:
{transcription}""",
    },
    "en": {
        "system": "You generate video metadata from transcriptions. Always write in English.",
        "user": """Generate a title and description for this video based on its transcription.

Guidelines:
- Title: Keep it short and engaging, maximum 140 characters
- Description: 1-2 sentences summarizing the video content
- Write in English

Transcription:
{transcription}""",
    },
}


def generate_content_metadata(
    transcription: str, output_path: Path, lang: str = "nl"
) -> dict[str, str]:
    """
    Generate title and description from transcription using Claude.

    Args:
        transcription: The full transcription text
        output_path: Path where metadata will be saved
        lang: Language for output ('nl' for Dutch, 'en' for English)

    Returns:
        Dictionary with 'title' and 'description' keys
    """
    console.print(f"[blue]Generating title and description with Claude ({lang})...[/blue]")

    settings = load_settings()

    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        api_key=settings["api_key"],
        base_url=settings.get("api_url"),
    )

    structured_llm = llm.with_structured_output(VideoMetadata)

    lang_prompts = PROMPTS.get(lang, PROMPTS["nl"])
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", lang_prompts["system"]),
            ("user", lang_prompts["user"]),
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
