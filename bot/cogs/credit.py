import discord
from discord.ext import commands

CREDIT_TEXT = "✨ by Saturn"
original_set_footer = discord.Embed.set_footer


def custom_set_footer(self, *args, **kwargs):
    existing_text = kwargs.get("text")
    if existing_text is None and args:
        existing_text = args[0]
        args = args[1:]

    if existing_text:
        if CREDIT_TEXT not in existing_text:
            kwargs["text"] = f"{existing_text} • {CREDIT_TEXT}"
        else:
            kwargs["text"] = existing_text
    else:
        kwargs["text"] = CREDIT_TEXT

    return original_set_footer(self, *args, **kwargs)


class FooterHookCog(commands.Cog, name="Footer Hook"):
    def __init__(self, bot):
        self.bot = bot
        discord.Embed.set_footer = custom_set_footer

    def cog_unload(self):
        discord.Embed.set_footer = original_set_footer


async def setup(bot):
    await bot.add_cog(FooterHookCog(bot))