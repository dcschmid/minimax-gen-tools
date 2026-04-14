#!/usr/bin/env python3
"""
Image Generator using MiniMax API

Features:
- Text-to-Image generation
- Image-to-Image generation with reference images
- Multiple aspect ratios
- Base64 or URL output
- Auto-loads .env file for API key
- Presets for Knowledge Image (anime 1980s) and Podcast (documentary style)
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


KNOWLEDGE_IMAGE_STYLE = """Japanese Anime Style from the 1980s with bold outlines, slightly exaggerated facial features, and cel-shaded shadows typical of hand-drawn animation. Vibrant but slightly desaturated colors. NO TEXT ON THE IMAGE. Single scene only, not a series. Creative but consistent anime aesthetic, varied scenes matching the musical theme. Refined graphic-novel realism, clearly visible line work, subtle cross-hatching, illustrated texture on skin and fabric. No photographic elements, no camera effects, no depth falloff."""

PODCAST_HOST_DANIEL = "Daniel, European type, mid-40s, shoulder-length dark hair neatly groomed, well-groomed beard, glasses, calm intelligent expression, grounded confident presence, seated at broadcast table"

PODCAST_HOST_ANNABELLE = "Annabelle, European/Latin type, early-40s, shoulder-length brown hair, subtle theme-appropriate makeup, warm attentive expression, open emotionally intelligent presence, seated at broadcast table"

PODCAST_STYLE = """hand-drawn illustrated documentary style, high-quality printed editorial illustration, clearly visible line work around faces, hair, clothing and objects, subtle cross-hatching and restrained paper-like grain, illustrated skin texture (no photographic skin blending), illustrated fabric texture with simplified folds and weight, lighting interpreted through drawing not camera optics, graphic-novel line emphasis, balanced contrast between figure and background. NO TEXT ON IMAGE. Single authentic moment captured mid-conversation, not staged, not symbolic."""


def build_knowledge_prompt(topic: str) -> str:
    return f"""{topic}. Style: {KNOWLEDGE_IMAGE_STYLE}"""


def build_podcast_prompt(theme: str) -> str:
    return f"""A refined graphic-novel documentary style scene in a podcast/broadcast studio appropriate for {theme}. Two podcast hosts are seated side by side at a shared wooden broadcast table equipped with studio microphones, headphones and authentic studio elements. {PODCAST_HOST_DANIEL} and {PODCAST_HOST_ANNABELLE} are mid-conversation, clearly visible from frontal view, seated together, natural conversational smiles (subtle, asymmetrical), relaxed engaged expressions, mouths slightly open or mid-speech. Both fully contained within a 16:9 horizontal composition. Clothing derived from {theme}. Subtle studio status sign if plausible. No text on image. Style: {PODCAST_STYLE}"""


def generate_image(
    api_key: str,
    prompt: str,
    model: str = "image-01",
    aspect_ratio: str = "1:1",
    response_format: str = "base64",
    subject_reference: list = None,
) -> dict:
    """
    Generates an image using the MiniMax API.

    Args:
        api_key: MiniMax API key
        prompt: Text description of the desired image
        model: Model to use (default: image-01)
        aspect_ratio: Image aspect ratio (default: 1:1)
        response_format: Output format - "base64" or "url"
        subject_reference: Optional list of reference images for character consistency

    Returns dict with: images (list of base64 or URLs), model, prompt
    """
    url = "https://api.minimax.io/v1/image_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": response_format,
    }

    if subject_reference:
        payload["subject_reference"] = subject_reference

    print(f"Generating image (model: {model}, ratio: {aspect_ratio})...")
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    images = data.get("data", {}).get("image_base64") or data.get("data", {}).get(
        "image_urls", []
    )

    return {
        "images": images,
        "model": model,
        "prompt": prompt,
    }


def download_file(url: str, filepath: str) -> None:
    """Downloads a file from a URL."""
    response = requests.get(url, timeout=600)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(response.content)


def main():
    parser = argparse.ArgumentParser(
        description="Image Generator using MiniMax API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text-to-image generation
  python image_generator.py "A sunset over the ocean"

  # Square image
  python image_generator.py "A cat sitting on a windowsill" --aspect-ratio 1:1

  # Wide 16:9 image
  python image_generator.py "Landscape with mountains" --aspect-ratio 16:9

  # Portrait image
  python image_generator.py "Portrait of a woman" --aspect-ratio 3:4

  # Image-to-image with reference
  python image_generator.py "The same character in a forest" \\
    --reference-url "https://example.com/character.jpg"

  # Local reference image
  python image_generator.py "The same person at the beach" \\
    --reference-file "person.jpg"

  # Custom output directory
  python image_generator.py "Abstract art" --output-dir my_images

  # Save as URL format
  python image_generator.py "City skyline" --response-format url
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="Description of the desired image (1-2000 chars). Required unless --preset is used.",
    )

    preset_group = parser.add_argument_group("Presets (build prompt automatically)")
    preset_group.add_argument(
        "--preset",
        choices=["knowledge", "podcast"],
        help="Use a preset: 'knowledge' for anime 1980s music images, 'podcast' for documentary-style podcast hosts",
    )
    preset_group.add_argument(
        "--theme",
        help="Topic/theme for preset (e.g., 'From Soul to Modern Dance Music - 50 Tracks That Map the Journey')",
    )

    parser.add_argument(
        "--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env var)"
    )

    parser.add_argument(
        "--model", default="image-01", help="Model to use (default: image-01)"
    )

    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        choices=["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"],
        help="Image aspect ratio (default: 1:1)",
    )

    parser.add_argument(
        "--response-format",
        default="base64",
        choices=["base64", "url"],
        help="Output format - base64 (saves files) or url (downloads)",
    )

    ref_group = parser.add_argument_group("Reference image (for character consistency)")
    ref_group.add_argument("--reference-url", help="URL of reference image")
    ref_group.add_argument("--reference-file", help="Local reference image file")

    parser.add_argument("--output-dir", default="images", help="Output directory")
    parser.add_argument(
        "--output-name", help="Custom output filename (without extension)"
    )

    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided. Set MINIMAX_API_KEY environment variable")
        print("       or use --api-key argument.")
        return 1

    if args.preset:
        if not args.theme:
            print("Error: --theme is required when using --preset")
            return 1
        if args.preset == "knowledge":
            prompt = build_knowledge_prompt(args.theme)
            if args.aspect_ratio == "1:1":
                args.aspect_ratio = "3:2"
        elif args.preset == "podcast":
            prompt = build_podcast_prompt(args.theme)
            args.aspect_ratio = "16:9"
        print(f"Using preset '{args.preset}' with theme: {args.theme}")
    else:
        if not args.prompt:
            print("Error: prompt is required when not using --preset")
            return 1
        prompt = args.prompt

    subject_reference = None
    if args.reference_url or args.reference_file:
        ref_image = None
        if args.reference_url:
            ref_image = args.reference_url
        elif args.reference_file:
            with open(args.reference_file, "rb") as f:
                ref_image = base64.b64encode(f.read()).decode("utf-8")

        subject_reference = [
            {
                "type": "character",
                "image_file": ref_image,
            }
        ]

    try:
        result = generate_image(
            api_key=api_key,
            prompt=prompt,
            model=args.model,
            aspect_ratio=args.aspect_ratio,
            response_format=args.response_format,
            subject_reference=subject_reference,
        )

        os.makedirs(args.output_dir, exist_ok=True)

        if args.output_name:
            base_name = sanitize_filename(args.output_name)
        else:
            base_name = sanitize_filename(prompt)[:50]

        timestamp = int(time.time())
        output_path = os.path.join(args.output_dir, f"{base_name}_{timestamp}")
        os.makedirs(output_path, exist_ok=True)

        images = result["images"]

        for i, image_data in enumerate(images):
            if args.response_format == "base64":
                img_path = os.path.join(output_path, f"image_{i}.jpeg")
                print(f"Saving image {i} to {img_path}...")
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(image_data))
            else:
                img_path = os.path.join(output_path, f"image_{i}.jpeg")
                print(f"Downloading image {i} from {image_data}...")
                download_file(image_data, img_path)

        meta_path = os.path.join(output_path, "metadata.txt")
        print(f"Saving metadata to {meta_path}...")

        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\n")
            f.write(f"Model: {args.model}\n")
            f.write(f"Aspect Ratio: {args.aspect_ratio}\n")
            f.write(f"Response Format: {args.response_format}\n")
            f.write(f"Images Generated: {len(images)}\n")
            if args.preset:
                f.write(f"Preset: {args.preset}\n")
                f.write(f"Theme: {args.theme}\n")
            if args.reference_url:
                f.write(f"Reference URL: {args.reference_url}\n")
            if args.reference_file:
                f.write(f"Reference File: {args.reference_file}\n")

        print(f"\nDone! {len(images)} image(s) saved to: {output_path}/")
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
