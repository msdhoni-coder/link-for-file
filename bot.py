import os
import sqlite3
import uuid
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant

# ===== ENV VARIABLES (DO NOT HARD-CODE) =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOY_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # IMPORTANT

# ===== FORCE SUB =====
FORCE_SUB_CHANNEL = -1002342160438
FORCE_SUB_LINK = "https://t.me/+tze-BpoZ4v01N2M1"

# ===== BOT CLIENT =====
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===== DATABASE =====
db = sqlite3.connect("database.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    id TEXT,
    file_id TEXT,
    file_name TEXT,
    file_size INTEGER
)
""")
db.commit()

# ===== FORCE SUB CHECK =====
async def check_subscription(client, message):
    try:
        await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        return True
    except UserNotParticipant:
        await message.reply_text(
            "🚫 Access Denied\n\n"
            "You must join our private channel to use this bot.\n\n"
            f"👉 Join here: {FORCE_SUB_LINK}",
            disable_web_page_preview=True
        )
        return False

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
async def get_file(client, message):

    if not await check_subscription(client, message):
        return

    file = message.document or message.video or message.audio
    unique_id = uuid.uuid4().hex

    cur.execute(
        "INSERT INTO files VALUES (?,?,?,?)",
        (unique_id, file.file_id, file.file_name, file.file_size)
    )
    db.commit()

    await message.reply_text(
        f"""𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !

📂 File : {file.file_name or "Unknown"}
📦 Size : {round(file.file_size/1024/1024,2)} MB

📥 Download : {BASE_URL}/dl/{unique_id}
🖥 Watch : {BASE_URL}/watch/{unique_id}

🔔 MUST FOLLOW : @shwe7ank
"""
    )

app.run()