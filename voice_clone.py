#!/usr/bin/env python3
"""
Voice Clone using MiniMax API

Features:
- Clone voice from audio file
- Optional prompt audio for enhanced quality
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


def upload_file(api_key: str, filepath: str, purpose: str) -> str:
    """
    Uploads a file and returns file_id.
    purpose: 'voice_clone' or 'prompt_audio'
    """
    url = "https://api.minimax.io/v1/files/upload"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"purpose": purpose}

    with open(filepath, "rb") as f:
        files = [("file", (os.path.basename(filepath), f))]
        response = requests.post(
            url, headers=headers, data=payload, files=files, timeout=60
        )
    response.raise_for_status()
    file_id = response.json().get("file", {}).get("file_id")
    print(f"Uploaded {filepath} -> file_id: {file_id}")
    return file_id


def clone_voice(
    api_key: str,
    file_id: str,
    voice_id: str,
    prompt_audio_id: str = None,
    prompt_text: str = None,
    model: str = "speech-2.8-hd",
    text: str = "A gentle breeze passes over the soft grass.",
) -> dict:
    """
    Clones a voice using the provided file_id.
    Returns the API response.
    """
    url = "https://api.minimax.io/v1/voice_clone"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "file_id": file_id,
        "voice_id": voice_id,
        "model": model,
        "text": text,
    }

    if prompt_audio_id and prompt_text:
        payload["clone_prompt"] = {
            "prompt_audio": prompt_audio_id,
            "prompt_text": prompt_text,
        }

    print(f"Cloning voice as '{voice_id}'...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def resolve_api_key(api_key: str) -> str:
    """Resolves API key from argument or environment variable."""
    if api_key:
        return api_key
    env_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("MINIMAX_API_TOKEN")
    if env_key:
        return env_key
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Voice Clone using MiniMax API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clone voice from audio file
  python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice

  # Clone with prompt audio for better quality
  python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice \\
    --prompt-audio sample.mp3 --prompt-text "This voice sounds natural."

  # With custom model
  python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice \\
    --model speech-02-hd
        """,
    )

    parser.add_argument(
        "--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env var)"
    )

    parser.add_argument(
        "--source-audio",
        required=True,
        help="Source audio file to clone (mp3, m4a, wav; 10s-5min, max 20MB)",
    )

    parser.add_argument(
        "--voice-id",
        required=True,
        help="Custom voice ID to assign to the cloned voice",
    )

    parser.add_argument(
        "--prompt-audio", help="Optional prompt audio for enhanced quality (<8s)"
    )

    parser.add_argument("--prompt-text", help="Text spoken in the prompt audio")

    parser.add_argument(
        "--model",
        default="speech-2.8-hd",
        choices=["speech-2.8-hd", "speech-02-hd"],
        help="Model to use (default: speech-2.8-hd)",
    )

    parser.add_argument(
        "--test-text",
        default="A gentle breeze passes over the soft grass, accompanied by the fresh scent and birdsong.",
        help="Test text for preview audio",
    )

    parser.add_argument("--output-dir", default="voices", help="Output directory")
    parser.add_argument(
        "--output-name", help="Custom output filename (without extension)"
    )

    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    try:
        print("Step 1: Uploading source audio...")
        source_file_id = upload_file(api_key, args.source_audio, "voice_clone")

        prompt_file_id = None
        if args.prompt_audio:
            print("Step 2: Uploading prompt audio...")
            prompt_file_id = upload_file(api_key, args.prompt_audio, "prompt_audio")

        print("Step 3: Cloning voice...")
        result = clone_voice(
            api_key=api_key,
            file_id=source_file_id,
            voice_id=args.voice_id,
            prompt_audio_id=prompt_file_id,
            prompt_text=args.prompt_text,
            model=args.model,
            text=args.test_text,
        )

        print(f"\nVoice cloned successfully!")
        print(f"Voice ID: {args.voice_id}")
        print(f"Use this voice_id in TTS scripts: --voice-id {args.voice_id}")
        print(f"\nAPI Response: {result}")

        voice_dir = os.path.join(args.output_dir, args.voice_id)
        os.makedirs(voice_dir, exist_ok=True)

        meta_path = os.path.join(voice_dir, "metadata.txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Voice ID: {args.voice_id}\n")
            f.write(f"Model: {args.model}\n")
            f.write(f"Source Audio: {args.source_audio}\n")
            f.write(f"Source File ID: {source_file_id}\n")
            if prompt_file_id:
                f.write(f"Prompt Audio: {args.prompt_audio}\n")
                f.write(f"Prompt Text: {args.prompt_text}\n")
            f.write(f"Test Text: {args.test_text}\n")

        print(f"\nMetadata saved to: {meta_path}")
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
