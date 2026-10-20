"""Provider-backed featured image generation."""
from __future__ import annotations

from urllib.parse import quote

import requests

POLLINATIONS_IMAGE_ENDPOINT = "https://image.pollinations.ai/prompt/"
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def generate_pollinations_image(topic: str, width: int = 768, height: int = 512) -> dict[str, str | int]:
    subject = " ".join(topic.split())
    if not subject or len(subject) > 500:
        raise ValueError("Enter an article topic of 1 to 500 characters.")
    if not 1 <= width <= 768 or not 1 <= height <= 768 or width * height > 768 * 768:
        raise ValueError("Image dimensions must be at most 768 by 768 pixels total area.")

    prompt = (
        f"Create a clear editorial illustration for a technical article about {subject}. "
        "Intended readers are working developers. Use accurate, relevant visual concepts, "
        "a clean professional style, and no text, labels, logos, or fabricated interface."
    )
    image_url = f"{POLLINATIONS_IMAGE_ENDPOINT}{quote(prompt, safe='')}"
    try:
        response = requests.get(
            image_url,
            params={"width": width, "height": height},
            timeout=(10, 75),
        )
    except requests.Timeout as exc:
        raise RuntimeError("Pollinations image generation timed out. Try again later or continue without an image.") from exc
    except requests.RequestException as exc:
        raise RuntimeError("Pollinations image generation is temporarily unavailable.") from exc

    if response.status_code == 429:
        raise RuntimeError("Pollinations rate limit reached. Wait before requesting another image.")
    if not response.ok:
        raise RuntimeError(f"Pollinations image generation failed with HTTP {response.status_code}.")
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if content_type != "image/jpeg" or not response.content.startswith(b"\xff\xd8\xff"):
        raise RuntimeError("Pollinations returned an invalid image response; no image was selected.")
    if not response.content or len(response.content) > MAX_IMAGE_BYTES:
        raise RuntimeError("Pollinations returned an empty or oversized image.")

    return {
        "image_url": response.url or image_url,
        "width": width,
        "height": height,
        "provider": "Pollinations AI",
        "hosting": "provider-hosted",
        "warning": (
            "Image bytes were validated, but this app has no durable image storage. "
            "The provider-hosted URL may not be permanent; verify it in Blogger before relying on it."
        ),
    }
