import json
from typing import Tuple
from PIL import Image

def is_underage_image(image: Image.Image) -> Tuple[bool, dict]:
    """Detect if an image likely contains underage content using DeepDanbooru + CLIP."""
    # Load thresholds and tag lists from config.json (expects a "content_filter" section or top-level keys)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    filter_conf = config.get("content_filter", config)  # support nested or top-level config keys
    underage_tags = filter_conf.get("underage_tags", ["loli", "shota", "child"])
    tag_threshold = filter_conf.get("underage_tag_threshold", 0.75)
    clip_threshold = filter_conf.get("clip_threshold", 0.5)
    flagged_tags = {}
    flagged = False

    # **DeepDanbooru model prediction** (pseudo-code; replace with actual model inference)
    try:
        # e.g., if a DeepDanbooru model instance is available as `dd_model`:
        # predictions = dd_model.predict(image)  # returns {tag: score}
        predictions = {}  # placeholder for actual tag predictions
    except Exception:
        predictions = {}
    # Check for any underage-indicative tags above the threshold
    for tag, score in predictions.items():
        if tag in underage_tags and score >= tag_threshold:
            flagged_tags[tag] = float(score)
            flagged = True

    # **CLIP-based filtering** (e.g., image captioning or classification for underage cues)
    try:
        # If using a CLIP model to get an image description or NSFW score:
        # clip_caption = clip_model.generate_caption(image)
        clip_caption = ""  # placeholder for actual CLIP processing
    except Exception:
        clip_caption = ""
    if clip_caption:
        # Flag if certain underage-related terms appear in the CLIP-generated caption
        underage_terms = filter_conf.get("clip_underage_terms", ["child", "kid"])
        caption_lower = clip_caption.lower()
        for term in underage_terms:
            if term in caption_lower:
                flagged_tags["clip"] = term
                flagged = True
                break

    return flagged, flagged_tags

def log_flag_event(user_id: str, prompt: str, flagged_tags: dict, file_name: str) -> None:
    """Append a log entry to flag_log.json when content is flagged."""
    # Prepare the log entry
    from datetime import datetime
    log_entry = {
        "user_id": user_id,
        "prompt": prompt,
        "flagged_tags": flagged_tags,
        "file_name": file_name,
        "timestamp": datetime.utcnow().isoformat()
    }
    # Load existing log (or start a new list) and append the entry
    try:
        with open('flag_log.json', 'r') as f:
            flag_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        flag_log = []
    flag_log.append(log_entry)
    # Write back to flag_log.json with indentation for readability
    with open('flag_log.json', 'w') as f:
        json.dump(flag_log, f, indent=4)

def update_user_flags(user_id: str) -> int:
    """Increment the offense count for a user in user_flags.json and return the new count."""
    try:
        with open('user_flags.json', 'r') as f:
            user_flags = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_flags = {}
    # Increment offense count
    new_count = user_flags.get(user_id, 0) + 1
    user_flags[user_id] = new_count
    # Save updated counts back to JSON (indent for easy editing)
    with open('user_flags.json', 'w') as f:
        json.dump(user_flags, f, indent=4)
    return new_count

def is_user_blocked(user_id: str) -> bool:
    """Check if the user’s offense count has reached the limit defined in config.json."""
    # Get offense limit from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    filter_conf = config.get("content_filter", config)
    offense_limit = filter_conf.get("offense_limit", 3)
    # Load current offense counts
    try:
        with open('user_flags.json', 'r') as f:
            user_flags = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_flags = {}
    current_count = user_flags.get(user_id, 0)
    return current_count >= offense_limit
