import discord
from discord.ext import commands
from discord import app_commands
import json
import random

class ReferenceCog(commands.Cog, name="Reference"):
    def __init__(self, bot):
        self.bot = bot
        with open('bot/data/herbs.json', 'r') as f:
            self.herbs = json.load(f)
        with open('bot/data/crystals.json', 'r') as f:
            self.crystals = json.load(f)
        with open('bot/data/elements.json', 'r') as f:
            self.elements = json.load(f)
        with open("bot/data/planetary_correspondences.json", "r", encoding="utf-8") as f:
            raw = json.load(f)

        # if the file has a top-level "planets" key, use that
        self.planets = raw.get("planets", raw)

        # make sure this is here too so the earlier error doesn’t come back
        self.planet_aliases: dict[str, str] = {
            "sol": "sun",
            "luna": "moon",
        }
    # ----------------------------------------- HELPERS -----------------------------------------

    def resolve_planet(self, name: str | None) -> tuple[str, dict] | None:
        """
        If name is None -> random planet.
        Else resolve case-insensitively + via alias map.
        Returns (key, data) or None.
        """
        if not self.planets:
            return None

        # random planet
        if name is None:
            key = random.choice(list(self.planets.keys()))
            return key, self.planets[key]

        raw = name.strip().lower()

        # direct match
        if raw in self.planets:
            return raw, self.planets[raw]

        # alias match
        if raw in self.planet_aliases:
            alias_key = self.planet_aliases[raw]
            if alias_key in self.planets:
                return alias_key, self.planets[alias_key]

        # loose case-insensitive match
        for k in self.planets.keys():
            if k.lower() == raw:
                return k, self.planets[k]

        return None

    def line_from_str(self, label: str, value: str | None) -> str | None:
        """
        Take a comma-separated string from JSON and turn it into:
        **label:** value
        Skip if it's empty or whitespace.
        """
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        return f"**{label}:** {value}"

    def build_planet_embed(self, key: str, data: dict) -> discord.Embed:
        """Build the reference-card style embed."""
        name = data.get("name", key.title())

        embed = discord.Embed(
            title=f"🪐 {name}",
            color=discord.Color.blurple()
        )
        # Order and labels for the lines
        fields = [
            ("colors", "colors"),
            ("metals", "metals"),
            ("crystals", "crystals"),
            ("plants", "spices, herbs, or plants"),
            ("foods", "foods"),
            ("scents", "scents"),
            ("animals", "animals"),
            ("physicality", "physicality"),
            ("traits", "traits"),
            ("archetypes", "archetypes"),
            ("activities", "activities"),
            ("places", "places"),
            ("symbols", "symbols"),
            ("days_and_times", "days and times"),
        ]

        lines: list[str] = []

        for json_key, label in fields:
            line = self.line_from_str(label.capitalize(), data.get(json_key))
            if line:
                lines.append(line)

        desc = "\n".join(lines)
        # safety trim for Discord’s 4096-char description limit
        if len(desc) > 4000:
            desc = desc[:3997] + "..."

        embed.description = desc
        return embed

    # -------------------------------------------------------- COMMANDS -------------------------------------------------------

    # planet command ----------------------------------------------

    @commands.command(name="planet", aliases=["celestialbody", "planetary"])
    async def planet_cmd(self, ctx: commands.Context, *, name: str | None = None):
        """
        Planetary correspondence reference card.

        !planet          -> random planet
        !planet sun      -> Sun correspondences
        !planet mercury  -> Mercury correspondences
        """
        resolved = self.resolve_planet(name)
        if resolved is None:
            return await ctx.send(
                "I don’t have any planetary correspondences loaded, "
                "or I couldn’t find that planet."
            )

        key, data = resolved
        embed = self.build_planet_embed(key, data)
        embed.set_footer(text=f"planet info for {ctx.author.display_name} written by miles (@chlor0form).")
        await ctx.send(embed=embed)

    # herbs command ----------------------------------------------

    @commands.command(name="herb", aliases=["herbs"])
    async def herb_info(self, ctx, *, herb_name: str = None):
        if not herb_name:
            herb = random.choice(self.herbs)
        else:
            herb = next((h for h in self.herbs if h['name'].lower() == herb_name.lower()), None)
            if not herb:
                available = ", ".join([h['name'] for h in self.herbs[:10]])
                await ctx.send(f"❌ Herb not found! Available: {available}... (and more)")
                return
        
        embed = discord.Embed(
            title=f"🌿 {herb['name']}",
            color=0x2ECC71
        )
        embed.add_field(name="Element", value=herb['element'], inline=True)
        embed.add_field(name="Planet", value=herb['planet'], inline=True)
        embed.add_field(name="Uses", value=herb['uses'], inline=False)
        embed.add_field(name="Properties", value=herb['properties'], inline=False)
        embed.set_footer(text="Use !herb <name> to search for a specific herb")
        
        await ctx.send(embed=embed)

    # crystals command ----------------------------------------------
    
    @commands.command(name="crystal", aliases=["crystals", "stone"])
    async def crystal_info(self, ctx, *, crystal_name: str = None):
        if not crystal_name:
            crystal = random.choice(self.crystals)
        else:
            crystal = next((c for c in self.crystals if c['name'].lower() == crystal_name.lower()), None)
            if not crystal:
                available = ", ".join([c['name'] for c in self.crystals[:10]])
                await ctx.send(f"❌ Crystal not found! Available: {available}... (and more)")
                return
        
        embed = discord.Embed(
            title=f"💎 {crystal['name']}",
            color=0x9B59B6
        )
        embed.add_field(name="Element", value=crystal['element'], inline=True)
        embed.add_field(name="Chakra", value=crystal['chakra'], inline=True)
        embed.add_field(name="Properties", value=crystal['properties'], inline=False)
        embed.add_field(name="Uses", value=crystal['uses'], inline=False)
        embed.set_footer(text="Use !crystal <name> to search for a specific crystal")
        
        await ctx.send(embed=embed)

    # elements command ----------------------------------------------

    @commands.command(name="element", aliases=["elements"])
    async def element_info(self, ctx, *, element_name: str = None):
        if not element_name:
            element_list = "\n".join([f"**{e['name']}** - {e['direction']}" for e in self.elements])
            embed = discord.Embed(
                title="🜁🜂🜃🜄 The Elements",
                description=element_list,
                color=0xE67E22
            )
            embed.set_footer(text="Use !element <name> to learn more about a specific element")
            await ctx.send(embed=embed)
            return
        
        element = next((e for e in self.elements if e['name'].lower() == element_name.lower()), None)
        if not element:
            await ctx.send("❌ Element not found! Available: Fire, Water, Air, Earth, Spirit")
            return
        
        embed = discord.Embed(
            title=f"{element['name']}",
            description=element['description'],
            color=0xE67E22
        )
        embed.add_field(name="Direction", value=element['direction'], inline=True)
        embed.add_field(name="Season", value=element['season'], inline=True)
        embed.add_field(name="Time", value=element['time'], inline=True)
        embed.add_field(name="Zodiac", value=element['zodiac'], inline=False)
        embed.add_field(name="Qualities", value=element['qualities'], inline=False)
        embed.add_field(name="Tools", value=element['tools'], inline=True)
        embed.add_field(name="Colors", value=element['colors'], inline=True)
        
        await ctx.send(embed=embed)

    # herb list command ----------------------------------------------

    @commands.command(name="herblist", aliases=["listherbs", "allherbs"])
    async def herb_list(self, ctx):
        herb_names = [h['name'] for h in self.herbs]
        chunks = [herb_names[i:i+3] for i in range(0, len(herb_names), 3)]
        
        herb_display = "\n".join([" • ".join(chunk) for chunk in chunks])
        
        embed = discord.Embed(
            title="🌿 Complete Herb Index",
            description=f"**{len(herb_names)} Herbs Available:**\n\n{herb_display}",
            color=0x2ECC71
        )
        embed.set_footer(text="Use !herb <name> to view details")
        
        await ctx.send(embed=embed)

