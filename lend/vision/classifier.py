"""Vision classification using Claude Haiku.

Captures frame from camera, sends to Claude for classification.
Returns category (fruit/snack/drink) plus item details.
"""
import base64
import json
import os
import anthropic

# Valid Anthropic model alias; override via CLAUDE_VISION_MODEL if needed.
MODEL = os.getenv("CLAUDE_VISION_MODEL", "claude-3-5-haiku-latest")

# Users sometimes set the key like "{sk-ant-...}" in PowerShell; trim wrapping braces.
API_KEY = (os.getenv("ANTHROPIC_API_KEY") or "").strip().strip("{}")
client = anthropic.Anthropic(api_key=API_KEY or None)

DETAILED_PROMPT = """Analyze the main food or beverage item in this image.
Return ONLY a JSON object with these fields (no other text):
{
  "category": "fruit" or "snack" or "drink",
  "item_name": "specific item name, e.g. Granny Smith Apple, Doritos Cool Ranch, Dasani Water",
  "estimated_weight_lbs": estimated weight in pounds as a number (e.g. 0.3),
  "estimated_expiry": "YYYY-MM-DD if visible on packaging, otherwise null"
}"""

SIMPLE_PROMPT = (
    "Classify the main food/beverage item in this image. "
    "Return exactly one lowercase word with no punctuation: "
    "fruit or snack or drink."
)

VALID_CATEGORIES = ("fruit", "snack", "drink")


def _send_image(image_data: str, media_type: str, prompt: str, max_tokens: int):
    """Send an image + prompt to Claude and return the raw text response."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return message.content[0].text.strip()


def _extract_category(text: str) -> str:
    """Extract a valid category from a text response, with fallback."""
    t = text.lower()
    if t in VALID_CATEGORIES:
        return t
    for cat in VALID_CATEGORIES:
        if cat in t:
            return cat
    print(f"Warning: unexpected response '{text}', defaulting to 'snack'")
    return "snack"


def classify_frame(frame_bytes: bytes, media_type: str = "image/jpeg") -> str:
    """Classify a frame as fruit, snack, or drink (simple, fast)."""
    image_data = base64.standard_b64encode(frame_bytes).decode("utf-8")
    response = _send_image(image_data, media_type, SIMPLE_PROMPT, max_tokens=10)
    return _extract_category(response)


def classify_frame_detailed(frame_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Classify a frame and return full item details.

    Returns:
        dict with keys: category, item_name, estimated_weight_lbs, estimated_expiry
    """
    image_data = base64.standard_b64encode(frame_bytes).decode("utf-8")
    response = _send_image(image_data, media_type, DETAILED_PROMPT, max_tokens=256)

    # Strip markdown fences if present
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"Warning: could not parse JSON, falling back. Raw: {text}")
        return {
            "category": _extract_category(text),
            "item_name": "unknown",
            "estimated_weight_lbs": None,
            "estimated_expiry": None,
        }

    # Ensure category is valid
    data["category"] = _extract_category(data.get("category", ""))
    return data


def classify_image(image_path: str) -> str:
    """Classify an image file as fruit, snack, or drink."""
    with open(image_path, "rb") as f:
        frame_bytes = f.read()
    ext = image_path.lower().split(".")[-1]
    media_type = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif", "webp": "image/webp",
    }.get(ext, "image/jpeg")
    return classify_frame(frame_bytes, media_type)


if __name__ == "__main__":
    test_image = "camera-test.jpg"
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set.")
        raise SystemExit(1)
    print(f"Using model: {MODEL}")
    if os.path.exists(test_image):
        print(f"Testing with {test_image}...")
        result = classify_image(test_image)
        print(f"Classification: {result}")
    else:
        print("No test image found. Usage: classify_image('path/to/image.jpg')")
