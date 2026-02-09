import os
import subprocess
import hashlib
import time
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InputSticker
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ⚠️ التوكن داخل الكود (غير آمن – بناءً على طلبك)
BOT_TOKEN = "8594603634:AAFYsUj-nG92jDMfo6358Ho0Stl_EOUj2Zk"

WATERMARK = "@iraq_viip"
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def fingerprint(user_id: int) -> str:
    raw = f"{user_id}-{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]

def protect_image(img: Image.Image, user_id: int) -> Image.Image:
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    mark = f"{WATERMARK} • {fingerprint(user_id)}"
    w, h = draw.textsize(mark, font=font)

    draw.text(
        (512 - w - 10, 512 - h - 10),
        mark,
        fill=(255, 255, 255, 160),
        font=font
    )

    # بصمة مخفية بسيطة
    for i in range(0, 512, 64):
        img.putpixel((i, i), (255, 255, 255, 1))

    return img

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot
    bot_username = (await bot.get_me()).username

    pack_name = f"iraq_viip_{user.id}_by_{bot_username}"
    pack_title = "@iraq_viip | Private Stickers"

    # 🖼️ صور
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        in_path = f"{TEMP_DIR}/input_img"
        out_path = f"{TEMP_DIR}/sticker.webp"
        await file.download_to_drive(in_path)

        img = Image.open(in_path).convert("RGBA")
        side = min(img.size)
        img = img.crop((0, 0, side, side)).resize((512, 512))
        img = protect_image(img, user.id)
        img.save(out_path, "WEBP")

    # 🎞️ فيديو / GIF
    elif update.message.video or update.message.animation:
        media = update.message.video or update.message.animation
        file = await media.get_file()
        in_path = f"{TEMP_DIR}/input_video"
        out_path = f"{TEMP_DIR}/sticker.webm"
        await file.download_to_drive(in_path)

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", in_path,
            "-vf", "scale=512:512",
            "-t", "3",
            "-an",
            "-c:v", "libvpx-vp9",
            out_path
        ], check=True)

    else:
        return

    sticker = InputSticker(
        sticker=open(out_path, "rb"),
        emoji_list=["🔥"]
    )

    try:
        await bot.add_sticker_to_set(user.id, pack_name, sticker)
    except:
        await bot.create_new_sticker_set(
            user.id,
            pack_name,
            pack_title,
            [sticker]
        )

    await update.message.reply_text(
        f"✅ تم إضافة الملصق\n"
        f"📦 حزمتك الخاصة:\n"
        f"https://t.me/addstickers/{pack_name}"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.ANIMATION,
            handle_media
        )
    )
    print("🤖 Bot is running (Polling)")
    app.run_polling()

if __name__ == "__main__":
    main()
