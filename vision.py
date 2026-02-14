"""Vision classification using Claude Haiku 4.5.

Captures frame from camera, sends to Claude for 1-word classification.
Returns: 'fruit', 'snack', or 'drink'
"""
import base64
import os
import anthropic

# Stable fast vision-capable model alias; override via CLAUDE_VISION_MODEL if needed.
MODEL = os.getenv("CLAUDE_VISION_MODEL", "claude-3-5-haiku-latest")

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var


def classify_image(image_path: str) -> str:
    """Classify an image as fruit, snack, or drink.
    
    Args:
        image_path: Path to image file (jpg/png)
    
    Returns:
        One of: 'fruit', 'snack', 'drink'
    """
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    ext = image_path.lower().split(".")[-1]
    media_type = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")
    
    message = client.messages.create(
        model=MODEL,
        max_tokens=10,
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
                    {
                        "type": "text",
                        "text": (
                            "Classify the main food/beverage item in this image. "
                            "Return exactly one lowercase word with no punctuation: "
                            "fruit or snack or drink."
                        ),
                    },
                ],
            }
        ],
    )
    
    response = message.content[0].text.strip().lower()
    
    if response in ("fruit", "snack", "drink"):
        return response
    
    for category in ("fruit", "snack", "drink"):
        if category in response:
            return category
    
    print(f"Warning: unexpected response '{response}', defaulting to 'snack'")
    return "snack"


def classify_frame(frame_bytes: bytes, media_type: str = "image/jpeg") -> str:
    """Classify a frame directly from bytes (for camera integration).
    
    Args:
        frame_bytes: Raw image bytes (e.g. from cv2.imencode)
        media_type: MIME type of the image
    
    Returns:
        One of: 'fruit', 'snack', 'drink'
    """
    image_data = base64.standard_b64encode(frame_bytes).decode("utf-8")
    
    message = client.messages.create(
        model=MODEL,
        max_tokens=10,
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
                    {
                        "type": "text",
                        "text": (
                            "Classify the main food/beverage item in this image. "
                            "Return exactly one lowercase word with no punctuation: "
                            "fruit or snack or drink."
                        ),
                    },
                ],
            }
        ],
    )
    
    response = message.content[0].text.strip().lower()
    
    if response in ("fruit", "snack", "drink"):
        return response
    
    for category in ("fruit", "snack", "drink"):
        if category in response:
            return category
    
    print(f"Warning: unexpected response '{response}', defaulting to 'snack'")
    return "snack"


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
