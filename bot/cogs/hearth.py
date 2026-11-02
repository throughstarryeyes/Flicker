import discord
from discord.ext import commands
import random
from datetime import datetime
from bot.services.database import store_offering, get_offerings


class HearthCog(commands.Cog, name="Hearth"):
    """Flicker's home! The Hearth is a place to leave offerings for Flicker."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.accept_lines = [
            "Flicker accepts your offering and places it atop the hearth.",
            "A small spark rises from the hearth as Flicker places your offering.",
            "Flicker takes your offering and scurries away.",
            "The hearth hums quietly as Flicker stores your gift.",
            "Flicker hides your offering somewhere only she knows about.",
        ]

        self.empty_altar_lines = [
            "The hearth is quiet. Flicker is waiting for the first offering.",
            "Bare wood, soft dust, and a single flickering light. No offerings… yet.",
        ]

        self.tended_lines = [
            "Flicker rearranges the offerings. Some disappear in a sparkling light. Some stay.",
            "Flicker sweeps wax and dust from the hearth. The energy feels cleaner now.",
            "The hearth cloth is shaken out; the offerings settle into new places.",
        ]

        # keyword / alias groups → extra reactions
        self.keyword_reactions = {
            # simple single-word triggers
            ("star",): [
                "The flames jump higher for a moment, as if trying to touch the stars.",
                "Little sparks drift upward like tiny constellations."
            ],
            ("moon",): [
                "For a moment, the firelight flickers blue.",
                "For a second, the hearthlight feels cool and distant, like the moon itself."
            ],
            ("ghost",): [
                "The shadows around the hearth bend in a strange, familiar way.",
                "For a moment, something unseen seems to sit beside the hearth."
            ],
            ("bone",): [
                "The fire pops once, sharply, as if acknowledging something ancient.",
                "Flicker handles the offering with unusual care, as if it carries a story."
            ],
            ("coffee",): [
                "The scent of roasted beans seems to hang in the air, even if it wasn't really there.",
                "Flicker perks up. She takes a pinch for herself and places the rest on the mantle."
            ],
            ("tea",): [
                "A gentle warmth spreads out from the hearth, like a cup between both hands.",
                "The hearth smells faintly of herbs and steam."
            ],
            ("flower",): [
                "For a moment, you could swear you see petals in the fire.",
                "The hearth glows softer, cradling the delicate offering."
            ],
            ("rock",): [
                "The offering lands with a small, satisfying clink among other quiet treasures.",
                "Flicker tucks the stone somewhere safe, like a dragon with a very small hoard."
            ],
            ("code",): [
                "The hearthlight flickers in a suspiciously binary pattern.",
                "Flicker hums a tiny tune that sounds like a computer booting up."
            ],
            ("tarot",): [
                "The hearthlight shifts to a deep, rich purple for a moment.",
                "Flicker props up the card among the offerings, as if it belongs there.",
                "The fire crackles once, like a card being drawn."
            ],

            # music
            ("music", "song", "melody", "tune"): [
                "Flicker hums softly, as if remembering the sound of your offering.",
                "The flames flicker melodically, as if they’re playing along."
            ],

            # crystals / gems / stones
            ("crystal", "gem", "stone"): [
                "The hearthlight refracts strangely, casting little rainbow shards across the floor.",
                "Flicker tucks the crystal away as if adding it to a secret hidden hoard.",
                "A faint chiming sound echoes when the crystal touches the hearth."
            ],

            # little trinkets
            ("trinket",): [
                "Flicker turns the trinket over in her hand before setting it down somewhere safe and unoccupied.",
                "The hearth glimmers like it remembers something small and precious."
            ],

            # jewelry group
            ("jewelry", "bracelet", "necklace", "ring"): [
                "Metal catches the firelight, glowing softly before disappearing into the hearth.",
                "Flicker handles the jewelry with delicate sparks, treating it like something sacred.",
                "You hear a small clink as the piece finds its place among hidden treasures."
            ],

            # bottles / potions / vials
            ("bottle", "potion", "vial"): [
                "Soft bubbling sounds rise from the hearth, even though nothing is actually boiling.",
                "The flames shift color for a moment, tasting the magic inside the bottle."
            ],

            # candles (expanded aliases)
            ("candle", "candles", "wick", "wax"): [
                "The hearth leans toward the offering like greeting an old friend.",
                ":flame: A tiny flame jumps from the hearth to the candle and back again, like a kiss.",
                "The air warms, smelling faintly of wax and something comforting.",
                "The flames lean toward the imagined wick, as if greeting a cousin.",
                "Wax seems to shimmer on the stones around the hearth."
            ],

            # herbs and plants
            ("herb", "herbs", "plant", "plants", "greens", "lavender", "thyme"): [
                "The hearth snaps gently, releasing an imagined herbal aroma.",
                "Flicker hums softly as the herbs vanish into the fire’s memory."
            ],

            # planets EXCEPT saturn
            ("mercury", "venus", "earth", "mars", "jupiter", "uranus", "neptune"): [
                "For a moment, the hearthfire swirls into a tiny orbiting sphere.",
                "The flames shimmer with cosmic curiosity.",
                "A faint planetary glow surrounds the offering before it vanishes."
            ],

            # special: miles :)
            ("miles",): [
                "The hearthlight brightens fondly.",
                "Flicker responds with a warm, mischievous spark, like she knows exactly who that is.",
                "The fire crackles once in a tone that can only be described as ‘affectionate side-eye.’"
            ],

            # special: saturn (you)
            ("saturn",): [
                "The hearth recognizes you instantly; its flames soften in greeting.",
                "Flicker hesitates for a moment, like she was expecting you.",
                "The flames flicker too quickly, as if breaking the rules of reality themselves. Flicker disappears with a laugh."
            ],

            # FIRE
            ("fire", "flame", "ember", "spark", "ash"): [
                "The hearth flares warmly, recognizing a sibling flame.",
                "Sparks dance upward like they’re celebrating your offering."
            ],

            # WATER
            ("water", "sea", "ocean", "rain", "river", "tide", "lake"): [
                "The flames hiss softly, steam forming a tiny swirling shape.",
                "The hearth settles, glowing a calmer blue-orange for a heartbeat.",
                "You swear you hear a single droplet fall somewhere inside the hearth."
            ],

            # AIR
            ("air", "wind", "breeze", "storm", "sky", "cloud"): [
                "A sudden draft circles the hearth, as if carrying your offering inward.",
                "The flame stretches tall, pulled by an unseen upward current.",
                "Ash rises in a delicate spiral, then gently returns to the stones."
            ],

            # EARTH
            ("earth", "soil", "dirt", "clay", "root", "stone", "mud"): [
                "The hearth hums deeply.",
                "The fire glows lower and richer, like molten amber.",
                "Flicker presses the offering into the coals as though planting it."
            ],

            # SPIRIT / AETHER / ARCANA
            ("spirit", "soul", "aether", "ether", "arcana", "magic"): [
                "The flame wavers—not from wind, but recognition.",
                "For a moment, the fire burns unnaturally still, listening.",
                "A soft ring of light appears above the hearth before fading away."
            ],
            # emotions
            ("happiness", "joy"): [
                "Flicker smiles as she takes your offering!",
                "Flicker leans towards the warmth of your offering.",
                "Your offering puts a smile on Flicker's face"
            ],
            ("patience",): [
                "Flicker sits with your offering for a long time.",
                "Flicker takes your offering and sits with it for a while.",
                "Flicker sits with your offering by the fire for a long time."
            ],
            ("love",): [
                "Flicker nestles your offering close to her heart.",
                "Flicker takes your offering and holds it close to her heart.",
                "Flicker cradles your offering in her arms."
            ],
            ("sadness",): [
                "Flicker cradles your offering, as if it's something precious and gentle.",
                "Flicker cradles your offering by the warmth of the fire.",
                "Flicker places your offering somewhere safe and warm."
            ],
            ("anger",): [
                "The fire crackles loudly, as if it's trying to calm you down.",
                "The fire leans towards your offering, recognizing itself in it."
            ],
            ("fear",): [
                "Flicker holds your offering like it's precious and fragile.",
                "Flicker leaves your offering by the fire, where it can be safe."
            ]
        }

        # super rare lines (low chance)
        self.rare_responses = [
            "For a moment, the entire hearth goes still, as if holding its breath around your offering.",
            "The flames spell out a shape you almost recognize... and then collapse back into ordinary fire.",
            "You feel, very faintly, that Flicker whispers a thank-you only you could have heard.",
            "Something under the hearth clicks into place, as if your offering completed a pattern.",
        ]

    @commands.command(name="offer", aliases=["offering"])
    async def offer(self, ctx: commands.Context, *, item: str):
        """Leave an offering for Flicker."""

        if ctx.guild is None:
            return await ctx.send("the hearth only exists in servers, not DMs.")

        item = item.strip()

        if not item:
            return await ctx.send(
                ":sparkles: Please specify what you'd like to offer."
                "I can't see images or attachments, so describe them to me."
            )

        timestamp = datetime.now()

        # store in database
        await store_offering(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            item=item,
            created_at=timestamp,
        )

        base_line = random.choice(self.accept_lines)
        normalized = item.lower()
        extra_lines = []

        # keyword reactions (including Saturn, Miles, elements, etc.)
        for keywords, reactions in self.keyword_reactions.items():
            if any(k in normalized for k in keywords):
                extra_lines.append(random.choice(reactions))

        # small chance for a rare extra line
        if random.random() < 0.05:  # 5% chance
            extra_lines.append(random.choice(self.rare_responses))

        # build final text:
        # if we got any keyword / rare reactions, use ONLY those.
        # if nothing matched, fall back to a generic 'accept' line.
        if extra_lines:
            flavor_text = "\n".join(extra_lines)
            message = f"{flavor_text}\n\n✨ Offering received: **{item}**"
        else:
            message = f"{base_line}\n\n✨ Offering received: **{item}**"

        await ctx.send(message)

    @commands.command(name="hearth", aliases=["altar"])
    async def hearth(self, ctx: commands.Context):
        """View offerings stored at the hearth."""

        if ctx.guild is None:
            return await ctx.send("the hearth only exists in servers, not DMs.")

        offerings = await get_offerings(ctx.guild.id)

        if not offerings:
            return await ctx.send(random.choice(self.empty_altar_lines))

        embed = discord.Embed(
            title="🔥 Flicker's Hearth Offerings",
            color=discord.Color.orange(),
        )

        for o in offerings[:25]:  # show last 25 only
            created = datetime.fromisoformat(o["created_at"]).strftime("%Y-%m-%d %H:%M")
            user = ctx.guild.get_member(o["user_id"])
            user_display = user.display_name if user else "Someone"

            embed.add_field(
                name=f"{user_display} offered:",
                value=f"• {o['item']}  \n*left at {created}*",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="tend")
    async def tend(self, ctx: commands.Context):
        """Clean/tend Flicker's altar."""
        await ctx.send(random.choice(self.tended_lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(HearthCog(bot))
