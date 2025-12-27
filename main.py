import os
import sqlite3
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pyrogram import Client

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

EXPIRY_SECONDS = 24 * 60 * 60
DAILY_LIMIT = 7

app = FastAPI()

tg = Client(
    "streamer",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

db = sqlite3.connect("database.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS requests (
    ip TEXT,
    date TEXT,
    count INTEGER,
    PRIMARY KEY (ip, date)
)
""")
db.commit()

@app.on_event("startup")
async def startup():
    await tg.start()

@app.on_event("shutdown")
async def shutdown():
    await tg.stop()

def check_rate_limit(ip: str):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    cur.execute(
        "SELECT count FROM requests WHERE ip=? AND date=?",
        (ip, today)
    )
    row = cur.fetchone()

    if row:
        if row[0] >= DAILY_LIMIT:
            return False
        cur.execute(
            "UPDATE requests SET count=count+1 WHERE ip=? AND date=?",
            (ip, today)
        )
    else:
        cur.execute(
            "INSERT INTO requests VALUES (?,?,1)",
            (ip, today)
        )

    db.commit()
    return True

async def get_file(uid: str):
    now = int(time.time())

    # cleanup expired files
    cur.execute(
        "DELETE FROM files WHERE ? - created_at > ?",
        (now, EXPIRY_SECONDS)
    )
    db.commit()

    cur.execute(
        "SELECT file_id, file_name, mime, created_at FROM files WHERE uid=?",
        (uid,)
    )
    row = cur.fetchone()

    if not row:
        return None

    file_id, name, mime, created_at = row

    if now - created_at > EXPIRY_SECONDS:
        cur.execute("DELETE FROM files WHERE uid=?", (uid,))
        db.commit()
        return None

    return file_id, name, mime

@app.get("/dl/{uid}")
async def download(uid: str, request: Request):
    ip = request.client.host

    if not check_rate_limit(ip):
        return JSONResponse(
            {"error": "Daily limit reached (7 requests). Try again tomorrow."},
            status_code=429
        )

    data = await get_file(uid)
    if not data:
        return JSONResponse(
            {"error": "⏱ Link expired (24 hours passed) or invalid"},
            status_code=404
        )

    file_id, name, _ = data
    stream = await tg.download_media(file_id, in_memory=True)

    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{name}"'}
    )

@app.get("/watch/{uid}")
async def watch(uid: str, request: Request):
    ip = request.client.host

    if not check_rate_limit(ip):
        return JSONResponse(
            {"error": "Daily limit reached (7 requests). Try again tomorrow."},
            status_code=429
        )

    data = await get_file(uid)
    if not data:
        return JSONResponse(
            {"error": "⏱ Link expired (24 hours passed) or invalid"},
            status_code=404
        )

    file_id, _, mime = data
    stream = await tg.download_media(file_id, in_memory=True)

    return StreamingResponse(
        stream,
        media_type=mime or "video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )
