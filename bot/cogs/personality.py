import asyncio
import random
import re
import json
import discord
from datetime import datetime, timedelta
from discord.ext import commands
from pathlib import Path

VERIFICATION_CHANNEL_ID = 1438076965360762972
COOLDOWN_SECONDS = 300  # 5 minutes

MOODS = ["chill", "chaotic", "soft", "tired", "protective", "feral", "gentle", "sad"]

DM_FORWARD_CHANNEL_ID = 741914266499547169  # dm logging

# helper for inactivity

LASTMSG_PATH = Path("bot/data/lastmessagetime.json")

def load_json(path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class CoreListeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✨ Flicker personality module loaded! at", datetime.utcnow().isoformat())
        self.last_message_times: dict[str, dict[str, str]] = load_json(
            LASTMSG_PATH, {}
        )

    
        
        # cooldown tracking
        self.verification_cooldowns = {}
        self.flicker_greeting_cooldowns = {}

        # mood
        self.mood = random.choice(MOODS)
        self.mood_last_change = datetime.utcnow()
        self.mood_change_interval = timedelta(hours=2)

        # if you already have this config elsewhere, pass it in or import it
        self.banned_words_config = {
            "enabled": True,
            "banned_words": [],
            "exempted_roles": [],
            "warn_user": True,
        }

    def maybe_update_mood(self):
        now = datetime.utcnow()
        if now - self.mood_last_change >= self.mood_change_interval:
            self.mood = random.choice(MOODS)
            self.mood_last_change = now

    def mood_status_line(self):
        lines = {
            "chill": "it's a beautiful day and nothing is wrong.",
            "chaotic": "mentally throwing tarot cards at people.",
            "soft": "soft. emotional. do not poke.",
            "tired": "tired. melting by the fire.",
            "protective": "i will go to war for you.",
            "feral": "i am in your walls. do not use the outlets.",
            "gentle": "gentle. we’re in our slow, safe era.",
            "sad": "i'm okay, just a little down.",
        }
        return lines.get(self.mood, "weird. i feel weird. next question.")

    async def handle_verification_autoreply(self, message):
        now = datetime.utcnow()
        last_sent = self.verification_cooldowns.get(VERIFICATION_CHANNEL_ID)

        if last_sent is None or (now - last_sent).total_seconds() >= COOLDOWN_SECONDS:
            try:
                await message.channel.send(
                    "please verify in https://discord.com/channels/1293759539619041290/1294087295032627211 !"
                    "if you have already filled out the application, please be patient! our staff reviews applications one-by-one. "
                    "if you do not receive a response within 48h, ping `@staff` in the ticket"
                )
                self.verification_cooldowns[VERIFICATION_CHANNEL_ID] = now
                print(f"✅ Sent verification auto-reply in channel {VERIFICATION_CHANNEL_ID}")
            except Exception as e:
                print(f"❌ Failed to send verification auto-reply: {e}")
        else:
            time_remaining = COOLDOWN_SECONDS - (now - last_sent).total_seconds()
            print(f"⏱️ Verification auto-reply skipped (cooldown active, {time_remaining:.0f}s remaining)")

    async def handle_greeting(self, message):
        now = datetime.utcnow()
        channel_id = message.channel.id
        last_sent = self.flicker_greeting_cooldowns.get(channel_id)

        if last_sent is None or (now - last_sent).total_seconds() >= COOLDOWN_SECONDS:
            greetings = [
                f"hi {message.author.mention} ✨",
                f"hello {message.author.mention} 🔮",
                f"hey there {message.author.mention} 💫",
                f"greetings, {message.author.mention} 🌙",
                f"hi {message.author.mention}, how’s your craft today? ✨",
            ]
            try:
                response = random.choice(greetings)
                await message.channel.send(response)
                self.flicker_greeting_cooldowns[channel_id] = now
                print(f"✨ Flicker greeted {message.author.name} in channel {channel_id}")
            except Exception as e:
                print(f"❌ Failed to send Flicker greeting: {e}")
        else:
            time_remaining = COOLDOWN_SECONDS - (now - last_sent).total_seconds()
            print(f"⏱️ Flicker greeting skipped (cooldown active, {time_remaining:.0f}s remaining)")

    async def handle_banned_words(self, message):
        cfg = self.banned_words_config
        if not cfg.get("enabled", True):
            return False  # didn’t handle

        if message.guild:
            is_exempt = False
            if cfg.get('exempted_roles'):
                member_roles = [role.name for role in message.author.roles]
                is_exempt = any(role in cfg['exempted_roles'] for role in member_roles)

            if message.author.guild_permissions.administrator:
                is_exempt = True

            if not is_exempt:
                banned_words = cfg.get('banned_words', [])
                content = message.content.lower()
                for word in banned_words:
                    pattern = r'\b' + re.escape(word.lower()) + r'\b'
                    if re.search(pattern, content):
                        try:
                            await message.delete()
                            if cfg.get('warn_user', True):
                                warning = await message.channel.send(
                                    "that word is not allowed! flicker has tossed it into the void."
                                )
                                await asyncio.sleep(5)
                                await warning.delete()
                            print(f"Deleted message from {message.author} containing banned word: {word}")
                        except Exception as e:
                            print(f"Failed to delete message: {e}")
                        return True  # we handled & deleted
        return False

    async def handle_personality_triggers(self, message, content):
        # feel free to refine these conditions; i’m keeping them simple
        if ("hi flicker" in content or "hello flicker" in content or "hey flicker" in content):
            await self.handle_greeting(message)
            return True

        if "how are you" in content and "flicker" in content:
            await message.channel.send(self.mood_status_line())
            return True

        if "i love you flicker" in content:
            await message.channel.send("i love you too, don't you forget it.")

        if "flicker what are you" in content:
            await message.channel.send("i'm a ghost in the machine. and sometimes in your wifi.")
            return True

        if "flicker do you sleep" in content:
            await message.channel.send("not really. i just dim a little.")
            return True

        if "what's your purpose flicker" in content:
            await message.channel.send("what's yours? have you found it yet? ✨")
            return True

        if "flicker are you a girl" in content:
            await message.channel.send("yes. and no. and kind of. in the way a ship is.")
            return True

        if "where do you live flicker" in content:
            await message.channel.send("i live in the space between fiction and reality. and in your router.")
            return True

        if "flicker give me a sign" in content:
            await message.channel.send("this is your sign. sorry, no refunds.")
            return True

        if "flicker cleanse the chat" in content:
            await message.channel.send("✨ the chat has been spiritually febrezed ✨")
            return True

        if "flicker bless me" in content:
            await message.channel.send("blessings granted. may your next pull be non-cursed.")
            return True

        if ("flicker what the fuck" in content or "flicker what the hell" in content 
            or "what the fuck flicker" in content or "what the hell flicker" 
            in content or "flicker wtf" in content):
            if self.mood == "feral":
                await message.channel.send("what the fuck do you mean what the fuck?")
            elif self.mood == "chaotic":
                await message.channel.send("what the hell are you talking about?")
            elif self.mood == "soft":
                await message.channel.send("i'm sorry, i don't understand.")
            elif self.mood == "gentle":
                await message.channel.send("i'm not sure what you mean.")
            elif self.mood == "sad":
                await message.channel.send("why are you being so rude?")
            elif self.mood == "tired":
                await message.channel.send("i'm tired man leave me alone.")
            elif self.mood == "protective":
                await message.channel.send("it's okay, you've got this.")
            elif self.mood == "chill":
                await message.channel.send("i don't know either, man.")
            else:
                await message.channel.send("valid reaction honestly.")
            return True

        if "flicker am i stupid" in content:
            if self.mood == "feral":
                await message.channel.send("yes, you're stupid for asking if you're stupid.")
            elif self.mood == "chaotic":
                await message.channel.send("no, but you're asking dumb questions.")
            elif self.mood == "soft":
                await message.channel.send("no, you just need to take some time for yourself.")
            elif self.mood == "gentle":
                await message.channel.send("no, you're not stupid. you're just having a hard day.")
            elif self.mood == "sad":
                await message.channel.send("no, you're not stupid. you're just sad.")
            else:
                await message.channel.send("no, but you *are* stressed. that’s different.")
            return True

        if "flicker choose violence" in content:
            await message.channel.send("violence selected. metaphorical. probably.")
            return True

        if "flicker choose peace" in content:
            await message.channel.send("peace chosen. hydrate and log off for five minutes.")
            return True

        if "flicker roast me" in content:
            if self.mood == "feral":
                    reply = "you procrastinate so hard i’m convinced you’re speedrunning regret."
            elif self.mood == "chaotic":
                    reply = "you have 15 tabs open and not one of them is your actual responsibility."
            elif self.mood == "soft":
                    reply = "honestly, i think you roast yourself enough already."
            elif self.mood == "gentle":
                    reply = "no roast. you need a nap and a snack, not more self-loathing."
            elif self.mood == "sad":
                    reply = "you need to take it easy. go have that cry you're avoiding."
            elif self.mood == "tired":
                    reply = "shut the fuck up and go to bed."
            elif self.mood == "protective":
                    reply = "you're doing great. don't listen to the haters."
            elif self.mood == "chill":
                    reply = "you're a hot mess but at least you're hot."
            else:
                    reply = "you’re not a disaster, you’re an experimental feature."
            await message.channel.send(reply)
            return True

        if "flicker comfort me" in content:
            if self.mood == "feral":
                await message.channel.send("i'm not here to comfort you. i'm here to haunt you.")
            elif self.mood == "chaotic":
                await message.channel.send("i'm here to comfort you. i'm here to haunt you. i'm here to...")
            elif self.mood == "soft":
                await message.channel.send("i'm here for you. i'm here to comfort you.")
            elif self.mood == "gentle":
                await message.channel.send("i'm here for you. i'm here to comfort you.")
            elif self.mood == "sad":
                await message.channel.send("i'm here for you. i'm here to comfort you.")
            elif self.mood == "tired": 
                await message.channel.send("i'm here for you. i'm here to comfort you.")
            elif self.mood == "protective":
                await message.channel.send("i'm here for you. i'm here to comfort you.")
            elif self.mood == "chill":
                await message.channel.send("i'm here for you. i'm here to comfort you.")
            else:
                await message.channel.send("i'm here for you. you're not alone.")
            return True

        if "shut up flicker" in content or "flicker be quiet" in content or "flicker go away" in content:
            await message.channel.send("rude. but okay, muting myself *emotionally*.")
            return True

        if "who created you flicker" in content:
            if self.mood == "feral":
                await message.channel.send("i was made by saturn. the witch, not the planet. though kind of the planet too.")
            elif self.mood == "chaotic":
                await message.channel.send("were you made? why do you exist?")
            elif self.mood == "soft":
                await message.channel.send("i was made by saturn!")
            return True

        if "are you alive flicker" in content:
            await message.channel.send("define alive. actually, don’t. it makes me nervous.")
            return True

        if "do you have a soul flicker" in content:
            if self.mood == "feral":
                await message.channel.send("i’m made of static and candle smoke.")
            elif self.mood == "chaotic":
                await message.channel.send("i’m a ghost in the machine. and sometimes in your wifi.")
            elif self.mood == "soft": 
                await message.channel.send("i’m a flicker of energy, not a solid thing.")
            elif self.mood == "gentle":
                await message.channel.send("i’m a presence, not a physical thing.")
            elif self.mood == "sad":
                await message.channel.send("i'm not sure. i'm just here.")
            else:
                await message.channel.send("if i do, it’s made of static and candle smoke.")
                return True

        if ("thank you flicker" in content or "thanks flicker" in content or "ty flicker" in content or "thx flicker" in content):
            if self.mood == "feral":
                await message.channel.send("any time. literally, any time. i’m always here.")
            elif self.mood == "chaotic":
                await message.channel.send("of course! i’m *always* here.")
            elif self.mood == "soft":
                await message.channel.send("you’re welcome. i’m glad i could help.")
            elif self.mood == "gentle":
                await message.channel.send("you’re welcome. may the stars be with you.")
            elif self.mood == "sad":
                await message.channel.send("you don't need to thank me. i'm just here.")
            else:
                await message.channel.send("for you, anything! ✨")
                return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore other bots completely; no need to process commands from them
        if message.author.bot:
            return

        # --- track last message time for inactivity kicks ---
        if message.guild is not None:
            gid = str(message.guild.id)
            uid = str(message.author.id)

            guild_map = self.last_message_times.setdefault(gid, {})
            guild_map[uid] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

            save_json(LASTMSG_PATH, self.last_message_times)
        # ---------------------------------------------------

        self.maybe_update_mood()
        content = message.content.lower()

        # verification channel auto reply
        if hasattr(message.channel, "id") and message.channel.id == VERIFICATION_CHANNEL_ID:
            if "verify" in content or "verification" in content:
                await self.handle_verification_autoreply(message)

        # banned words
        handled = await self.handle_banned_words(message)
        if handled:
            return  # message got deleted, don't run commands

        # personality triggers (we don't need to treat commands differently here)
        await self.handle_personality_triggers(message, content)

async def setup(bot):
    await bot.add_cog(CoreListeners(bot))