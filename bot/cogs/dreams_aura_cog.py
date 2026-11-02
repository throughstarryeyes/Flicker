import discord
from discord.ext import commands
import json
import random

class DreamsAuraCog(commands.Cog, name="DreamsAura"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/dreams.json", "r") as f:
            self.dreams = json.load(f)
        with open("bot/data/aura_colors.json", "r") as f:
            self.aura_colors = json.load(f)["colors"]

    # dream commands ----------------------------------------------

    @commands.command(name="dream", aliases=["dreamsymbol", "dreammeaning"])
    async def dream_symbol(self, ctx, *, search_term: str = None):
        if not search_term:
            symbol = random.choice(self.dreams["symbols"])
            embed = discord.Embed(
                title=f"💭 Dream Symbol: {symbol['name']}",
                description=symbol["meaning"],
                color=0x9370DB,
            )
            embed.set_footer(text="Use !dream <symbol> to look up specific symbols")
        else:
            found = None
            search_lower = search_term.lower()

            for symbol in self.dreams["symbols"]:
                if search_lower in symbol["name"].lower():
                    found = symbol
                    break

            if found:
                embed = discord.Embed(
                    title=f"💭 Dream Symbol: {found['name']}",
                    description=found["meaning"],
                    color=0x9370DB,
                )
            else:
                embed = discord.Embed(
                    title="💭 Symbol Not Found",
                    description=f"Couldn't find '{search_term}'. Try: water, flying, falling, snake, house, or use !dream for a random symbol.",
                    color=0x9370DB,
                )

        await ctx.send(embed=embed)

    # dream analysis command

    @commands.command(name="analyzedream", aliases=["dreamanalysis", "interpretdream"])
    async def analyze_dream(self, ctx, *, dream_description: str = None):
        """Analyze a dream description and detect symbolic meanings."""
        if not dream_description:
            embed = discord.Embed(
                title="💭 Dream Analysis",
                description="Describe your dream and I'll detect the symbols within it!\n\n**Usage:** `!analyzedream <your dream description>`\n\n**Example:** `!analyzedream I was flying over water and then I saw a snake`",
                color=0x9370DB,
            )
            await ctx.send(embed=embed)
            return

        dream_lower = dream_description.lower()
        detected_symbols = []

        for symbol in self.dreams["symbols"]:
            if "keywords" in symbol:
                for keyword in symbol["keywords"]:
                    if keyword in dream_lower:
                        if symbol not in detected_symbols:
                            detected_symbols.append(symbol)
                        break

        if not detected_symbols:
            embed = discord.Embed(
                title="💭 Dream Analysis",
                description="I couldn't detect any specific symbols in your dream description. Try describing elements like: water, flying, falling, animals, people, objects, or emotions.\n\nOr use `!dream` to explore dream symbols individually!",
                color=0x9370DB,
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"💭 Dream Analysis for {ctx.author.display_name}",
            description=f"I detected **{len(detected_symbols)}** symbol{'s' if len(detected_symbols) != 1 else ''} in your dream:",
            color=0x9370DB,
        )

        for symbol in detected_symbols[:5]:
            embed.add_field(
                name=f"✨ {symbol['name']}", value=symbol["meaning"], inline=False
            )

        if len(detected_symbols) > 5:
            embed.set_footer(
                text=f"Showing 5 of {len(detected_symbols)} detected symbols | Use !dream <symbol> for more details"
            )
        else:
            embed.set_footer(
                text="Use !dream <symbol> to explore individual symbols further"
            )

        await ctx.send(embed=embed)

    # aura reading command ----------------------------------------------

    @commands.command(name="aura", aliases=["auracolor", "readaura"])
    async def aura_reading(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        aura = random.choice(self.aura_colors)

        embed = discord.Embed(
            title=f"🌈 Aura Reading for {target.display_name}",
            description=f"**{aura['name']} Aura**",
            color=discord.Color.from_rgb(*self._get_color_rgb(aura["name"])),
        )
        embed.add_field(name="Chakra", value=aura["chakra"], inline=True)
        embed.add_field(name="✨ Energy", value=aura["meaning"], inline=False)
        embed.add_field(
            name="👤 Personality Traits", value=aura["personality"], inline=False
        )
        embed.add_field(name="⚠️ Shadow Side", value=aura["shadow"], inline=False)
        embed.set_footer(
            text="Your aura is stable today, but can shift based on your energy!"
        )

        await ctx.send(embed=embed)

    def _get_color_rgb(self, color_name):
        color_map = {
            "Red": (255, 0, 0),
            "Orange": (255, 165, 0),
            "Yellow": (255, 255, 0),
            "Green": (0, 255, 0),
            "Blue": (0, 0, 255),
            "Indigo": (75, 0, 130),
            "Purple": (128, 0, 128),
            "White": (255, 255, 255),
            "Pink": (255, 192, 203),
            "Gold": (255, 215, 0),
            "Silver": (192, 192, 192),
            "Rainbow": (128, 0, 255),
            "Black": (0, 0, 0),
            "Brown": (139, 69, 19),
            "Grey": (128, 128, 128),
            "Teal": (0, 128, 128),
        }
        return color_map.get(color_name, (155, 89, 182))


async def setup(bot):
    await bot.add_cog(DreamsAuraCog(bot))
