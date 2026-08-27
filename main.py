import json
import os
import random
import time
import unicodedata
from urllib import response
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont
import cloudinary
import cloudinary.uploader

from PIL import Image, ImageDraw, ImageFont
import os

# ==============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
IG_USER_ID = os.getenv("IG_USER_ID")
META_PAGE_TOKEN = os.getenv("META_PAGE_TOKEN")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


META_API_VERSION = "v25.0"

# Initialize Cloudinary SDK
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# ==============================================================================
# STEP 1: GENERATE QUOTE & PROMPT VIA GEMINI API
# ==============================================================================
def load_previous_quotes(file_path="previous_quotes.txt"):
    """Loads previously generated quote text from a local file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return lines
    except FileNotFoundError:
        return []


def load_bg_prompt(file_path="bg_img_prompts.txt"):
    """Loads a random background prompt from a local file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return "misty mountain peak at sunrise, cinematic lighting, detailed, vibrant, ultra realistic"
        prompt = random.choice(lines) + " cinematic lighting, detailed, vibrant, ultra realistic, darker mood, epic "
        return prompt
    except FileNotFoundError:
        return "misty mountain peak at sunrise, cinematic lighting, detailed, vibrant, ultra realistic"


def generate_quote_data():
    """Generates a quote, author, and background prompt in structured JSON."""
    print("🤖 Requesting quote and image prompt from Gemini...")
    # url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    previous_quotes = load_previous_quotes()
    previous_quotes_text = "\n".join(f"- {quote}" for quote in previous_quotes)
    bg_img_prompt = load_bg_prompt()

    quote_themes = [
        "Self-belief",
        "Discipline",
        "Persistence",
        "Failure & learning",
        "Courage",
        "Patience",
        "Growth",
        "Dreams & ambition",
        "Consistency",
        "Overcoming fear",
        "Success",
        "Positive mindset",
        "Hard work",
        "Life perspective",
        "Resilience"
    ]

    prompt_text_1 = (
        "Generate a powerful, short motivational quote. "
        "The quote must be substantially different in meaning, wording, and message from all previously generated quotes. "
        f"Previously generated quotes:\n{previous_quotes_text if previous_quotes_text else 'None so far.'}\n"
        "Output strictly valid JSON with no markdown wrapping. Schema: "
        '{"quote": "...", "author": "...", "bg_prompt": "...", "hashtags": "..."}. '
        f"bg_prompt : {bg_img_prompt}."
    )

    prompt_text_2 = (
        "You are a motivational quote generator. Generate ONE original motivational quote for today. "
        "Requirements: The quote must be inspiring, meaningful, and suitable for a general audience. "
        "Today's quote should be based on the theme of: " + random.choice(quote_themes) + ". "
        "It should feel natural and emotionally powerful. Keep it concise: 1-2 sentences maximum. "
        "Do not use clichés unless you give them a fresh and original expression. Do not mention today's date. "
        "Do not include emojis. Do not add explanations or commentary. Do not attribute the quote to a real person. "
        "The quote must be substantially different in meaning, wording, and message from all previously generated quotes. "
        f"Previously generated quotes:\n{previous_quotes_text if previous_quotes_text else 'None so far.'}\n"
        "Avoid repeating the same motivational theme too frequently. "
        "Output strictly valid JSON with no markdown wrapping. Schema: "
        '{"quote": "...", "author": "Unknown", "bg_prompt": "...", "hashtags": "..."}. '
        f"bg_prompt : {bg_img_prompt}."
    )

    prompt_text = random.choice([prompt_text_1, prompt_text_2])

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    for attempt in range(1, 101):
        response = requests.post(url, json=payload)

        # print(f"Response message: {response.text}")

        if response.status_code == 503 and attempt < 100:
            delay = 2 + random.randint(4, 8)
            print(f"⚠️ Gemini returned 503 on attempt {attempt}/100. Retrying in {delay} seconds...")
            time.sleep(delay)
            continue

        if response.status_code == 429 and attempt < 100:
            delay = 60 + random.randint(4, 8)
            print(f"⚠️ Gemini returned 429 on attempt {attempt}/100. Retrying in {delay} seconds...")
            time.sleep(delay)
            continue

        response.raise_for_status()
        raw_json = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw_json)

        # insert the new quote into previous_quotes.txt to avoid duplicates in future runs
        with open("previous_quotes.txt", "a", encoding="utf-8") as f:
            f.write(data["quote"] + "\n")

        print(f"✨ Quote: \"{data['quote']}\" — {data['author']}")
        return data

    raise RuntimeError("Gemini API failed after 10 attempts with HTTP 503.")

