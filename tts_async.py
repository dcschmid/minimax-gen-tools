#!/usr/bin/env python3
"""
Async Text-to-Speech using MiniMax API

Features:
- Long-form audio synthesis (up to 1M characters)
- Multiple voices and languages
- Adjustable speed, pitch, volume
- Voice effects
- Timestamp/subtitle support
- Auto-loads .env file for API key
"""

import os
import requests
import argparse
import time


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


def create_tts_task(
    api_key: str,
    text: str = None,
    text_file_id: str = None,
    voice_id: str = "English_expressive_narrator",
    model: str = "speech-2.8-hd",
    language_boost: str = "auto",
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: float = 1.0,
    sample_rate: int = 32000,
    bitrate: int = 128000,
    audio_format: str = "mp3",
    channel: int = 2,
    voice_modify: dict = None,
    pronunciation_dict: dict = None,
) -> str:
    """
    Creates an async TTS task and returns task_id.
    """
    url = "https://api.minimax.io/v1/t2a_async_v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": vol,
            "pitch": pitch,
        },
        "audio_setting": {
            "audio_sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
            "channel": channel,
        },
    }

    if text:
        payload["text"] = text
    if text_file_id:
        payload["text_file_id"] = text_file_id
    if language_boost:
        payload["language_boost"] = language_boost
    if voice_modify:
        payload["voice_modify"] = voice_modify
    if pronunciation_dict:
        payload["pronunciation_dict"] = pronunciation_dict

    print(f"Creating TTS task (model: {model}, voice: {voice_id})...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    task_id = response.json().get("task_id")
    return task_id


def query_task_status(api_key: str, task_id: str, poll_interval: int = 10) -> dict:
    """
    Polls task status until completion.
    Returns dict with status info including file_id on success.
    """
    url = f"https://api.minimax.io/v1/query/t2a_async_query_v2?task_id={task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"Polling task status (interval: {poll_interval}s)...")
    while True:
        time.sleep(poll_interval)
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        print(f"  Status: {status}")

        if status == "Success":
            return data
        elif status == "Fail":
            raise Exception(f"TTS failed: {data.get('error_message', 'Unknown error')}")


def download_audio(api_key: str, file_id: str, output_path: str) -> None:
    """Downloads the generated audio file."""
    url = f"https://api.minimax.io/v1/files/retrieve_content?file_id={file_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"Downloading audio (file_id: {file_id})...")
    response = requests.get(url, headers=headers, timeout=600)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Audio saved to: {output_path}")


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
        description="Async Text-to-Speech using MiniMax API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic TTS
  python tts_async.py "Hello world, this is a test."

  # With custom voice
  python tts_async.py "Hello world" --voice-id "English_CalmWoman"

  # Long text from file
  python tts_async.py --text-file mytext.txt

  # With voice effects
  python tts_async.py "Hello world" --effect spacious_echo

  # Custom speed and pitch
  python tts_async.py "Hello world" --speed 1.2 --pitch 2 --vol 1.5

  # Custom model
  python tts_async.py "Hello world" --model speech-02-turbo

Voice Effects: spacious_echo, small_room, large_hall, ethereal_echo, resonant_hall
        """,
    )

    parser.add_argument("text", nargs="?", help="Text to synthesize")

    parser.add_argument(
        "--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env var)"
    )

    parser.add_argument(
        "--text-file",
        help="Text file to synthesize (alternative to passing text directly)",
    )

    parser.add_argument(
        "--model",
        default="speech-2.8-hd",
        choices=MODELS,
        help="Model to use (default: speech-2.8-hd)",
    )

    parser.add_argument(
        "--voice-id",
        default="English_expressive_narrator",
        help="Voice ID (default: English_expressive_narrator)",
    )

    parser.add_argument(
        "--language-boost",
        default="auto",
        help="Language boost: auto, Chinese, English, etc. (default: auto)",
    )

    parser.add_argument(
        "--speed", type=float, default=1.0, help="Speech speed (default: 1.0)"
    )

    parser.add_argument("--vol", type=float, default=1.0, help="Volume (default: 1.0)")

    parser.add_argument("--pitch", type=float, default=1.0, help="Pitch (default: 1.0)")

    parser.add_argument(
        "--effect",
        help="Voice effect: spacious_echo, small_room, large_hall, ethereal_echo, resonant_hall",
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
        choices=["mp3", "wav", "pcm"],
        help="Audio format (default: mp3)",
    )

    parser.add_argument(
        "--channel",
        type=int,
        default=2,
        choices=[1, 2],
        help="Audio channels: 1 (mono) or 2 (stereo) (default: 2)",
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Poll interval in seconds (default: 10)",
    )

    parser.add_argument("--output-dir", default="speech", help="Output directory")
    parser.add_argument(
        "--output-name", help="Custom output filename (without extension)"
    )

    args = parser.parse_args()

    if not args.text and not args.text_file:
        print("Error: Either text or --text-file must be provided")
        return 1

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    text = args.text
    text_file_id = None

    if args.text_file:
        print(f"Reading text from {args.text_file}...")
        with open(args.text_file, "r", encoding="utf-8") as f:
            text = f.read()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.output_name:
        base_name = sanitize_filename(args.output_name)
    else:
        base_name = sanitize_filename(text[:30]) if text else "speech"

    timestamp = int(time.time())
    output_path = os.path.join(
        args.output_dir, f"{base_name}_{timestamp}.{args.format}"
    )

    voice_modify = None
    if args.effect:
        voice_modify = {
            "pitch": 0,
            "intensity": 0,
            "timbre": 0,
            "sound_effects": args.effect,
        }

    try:
        task_id = create_tts_task(
            api_key=api_key,
            text=text,
            text_file_id=text_file_id,
            voice_id=args.voice_id,
            model=args.model,
            language_boost=args.language_boost,
            speed=args.speed,
            vol=args.vol,
            pitch=args.pitch,
            sample_rate=args.sample_rate,
            bitrate=args.bitrate,
            audio_format=args.format,
            channel=args.channel,
            voice_modify=voice_modify,
        )
        print(f"Task ID: {task_id}")

        result = query_task_status(api_key, task_id, args.poll_interval)

        file_id = result.get("file_id")
        if not file_id:
            raise Exception("No file_id in response")

        download_audio(api_key, file_id, output_path)

        meta_path = output_path + ".metadata.txt"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Task ID: {task_id}\n")
            f.write(f"File ID: {file_id}\n")
            f.write(f"Model: {args.model}\n")
            f.write(f"Voice ID: {args.voice_id}\n")
            f.write(f"Speed: {args.speed}\n")
            f.write(f"Volume: {args.vol}\n")
            f.write(f"Pitch: {args.pitch}\n")
            f.write(f"Sample Rate: {args.sample_rate}\n")
            f.write(f"Bitrate: {args.bitrate}\n")
            f.write(f"Format: {args.format}\n")
            f.write(f"Channel: {args.channel}\n")
            if args.effect:
                f.write(f"Effect: {args.effect}\n")
            f.write(f"Text Length: {len(text)} chars\n")
            f.write(f"Output: {output_path}\n")

        print(f"\nDone! Audio saved to: {output_path}")
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
