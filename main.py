import os
import traceback
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

load_dotenv(ENV_PATH, override=True)
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError(f"TOKEN is not set in {ENV_PATH}")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # keep if you use member events / moderation stuff


async def get_prefix(bot: commands.Bot, message: discord.Message):
    # example: default prefix
    return "!"


class FlickerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, intents=intents, help_command=None, description="Flicker Mystical Bot")

    async def setup_hook(self) -> None:
        print("setup_hook: loading cogs...")

        cogs_dir = ROOT / "bot" / "cogs"
        if not cogs_dir.exists():
            print(f"❌ cogs_dir not found: {cogs_dir}")
            return

        for path in cogs_dir.glob("*.py"):
            if path.name.startswith("_") or path.name == "__init__.py":
                continue

            ext = f"bot.cogs.{path.stem}"
            print(f"trying to load: {ext}")
            try:
                await self.load_extension(ext)
                print(f"✅ loaded: {ext}")
            except Exception:
                print(f"❌ failed: {ext}")
                traceback.print_exc()

        print("setup_hook: done loading cogs.")


bot = FlickerBot()


@bot.event
async def on_ready():
    print(f"flicker is online; logged in as {bot.user} (id={bot.user.id}) ✨🕯️")

@bot.command()
async def ping(ctx: commands.Context):
    """check latency and responsiveness: sanity check"""
    latency = round(bot.latency * 1000, 2)
    await ctx.send(f"🏓 pong! **latency: {latency}ms** ✨")


bot.run(TOKEN)