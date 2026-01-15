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
    duration: float = 5.0
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

        # Create a semi-transparent overlay for better text visibility
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw a gradient-like overlay at the bottom for text
        gradient_height = video_height // 3
        for i in range(gradient_height):
            alpha = int(180 * (i / gradient_height))  # Gradient from 0 to 180
            y = video_height - gradient_height + i
            draw.line([(0, y), (video_width, y)], fill=(0, 0, 0, alpha))

        # Composite the overlay
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fallback to default
        title_font_size = max(video_width // 20, 24)
        subtitle_font_size = max(video_width // 30, 16)

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

        # Calculate text positions (centered, near bottom)
        padding = 40

        # Title position
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (video_width - title_width) // 2
        title_y = video_height - padding - subtitle_font_size - 20 - title_font_size

        # Subtitle position
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (video_width - subtitle_width) // 2
        subtitle_y = video_height - padding - subtitle_font_size

        # Draw text with shadow for better visibility
        shadow_offset = 2

        # Title shadow
        draw.text(
            (title_x + shadow_offset, title_y + shadow_offset),
            title,
            font=title_font,
            fill=(0, 0, 0, 200)
        )
        # Title
        draw.text(
            (title_x, title_y),
            title,
            font=title_font,
            fill=(255, 255, 255, 255)
        )

        # Subtitle shadow
        draw.text(
            (subtitle_x + shadow_offset, subtitle_y + shadow_offset),
            subtitle,
            font=subtitle_font,
            fill=(0, 0, 0, 200)
        )
        # Subtitle
        draw.text(
            (subtitle_x, subtitle_y),
            subtitle,
            font=subtitle_font,
            fill=(220, 220, 220, 255)
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
    thumbnail_duration: float = 5.0
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
            (s for s in probe['streams'] if s['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            raise ValueError("No video stream found in input video")

        width = int(video_stream['width'])
        height = int(video_stream['height'])

        # Get frame rate
        fps_parts = video_stream.get('r_frame_rate', '30/1').split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

        # Create video from thumbnail image
        thumbnail_video = output_path / "thumbnail_video.mp4"

        # Create a video from the static image
        (
            ffmpeg
            .input(str(thumbnail_path), loop=1, t=thumbnail_duration)
            .output(
                str(thumbnail_video),
                vcodec='libx264',
                pix_fmt='yuv420p',
                r=fps,
                t=thumbnail_duration,
                **{'c:a': 'aac'}  # Silent audio track
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Now concatenate thumbnail video with main video
        # Create a concat file
        concat_file = output_path / "concat_list.txt"
        concat_file.write_text(
            f"file '{thumbnail_video.absolute()}'\nfile '{video_path.absolute()}'"
        )

        # Concatenate using ffmpeg concat demuxer
        (
            ffmpeg
            .input(str(concat_file), f='concat', safe=0)
            .output(
                str(final_output),
                c='copy'
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
