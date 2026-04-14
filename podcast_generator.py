#!/usr/bin/env python3
"""
Podcast Generator using MiniMax TTS API

Features:
- Generate podcast audio from script with multiple speakers
- Different voices and speeds for different speakers
- Natural dialogue flow with pauses and variations
- Auto-loads .env file for API key
"""

import os
import re
import requests
import argparse
import time
import struct

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from utils import resolve_api_key, sanitize_filename, poll_task_status


MODELS = [
    "speech-2.8-hd",
    "speech-2.6-hd",
    "speech-2.8-turbo",
    "speech-2.6-turbo",
    "speech-02-hd",
    "speech-02-turbo",
]


SPEAKER_CONFIGS = {
    "Daniel": {
        "voice": "English_magnetic_voiced_man",
        "speed": 0.95,
        "pause_before_ms": 300,
        "pitch": 1.0,
    },
    "Annabelle": {
        "voice": "English_radiant_girl",
        "speed": 1.0,
        "pause_before_ms": 200,
        "pitch": 1.1,
    },
}


def generate_tts(
    api_key: str,
    text: str,
    voice_id: str,
    model: str = "speech-2.8-hd",
    speed: float = 1.0,
    pitch: float = 1.0,
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
            "pitch": int(pitch),
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

    status_url = f"https://api.minimax.io/v1/query/t2a_async_query_v2?task_id={task_id}"
    print(f"  Polling task status...")
    result = poll_task_status(
        api_key, status_url, poll_interval=5, max_retries=60, timeout_seconds=600
    )

    file_id = result.get("file_id")

    download_url = f"https://api.minimax.io/v1/files/retrieve_content?file_id={file_id}"
    audio_response = requests.get(download_url, headers=headers, timeout=600)
    audio_response.raise_for_status()

    return audio_response.content


def create_silence_mp3(duration_ms: int, sample_rate: int = 32000) -> bytes:
    """
    Creates a silent MP3 segment using pydub.
    Falls back to valid silent WAV if pydub unavailable.
    """
    try:
        from pydub import AudioSegment

        silence = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
        return silence.export(format="mp3").read()
    except ImportError:
        pass

    try:
        import io
        import wave

        num_samples = int(sample_rate * duration_ms / 1000)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(num_samples * 2))
        return buffer.getvalue()
    except ImportError:
        num_samples = int(sample_rate * duration_ms / 1000)
        return struct.pack("<" + "h" * num_samples, *([0] * num_samples))


