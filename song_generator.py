#!/usr/bin/env python3
"""
Song Generator using MiniMax API

Features:
- Generates lyrics from a prompt or uses custom lyrics
- Creates songs with optional cover audio reference
- Supports instrumental mode
- Multiple output formats (MP3, WAV, PCM)
- Lyrics editing and optimization
- Auto-loads .env file for API key
"""

import os
import requests
import argparse
import base64
import time

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from utils import resolve_api_key, sanitize_filename


def generate_lyrics(
    api_key: str,
    prompt: str,
    mode: str = "write_full_song",
    existing_lyrics: str = None,
    title: str = None,
) -> dict:
    """
    Generates or edits lyrics based on the prompt.

    Returns dict with: lyrics, song_title, style_tags
    """
    url = "https://api.minimax.io/v1/lyrics_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "lyrics-3",
        "prompt": prompt,
        "mode": mode,
    }
    if existing_lyrics:
        payload["lyrics"] = existing_lyrics
    if title:
        payload["title"] = title

    print("Generating lyrics...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    return {
        "lyrics": data["lyrics"],
        "song_title": data.get("song_title", ""),
        "style_tags": data.get("style_tags", ""),
    }


def generate_music(
    api_key: str,
    prompt: str,
    model: str = "music-2.6",
    lyrics: str = None,
    instrumental: bool = False,
    audio_url: str = None,
    audio_base64: str = None,
    output_format: str = "url",
    sample_rate: int = 44100,
    bitrate: int = 256000,
    audio_format: str = "mp3",
    lyrics_optimizer: bool = False,
    stream: bool = False,
) -> dict:
    """
    Creates music track using the MiniMax API.

    Returns dict with: music_url (if url format) or audio_hex, status, extra_info
    """
    url = "https://api.minimax.io/v1/music_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "output_format": output_format,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
        },
        "stream": stream,
    }

    # Add lyrics or instrumental mode
    if instrumental:
        payload["is_instrumental"] = True
    elif lyrics:
        payload["lyrics"] = lyrics
    elif lyrics_optimizer:
        payload["lyrics_optimizer"] = True

    # Add cover audio if provided
    if audio_url:
        payload["audio_url"] = audio_url
    if audio_base64:
        payload["audio_base64"] = audio_base64

    print(f"Generating music (model: {model})...")
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    response.raise_for_status()
    data = response.json()

    result = {
        "status": data.get("data", {}).get("status"),
        "extra_info": data.get("extra_info", {}),
    }

    if output_format == "url":
        music_url = data.get("data", {}).get("audio")
        result["music_url"] = music_url
    else:
        result["audio_hex"] = data.get("data", {}).get("audio_hex", "")

    return result


def download_file(url: str, filepath: str) -> None:
    """Downloads a file from a URL."""
    response = requests.get(url, timeout=600)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(response.content)


def read_file(filepath: str) -> str:
    """Reads text file content."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(
        description="Song Generator using MiniMax API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic song generation
  python song_generator.py "A joyful pop song about summer"

  # Instrumental track
  python song_generator.py "Relaxing lo-fi beat" --instrumental

  # With custom lyrics
  python song_generator.py "Epic rock ballad" --lyrics "Verse 1: Standing tall..."

  # Edit existing lyrics
  python song_generator.py "Make it more dramatic" --edit-lyrics lyrics.txt

  # Cover generation from audio URL
  python song_generator.py "Similar style to reference" --audio-url "https://..."

  # Use free model tier
  python song_generator.py "Simple acoustic tune" --model "music-2.6-free"

  # Custom output format
  python song_generator.py "Electronic dance track" --format wav --bitrate 320000

  # With title preservation
  python song_generator.py "Upbeat summer hit" --title "Sunshine Days"
        """,
    )

    # Required
    parser.add_argument("prompt", help="Description of the desired song (1-2000 chars)")

    # API options
    parser.add_argument(
        "--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env var)"
    )

    # Model selection
    parser.add_argument(
        "--model",
        default="music-2.6",
        choices=["music-2.6", "music-cover", "music-2.6-free", "music-cover-free"],
        help="Model to use (default: music-2.6)",
    )

    # Lyrics options (mutually exclusive)
    lyrics_group = parser.add_mutually_exclusive_group()
    lyrics_group.add_argument("--lyrics", help="Custom lyrics for the song")
    lyrics_group.add_argument("--lyrics-file", help="File containing custom lyrics")
    lyrics_group.add_argument(
        "--lyrics-optimizer",
        action="store_true",
        help="Auto-generate lyrics from prompt (no separate lyrics call)",
    )

    # Lyrics editing
    parser.add_argument("--edit-lyrics", help="Edit existing lyrics (filename or text)")
    parser.add_argument("--title", help="Preserve song title")

    # Cover audio
    cover_group = parser.add_argument_group("Cover audio (for music-cover model)")
    cover_group.add_argument(
        "--audio-url", help="URL of reference audio (6 sec - 6 min, max 50MB)"
    )
    cover_group.add_argument(
        "--audio-file", help="Local reference audio file for cover generation"
    )

    # Output options
    parser.add_argument("--output-dir", default="songs", help="Output directory")
    parser.add_argument(
        "--output-format",
        default="url",
        choices=["url", "hex"],
        help="Output format: url (download link) or hex (encoded audio)",
    )
    parser.add_argument(
        "--format",
        default="mp3",
        choices=["mp3", "wav", "pcm"],
        help="Audio format (default: mp3)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        help="Sample rate in Hz (default: 44100)",
    )
    parser.add_argument(
        "--bitrate", type=int, default=256000, help="Bitrate in bps (default: 256000)"
    )

    # Instrumental mode
    parser.add_argument(
        "--instrumental",
        action="store_true",
        help="Generate instrumental track (no vocals)",
    )

    # Streaming mode
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode (returns hex audio)",
    )

    args = parser.parse_args()

    # Resolve API key
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    # Prepare lyrics
    lyrics = None
    song_title = None
    style_tags = None

    if args.lyrics:
        lyrics = args.lyrics
    elif args.lyrics_file:
        lyrics = read_file(args.lyrics_file)
    elif args.edit_lyrics:
        # Check if it's a file or direct text
        if os.path.isfile(args.edit_lyrics):
            existing_lyrics = read_file(args.edit_lyrics)
        else:
            existing_lyrics = args.edit_lyrics
        result = generate_lyrics(
            api_key,
            args.prompt,
            mode="edit",
            existing_lyrics=existing_lyrics,
            title=args.title,
        )
        lyrics = result["lyrics"]
        song_title = result.get("song_title")
        style_tags = result.get("style_tags")
    elif not args.lyrics_optimizer and not args.instrumental:
        # Generate lyrics by default (unless optimizer or instrumental is used)
        result = generate_lyrics(api_key, args.prompt, title=args.title)
        lyrics = result["lyrics"]
        song_title = result.get("song_title")
        style_tags = result.get("style_tags")

    # Prepare cover audio
    audio_base64 = None
    if args.audio_file:
        with open(args.audio_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

    # Set output format for streaming
    output_format = "hex" if args.stream else args.output_format

    # Generate music
    music_result = generate_music(
        api_key=api_key,
        prompt=args.prompt,
        model=args.model,
        lyrics=lyrics,
        instrumental=args.instrumental,
        audio_url=args.audio_url,
        audio_base64=audio_base64,
        output_format=output_format,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
        audio_format=args.format,
        lyrics_optimizer=args.lyrics_optimizer,
        stream=args.stream,
    )

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    base_name = sanitize_filename(args.prompt)[:50]
    timestamp = int(time.time())
    song_dir = os.path.join(args.output_dir, f"{base_name}_{timestamp}")
    os.makedirs(song_dir, exist_ok=True)

    def format_duration(ms):
        """Format milliseconds to mm:ss format."""
        if ms is None:
            return "N/A"
        seconds = ms / 1000
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    # Save output
    try:
        if output_format == "url" and music_result.get("music_url"):
            mp3_path = os.path.join(song_dir, f"song.{args.format}")
            print(f"Saving audio to {mp3_path}...")
            download_file(music_result["music_url"], mp3_path)
        elif music_result.get("audio_hex"):
            hex_path = os.path.join(song_dir, f"song.{args.format}.hex")
            print(f"Saving hex audio to {hex_path}...")
            with open(hex_path, "w") as f:
                f.write(music_result["audio_hex"])

        # Save lyrics
        if lyrics:
            lyrics_path = os.path.join(song_dir, "lyrics.txt")
            print(f"Saving lyrics to {lyrics_path}...")
            with open(lyrics_path, "w", encoding="utf-8") as f:
                f.write(lyrics)

        # Save metadata
        meta_path = os.path.join(song_dir, "metadata.txt")
        print(f"Saving metadata to {meta_path}...")

        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Prompt: {args.prompt}\n")
            f.write(f"Model: {args.model}\n")
            if song_title:
                f.write(f"Title: {song_title}\n")
            if style_tags:
                f.write(f"Style: {style_tags}\n")
            f.write(f"Format: {args.format}\n")
            f.write(f"Sample Rate: {args.sample_rate}\n")
            f.write(f"Bitrate: {args.bitrate}\n")
            f.write(f"Instrumental: {args.instrumental}\n")
            if "extra_info" in music_result:
                ei = music_result["extra_info"]
                duration_ms = ei.get("music_duration")
                f.write(f"Duration: {format_duration(duration_ms)} ({duration_ms}ms)\n")
                f.write(f"Sample Rate: {ei.get('music_sample_rate', 'N/A')} Hz\n")
                f.write(f"Channels: {ei.get('music_channel', 'N/A')}\n")
                f.write(f"Bitrate: {ei.get('bitrate', 'N/A')} bps\n")
                f.write(f"Size: {ei.get('music_size', 'N/A')} bytes\n")

        # Print summary with duration
        duration_ms = music_result.get("extra_info", {}).get("music_duration")
        duration_str = format_duration(duration_ms)
        print(f"\nDone! Files saved to: {song_dir}/")
        print(f"   Duration: {duration_str}")
        return 0

    except requests.HTTPError as e:
        print(f"API error: {e}")
        print(f"   Response: {e.response.text}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
