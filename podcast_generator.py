#!/usr/bin/env python3
"""
Podcast Generator using MiniMax TTS API

Features:
- Generate podcast audio from script with multiple speakers
- Different voices for different speakers
- Automatic silence insertion between speakers
- Auto-loads .env file for API key
"""

import os
import re
import requests
import argparse
import time
import base64


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


MODELS = [
    "speech-2.8-hd",
    "speech-2.6-hd",
    "speech-2.8-turbo",
    "speech-2.6-turbo",
    "speech-02-hd",
    "speech-02-turbo",
]


def generate_tts(
    api_key: str,
    text: str,
    voice_id: str,
    model: str = "speech-2.8-hd",
    speed: float = 1.0,
    sample_rate: int = 32000,
    bitrate: int = 128000,
    audio_format: str = "mp3",
) -> bytes:
    """
    Generates TTS audio using the async API.
    Returns audio bytes.
    """
    url = "https://api.minimax.io/v1/t2a_async_v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": 1.0,
            "pitch": 1.0,
        },
        "audio_setting": {
            "audio_sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
            "channel": 1,
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    task_id = response.json().get("task_id")

    while True:
        time.sleep(5)
        status_url = (
            f"https://api.minimax.io/v1/query/t2a_async_query_v2?task_id={task_id}"
        )
        status_response = requests.get(status_url, headers=headers, timeout=30)
        status_data = status_response.json()

        if status_data.get("status") == "Success":
            file_id = status_data.get("file_id")
            break
        elif status_data.get("status") == "Fail":
            raise Exception(f"TTS failed: {status_data.get('error_message')}")

    download_url = f"https://api.minimax.io/v1/files/retrieve_content?file_id={file_id}"
    audio_response = requests.get(download_url, headers=headers, timeout=600)
    audio_response.raise_for_status()

    return audio_response.content


def parse_podcast_script(script_text: str) -> list:
    """
    Parses podcast script and returns list of (speaker, text) tuples.
    Supports formats like:
    - daniel: Hello world
    - [daniel] Hello world
    - Daniel: Hello world
    """
    segments = []
    lines = script_text.strip().split("\n")

    speaker_pattern = re.compile(
        r"^(daniel|annabelle|\[?(daniel|annabelle)\]?)\s*[:\-]\s*(.+)$", re.IGNORECASE
    )

    current_speaker = None
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = speaker_pattern.match(line)
        if match:
            if current_speaker and current_text:
                segments.append((current_speaker, " ".join(current_text)))

            speaker = match.group(1).lower()
            if speaker == "annabelle" or speaker == "daniel":
                current_speaker = speaker.capitalize()
            else:
                continue

            current_text = [match.group(3)]
        elif current_speaker:
            current_text.append(line)

    if current_speaker and current_text:
        segments.append((current_speaker, " ".join(current_text)))

    return segments


def create_silence(duration_ms: int = 500, sample_rate: int = 32000) -> bytes:
    """
    Creates a silent audio segment.
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    silence = bytes(num_samples)
    return silence


def combine_audio_segments(
    segments: list, output_path: str, sample_rate: int = 32000
) -> None:
    """
    Combines audio segments into a single file.
    For MP3, we write raw PCM and then convert, or just concatenate MP3s.
    """
    import subprocess

    temp_dir = os.path.join(os.path.dirname(output_path), "temp_segments")
    os.makedirs(temp_dir, exist_ok=True)

    segment_files = []
    for i, (speaker, audio_data) in enumerate(segments):
        seg_path = os.path.join(temp_dir, f"segment_{i:04d}.mp3")
        with open(seg_path, "wb") as f:
            f.write(audio_data)
        segment_files.append(seg_path)

    with open(output_path, "wb") as outfile:
        for seg_file in segment_files:
            with open(seg_file, "rb") as infile:
                outfile.write(infile.read())

    for seg_file in segment_files:
        os.remove(seg_file)
    os.rmdir(temp_dir)


def resolve_api_key(api_key: str) -> str:
    """Resolves API key from argument or environment variable."""
    if api_key:
        return api_key
    env_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("MINIMAX_API_TOKEN")
    if env_key:
        return env_key
    return None


def sanitize_filename(name: str) -> str:
    """Removes invalid characters from a filename."""
    keepcharacters = " ._-"
    return "".join(c for c in name if c.isalnum() or c in keepcharacters).strip()


def main():
    parser = argparse.ArgumentParser(
        description="Podcast Generator using MiniMax TTS API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate podcast from script file
  python podcast_generator.py --script podcast.txt

  # With custom voices
  python podcast_generator.py --script podcast.txt \\
    --voice-daniel "English_CalmWoman" \\
    --voice-annabelle "English_radiant_girl"

  # Custom model
  python podcast_generator.py --script podcast.txt --model speech-02-turbo

  # Save with custom name
  python podcast_generator.py --script podcast.txt --output my_podcast.mp3

Script Format:
  daniel: Hello everyone, welcome to the show.
  annabelle: Thanks daniel, it's great to be here.
  daniel: Today we're discussing...
        """,
    )

    parser.add_argument(
        "--script", required=True, help="Podcast script file (txt or md)"
    )

    parser.add_argument(
        "--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env var)"
    )

    parser.add_argument(
        "--model",
        default="speech-2.8-hd",
        choices=MODELS,
        help="Model to use (default: speech-2.8-hd)",
    )

    parser.add_argument(
        "--voice-daniel",
        default="English_magnetic_voiced_man",
        help="Voice for Daniel (default: English_magnetic_voiced_man)",
    )

    parser.add_argument(
        "--voice-annabelle",
        default="English_radiant_girl",
        help="Voice for Annabelle (default: English_radiant_girl)",
    )

    parser.add_argument(
        "--speed", type=float, default=1.0, help="Speech speed (default: 1.0)"
    )

    parser.add_argument(
        "--sample-rate",
        type=int,
        default=32000,
        help="Sample rate in Hz (default: 32000)",
    )

    parser.add_argument(
        "--bitrate", type=int, default=128000, help="Bitrate in bps (default: 128000)"
    )

    parser.add_argument(
        "--format",
        default="mp3",
        choices=["mp3", "wav"],
        help="Audio format (default: mp3)",
    )

    parser.add_argument("--output-dir", default="podcasts", help="Output directory")

    parser.add_argument(
        "--output-name", help="Custom output filename (without extension)"
    )

    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    print(f"Reading script from {args.script}...")
    with open(args.script, "r", encoding="utf-8") as f:
        script_text = f.read()

    segments = parse_podcast_script(script_text)
    if not segments:
        print("Error: No valid podcast segments found.")
        print("Format should be: speaker: text (e.g., daniel: Hello world)")
        return 1

    print(f"Found {len(segments)} segments")

    voice_map = {
        "Daniel": args.voice_daniel,
        "Annabelle": args.voice_annabelle,
    }

    os.makedirs(args.output_dir, exist_ok=True)

    if args.output_name:
        base_name = sanitize_filename(args.output_name)
    else:
        base_name = sanitize_filename(os.path.basename(args.script)).rsplit(".", 1)[0]

    timestamp = int(time.time())
    output_path = os.path.join(
        args.output_dir, f"{base_name}_{timestamp}.{args.format}"
    )

    print(f"Generating podcast audio...")
    print(
        f"Voice mapping: Daniel={args.voice_daniel}, Annabelle={args.voice_annabelle}"
    )

    audio_segments = []

    for i, (speaker, text) in enumerate(segments):
        voice_id = voice_map.get(speaker)
        if not voice_id:
            print(f"Warning: No voice configured for {speaker}, skipping...")
            continue

        print(f"  [{i + 1}/{len(segments)}] {speaker}: {text[:50]}...")

        try:
            audio_data = generate_tts(
                api_key=api_key,
                text=text,
                voice_id=voice_id,
                model=args.model,
                speed=args.speed,
                sample_rate=args.sample_rate,
                bitrate=args.bitrate,
                audio_format=args.format,
            )
            audio_segments.append((speaker, audio_data))

        except Exception as e:
            print(f"Error generating audio for segment {i + 1}: {e}")
            continue

    if not audio_segments:
        print("Error: No audio segments generated")
        return 1

    print(f"\nCombining {len(audio_segments)} segments...")
    combine_audio_segments(audio_segments, output_path, args.sample_rate)

    meta_path = output_path + ".metadata.txt"
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"Script: {args.script}\n")
        f.write(f"Model: {args.model}\n")
        f.write(f"Speed: {args.speed}\n")
        f.write(f"Daniel Voice: {args.voice_daniel}\n")
        f.write(f"Annabelle Voice: {args.voice_annabelle}\n")
        f.write(f"Segments: {len(audio_segments)}\n")
        f.write(f"Output: {output_path}\n")

    intro_path = os.path.join(args.output_dir, f"{base_name}_{timestamp}_script.txt")
    with open(intro_path, "w", encoding="utf-8") as f:
        for speaker, text in segments:
            f.write(f"{speaker}: {text}\n")

    print(f"\nDone! Podcast saved to: {output_path}")
    print(f"Script saved to: {intro_path}")
    return 0


if __name__ == "__main__":
    exit(main())
