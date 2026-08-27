# Page Automation

Generates an original motivational quote with Gemini, creates an AI background image, renders the quote with Pillow, uploads it to Cloudinary, sends a Telegram notification, and publishes it to Facebook and Instagram.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Set these environment variables before running:

`GEMINI_API_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `TELEGRAM_BOT_TOKEN`, `CHAT_ID`, `FB_PAGE_ID`, `IG_USER_ID`, and `META_PAGE_TOKEN`.

Keep `bg_img_prompts.txt`, `previous_quotes.txt`, and `Lora/static/Lora-Regular.ttf` in the project directory. Add `logo.png` if a logo overlay is required.

## Run

```bash
python main.py
```

The final image is saved as `final_post.jpg`. The script uses Gemini and Pollinations.ai for content generation, then posts through Cloudinary, Telegram, Facebook, and Instagram.
