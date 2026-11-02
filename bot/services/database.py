import aiosqlite
import hashlib
from datetime import datetime

DATABASE_PATH = "storage/bot.db"

async def init_database():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                due_at TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS saved_spells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                spell_name TEXT NOT NULL,
                spell_content TEXT NOT NULL,
                intention TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS offerings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        await db.commit()

async def store_secret(user_id: int, content: str):
    user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
    created_at = datetime.now().isoformat()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO secrets (user_hash, content, created_at) VALUES (?, ?, ?)",
            (user_hash, content, created_at)
        )
        await db.commit()

async def add_reminder(user_id: int, channel_id: int, due_at: datetime, message: str):
    created_at = datetime.now().isoformat()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO reminders (user_id, channel_id, due_at, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, channel_id, due_at.isoformat(), message, created_at)
        )
        await db.commit()

async def get_due_reminders():
    now = datetime.now().isoformat()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, user_id, channel_id, message FROM reminders WHERE due_at <= ? ORDER BY due_at",
            (now,)
        ) as cursor:
            reminders = await cursor.fetchall()
            
        if reminders:
            reminder_ids = [r[0] for r in reminders]
            await db.execute(
                f"DELETE FROM reminders WHERE id IN ({','.join('?' * len(reminder_ids))})",
                reminder_ids
            )
            await db.commit()
        
        return reminders

async def save_spell(user_id: int, spell_name: str, spell_content: str, intention: str):
    created_at = datetime.now().isoformat()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO saved_spells (user_id, spell_name, spell_content, intention, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, spell_name, spell_content, intention, created_at)
        )
        await db.commit()

async def get_user_spells(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, spell_name, spell_content, intention, created_at FROM saved_spells WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            spells = await cursor.fetchall()
        return spells

async def delete_spell(user_id: int, spell_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM saved_spells WHERE id = ? AND user_id = ?",
            (spell_id, user_id)
        )
        await db.commit()

async def store_offering(user_id, guild_id, item, created_at):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO offerings (user_id, guild_id, item, created_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, guild_id, item, created_at.isoformat()),
        )
        await db.commit()


async def get_offerings(guild_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """SELECT id, user_id, guild_id, item, created_at
               FROM offerings
               WHERE guild_id = ?
               ORDER BY id DESC""",
            (guild_id,)
        )
        rows = await cursor.fetchall()
    # convert sqlite rows to dicts for easier embed building
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "guild_id": row[2],
            "item": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]
            