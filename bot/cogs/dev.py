import logging
from collections import deque
import io

import discord
from discord import app_commands
from discord.ext import commands

# ----- Log buffer handler -----
class RingBufferHandler(logging.Handler):
    def __init__(self, max_lines: int = 300):
        super().__init__()
        self.buffer = deque(maxlen=max_lines)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.buffer.append(msg)
        except Exception:
            # Never let logging crash your bot
            pass

    def tail(self, n: int | None = None) -> str:
        if n is None or n >= len(self.buffer):
            return "\n".join(self.buffer)
        return "\n".join(list(self.buffer)[-n:])


def setup_logging(max_lines: int = 300) -> RingBufferHandler:
    handler = RingBufferHandler(max_lines=max_lines)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)  # flip to DEBUG when you want more noise
    root.addHandler(handler)

    return handler


# ----- Dev cog -----
class DevCog(commands.Cog):
    def __init__(self, bot: commands.Bot, log_handler: RingBufferHandler, owner_id: int):
        self.bot = bot
        self.log_handler = log_handler
        self.owner_id = owner_id

    # --- shared owner checks ---
    def is_owner_id(self, user_id: int | None) -> bool:
        return user_id is not None and user_id == self.owner_id

    def is_owner_interaction(self, interaction: discord.Interaction) -> bool:
        return interaction.user is not None and self.is_owner_id(interaction.user.id)

    def is_owner_ctx(self, ctx: commands.Context) -> bool:
        return self.is_owner_id(getattr(ctx.author, "id", None))

    # --- shared log sending helper ---
    async def send_logs_as_message_or_file(
        self,
        *,
        send_func,
        text: str,
        filename: str = "bot_logs.txt",
        message_limit: int = 1800,
    ):
        if not text.strip():
            await send_func("No logs yet.")
            return

        if len(text) <= message_limit:
            await send_func(f"```text\n{text}\n```")
            return

        data = text.encode("utf-8", errors="replace")
        file = discord.File(fp=io.BytesIO(data), filename=filename)
        await send_func("Logs attached:", file=file)

    # ----- Slash command -----
    @app_commands.command(name="dev_logs", description="Show recent bot logs (owner only).")
    @app_commands.describe(lines="How many log lines to show (max 300).")
    async def dev_logs(self, interaction: discord.Interaction, lines: int = 80):
        if not self.is_owner_interaction(interaction):
            await interaction.response.send_message("Nope 🙂", ephemeral=True)
            return

        lines = max(1, min(300, lines))
        text = self.log_handler.tail(lines)

        # If you already responded elsewhere, use followup
        if interaction.response.is_done():
            await self.send_logs_as_message_or_file(
                send_func=interaction.followup.send,
                text=text,
            )
        else:
            await self.send_logs_as_message_or_file(
                send_func=interaction.response.send_message,
                text=text,
            )

    # ----- Classic prefix command -----
    @commands.command(name="devlogs", aliases=["logs", "dlogs"])
    async def devlogs(self, ctx: commands.Context, lines: int = 80):
        if not self.is_owner_ctx(ctx):
            return

        lines = max(1, min(300, lines))
        text = self.log_handler.tail(lines)

        await self.send_logs_as_message_or_file(
            send_func=ctx.send,
            text=text,
        )


async def setup(bot: commands.Bot):
    """Setup function for the DevCog. This function is called when the cog is loaded."""
    log_handler = getattr(bot, "log_handler", None)
    owner_id = getattr(bot, "owner_id", None)

    if log_handler is None:
        raise RuntimeError("DevCog needs bot.log_handler (RingBufferHandler). Set it in main before loading the extension.")
    if owner_id is None:
        raise RuntimeError("DevCog needs bot.owner_id (int). Set it in main before loading the extension.")

    await bot.add_cog(DevCog(bot, log_handler, owner_id))