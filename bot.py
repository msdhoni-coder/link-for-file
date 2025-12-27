import os
import sqlite3
import uuid
import time
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

FORCE_SUB_CHANNEL = -1002342160438
FORCE_SUB_LINK = "https://t.me/+tze-BpoZ4v01N2M1"

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

db = sqlite3.connect("database.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    uid TEXT PRIMARY KEY,
    file_id TEXT,
    file_name TEXT,
    file_size INTEGER,
    mime TEXT,
    created_at INTEGER
)
""")
db.commit()

async def check_subscription(client, message):
    try:
        await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        return True
    except UserNotParticipant:
        await message.reply_text(
            f"🚫 Access denied\n\n👉 Join first: {FORCE_SUB_LINK}",
            disable_web_page_preview=True
        )
        return False

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):

    # C. block bots
    if message.from_user.is_bot:
        return

    if not await check_subscription(client, message):
        return

    file = message.document or message.video or message.audio
    uid = uuid.uuid4().hex

    cur.execute(
        "INSERT INTO files VALUES (?,?,?,?,?,?)",
        (
            uid,
            file.file_id,
            file.file_name or "file",
            file.file_size,
            file.mime_type,
            int(time.time())
        )
    )
    db.commit()

    await message.reply_text(
        f"""✅ Link Generated

⏱ Valid for: 24 hours  
📄 {file.file_name}
📦 {round(file.file_size / 1024 / 1024, 2)} MB

⬇ Download:
{BASE_URL}/dl/{uid}

▶ Stream:
{BASE_URL}/watch/{uid}
"""
    )

app.run()
