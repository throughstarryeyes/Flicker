import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import sys
import json
import re
import random
from datetime import datetime, timedelta

PREFIX_FILE = "bot/data/prefixes.json"

class MiscCog(commands.Cog, name="Misc"):
    """Miscellaneous and custom commands - tinker zone!"""
    
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/eightball_data.json", "r") as f:
            self.eightball_data = json.load(f)

    @commands.command(name="kiss")
    async def kiss(self, ctx: commands.Context):
        """Sanity check - replies with thank you."""
        await ctx.send("thank you! :star:")
        
    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context):
        """Greets the user."""
        await ctx.send("hi there, starlight!")

    @commands.command(name="booty_butt")
    async def booty_butt(self, ctx: commands.Context):
        """Special for Miles."""
        await ctx.send(":egg:")

    @commands.command(name="miles")
    async def miles(self, ctx: commands.Context):
        """Special for Miles part 2"""
        await ctx.send("miles is the best")

    @commands.command(name="saturn")
    async def saturn(self, ctx: commands.Context):
        """I coded this bot!"""
        await ctx.send("saturn is amazing!")

    @commands.command(name="flicker")
    async def flicker(self, ctx: commands.Context):
        """I am flicker!"""
        await ctx.send("hi there! i am flicker, the friendly community ghost that haunts the halls of stars and cards. i'm here to help you with all your magical needs!")

    @commands.command(name="oracle")
    async def oracle(self, ctx):
        responses = [
            "the stars say yes ✨",
            "hmm… maybe later 🌙",
            "not in this timeline 🪐",
            "absolutely! 🌟"
        ]
        await ctx.send(random.choice(responses)) 

    @commands.command(name="pick")
    async def pick(self, ctx, *, options: str):
        """Pick from multiple options separated by commas."""
        choices = [choice.strip() for choice in options.split(',') if choice.strip()]
        if not choices:
            await ctx.send("❌ Please provide options separated by commas!")
            return
        
        selected = random.choice(choices)
        await ctx.send(f"✨ I choose: **{selected}**")

    @commands.command(name="joke")
    async def joke(self, ctx):
        jokes = [
            "How do you organize a space party? You planet!",
            "What "
        ]
        await ctx.send(random.choice(jokes))

    @commands.command(name="spacefact")
    async def spacefact(self, ctx):
        spacefacts = [
            "The Sun makes up 99.86% of the mass in the solar system.",
            "One million Earths could fit inside the Sun.",
            "There are more stars in the universe than grains of sand on Earth."
            "The largest volcano in the solar system is on Mars and is called Olympus Mons."
            "A day on Venus is longer than a year on Venus."
            "Saturn's rings are made of ice and rock particles."
            "Neptune has the strongest winds in the solar system, reaching up to 1,200 mph."
             "The Great Red Spot on Jupiter has been raging for at least 350 years."
            "Pluto has five moons: Charon, Styx, Nix, Kerberos, and Hydra."
            "The International Space Station orbits Earth every 90 minutes."
            "A black hole is so dense that not even light can escape its gravity."
             "The first human in space was Yuri Gagarin in 1961."
            "The coldest place in the universe is the Boomerang Nebula, which is -272°C."
        ]
        await ctx.send(random.choice(spacefacts))


    @commands.command(name="parrot")
    @commands.has_permissions(manage_messages=True)
    async def parrot(self, ctx: commands.Context, *, args: str = None):
        """Repeat a message in any channel or send a DM, with optional self-destruct timing.

        Usage:
        - !parrot <channel_id> <duration> <message>
        - !parrot @user <duration> <message>
        - !parrot <user_id> <duration> <message>
        - !parrot <duration> <message>       (current channel)
        - !parrot <message>                  (just repeats, no delete)
        """

        if not args:
            return await ctx.send("❌ Please provide a message to parrot!", delete_after=5)

        # ----------------------------------------------------
        # STEP 1: Extract possible target (channel or user)
        # ----------------------------------------------------
        parts = args.split(None, 1)

        target_channel = None
        target_user = None
        delete_original = True
        found_target = False
        duration = 0  # default: no self-destruct

        # Try to parse first word as target
        if len(parts) >= 2:
            target_arg = parts[0].strip("<>@!#&")

            if target_arg.isdigit():
                try:
                    # Try channel
                    target_channel = self.bot.get_channel(int(target_arg))
                    if target_channel:
                        rest = parts[1]
                        delete_original = False
                        found_target = True
                    else:
                        # Try user
                        target_user = await self.bot.fetch_user(int(target_arg))
                        if target_user:
                            rest = parts[1]
                            delete_original = False
                            found_target = True
                except (ValueError, discord.NotFound):
                    pass

            # Mentioned user → DM
            if not found_target and ctx.message.mentions:
                target_user = ctx.message.mentions[0]
                rest = parts[1]
                delete_original = False
                found_target = True

        # No target found → send to the current channel
        if not found_target:
            target_channel = ctx.channel
            rest = args

        # ----------------------------------------------------
        # STEP 2: Parse duration (optional)
        # ----------------------------------------------------
        rest_parts = rest.split(None, 1)

        if rest_parts[0].isdigit():
            duration = int(rest_parts[0])
            if len(rest_parts) == 1:
                return await ctx.send("❌ Please provide a message after the duration!", delete_after=5)
            message_content = rest_parts[1]
        else:
            message_content = rest

        # ----------------------------------------------------
        # STEP 3: Send message with typing + optional delete
        # ----------------------------------------------------
        try:
            # DM MODE
            if target_user:
                dm = await target_user.create_dm()
                async with dm.typing():
                    await asyncio.sleep(2)
                    sent = await dm.send(message_content)

                await ctx.message.add_reaction("📬")
                await ctx.send(
                    f"✅ DM sent to {target_user.name}!"
                    + (f" (self-destruct in {duration}s)" if duration > 0 else ""),
                    delete_after=5
                )

            # CHANNEL MODE
            else:
                allowed_mentions = discord.AllowedMentions(everyone=True, users=True, roles=True)

                async with target_channel.typing():
                    await asyncio.sleep(2)
                    sent = await target_channel.send(
                        message_content,
                        allowed_mentions=allowed_mentions
                    )

                if delete_original:
                    try:
                        await ctx.message.delete()
                    except discord.Forbidden:
                        pass
                else:
                    await ctx.message.add_reaction("✅")

            # SELF-DESTRUCT TIMER
            if duration > 0:
                await asyncio.sleep(duration)
                try:
                    await sent.delete()
                except discord.NotFound:
                    pass

        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send messages there!", delete_after=5)


    @commands.command(name="eightball", aliases=["8ball"])
    async def eightball(self, ctx, *, question: str = None):

        response = random.choice(self.eightball_data["responses"])
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=response,
            color=0x2C3E50
        )

        if question:
            embed.set_footer(text=f"Question: {question}")

        await ctx.send(embed=embed)

    @commands.command(name="ghosttype")
    @commands.has_permissions(manage_messages=True)
    async def ghosttype(self, ctx, channel_id: int, duration: int):
        """Ghost typing in a channel without sending a message."""

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return await ctx.send("Channel not found!")

        # Flicker types silently for <duration> seconds
        async with channel.typing():
            await asyncio.sleep(duration)

        # confirmation in the command channel
        await ctx.send(f"Typing for {duration} seconds in <#{channel_id}> complete 👻")

    @commands.command(name="setprefix")
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, ctx, new_prefix: str):
        """Set a custom prefix for this server."""

        if not ctx.guild:
            return await ctx.send("Prefixes can only be changed in servers.")

        if len(new_prefix) > 5:
            return await ctx.send("Let's keep prefixes 5 characters or less, starlight ✨")

        # make sure the bot has a prefixes dict
        if not hasattr(self.bot, "prefixes"):
            self.bot.prefixes = {}

        # update in-memory prefixes
        self.bot.prefixes[str(ctx.guild.id)] = new_prefix

        # save to file so it survives restarts
        with open(PREFIX_FILE, "w") as f:
            json.dump(self.bot.prefixes, f, indent=2)

        await ctx.send(f"✨ Prefix set to `{new_prefix}` for this server!")

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Show how long Flicker has been online."""
        start = getattr(self.bot, "start_time", None)
        if start is None:
            return await ctx.send("I just woke up and don't remember when. Try again in a bit? 👻")

        delta = datetime.utcnow() - start
    # break into days/hours/minutes/seconds
        seconds = int(delta.total_seconds())
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        formatted = " ".join(parts)
        await ctx.send(f"⏱️ I've been awake for **{formatted}**.")

    async def find_message_across_guilds(self, ctx, message_id: int):
        """Search for a message by ID across all channels the bot can access, similar to how parrot works."""
        # First try the current channel (most common case)
        try:
            message = await ctx.channel.fetch_message(message_id)
            return message
        except (discord.NotFound, discord.Forbidden):
            pass
        except Exception:
            pass
        
        # Search across all guilds and channels
        for guild in self.bot.guilds:
            # Get all text channels the bot can see
            for channel in guild.text_channels:
                # Skip if we already tried this channel
                if channel.id == ctx.channel.id:
                    continue
                
                # Check if bot has permission to read message history
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                
                try:
                    message = await channel.fetch_message(message_id)
                    return message
                except discord.NotFound:
                    continue
                except discord.Forbidden:
                    continue
                except Exception:
                    continue
        
        return None

    @commands.command(name="react")
    async def react(self, ctx, message_id: int, emoji: str):
        """React to a message with a specific emoji.
        
        Usage: !react [message_id] [emoji]
        """
        # Search for the message across all accessible channels
        target_message = await self.find_message_across_guilds(ctx, message_id)
        
        if not target_message:
            await ctx.send("i can't react with that! reactions must be in emojis, not text or images")
            return

        # Try to react with the emoji
        try:
            await target_message.add_reaction(emoji)
            # Success - add checkmark to command message
            await ctx.message.add_reaction("✅")
        except discord.HTTPException:
            # Emoji is invalid or can't be used
            await ctx.send("i can't react with that! reactions must be in emojis, not text or images")
        except discord.Forbidden:
            await ctx.send("i can't react with that! reactions must be in emojis, not text or images")
        except Exception:
            await ctx.send("i can't react with that! reactions must be in emojis, not text or images")

    @commands.command(name="reply")
    async def reply(self, ctx, message_id: int, *, content: str):
        """Reply to a specific message by ID.
        
        Usage: !reply [message_id] [content]
        """
        # Search for the message across all accessible channels
        target_message = await self.find_message_across_guilds(ctx, message_id)
        
        if not target_message:
            await ctx.send("❌ i can't reply to that.")
            return

        # Try to reply to the message
        try:
            await target_message.reply(content)
            # Success - add checkmark to command message
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            await ctx.send("❌ i can't reply to that.")
        except Exception:
            await ctx.send("❌ i can't reply to that.")
    
    @commands.command(name="servers")
    async def servers(self, ctx):
        """Display the list of servers the bot is in."""
        guilds = self.bot.guilds
        if not guilds:
            await ctx.send("❌ i'm not in any servers.")
            return

        embed = discord.Embed(
            title="Servers",
            description=" ",
            color=0x00FF00,
        )

        for guild in guilds:
            embed.add_field(name=guild.name, value=f"Members: {guild.member_count}", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="leaveserver")
    async def leave_server(self, ctx, *, server_name: str):
        """Leave a specific server."""
        guild = discord.utils.get(self.bot.guilds, name=server_name)
        if not guild:
            await ctx.send("❌ i'm not in that server.")
            return
        if guild == ctx.guild:
            await ctx.send("❌ i can't leave *this* server! you must use the command in a different server.")
            return
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("❌ you don't have permission to leave servers.")
            return

        await guild.leave()
        await ctx.send(f"✅ left the server: {guild.name}")

async def setup(bot):
    await bot.add_cog(MiscCog(bot))