def add_natural_pauses(text: str) -> str:
    """
    Adds natural pauses indicators to make speech more conversational.
    """
    text = re.sub(r",(\s+)", r", ... ", text)
    text = re.sub(r";(\s+)", r"; ... ", text)
    text = re.sub(r"\.(\s+[A-Z])", r". ... \1", text)
    text = re.sub(r"\?(\s+[A-Z])", r"? ... \1", text)
    text = re.sub(r"!(\s+[A-Z])", r"! ... \1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_podcast_script(script_text: str) -> list:
    """
    Parses podcast script and returns list of (speaker, text) tuples.
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
            if speaker in ("annabelle", "daniel"):
                current_speaker = speaker.capitalize()
            else:
                continue

            current_text = [match.group(3)]
        elif current_speaker:
            current_text.append(line)

    if current_speaker and current_text:
        segments.append((current_speaker, " ".join(current_text)))

    return segments


def combine_audio_with_pauses(
    audio_segments: list, output_path: str, sample_rate: int = 32000
) -> None:
    """
    Combines audio segments with natural pauses between speakers.
    """
    temp_dir = os.path.join(os.path.dirname(output_path) or ".", "temp_podcast")
    os.makedirs(temp_dir, exist_ok=True)

    segment_files = []
    pause_files = []

    try:
        for i, (speaker, audio_data) in enumerate(audio_segments):
            seg_path = os.path.join(temp_dir, f"segment_{i:04d}.mp3")
            with open(seg_path, "wb") as f:
                f.write(audio_data)
            segment_files.append(seg_path)

            if i < len(audio_segments) - 1:
                next_speaker = audio_segments[i + 1][0]
                current_config = SPEAKER_CONFIGS.get(speaker, {})
                next_config = SPEAKER_CONFIGS.get(next_speaker, {})
                pause_duration = max(
                    current_config.get("pause_before_ms", 300),
                    next_config.get("pause_before_ms", 200),
                )

                pause_path = os.path.join(temp_dir, f"pause_{i:04d}.mp3")
                pause_data = create_silence_mp3(pause_duration, sample_rate)
                with open(pause_path, "wb") as f:
                    f.write(pause_data)
                pause_files.append(pause_path)

        with open(output_path, "wb") as outfile:
            for i, seg_file in enumerate(segment_files):
                with open(seg_file, "rb") as infile:
                    outfile.write(infile.read())
                if i < len(pause_files):
                    with open(pause_files[i], "rb") as infile:
                        outfile.write(infile.read())
    finally:
        for seg_file in segment_files:
            if os.path.exists(seg_file):
                os.remove(seg_file)
        for pause_file in pause_files:
            if os.path.exists(pause_file):
                os.remove(pause_file)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Podcast Generator using MiniMax TTS API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate podcast from script file
  python podcast_generator.py --script podcast.txt

  # With different voices and speeds
  python podcast_generator.py --script podcast.txt \
    --voice-daniel "English_magnetic_voiced_man" --speed-daniel 0.95 \
    --voice-annabelle "English_radiant_girl" --speed-annabelle 1.0

  # List recommended voices
  python podcast_generator.py --list-voices

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
        default=SPEAKER_CONFIGS["Daniel"]["voice"],
        help=f"Voice for Daniel (default: {SPEAKER_CONFIGS['Daniel']['voice']})",
    )

    parser.add_argument(
        "--voice-annabelle",
        default=SPEAKER_CONFIGS["Annabelle"]["voice"],
        help=f"Voice for Annabelle (default: {SPEAKER_CONFIGS['Annabelle']['voice']})",
    )

    parser.add_argument(
        "--speed-daniel",
        type=float,
        default=SPEAKER_CONFIGS["Daniel"]["speed"],
        help="Speech speed for Daniel (default: 0.95)",
    )

    parser.add_argument(
        "--speed-annabelle",
        type=float,
        default=SPEAKER_CONFIGS["Annabelle"]["speed"],
        help="Speech speed for Annabelle (default: 1.0)",
    )

    parser.add_argument(
        "--pitch-daniel",
        type=float,
        default=SPEAKER_CONFIGS["Daniel"]["pitch"],
        help="Pitch for Daniel (default: 1.0)",
    )

    parser.add_argument(
        "--pitch-annabelle",
        type=float,
        default=SPEAKER_CONFIGS["Annabelle"]["pitch"],
        help="Pitch for Annabelle (default: 1.1)",
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

    parser.add_argument(
        "--list-voices", action="store_true", help="List recommended voices for podcast"
    )

    args = parser.parse_args()

    if args.list_voices:
        print("Recommended voices for podcasts:")
        print("\nMale voices (for Daniel):")
        for v in [
            "English_magnetic_voiced_man",
            "English_CalmWoman",
            "English_Gentle-voiced_man",
            "English_Trustworth_Man",
            "English_ManWithDeepVoice",
            "English_Deep-VoicedGentleman",
        ]:
            print(f"  - {v}")
        print("\nFemale voices (for Annabelle):")
        for v in [
            "English_radiant_girl",
            "English_captivating_female1",
            "English_Upbeat_Woman",
            "English_PlayfulGirl",
            "English_LovelyGirl",
            "English_Soft-spokenGirl",
        ]:
            print(f"  - {v}")
        return 0

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
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
        "Daniel": {
            "voice_id": args.voice_daniel,
            "speed": args.speed_daniel,
            "pitch": args.pitch_daniel,
        },
        "Annabelle": {
            "voice_id": args.voice_annabelle,
            "speed": args.speed_annabelle,
            "pitch": args.pitch_annabelle,
        },
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
    print(f"Voice mapping:")
    print(
        f"  Daniel: voice={args.voice_daniel}, speed={args.speed_daniel}, pitch={args.pitch_daniel}"
    )
    print(
        f"  Annabelle: voice={args.voice_annabelle}, speed={args.speed_annabelle}, pitch={args.pitch_annabelle}"
    )

    audio_segments = []

    for i, (speaker, text) in enumerate(segments):
        config = voice_map.get(speaker)
        if not config:
            print(f"Warning: No voice configured for {speaker}, skipping...")
            continue

        processed_text = add_natural_pauses(text)

        print(f"  [{i + 1}/{len(segments)}] {speaker}: {text[:50]}...")

        try:
            audio_data = generate_tts(
                api_key=api_key,
                text=processed_text,
                voice_id=config["voice_id"],
                model=args.model,
                speed=config["speed"],
                pitch=config["pitch"],
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

    print(f"\nCombining {len(audio_segments)} segments with natural pauses...")
    combine_audio_with_pauses(audio_segments, output_path, args.sample_rate)

    meta_path = output_path + ".metadata.txt"
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"Script: {args.script}\n")
        f.write(f"Model: {args.model}\n")
        f.write(
            f"Daniel: voice={args.voice_daniel}, speed={args.speed_daniel}, pitch={args.pitch_daniel}\n"
        )
        f.write(
            f"Annabelle: voice={args.voice_annabelle}, speed={args.speed_annabelle}, pitch={args.pitch_annabelle}\n"
        )
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
