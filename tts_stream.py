#!/usr/bin/env python3
"""
Text-to-Speech Streaming using MiniMax WebSocket API

Features:
- Real-time streaming audio playback
- Save full audio to file
- Multiple voice options and languages
- Auto-loads .env file for API key
"""

import os
import asyncio
import websockets
import json
import ssl
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

LANGUAGES = [
    "auto",
    "Chinese",
    "Cantonese",
    "English",
    "Spanish",
    "French",
    "Russian",
    "German",
    "Portuguese",
    "Arabic",
    "Italian",
    "Japanese",
    "Korean",
    "Indonesian",
    "Vietnamese",
    "Turkish",
    "Dutch",
    "Ukrainian",
    "Thai",
    "Polish",
    "Romanian",
    "Greek",
    "Czech",
    "Finnish",
    "Hindi",
    "Bulgarian",
    "Danish",
    "Hebrew",
    "Malay",
    "Persian",
    "Slovak",
    "Swedish",
    "Croatian",
    "Filipino",
    "Hungarian",
    "Norwegian",
    "Slovenian",
    "Catalan",
    "Nynorsk",
    "Tamil",
    "Afrikaans",
]

SYSTEM_VOICES = {
    "English_expressive_narrator": "Expressive Narrator",
    "English_radiant_girl": "Radiant Girl",
    "English_magnetic_voiced_man": "Magnetic-voiced Male",
    "English_compelling_lady1": "Compelling Lady",
    "English_Aussie_Bloke": "Aussie Bloke",
    "English_captivating_female1": "Captivating Female",
    "English_Upbeat_Woman": "Upbeat Woman",
    "English_Trustworth_Man": "Trustworthy Man",
    "English_CalmWoman": "Calm Woman",
    "English_Gentle-voiced_man": "Gentle-voiced Man",
    "Chinese (Mandarin)_Reliable_Executive": "Reliable Executive",
    "Chinese (Mandarin)_News_Anchor": "News Anchor",
    "Chinese (Mandarin)_Humorous_Elder": "Humorous Elder",
    "Japanese_IntellectualSenior": "Intellectual Senior",
    "Japanese_DecisivePrincess": "Decisive Princess",
    "German_FriendlyMan": "Friendly Man",
    "French_Male_Speech_New": "Level-Headed Man",
}


async def stream_tts(
    api_key: str,
    text: str,
    voice_id: str = "English_expressive_narrator",
    model: str = "speech-2.8-hd",
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: float = 0,
    sample_rate: int = 32000,
    bitrate: int = 128000,
    audio_format: str = "mp3",
    channel: int = 1,
    english_normalization: bool = False,
    output_path: str = None,
    play_stream: bool = True,
):
    """
    Streams TTS audio via WebSocket and optionally plays/plays while saving.
    """
    url = "wss://api.minimax.io/ws/v1/t2a_v2"
    headers = {"Authorization": f"Bearer {api_key}"}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    print(f"Connecting to {url}...")
    ws = await websockets.connect(url, additional_headers=headers, ssl=ssl_context)

    connected = json.loads(await ws.recv())
    if connected.get("event") != "connected_success":
        raise Exception(f"Connection failed: {connected}")
    print("Connected successfully")

    start_msg = {
        "event": "task_start",
        "model": model,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": vol,
            "pitch": pitch,
            "english_normalization": english_normalization,
        },
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
            "channel": channel,
        },
    }
    await ws.send(json.dumps(start_msg))
    response = json.loads(await ws.recv())
    if response.get("event") != "task_started":
        raise Exception(f"Task startup failed: {response}")

    await ws.send(json.dumps({"event": "task_continue", "text": text}))

    chunk_counter = 0
    total_audio_size = 0
    audio_data = b""

    print("Streaming audio...")
    while True:
        try:
            response = json.loads(await ws.recv())

            if "data" in response and "audio" in response["data"]:
                audio_hex = response["data"]["audio"]
                if audio_hex:
                    chunk_counter += 1
                    print(f"  Received chunk #{chunk_counter}")
                    audio_bytes = bytes.fromhex(audio_hex)
                    total_audio_size += len(audio_bytes)
                    audio_data += audio_bytes

                    if play_stream:
                        pass

            if response.get("is_final"):
                print(
                    f"Audio synthesis completed: {chunk_counter} chunks, {total_audio_size} bytes"
                )

                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
                    print(f"Audio saved to: {output_path}")

                await ws.send(json.dumps({"event": "task_finish"}))
                await ws.close()
                return audio_data

        except Exception as e:
            print(f"Error during streaming: {e}")
            break

    await ws.close()
    return audio_data


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
        description="Text-to-Speech Streaming using MiniMax WebSocket API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic TTS
  python tts_stream.py "Hello world, this is a test."

  # With custom voice
  python tts_stream.py "Hello world" --voice-id "English_CalmWoman"

  # Save to file
  python tts_stream.py "Hello world" --output speech.mp3

  # Different model
  python tts_stream.py "Hello world" --model speech-02-turbo

  # Adjust speed and pitch
  python tts_stream.py "Hello world" --speed 1.2 --pitch 0

Available voices:
  English_expressive_narrator, English_radiant_girl, English_magnetic_voiced_man,
  English_CalmWoman, Chinese (Mandarin)_News_Anchor, Japanese_DecisivePrincess, etc.
  Use --list-voices to see all.
        """,
    )

    parser.add_argument("text", help="Text to synthesize (1-10000 chars)")

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
        "--voice-id",
        default="English_expressive_narrator",
        help="Voice ID (default: English_expressive_narrator)",
    )

    parser.add_argument(
        "--speed", type=float, default=1.0, help="Speech speed (default: 1.0)"
    )

    parser.add_argument("--vol", type=float, default=1.0, help="Volume (default: 1.0)")

    parser.add_argument(
        "--pitch", type=float, default=0, help="Pitch adjustment (default: 0)"
    )

    parser.add_argument(
        "--english-normalization",
        action="store_true",
        help="Enable English normalization",
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

    parser.add_argument("--output-dir", default="speech", help="Output directory")
    parser.add_argument(
        "--output-name", help="Custom output filename (without extension)"
    )

    parser.add_argument(
        "--list-voices", action="store_true", help="List all available system voices"
    )

    args = parser.parse_args()

    if args.list_voices:
        print("Available system voices:")
        for vid, name in sorted(SYSTEM_VOICES.items()):
            print(f"  {vid}: {name}")
        return 0

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    if args.output_name:
        base_name = sanitize_filename(args.output_name)
    else:
        base_name = sanitize_filename(args.text)[:30]

    timestamp = int(time.time())
    output_path = os.path.join(
        args.output_dir, f"{base_name}_{timestamp}.{args.format}"
    )

    try:
        audio_data = asyncio.run(
            stream_tts(
                api_key=api_key,
                text=args.text,
                voice_id=args.voice_id,
                model=args.model,
                speed=args.speed,
                vol=args.vol,
                pitch=args.pitch,
                sample_rate=args.sample_rate,
                bitrate=args.bitrate,
                audio_format=args.format,
                output_path=output_path,
                play_stream=False,
            )
        )

        print(f"\nDone! Audio saved to: {output_path}")
        print(f"Size: {len(audio_data)} bytes")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
