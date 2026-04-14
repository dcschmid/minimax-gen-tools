# MiniMax Generator Tools

A collection of CLI tools for generating songs, images, videos, and speech using the [MiniMax API](https://platform.minimax.io).

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Song Generator](#song-generator)
- [Image Generator](#image-generator)
- [Video Generator](#video-generator)
- [Voice Clone](#voice-clone)
- [TTS Streaming](#tts-streaming)
- [TTS Async](#tts-async)
- [Podcast Generator](#podcast-generator)
- [API Reference](#api-reference)

---

## Overview

This project provides command-line tools for various MiniMax AI generation capabilities:

| Tool | Script | Description |
|------|--------|-------------|
| 🎵 Songs | `song_generator.py` | Generate complete songs with lyrics |
| 🎨 Images | `image_generator.py` | Text-to-Image and Image-to-Image |
| 🎬 Videos | `video_generator.py` | Text-to-Video and Image-to-Video |
| 🎙️ Voice Clone | `voice_clone.py` | Clone voice from audio samples |
| 🔊 TTS Streaming | `tts_stream.py` | Real-time WebSocket TTS |
| 📖 TTS Async | `tts_async.py` | Long-form text-to-speech |
| 🎙️ Podcast | `podcast_generator.py` | Multi-speaker podcast generation |

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file with your MiniMax API key:

```bash
echo "MINIMAX_API_KEY=your-api-key" > .env
```

Get your API key at [platform.minimax.io](https://platform.minimax.io/user-center/basic-information).

### 3. Run a Generator

```bash
# Generate a song
python song_generator.py "A joyful pop song about summer"

# Generate an image
python image_generator.py "A sunset over the ocean"

# Generate a podcast from script
python podcast_generator.py --script my_podcast.txt
```

---

## Song Generator

Generate complete songs with lyrics from text prompts.

### Basic Usage

```bash
# Text-to-music with auto-generated lyrics
python song_generator.py "A joyful pop song about summer"

# Instrumental track (no vocals)
python song_generator.py "Relaxing lo-fi beat" --instrumental

# Custom lyrics
python song_generator.py "Epic rock ballad" --lyrics "Verse 1: Standing tall..."

# Cover from audio URL
python song_generator.py "Similar vibe" --model music-cover \
  --audio-url "https://example.com/reference.mp3"
```

### Advanced Options

```bash
# Use free model tier
python song_generator.py "Simple tune" --model music-2.6-free

# WAV output with custom settings
python song_generator.py "Electronic track" --format wav --bitrate 320000

# Preserve song title
python song_generator.py "Hit song" --title "My Song Title"

# Streaming mode (returns hex audio)
python song_generator.py "Long ambient track" --stream
```

### Song Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Song description (1-2000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model: music-2.6, music-cover, music-2.6-free | `music-2.6` |
| `--lyrics` | Custom lyrics text | Auto-generate |
| `--lyrics-file` | File with custom lyrics | - |
| `--lyrics-optimizer` | Auto-generate lyrics (single call) | False |
| `--edit-lyrics` | Edit existing lyrics (file or text) | - |
| `--title` | Preserve song title | - |
| `--audio-url` | Reference audio URL for covers | - |
| `--audio-file` | Local reference audio file | - |
| `--instrumental` | Generate without vocals | False |
| `--format` | Audio format: mp3, wav, pcm | `mp3` |
| `--sample-rate` | Sample rate in Hz | `44100` |
| `--bitrate` | Bitrate in bps | `256000` |
| `--output-dir` | Output directory | `songs` |

---

## Image Generator

Generate images from text prompts or with reference images.

### Basic Usage

```bash
# Text-to-Image
python image_generator.py "A sunset over the ocean"

# Different aspect ratios
python image_generator.py "Mountain landscape" --aspect-ratio 16:9
python image_generator.py "Portrait" --aspect-ratio 3:4

# Image-to-Image with reference
python image_generator.py "The same character in a forest" \
  --reference-url "https://example.com/character.jpg"
```

### Image Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Image description (1-2000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `image-01` |
| `--aspect-ratio` | Ratio: 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9 | `1:1` |
| `--response-format` | Output: base64, url | `base64` |
| `--reference-url` | Reference image URL | - |
| `--reference-file` | Local reference image file | - |
| `--output-dir` | Output directory | `images` |
| `--output-name` | Custom output filename | - |

---

## Video Generator

Generate videos from text or images. Note: Most video models require `--first-frame`.

### Basic Usage

```bash
# Image-to-Video (default model requires first-frame)
python video_generator.py "The person starts dancing" \
  --first-frame "photo.jpg"

# Image-to-Video with URL
python video_generator.py "The person starts dancing" \
  --first-frame "https://example.com/photo.jpg"

# First-Last-Frame Video
python video_generator.py "A girl growing up" \
  --first-frame "child.jpg" --last-frame "adult.jpg"
```

### Video Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Video description (1-2000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `MiniMax-Hailuo-2.3-Fast` |
| `--duration` | Duration: 5 or 10 seconds | `6` |
| `--resolution` | Resolution: 512P, 768P, 1080P | `768P` |
| `--first-frame` | First frame image (URL or local file) | Required |
| `--last-frame` | Last frame image (URL or local file) | - |
| `--subject-reference` | Subject reference image | - |
| `--poll-interval` | Poll interval in seconds | `10` |
| `--output-dir` | Output directory | `videos` |

---

## Voice Clone

Clone a voice from an audio file to use with TTS.

### Basic Usage

```bash
# Clone voice from audio
python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice

# Clone with prompt audio for better quality
python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice \
  --prompt-audio sample.mp3 --prompt-text "This voice sounds natural."
```

### Use Cloned Voice in TTS

After cloning, use your custom voice_id with TTS scripts:

```bash
python tts_async.py "Hello world" --voice-id my_voice
python podcast_generator.py --script podcast.txt --voice-daniel my_voice
```

### Voice Clone Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source-audio` | Source audio (mp3, m4a, wav; 10s-5min, max 20MB) | Required |
| `--voice-id` | Custom voice ID to assign | Required |
| `--prompt-audio` | Optional prompt audio (<8s) for quality | - |
| `--prompt-text` | Text spoken in prompt audio | - |
| `--model` | Model: speech-2.8-hd, speech-02-hd | `speech-2.8-hd` |
| `--output-dir` | Output directory | `voices` |

---

## TTS Streaming

Real-time WebSocket-based text-to-speech synthesis.

### Basic Usage

```bash
# Basic TTS
python tts_stream.py "Hello world, this is a test."

# With custom voice
python tts_stream.py "Hello world" --voice-id "English_CalmWoman"

# Custom speed and pitch
python tts_stream.py "Hello world" --speed 1.2 --pitch 0
```

### List Available Voices

```bash
python tts_stream.py --list-voices
```

### TTS Streaming Options

| Option | Description | Default |
|--------|-------------|---------|
| `text` | Text to synthesize (1-10000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model: speech-2.8-hd, speech-2.6-hd, speech-02-hd, etc. | `speech-2.8-hd` |
| `--voice-id` | Voice ID | `English_expressive_narrator` |
| `--speed` | Speech speed | `1.0` |
| `--pitch` | Pitch adjustment | `0` |
| `--vol` | Volume | `1.0` |
| `--sample-rate` | Sample rate in Hz | `32000` |
| `--bitrate` | Bitrate in bps | `128000` |
| `--format` | Audio format: mp3, wav, pcm | `mp3` |

---

## TTS Async

Asynchronous long-form text-to-speech for longer texts.

### Basic Usage

```bash
# Basic TTS
python tts_async.py "Hello world, this is a test."

# Long text from file
python tts_async.py --text-file mybook.txt

# With voice effects
python tts_async.py "Hello world" --effect spacious_echo

# Custom voice settings
python tts_async.py "Hello world" \
  --voice-id "Chinese (Mandarin)_News_Anchor" \
  --speed 1.0 --pitch 1.5 --vol 1.2
```

### Voice Effects

Available effects: `spacious_echo`, `small_room`, `large_hall`, `ethereal_echo`, `resonant_hall`

### TTS Async Options

| Option | Description | Default |
|--------|-------------|---------|
| `text` | Text to synthesize (or use --text-file) | - |
| `--text-file` | Text file for long content | - |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `speech-2.8-hd` |
| `--voice-id` | Voice ID | `English_expressive_narrator` |
| `--language-boost` | Language: auto, Chinese, English, etc. | `auto` |
| `--speed` | Speech speed | `1.0` |
| `--pitch` | Pitch | `1.0` |
| `--vol` | Volume | `1.0` |
| `--effect` | Voice effect | - |
| `--sample-rate` | Sample rate in Hz | `32000` |
| `--bitrate` | Bitrate in bps | `128000` |
| `--format` | Audio format: mp3, wav, pcm | `mp3` |
| `--channel` | Channels: 1 (mono), 2 (stereo) | `2` |

---

## Podcast Generator

Generate multi-speaker podcasts from script files with natural-sounding dialogue.

### Basic Usage

```bash
# Generate podcast from script
python podcast_generator.py --script podcast.txt
```

### Script Format

```text
daniel: Hello everyone, welcome to the show.
annabelle: Thanks daniel, it's great to be here.
daniel: Today we're discussing the evolution of music.
annabelle: That's right. From soul to modern dance music.
```

### Natural Dialogue Features

- **Different speech speeds** - Each speaker can have unique speed
- **Different pitch** - Voices are distinct and recognizable
- **Natural pauses** - Pauses between speakers for realistic flow
- **Micro-pauses** - Added in sentences for conversational feel

### Example with Custom Voices

```bash
python podcast_generator.py --script podcast.txt \
  --voice-daniel "English_magnetic_voiced_man" --speed-daniel 0.95 \
  --voice-annabelle "English_radiant_girl" --speed-annabelle 1.0
```

### Pitch for Voice Distinction

```bash
python podcast_generator.py --script podcast.txt \
  --pitch-daniel 1.0 --pitch-annabelle 1.1
```

### List Recommended Voices

```bash
python podcast_generator.py --list-voices
```

### Podcast Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `--script` | Podcast script file (txt or md) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `speech-2.8-hd` |
| `--voice-daniel` | Voice for Daniel | `English_magnetic_voiced_man` |
| `--voice-annabelle` | Voice for Annabelle | `English_radiant_girl` |
| `--speed-daniel` | Speech speed for Daniel | `0.95` |
| `--speed-annabelle` | Speech speed for Annabelle | `1.0` |
| `--pitch-daniel` | Pitch for Daniel | `1.0` |
| `--pitch-annabelle` | Pitch for Annabelle | `1.1` |
| `--sample-rate` | Sample rate in Hz | `32000` |
| `--bitrate` | Bitrate in bps | `128000` |
| `--format` | Audio format: mp3, wav | `mp3` |
| `--output-dir` | Output directory | `podcasts` |
| `--list-voices` | List recommended voices | - |

---

## Output Structure

Generated files are saved to `<output-dir>/<name>_<timestamp>/`:

```
songs/A_joyful_pop_song_1744500000/
├── song.mp3          # Generated audio file
├── lyrics.txt        # Song lyrics (songs only)
├── metadata.txt      # Generation details
└── ...

podcasts/my_podcast_1744500000/
├── my_podcast.mp3    # Generated podcast
├── my_podcast_metadata.txt
└── my_podcast_script.txt  # Original script
```

---

## API Reference

Official MiniMax API documentation:

- [Music Generation](https://platform.minimax.io/docs/guides/music-generation)
- [Lyrics Generation](https://platform.minimax.io/docs/guides/lyrics-generation)
- [Image Generation](https://platform.minimax.io/docs/guides/image-generation)
- [Video Generation](https://platform.minimax.io/docs/guides/video-generation)
- [Voice Clone](https://platform.minimax.io/docs/guides/speech-voice-clone)
- [TTS WebSocket](https://platform.minimax.io/docs/guides/speech-t2a-websocket)
- [TTS Async](https://platform.minimax.io/docs/guides/speech-t2a-async)
- [System Voice IDs](https://platform.minimax.io/docs/faq/system-voice-id)

---

## Models Summary

### Music Models

| Model | Description |
|-------|-------------|
| `music-2.6` | Standard text-to-music (recommended, paid) |
| `music-cover` | Cover generation from reference audio (paid) |
| `music-2.6-free` | Free text-to-music |
| `music-cover-free` | Free cover generation |

### Speech Models

| Model | Description |
|-------|-------------|
| `speech-2.8-hd` | Best quality, tonal nuances |
| `speech-2.6-hd` | Ultra-low latency, enhanced naturalness |
| `speech-2.8-turbo` | Faster, more affordable |
| `speech-2.6-turbo` | Fast, ideal for agents |
| `speech-02-hd` | Superior rhythm and stability |
| `speech-02-turbo` | Enhanced multilingual capabilities |

### Video Models

| Model | Description |
|-------|-------------|
| `MiniMax-Hailuo-2.3-Fast` | Fast video generation (requires --first-frame) |

---

## Troubleshooting

### Video Generation

**"Token plan not support model"**
- Your current plan may not include video generation
- Check your plan at [platform.minimax.io/subscribe/token-plan](https://platform.minimax.io/subscribe/token-plan)
- Most video models require `--first-frame` image input

### TTS Issues

**"Empty status" in polling**
- Check your API key is valid
- Ensure your plan includes TTS services

### Audio Playback

For streaming TTS, install mpv player for real-time audio playback.