# ==============================================================================
# STEP 2: FETCH AI BACKGROUND IMAGE
# ==============================================================================
def download_background_image(bg_prompt):
    """Downloads an AI-generated background image from Pollinations.ai."""
    print("🎨 Generating background image via Pollinations.ai...")
    encoded_prompt = urllib.parse.quote(bg_prompt)
    seed = random.randint(1000, 99999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&seed={seed}&nologo=true"
    
    resp = requests.get(image_url, stream=True)
    resp.raise_for_status()
    
    bg_path = "temp_bg.jpg"
    with open(bg_path, "wb") as f:
        f.write(resp.content)
    return bg_path

# ==============================================================================
# STEP 3: COMPOSITE TEXT & IMAGE WITH PILLOW
# ==============================================================================


def wrap_text(text, font, max_width, draw):
    """
    Wraps text dynamically so that no single line exceeds max_width.
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        # Get the pixel dimensions of the line if we add this word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            # The line is too long, save the current line and start a new one
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
        
    return "\n".join(lines)

def generate_quote_image(input_image_path, output_image_path, quote, author = "Unknown", font_path="Lora/static/Lora-Regular.ttf"):
    # 1. Open the image and convert to RGB (standard for JPG)
    try:
        img = Image.open(input_image_path).convert("RGB")
    except FileNotFoundError:
        print(f"Error: Could not find input image at {input_image_path}")
        return
        
    draw = ImageDraw.Draw(img)
    img_w, img_h = img.size

    # 2. Target dimensions to cover ~65% of the image area
    target_width = img_w * 0.65
    target_height = img_h * 0.65

    # 3. Binary search to find the absolute largest font size that fits 65%
    min_size = 10
    max_size = min(img_w, img_h)
    best_size = min_size
    best_wrapped_quote = quote

    while min_size <= max_size:
        mid_size = (min_size + max_size) // 2
        try:
            quote_font = ImageFont.truetype(font_path, mid_size)
            author_font = ImageFont.truetype(font_path, int(mid_size * 0.5))
        except OSError:
            print(f"Error: Could not load font '{font_path}'. Ensure it is in the same directory.")
            return

        wrapped_quote = wrap_text(quote, quote_font, target_width, draw)

        # Measure height and width of quote block
        q_bbox = draw.multiline_textbbox((0, 0), wrapped_quote, font=quote_font, align="center")
        q_w = q_bbox[2] - q_bbox[0]
        q_h = q_bbox[3] - q_bbox[1]

        # Measure height of author block
        a_text = f"~ {author}"
        a_bbox = draw.textbbox((0, 0), a_text, font=author_font)
        a_h = a_bbox[3] - a_bbox[1]

        spacing = int(mid_size * 0.7)
        total_h = q_h + spacing + a_h

        # Check if text fits inside our 65% area bounds
        if total_h <= target_height and q_w <= target_width:
            best_size = mid_size
            best_wrapped_quote = wrapped_quote
            min_size = mid_size + 1
        else:
            max_size = mid_size - 1

    # 4. Prepare final render with optimal sizing
    quote_font = ImageFont.truetype(font_path, best_size)
    author_font = ImageFont.truetype(font_path, int(best_size * 0.5))

    # Recalculate final heights for centering
    q_bbox = draw.multiline_textbbox((0, 0), best_wrapped_quote, font=quote_font, align="center")
    q_h = q_bbox[3] - q_bbox[1]

    a_text = f"~ {author}"
    a_bbox = draw.textbbox((0, 0), a_text, font=author_font)
    a_h = a_bbox[3] - a_bbox[1]

    spacing = int(best_size * 0.7)
    total_h = q_h + spacing + a_h

    # Calculate starting Y to ensure perfect vertical center
    start_y = (img_h - total_h) / 2

    # We add a subtle black stroke/outline so white text is visible even on bright image backgrounds
    outline_color = "black"
    outline_width = max(1, best_size // 40)

    # 5. Draw the quote
    draw.multiline_text(
        (img_w / 2, start_y),
        best_wrapped_quote,
        font=quote_font,
        fill="white",
        align="center",
        anchor="ma", # Middle-Ascender alignment (centers horizontally, renders downwards)
        stroke_width=outline_width,
        stroke_fill=outline_color
    )

    # 6. Draw the author
    author_y = start_y + q_h + spacing
    draw.text(
        (img_w / 2, author_y),
        a_text,
        font=author_font,
        fill="white",
        anchor="ma",
        stroke_width=max(1, outline_width // 2),
        stroke_fill=outline_color
    )

    # 7. Add semi-transparent logo in the bottom-right corner
    try:
        logo = Image.open("logo.png").convert("RGBA")
    except FileNotFoundError:
        print("Logo file not found; skipping logo overlay.")
    else:
        max_logo_side = max(1, min(img_w, img_h) // 6)
        logo_aspect = logo.width / logo.height
        if logo.width >= logo.height:
            new_logo_width = max_logo_side
            new_logo_height = max(1, int(new_logo_width / logo_aspect))
        else:
            new_logo_height = max_logo_side
            new_logo_width = max(1, int(new_logo_height * logo_aspect))

        logo = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
        alpha = logo.getchannel("A")
        logo.putalpha(alpha.point(lambda p: int(p * 0.45)))

        padding = max(20, int(min(img_w, img_h) * 0.03))
        x = img_w - new_logo_width - padding
        y = img_h - new_logo_height - padding
        img.paste(logo, (x, y), logo)

    # 8. Save output as JPG
    img.save(output_image_path, "JPEG", quality=95)
    print(f"Success! Quote added and saved to: {output_image_path}")

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    my_quote = "The only limit to our realization of tomorrow is our doubts of today."
    my_author = "Franklin D. Roosevelt"
    
    generate_quote_image(
        input_image_path="input_background.jpg", 
        output_image_path="output_quote.jpg", 
        quote=my_quote, 
        author=my_author,
        font_path="Lora-Regular.ttf" 
    )

# ==============================================================================
# STEP 4: UPLOAD TO CLOUDINARY FOR PUBLIC HTTPS URL
# ==============================================================================
def upload_to_cloudinary(filepath):
    """Uploads image to Cloudinary and returns public URL for Meta API."""
    print("☁️ Uploading final post to Cloudinary CDN...")
    res = cloudinary.uploader.upload(filepath)
    url = res.get("secure_url")
    # print(f"🔗 Public CDN URL: {url}")
    return url

# ==============================================================================
# STEP 5: SEND TELEGRAM NOTIFICATION
# ==============================================================================
def send_telegram_notification(image_url, caption):
    """Sends a notification to a Telegram chat with the posted image and caption."""
    print("📤 Sending notification to Telegram...")

    keyboard = {
    "inline_keyboard": [
            [
                {
                    "text": "✅ APPROVE",
                    "callback_data": "approve:day-001"
                },
                {
                    "text": "❌ REJECT",
                    "callback_data": "reject:day-001"
                }
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "reply_markup": json.dumps(keyboard)
    }
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("✅ Notification sent to Telegram!")
    else:
        print(f"❌ Error sending notification to Telegram: {response.status_code}")

# ==============================================================================
# STEP 6: PUBLISH TO FACEBOOK & INSTAGRAM
# ==============================================================================
def post_to_facebook(image_url, caption):
    """Posts directly to the Facebook Page photo feed."""
    print("📢 Posting to Facebook Page...")
    endpoint = f"https://graph.facebook.com/{META_API_VERSION}/{FB_PAGE_ID}/photos"
    payload = {
        "url": image_url,
        "caption": caption,
        "access_token": META_PAGE_TOKEN
    }
    res = requests.post(endpoint, data=payload).json()
    if "id" in res:
        print(f"✅ Facebook Post Published! Post ID: {res['id']}")
    else:
        print(f"❌ Facebook Error: {res}")

def post_to_instagram(image_url, caption):
    """Posts to Instagram using the two-step Container Publishing API."""
    print("📸 Initiating Instagram upload pipeline...")
    
    # Step A: Create Media Container
    container_endpoint = f"https://graph.facebook.com/{META_API_VERSION}/{IG_USER_ID}/media"
    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": META_PAGE_TOKEN
    }
    res_container = requests.post(container_endpoint, data=container_payload).json()
    
    if "id" not in res_container:
        print(f"❌ Instagram Container Error: {res_container}")
        return
        
    container_id = res_container["id"]
    print(f"📦 Container created (ID: {container_id}). Waiting for processing...")
    
    # Wait 10 seconds for Meta servers to process the image
    time.sleep(10)
    
    # Step B: Publish Container
    publish_endpoint = f"https://graph.facebook.com/{META_API_VERSION}/{IG_USER_ID}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": META_PAGE_TOKEN
    }
    res_publish = requests.post(publish_endpoint, data=publish_payload).json()
    
    if "id" in res_publish:
        print(f"✅ Instagram Post Published! Media ID: {res_publish['id']}")
    else:
        print(f"❌ Instagram Publishing Error: {res_publish}")

# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def main():
    try:
        # # 1. Fetch content from Gemini
        quote_data = generate_quote_data()
        caption = [
            "#motivation", "#quotes", "#inspiration", "#motivationalquotes", "#inspirationalquotes",
            "#motivationdaily", "#dailyquotes", "#dailymotivation", "#inspirational", "#motivational",
            "#mindset", "#growthmindset", "#positivemindset", "#success", "#successmindset",
            "#selfimprovement", "#personalgrowth", "#selfgrowth", "#believeinyourself", "#believe",
            "#nevergiveup", "#keepgoing", "#staypositive", "#positivevibes", "#positivity",
            "#inspire", "#dreambig", "#dreams", "#goals", "#goalsetting", "#discipline",
            "#determination", "#perseverance", "#resilience", "#courage", "#confidence",
            "#innerstrength", "#hardwork", "#consistency", "#lifelessons", "#wisdom",
            "#lifequotes", "#quotesdaily", "#quoteoftheday", "#thoughtoftheday", "#wordsofwisdom",
            "#positivequotes", "#successquotes", "#mindsetmatters", "#youcandoit"
        ]
        selected_caption = random.sample(caption, random.randint(5, 10))
        selected_caption = " ".join(selected_caption)

        # # 2. Download background
        bg_file = download_background_image(quote_data["bg_prompt"])

        # # 3. Render final graphic
        final_image = generate_quote_image(bg_file, "final_post.jpg", quote_data["quote"], quote_data["author"] )

        final_image = "final_post.jpg"  # Assuming the image is generated and saved as final_post.jpg

        # 4. Host on public HTTPS URL
        public_url = upload_to_cloudinary(final_image)

        # public_url = "https://res.cloudinary.com/l5s8jebk/image/upload/v1787233877/suvcxiz6fadnqihfb46c.jpg"
        # print(f"✅ Final image is publicly accessible at: {public_url}")

        # 5. Send notification to Telegram
        send_telegram_notification(public_url, selected_caption)

        # 6. Broadcast to Social Media Platforms

        # 30 seconds delay to ensure the image is fully processed and available on Cloudinary before posting
        time.sleep(30)

        post_to_facebook(public_url, selected_caption)
        post_to_instagram(public_url, selected_caption)
        
        # Clean up local temporary files
        # if os.path.exists(bg_file): os.remove(bg_file)
        # if os.path.exists(final_image): os.remove(final_image)
        print("🎉 Full workflow completed successfully!")

    except Exception as e:
        print(f"💥 Pipeline failed: {str(e)}")

if __name__ == "__main__":
    main()