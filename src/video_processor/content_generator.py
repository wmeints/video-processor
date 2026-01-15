"""Content generation module using LangChain + Claude for titles and descriptions."""

import json
from functools import cache
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from rich.console import Console

from .settings import load_settings

console = Console()

PROMPTS_DIR = Path(__file__).parent / "prompts"


class VideoMetadata(BaseModel):
    """Structured output for video metadata."""

    title: str = Field(description="Video title, max 140 characters")
    description: str = Field(description="Video description, 1-2 sentences")


@cache
def load_prompts(lang: str) -> dict[str, str]:
    """
    Load prompts for a given language from the prompts directory.

    Parameters
    ----------
    lang : str
        Language code ('nl' or 'en').

    Returns
    -------
    dict[str, str]
        Dictionary with 'system' and 'user' prompt strings.
    """
    system_file = PROMPTS_DIR / f"{lang}_system.md"
    user_file = PROMPTS_DIR / f"{lang}_user.md"

    if not system_file.exists():
        system_file = PROMPTS_DIR / "nl_system.md"
        user_file = PROMPTS_DIR / "nl_user.md"

    return {
        "system": system_file.read_text(encoding="utf-8").strip(),
        "user": user_file.read_text(encoding="utf-8").strip(),
    }


def generate_content_metadata(
    transcription: str, output_path: Path, lang: str = "nl"
) -> dict[str, str]:
    """
    Generate title and description from transcription using Claude.

    Parameters
    ----------
    transcription : str
        The full transcription text.
    output_path : Path
        Path where metadata will be saved.
    lang : str, optional
        Language for output ('nl' for Dutch, 'en' for English). Default is 'nl'.

    Returns
    -------
    dict[str, str]
        Dictionary with 'title' and 'description' keys.
    """
    console.print(
        f"[blue]Generating title and description with Claude ({lang})...[/blue]"
    )

    settings = load_settings()

    llm = ChatAnthropic(
        model="claude-sonnet-4-5",  # type: ignore[call-arg]
        api_key=settings["api_key"],
        base_url=settings.get("api_url"),
    )

    structured_llm = llm.with_structured_output(VideoMetadata)

    lang_prompts = load_prompts(lang)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", lang_prompts["system"]),
            ("user", lang_prompts["user"]),
        ]
    )

    chain = prompt | structured_llm
    result = chain.invoke({"transcription": transcription})

    metadata = {
        "title": result.title,  # type: ignore[union-attr]
        "description": result.description,  # type: ignore[union-attr]
    }

    # Save metadata to JSON file
    metadata_file = output_path / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    console.print(f"[green]\u2713 Generated title:[/green] {result.title}")  # type: ignore[union-attr]
    console.print(f"[green]\u2713 Generated description:[/green] {result.description}")  # type: ignore[union-attr]
    console.print(f"[dim]Metadata saved to: {metadata_file}[/dim]")

    return metadata
