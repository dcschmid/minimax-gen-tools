#!/usr/bin/env python3
"""
Video Generator using MiniMax API

Features:
- Text-to-Video generation
- Image-to-Video generation
- First-Last-Frame-to-Video generation
- Subject Reference Video (character consistency)
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


def create_video_task(
    api_key: str,
    prompt: str,
    model: str = "MiniMax-Hailuo-2.3",
    duration: int = 6,
    resolution: str = "1080P",
    first_frame_image: str = None,
    last_frame_image: str = None,
    subject_reference: list = None,
) -> str:
    """
    Creates a video generation task and returns task_id.

    Returns str: task_id
    """
    url = "https://api.minimax.io/v1/video_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "model": model,
        "duration": duration,
        "resolution": resolution,
    }

    if first_frame_image:
        payload["first_frame_image"] = first_frame_image
    if last_frame_image:
        payload["last_frame_image"] = last_frame_image
    if subject_reference:
        payload["subject_reference"] = subject_reference

    print(f"Creating video task (model: {model}, duration: {duration}s)...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response_json = response.json()
    print(f"  Response: {response_json}")

    base_resp = response_json.get("base_resp", {})
    if base_resp.get("status_code") != 0:
        status_msg = base_resp.get("status_msg", "Unknown error")
        raise Exception(f"API Error {base_resp.get('status_code')}: {status_msg}")

    response.raise_for_status()
    task_id = response_json.get("task_id")
    if not task_id:
        raise Exception(f"No task_id in response: {response_json}")
    return task_id


def query_task_status(api_key: str, task_id: str, poll_interval: int = 10) -> str:
    """
    Polls task status until success or failure.
    Returns file_id on success.
    """
    url = "https://api.minimax.io/v1/query/video_generation"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"task_id": task_id}

    print(f"Polling task status (interval: {poll_interval}s)...")
    while True:
        time.sleep(poll_interval)
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        response_json = response.json()

        status = response_json.get("status")
        print(f"  Raw response: {response_json}")

        if not status:
            base_resp = response_json.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                status_msg = base_resp.get("status_msg", "Unknown error")
                raise Exception(
                    f"API Error {base_resp.get('status_code')}: {status_msg}"
                )
            print("  Empty status, retrying...")
            continue

        print(f"  Status: {status}")

        if status == "Success":
            return response_json.get("file_id")
        elif status == "Fail":
            raise Exception(
                f"Video generation failed: {response_json.get('error_message', 'Unknown error')}"
            )


def fetch_video(api_key: str, file_id: str, output_path: str) -> None:
    """
    Fetches video from file_id and saves to output_path.
    """
    url = "https://api.minimax.io/v1/files/retrieve"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"file_id": file_id}

    print(f"Fetching video (file_id: {file_id})...")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    download_url = response.json()["file"]["download_url"]

    response = requests.get(download_url, timeout=600)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Video saved to: {output_path}")


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


def load_image(image_source: str) -> str:
    """
    Loads image from URL or local file.
    Returns base64 encoded string for local files, URL string otherwise.
    """
    if image_source.startswith("http://") or image_source.startswith("https://"):
        return image_source
    elif os.path.isfile(image_source):
        with open(image_source, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    else:
        raise ValueError(f"Invalid image source: {image_source}")


def main():
    parser = argparse.ArgumentParser(
        description="Video Generator using MiniMax API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Image-to-Video (default model requires first-frame image)
  python video_generator.py "The person starts dancing" --first-frame "photo.jpg"

  # Image-to-Video with URL
  python video_generator.py "The person starts dancing" \\
    --first-frame "https://example.com/photo.jpg"

  # First-Last-Frame Video
  python video_generator.py "A girl growing up" \\
    --first-frame "child.jpg" --last-frame "adult.jpg"

  # Subject Reference (character consistency)
  python video_generator.py "The model walking in a historic alleyway" \\
    --first-frame "photo.jpg" --subject-reference "face_photo.jpg"

  # Custom duration
  python video_generator.py "Cinematic drone shot" --duration 10
        """,
    )

    parser.add_argument(
        "prompt", help="Description of the desired video (1-2000 chars)"
    )

    parser.add_argument(
        "--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env var)"
    )

    parser.add_argument(
        "--model",
        default="MiniMax-Hailuo-2.3-Fast",
        help="Model to use (default: MiniMax-Hailuo-2.3-Fast, requires --first-frame)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=6,
        choices=[5, 10],
        help="Video duration in seconds (default: 6)",
    )

    parser.add_argument(
        "--resolution",
        default="768P",
        choices=["512P", "768P", "1080P"],
        help="Video resolution (default: 768P)",
    )

    parser.add_argument("--first-frame", help="First frame image (URL or local file)")

    parser.add_argument("--last-frame", help="Last frame image (URL or local file)")

    parser.add_argument(
        "--subject-reference", help="Subject reference image for character consistency"
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Poll interval in seconds (default: 10)",
    )

    parser.add_argument("--output-dir", default="videos", help="Output directory")
    parser.add_argument(
        "--output-name", help="Custom output filename (without extension)"
    )

    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    first_frame_image = None
    last_frame_image = None
    subject_reference = None

    if args.first_frame:
        first_frame_image = load_image(args.first_frame)

    if args.last_frame:
        last_frame_image = load_image(args.last_frame)

    if args.subject_reference:
        subject_reference = [
            {
                "type": "character",
                "image": [load_image(args.subject_reference)],
            }
        ]

    os.makedirs(args.output_dir, exist_ok=True)

    if args.output_name:
        base_name = sanitize_filename(args.output_name)
    else:
        base_name = sanitize_filename(args.prompt)[:50]

    timestamp = int(time.time())
    output_dir = os.path.join(args.output_dir, f"{base_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(output_dir, "video.mp4")

    try:
        task_id = create_video_task(
            api_key=api_key,
            prompt=args.prompt,
            model=args.model,
            duration=args.duration,
            resolution=args.resolution,
            first_frame_image=first_frame_image,
            last_frame_image=last_frame_image,
            subject_reference=subject_reference,
        )
        print(f"Task ID: {task_id}")

        file_id = query_task_status(api_key, task_id, args.poll_interval)
        print(f"File ID: {file_id}")

        fetch_video(api_key, file_id, video_path)

        meta_path = os.path.join(output_dir, "metadata.txt")
        print(f"Saving metadata to {meta_path}...")

        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Prompt: {args.prompt}\n")
            f.write(f"Model: {args.model}\n")
            f.write(f"Duration: {args.duration}s\n")
            f.write(f"Resolution: {args.resolution}\n")
            f.write(f"Task ID: {task_id}\n")
            f.write(f"File ID: {file_id}\n")
            if args.first_frame:
                f.write(f"First Frame: {args.first_frame}\n")
            if args.last_frame:
                f.write(f"Last Frame: {args.last_frame}\n")
            if args.subject_reference:
                f.write(f"Subject Reference: {args.subject_reference}\n")

        print(f"\nDone! Video saved to: {video_path}")
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
