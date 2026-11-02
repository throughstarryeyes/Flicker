import discord
import asyncio
from discord.ext import commands


class CleanupCog(commands.Cog, name="Cleanup"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, amount: int, *flags):
        """Delete messages with advanced filtering.

        Usage:
            !purge 50                    → Delete last 50 messages (< 14 days old)
            !purge 100 --bots            → Delete last 100 bot messages
            !purge 25 --user @SomeUser   → Delete last 25 messages from specific user
            !purge 20 --contains moon    → Delete messages containing "moon"
            !purge 200 --any_age         → Delete messages of any age (slow)
        """
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("❌ This command only works in text channels.", delete_after=6)
            return

        chan = ctx.channel

        flags_dict: dict[str, bool | int | str] = {}
        i = 0
        while i < len(flags):
            flag = flags[i]
            if flag == "--bots":
                flags_dict["bots"] = True
                i += 1
            elif flag == "--user" and i + 1 < len(flags):
                user_mention = flags[i + 1]
                user_id = user_mention.strip("<@!>")
                try:
                    flags_dict["user_id"] = int(user_id)
                except ValueError:
                    await ctx.send(f"❌ Invalid user mention: {user_mention}", delete_after=6)
                    return
                i += 2
            elif flag == "--contains" and i + 1 < len(flags):
                flags_dict["contains"] = flags[i + 1]
                i += 2
            elif flag == "--any_age":
                flags_dict["any_age"] = True
                i += 1
            else:
                await ctx.send(f"❌ Unknown flag or missing argument: {flag}", delete_after=6)
                return

        def check_message(msg: discord.Message) -> bool:
            if msg.id == ctx.message.id:
                return True

            if "bots" in flags_dict and not msg.author.bot:
                return False

            if "user_id" in flags_dict and msg.author.id != flags_dict.get("user_id", 0):
                return False

            if "contains" in flags_dict:
                contains_val = flags_dict.get("contains", "")
                if isinstance(contains_val, str) and contains_val.lower() not in msg.content.lower():
                    return False

            return True

        try:
            if "any_age" in flags_dict:
                status_msg = await ctx.send(f"🧹 Deleting up to **{amount}** messages (any age, this may take a while)…")
                count = 0
                async for msg in chan.history(limit=None, oldest_first=False):
                    if count >= amount:
                        break
                    if check_message(msg):
                        try:
                            await msg.delete()
                            count += 1
                            await asyncio.sleep(0.3)
                        except Exception:
                            pass

                await status_msg.delete()
                await ctx.send(f"✅ Deleted **{count}** messages.", delete_after=5)
            else:
                deleted = await chan.purge(limit=amount + 50, check=check_message, bulk=True)
                actual_count = len([m for m in deleted if m.id != ctx.message.id])
                await ctx.send(f"✅ Deleted **{actual_count}** messages.", delete_after=5)

        except discord.Forbidden:
            await ctx.send("❌ I need **Manage Messages** + **Read Message History** here.", delete_after=6)
        except Exception as e:
            await ctx.send(f"❌ Purge failed: {e}", delete_after=6)

    @commands.command(name="cleanme")
    @commands.guild_only()
    async def cleanme(self, ctx: commands.Context, amount: int = 10):
        """Delete your own recent messages.

        Usage: !cleanme [amount]  (default: 10)
        """
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("❌ This command only works in text channels.", delete_after=6)
            return

        chan = ctx.channel

        def is_author(msg: discord.Message) -> bool:
            return msg.author.id == ctx.author.id

        try:
            deleted = await chan.purge(limit=100, check=is_author, bulk=True)
            actual_count = min(len(deleted), amount)
            await ctx.send(f"✅ Cleaned **{actual_count}** of your messages.", delete_after=3)
        except Exception as e:
            await ctx.send(f"❌ Clean failed: {e}", delete_after=6)

    @commands.command(name="sweep")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def sweep(self, ctx: commands.Context, amount: int = 50):
        """Delete non-pinned messages only.

        Usage: !sweep [amount]  (default: 50)
        """
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("❌ This command only works in text channels.", delete_after=6)
            return

        chan = ctx.channel

        def not_pinned(msg: discord.Message) -> bool:
            return not msg.pinned

        try:
            deleted = await chan.purge(limit=amount + 50, check=not_pinned, bulk=True)
            await ctx.send(f"✅ Swept **{len(deleted)}** non-pinned messages.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ I need **Manage Messages** + **Read Message History** here.", delete_after=6)
        except Exception as e:
            await ctx.send(f"❌ Sweep failed: {e}", delete_after=6)


async def setup(bot):
    await bot.add_cog(CleanupCog(bot))
