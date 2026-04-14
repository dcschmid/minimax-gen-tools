# Song, Image, Video & Speech Generator

Generate songs, images, videos, and speech using the MiniMax API.

## Features

### Song Generator (`song_generator.py`)
- **Lyrics generation** - Generate complete song lyrics from a text prompt
- **Lyrics editing** - Edit existing lyrics with new instructions
- **Custom lyrics** - Provide your own lyrics
- **Instrumental mode** - Generate music without vocals
- **Cover generation** - Create songs inspired by reference audio
- **Multiple formats** - MP3, WAV, PCM output
- **Custom audio settings** - Adjustable sample rate and bitrate
- **Lyrics optimizer** - Auto-generate lyrics in a single API call
- **Streaming mode** - Get hex-encoded audio in real-time

### Image Generator (`image_generator.py`)
- **Text-to-Image** - Generate images from detailed text prompts
- **Image-to-Image** - Generate images with reference character consistency
- **Multiple aspect ratios** - 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9
- **Character consistency** - Use reference images to maintain subject identity

### Video Generator (`video_generator.py`)
- **Text-to-Video** - Generate videos from text descriptions
- **Image-to-Video** - Animate static images into videos
- **First-Last-Frame Video** - Specify start and end frames
- **Subject Reference** - Maintain character consistency using face photos
- **Multiple resolutions** - 720P and 1080P output
- **Configurable duration** - 5 or 10 second clips

### Voice Clone (`voice_clone.py`)
- **Voice cloning** - Clone voice from audio file (10s-5min)
- **Enhanced quality** - Optional prompt audio for better results
- **Custom voice IDs** - Use cloned voices in TTS

### TTS Streaming (`tts_stream.py`)
- **WebSocket streaming** - Real-time audio synthesis
- **Multiple voices** - 300+ system voices across 40 languages
- **Speed/pitch control** - Adjust voice characteristics
- **Streaming playback** - Hear audio as it's generated

### TTS Async (`tts_async.py`)
- **Long-form synthesis** - Up to 1M characters per request
- **Voice effects** - Echo, room reverb, hall effects
- **Multiple formats** - MP3, WAV, PCM output
- **Timestamp support** - Accurate sentence-level timestamps

### Podcast Generator (`podcast_generator.py`)
- **Multi-speaker podcasts** - Generate podcasts with multiple hosts
- **Different voices** - Assign unique voices to each speaker
- **Script parsing** - Automatically parses conversation format
- **Combined output** - Single audio file with all segments

## Setup

```bash
pip install -r requirements.txt

# Create .env file with your API key
echo "MINIMAX_API_KEY=your-api-key" > .env
```

