"""Thumbnail processing module for adding overlay images with text to videos."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console

console = Console()


def create_thumbnail_with_text(
    thumbnail_path: Path,
    title: str,
    subtitle: str,
    output_path: Path,
    video_width: int,
    video_height: int,
    duration: float = 5.0,
) -> Path:
    """
    Create a thumbnail image with title and subtitle text overlay.

    Args:
        thumbnail_path: Path to the original thumbnail image
        title: Title text to overlay
        subtitle: Subtitle text to overlay
        output_path: Directory where processed thumbnail will be saved
        video_width: Width of the target video
        video_height: Height of the target video
        duration: How long to show the thumbnail (seconds)

    Returns:
        Path to the processed thumbnail image
    """
    console.print(f"[blue]Processing thumbnail:[/blue] {thumbnail_path}")

    processed_thumbnail = output_path / "thumbnail_with_text.png"

    try:
        # Open and resize thumbnail to match video dimensions
        img = Image.open(thumbnail_path)
        img = img.convert("RGBA")
        img = img.resize((video_width, video_height), Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fallback to default
        title_font_size = 56
        subtitle_font_size = 48

        try:
            # Try common system fonts
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/System/Library/Fonts/SFNSDisplay.ttf",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "C:/Windows/Fonts/arial.ttf",  # Windows
            ]

            title_font = None
            subtitle_font = None

            for font_path in font_paths:
                if Path(font_path).exists():
                    title_font = ImageFont.truetype(font_path, title_font_size)
                    subtitle_font = ImageFont.truetype(font_path, subtitle_font_size)
                    break

            if title_font is None:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()

        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Text positions: vertically centered, left-aligned
        padding_x = int(video_width * 0.05)  # 5% from left

        # Calculate total text block height for vertical centering
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_height = title_bbox[3] - title_bbox[1]
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
        gap = int(video_height * 0.01)
        total_text_height = title_height + gap + subtitle_height

        # Title position (one third from top, left-aligned)
        title_x = padding_x
        title_y = (video_height // 3) - (total_text_height // 2)

        # Subtitle position (below title)
        subtitle_x = padding_x
        subtitle_y = title_y + title_height + gap

        # Colors matching the example
        title_color = (0, 101, 163, 255)  # Dark blue
        subtitle_color = (80, 80, 80, 255)  # Dark gray

        # Draw title
        draw.text((title_x, title_y), title, font=title_font, fill=title_color)

        # Draw subtitle
        draw.text(
            (subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=subtitle_color
        )

        # Save the processed thumbnail
        img.save(processed_thumbnail, "PNG")

        console.print(f"[green]✓ Thumbnail processed:[/green] {processed_thumbnail}")

        return processed_thumbnail

    except Exception as e:
        console.print(f"[red]Error processing thumbnail:[/red] {e}")
        raise RuntimeError(f"Failed to process thumbnail: {e}")


def add_thumbnail_to_video(
    video_path: Path,
    thumbnail_path: Path,
    output_path: Path,
    thumbnail_duration: float = 5.0,
) -> Path:
    """
    Add a thumbnail image at the beginning of a video.

    Args:
        video_path: Path to the input video
        thumbnail_path: Path to the thumbnail image
        output_path: Directory where final video will be saved
        thumbnail_duration: Duration to show thumbnail (seconds)

    Returns:
        Path to the video with thumbnail prepended
    """
    import ffmpeg

    console.print("[blue]Adding thumbnail to video...[/blue]")

    final_output = output_path / "video_with_thumbnail.mp4"

    try:
        # Get video properties
        probe = ffmpeg.probe(str(video_path))
        video_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "video"), None
        )

        if not video_stream:
            raise ValueError("No video stream found in input video")

        # Get frame rate
        fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

        # Create video from thumbnail image with silent audio
        thumbnail_video = output_path / "thumbnail_video.mp4"

        # Create video from static image with silent audio track
        video_input = ffmpeg.input(str(thumbnail_path), loop=1, t=thumbnail_duration)
        audio_input = ffmpeg.input(
            "anullsrc=r=48000:cl=stereo", f="lavfi", t=thumbnail_duration
        )

        (
            ffmpeg.output(
                video_input,
                audio_input,
                str(thumbnail_video),
                vcodec="libx264",
                acodec="aac",
                pix_fmt="yuv420p",
                r=fps,
                shortest=None,
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Now concatenate thumbnail video with main video using filter_complex
        # This re-encodes to ensure compatibility between the two videos
        thumbnail_input = ffmpeg.input(str(thumbnail_video))
        main_input = ffmpeg.input(str(video_path))

        # Concat video streams separately from audio streams
        video_joined = ffmpeg.concat(
            thumbnail_input.video,
            main_input.video,
            v=1,
            a=0,
        )
        audio_joined = ffmpeg.concat(
            thumbnail_input.audio,
            main_input.audio,
            v=0,
            a=1,
        )

        (
            ffmpeg.output(
                video_joined,
                audio_joined,
                str(final_output),
                vcodec="libx264",
                acodec="aac",
                pix_fmt="yuv420p",
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        console.print(f"[green]✓ Thumbnail added to video:[/green] {final_output}")

        return final_output

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        console.print(f"[red]Error adding thumbnail:[/red] {error_msg}")
        raise RuntimeError(f"Failed to add thumbnail: {error_msg}")