# crystal list command ----------------------------------------------
    
    @commands.command(name="crystallist", aliases=["listcrystals", "allcrystals"])
    async def crystal_list(self, ctx):
        crystal_names = [c['name'] for c in self.crystals]
        chunks = [crystal_names[i:i+3] for i in range(0, len(crystal_names), 3)]
        
        crystal_display = "\n".join([" • ".join(chunk) for chunk in chunks])
        
        embed = discord.Embed(
            title="💎 Complete Crystal Index",
            description=f"**{len(crystal_names)} Crystals Available:**\n\n{crystal_display}",
            color=0x9B59B6
        )
        embed.set_footer(text="Use !crystal <name> to view details")
        
        await ctx.send(embed=embed)

    # ------------------------------------------------ SLASH COMMANDS -----------------------------------------------

    # herbs slash command ----------------------------------------------
    
    @app_commands.command(name="herb", description="Learn about magical herb correspondences")
    @app_commands.describe(name="The herb name (leave empty for random)")
    async def herb_slash(self, interaction: discord.Interaction, name: str = None):
        """Slash command for herb information."""
        if not name:
            herb = random.choice(self.herbs)
        else:
            herb = next((h for h in self.herbs if h['name'].lower() == name.lower()), None)
            if not herb:
                available = ", ".join([h['name'] for h in self.herbs[:10]])
                await interaction.response.send_message(f"❌ Herb not found! Available: {available}... (and more)", ephemeral=True)
                return
        
        embed = discord.Embed(
            title=f"🌿 {herb['name']}",
            color=0x2ECC71
        )
        embed.add_field(name="Element", value=herb['element'], inline=True)
        embed.add_field(name="Planet", value=herb['planet'], inline=True)
        embed.add_field(name="Uses", value=herb['uses'], inline=False)
        embed.add_field(name="Properties", value=herb['properties'], inline=False)
        embed.set_footer(text=f"Herb info for {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

# crystals slash command ----------------------------------------------
    
    @app_commands.command(name="crystal", description="Learn about crystal properties and meanings")
    @app_commands.describe(name="The crystal name (leave empty for random)")
    async def crystal_slash(self, interaction: discord.Interaction, name: str = None):
        """Slash command for crystal information."""
        if not name:
            crystal = random.choice(self.crystals)
        else:
            crystal = next((c for c in self.crystals if c['name'].lower() == name.lower()), None)
            if not crystal:
                available = ", ".join([c['name'] for c in self.crystals[:10]])
                await interaction.response.send_message(f"❌ Crystal not found! Available: {available}... (and more)", ephemeral=True)
                return
        
        embed = discord.Embed(
            title=f"💎 {crystal['name']}",
            color=0x9B59B6
        )
        embed.add_field(name="Element", value=crystal['element'], inline=True)
        embed.add_field(name="Chakra", value=crystal['chakra'], inline=True)
        embed.add_field(name="Properties", value=crystal['properties'], inline=False)
        embed.add_field(name="Uses", value=crystal['uses'], inline=False)
        embed.set_footer(text=f"Crystal info for {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(ReferenceCog(bot))