Get your API key at [platform.minimax.io](https://platform.minimax.io).

## Usage

### Basic song generation

```bash
python song_generator.py "A joyful pop song about summer"
```

### Instrumental track

```bash
python song_generator.py "Relaxing lo-fi beat" --instrumental
```

### Custom lyrics

```bash
python song_generator.py "Epic rock ballad" --lyrics "Verse 1: Standing tall..."
```

### Edit existing lyrics

```bash
python song_generator.py "Make it more dramatic" --edit-lyrics lyrics.txt
```

### Cover from audio URL

```bash
python song_generator.py "Similar vibe" --model music-cover --audio-url "https://example.com/reference.mp3"
```

### Cover from local audio file

```bash
python song_generator.py "Similar vibe" --model music-cover --audio-file mysong.mp3
```

### Auto-generate lyrics (single API call)

```bash
python song_generator.py "Upbeat summer hit" --lyrics-optimizer
```

### Use free model tier

```bash
python song_generator.py "Simple tune" --model music-2.6-free
```

### WAV output with custom settings

```bash
python song_generator.py "Electronic track" --format wav --bitrate 320000 --sample-rate 48000
```

### Preserve song title

```bash
python song_generator.py "Hit song" --title "My Song Title"
```

### Streaming mode (returns hex audio)

```bash
python song_generator.py "Long ambient track" --stream
```

---

## Image Generator

### Basic image generation

```bash
python image_generator.py "A sunset over the ocean"
```

### Different aspect ratios

```bash
python image_generator.py "Landscape with mountains" --aspect-ratio 16:9
python image_generator.py "Portrait of a woman" --aspect-ratio 3:4
python image_generator.py "City skyline" --aspect-ratio 21:9
```

### Image-to-Image with reference

```bash
python image_generator.py "The same character in a forest" --reference-url "https://example.com/character.jpg"
```

### Reference from local file

```bash
python image_generator.py "The same person at the beach" --reference-file person.jpg
```

### Save as URL format (downloads instead of base64)

```bash
python image_generator.py "Abstract art" --response-format url
```

### Custom output

```bash
python image_generator.py "Digital artwork" --output-dir my_images --output-name artwork1
```

---

## Video Generator

Note: Video generation is asynchronous. The script polls for completion automatically.

### Text-to-Video

```bash
python video_generator.py "A dancer doing flips on a beach"
```

### Image-to-Video

```bash
python video_generator.py "The person starts dancing" --first-frame "photo.jpg"
```

### First-Last-Frame Video

```bash
python video_generator.py "A girl growing up" --first-frame "child.jpg" --last-frame "adult.jpg"
```

### Subject Reference (character consistency)

```bash
python video_generator.py "The model walking in a historic alleyway" --subject-reference "face_photo.jpg"
```

### Different duration and resolution

```bash
python video_generator.py "Cinematic drone shot" --duration 10 --resolution 1080P
```

### Custom model

```bash
python video_generator.py "Subject video" --model S2V-01 --subject-reference "person.jpg"
```

---

## Voice Clone

### Clone voice from audio

```bash
python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice
```

### Clone with prompt audio for better quality

```bash
python voice_clone.py --source-audio myvoice.mp3 --voice-id my_voice \
  --prompt-audio sample.mp3 --prompt-text "This voice sounds natural."
```

### Use cloned voice in TTS

After cloning, use the voice_id with TTS scripts:
```bash
python tts_async.py "Hello world" --voice-id my_voice
```

---

## TTS Streaming

Real-time WebSocket-based text-to-speech.

### Basic TTS

```bash
python tts_stream.py "Hello world, this is a test."
```

### With custom voice

```bash
python tts_stream.py "Hello world" --voice-id "English_CalmWoman"
```

### List available voices

```bash
python tts_stream.py --list-voices
```

### Custom speed and model

```bash
python tts_stream.py "Hello world" --speed 1.2 --model speech-02-turbo
```

---

## TTS Async

Asynchronous long-form text-to-speech.

### Basic TTS

```bash
python tts_async.py "Hello world, this is a test."
```

### Long text from file

```bash
python tts_async.py --text-file mybook.txt
```

### With voice effects

```bash
python tts_async.py "Hello world" --effect spacious_echo
```

### Custom voice settings

```bash
python tts_async.py "Hello world" --voice-id "Chinese (Mandarin)_News_Anchor" \
  --speed 1.0 --pitch 1.5 --vol 1.2
```

---

## Podcast Generator

Generate multi-speaker podcasts from script files.

### Basic podcast

```bash
python podcast_generator.py --script podcast.txt
```

### With custom voices

```bash
python podcast_generator.py --script podcast.txt \
  --voice-daniel "English_magnetic_voiced_man" \
  --voice-annabelle "English_radiant_girl"
```

### Custom model and speed

```bash
python podcast_generator.py --script podcast.txt --model speech-02-turbo --speed 1.1
```

### Script Format

```text
daniel: Hello everyone, welcome to the show.
annabelle: Thanks daniel, it's great to be here.
daniel: Today we're discussing...
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Song description (1-2000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `music-2.6` |
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
| `--output-format` | Output type: url, hex | `url` |
| `--stream` | Enable streaming mode | False |
| `--output-dir` | Output directory | `songs` |

### Image Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Image description (1-2000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `image-01` |
| `--aspect-ratio` | Image ratio: 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9 | `1:1` |
| `--response-format` | Output format: base64, url | `base64` |
| `--reference-url` | Reference image URL for character | - |
| `--reference-file` | Local reference image file | - |
| `--output-dir` | Output directory | `images` |
| `--output-name` | Custom output filename | - |

### Video Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Video description (1-2000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `MiniMax-Hailuo-2.3` |
| `--duration` | Video duration: 5, 10 seconds | `6` |
| `--resolution` | Resolution: 720P, 1080P | `1080P` |
| `--first-frame` | First frame image (URL or local file) | - |
| `--last-frame` | Last frame image (URL or local file) | - |
| `--subject-reference` | Subject reference image for character | - |
| `--poll-interval` | Poll interval in seconds | `10` |
| `--output-dir` | Output directory | `videos` |
| `--output-name` | Custom output filename | - |

### Voice Clone Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source-audio` | Source audio file (mp3, m4a, wav; 10s-5min) | Required |
| `--voice-id` | Custom voice ID to assign | Required |
| `--prompt-audio` | Optional prompt audio (<8s) for quality | - |
| `--prompt-text` | Text spoken in prompt audio | - |
| `--model` | Model: speech-2.8-hd, speech-02-hd | `speech-2.8-hd` |
| `--test-text` | Preview text | Default sample |

### TTS Streaming Options

| Option | Description | Default |
|--------|-------------|---------|
| `text` | Text to synthesize (1-10000 chars) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `speech-2.8-hd` |
| `--voice-id` | Voice ID | `English_expressive_narrator` |
| `--speed` | Speech speed | `1.0` |
| `--pitch` | Pitch adjustment | `0` |
| `--vol` | Volume | `1.0` |
| `--sample-rate` | Sample rate in Hz | `32000` |
| `--bitrate` | Bitrate in bps | `128000` |
| `--format` | Audio format: mp3, wav, pcm | `mp3` |
| `--list-voices` | List available system voices | - |

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
| `--poll-interval` | Poll interval in seconds | `10` |

### Podcast Generator Options

| Option | Description | Default |
|--------|-------------|---------|
| `--script` | Podcast script file (txt or md) | Required |
| `--api-key` | MiniMax API key | Env: `MINIMAX_API_KEY` |
| `--model` | Model to use | `speech-2.8-hd` |
| `--voice-daniel` | Voice for Daniel | `English_magnetic_voiced_man` |
| `--voice-annabelle` | Voice for Annabelle | `English_radiant_girl` |
| `--speed` | Speech speed | `1.0` |
| `--sample-rate` | Sample rate in Hz | `32000` |
| `--bitrate` | Bitrate in bps | `128000` |
| `--format` | Audio format: mp3, wav | `mp3` |
| `--output-dir` | Output directory | `podcasts` |
| `--output-name` | Custom output filename | - |

## Models

| Model | Description |
|-------|-------------|
| `music-2.6` | Standard text-to-music (recommended, paid) |
| `music-cover` | Cover generation from reference audio (paid) |
| `music-2.6-free` | Free text-to-music |
| `music-cover-free` | Free cover generation |

## Output

Files are saved to `songs/<prompt>_<timestamp>/`:

```
songs/A_joyful_pop_song_about_s_1744500000/
├── song.mp3          # Generated audio file
├── lyrics.txt        # Song lyrics
└── metadata.txt      # Generation details
```

## API Reference

- [Music Generation](https://platform.minimax.io/docs/guides/music-generation)
- [Lyrics Generation](https://platform.minimax.io/docs/guides/lyrics-generation)
- [Image Generation](https://platform.minimax.io/docs/guides/image-generation)
- [Video Generation](https://platform.minimax.io/docs/guides/video-generation)
- [Voice Clone](https://platform.minimax.io/docs/guides/speech-voice-clone)
- [TTS WebSocket](https://platform.minimax.io/docs/guides/speech-t2a-websocket)
- [TTS Async](https://platform.minimax.io/docs/guides/speech-t2a-async)
- [System Voice IDs](https://platform.minimax.io/docs/faq/system-voice-id)
- [API Reference](https://platform.minimax.io/docs/api-reference/music-generation)
