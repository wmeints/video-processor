"""Content generation module for creating titles and descriptions from transcriptions."""

import json
import re
from pathlib import Path

from rich.console import Console

console = Console()


def extract_key_phrases(text: str, max_phrases: int = 5) -> list[str]:
    """
    Extract key phrases from text using simple heuristics.

    Args:
        text: The transcription text
        max_phrases: Maximum number of phrases to extract

    Returns:
        List of key phrases
    """
    # Clean and normalize text
    text = text.lower().strip()

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)

    # Get first few meaningful sentences as they often contain the topic
    key_phrases = []
    for sentence in sentences[:max_phrases]:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Filter out very short fragments
            key_phrases.append(sentence)

    return key_phrases


def generate_title(transcription: str, max_length: int = 60) -> str:
    """
    Generate a title from the transcription.

    Uses the beginning of the transcription to create a concise title,
    as speakers typically introduce their topic early.

    Args:
        transcription: The full transcription text
        max_length: Maximum length of the title

    Returns:
        A generated title string
    """
    # Clean the transcription
    text = transcription.strip()

    if not text:
        return "Untitled Video"

    # Get the first sentence or meaningful chunk
    first_sentence = re.split(r'[.!?]', text)[0].strip()

    # If first sentence is too long, truncate intelligently
    if len(first_sentence) > max_length:
        # Try to cut at a word boundary
        words = first_sentence[:max_length].split()
        if len(words) > 1:
            words = words[:-1]  # Remove potentially cut-off word
        first_sentence = ' '.join(words)

    # Capitalize for title case
    title = first_sentence.title()

    # Remove common filler words at the start
    filler_starters = ['so ', 'well ', 'okay ', 'um ', 'uh ', 'like ']
    title_lower = title.lower()
    for filler in filler_starters:
        if title_lower.startswith(filler):
            title = title[len(filler):].strip().capitalize()
            break

    return title if title else "Untitled Video"


def generate_description(transcription: str, max_sentences: int = 2) -> str:
    """
    Generate a 2-sentence description from the transcription.

    Args:
        transcription: The full transcription text
        max_sentences: Maximum number of sentences for the description

    Returns:
        A generated description string
    """
    # Clean the transcription
    text = transcription.strip()

    if not text:
        return "A video presentation."

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter and clean sentences
    clean_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        # Skip very short sentences or those with too many filler words
        if len(sentence) > 20:
            clean_sentences.append(sentence)
            if len(clean_sentences) >= max_sentences:
                break

    if not clean_sentences:
        # Fallback: use first chunk of text
        words = text.split()[:30]
        return ' '.join(words) + '...'

    # Join sentences for description
    description = ' '.join(clean_sentences)

    # Ensure it ends with proper punctuation
    if not description.endswith(('.', '!', '?')):
        description += '.'

    return description


def generate_content_metadata(
    transcription: str,
    output_path: Path
) -> dict[str, str]:
    """
    Generate title and description from transcription and save to file.

    Args:
        transcription: The full transcription text
        output_path: Path where metadata will be saved

    Returns:
        Dictionary with 'title' and 'description' keys
    """
    console.print("[blue]Generating title and description...[/blue]")

    title = generate_title(transcription)
    description = generate_description(transcription)

    metadata = {
        "title": title,
        "description": description,
    }

    # Save metadata to JSON file
    metadata_file = output_path / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    console.print(f"[green]✓ Generated title:[/green] {title}")
    console.print(f"[green]✓ Generated description:[/green] {description}")
    console.print(f"[dim]Metadata saved to: {metadata_file}[/dim]")

    return metadata
