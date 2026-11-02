import discord
from discord.ext import commands
from discord import app_commands
import json
import random

class GamesDivinationCog(commands.Cog, name="GamesDivination"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/fortunes.json", "r") as f:
            self.fortunes = json.load(f)
        with open("bot/data/colors.json", "r") as f:
            self.oracle_colors = json.load(f)["colors"]

    # fortune command ----------------------------------------------

    @commands.command(name="fortune")
    async def fortune_teller(self, ctx):
        fortune = random.choice(self.fortunes)

        embed = discord.Embed(
            title="✨ Your Fortune", description=fortune, color=0xFFD700
        )
        embed.set_footer(text=f"Fortune told for {ctx.author.display_name}")

        await ctx.send(embed=embed)

    # pendulum command ----------------------------------------------

    @commands.command(name="pendulum")
    async def pendulum(self, ctx, *, question: str = None):
        if not question:
            await ctx.send(
                "❓ Ask the pendulum a yes/no question! Usage: `!pendulum <your question>`"
            )
            return

        responses = [
            ("Yes", "The pendulum swings strongly in affirmation.", 0x00FF00),
            ("No", "The pendulum swings clearly in denial.", 0xFF0000),
            ("Maybe", "The pendulum circles uncertainly.", 0xFFFF00),
            (
                "Ask again later",
                "The pendulum is still, the answer is not yet clear.",
                0x808080,
            ),
            ("Uncertain", "The pendulum wavers, the energy is mixed.", 0xFFA500),
        ]

        answer, description, color = random.choice(responses)

        embed = discord.Embed(
            title="🔘 Pendulum Reading",
            description=f"**Question:** {question}\n\n**Answer:** {answer}\n\n*{description}*",
            color=color,
        )
        embed.set_footer(text=f"Reading for {ctx.author.display_name}")

        await ctx.send(embed=embed)

    # dice rolling command ----------------------------------------------

    @commands.command(name="roll", aliases=["dice", "rolldice", "diceroll"])
    async def roll_dice(self, ctx, dice: str = "1d6"):
        try:
            rolls, sides = map(int, dice.lower().split("d"))

            if rolls > 100 or sides > 1000:
                await ctx.send("❌ Too many dice or sides! Max: 100d1000")
                return

            results = [random.randint(1, sides) for _ in range(rolls)]
            total = sum(results)

            if len(results) <= 20:
                result_str = ", ".join(map(str, results))
            else:
                result_str = (
                    f"{', '.join(map(str, results[:20]))}... (showing first 20)"
                )

            embed = discord.Embed(title=f"🎲 Rolling {dice}", color=0xE74C3C)
            embed.add_field(name="Results", value=result_str, inline=False)
            embed.add_field(name="Total", value=str(total), inline=False)
            embed.set_footer(text=f"Rolled by {ctx.author.display_name}")

            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send(
                "❌ Invalid format! Use format like: `!roll 2d6` or `!roll 1d20`"
            )

    # coin flip command ----------------------------------------------

    @commands.command(name="coinflip", aliases=["flipcoin", "coin", "flip", "tosscoin"])
    async def coinflip(self, ctx):
        responses = [
            ":coin: . . . the coin spins wildly before landing on heads!",
            ":coin: . . . the coin flips in the air before landing on tails!",
            ":coin: . . . the coin rolls under the table... try again!",
            ":coin: . . . it lands on its edge! :scales:",
        ]
        await ctx.send(random.choice(responses))

    # flame reading command ----------------------------------------------

    @commands.command(name="flamereading", aliases=["flame", "candlereading"])
    async def flame(self, ctx, *, description: str = ""):
        """
        Interpret a candle or fire flame.
        - No description → random omen
        - Description → simple keyword-based reading
        """

        desc = description.lower().strip()

        # -----------------------
        # NO DESCRIPTION → RANDOM
        # -----------------------
        if not desc:
            omens = [
                "A flame suddenly flares, then settles. Your intention just got a boost.",
                "The flame dims, then brightens again. Something hidden is coming to light.",
                "The flame sways side to side; a decision is being made, but not yet final.",
                "A low but steady flame. Slow, patient progress with solid foundations.",
                "A bright, tall flame. Strong willpower and fast movement around this situation.",
                "The flame crackles softly. Outside energy is affecting you.",
                "The wick glows even when the flame is small. Your spark is still here.",
            ]
            omen = random.choice(omens)
            await ctx.send(f"🔥 **Flame Omen**\n{omen}")
            return

        # -----------------------
        # KEYWORD INTERPRETATION
        # -----------------------
        meanings = []

        # steady vs flickering
        if any(word in desc for word in ["steady", "still", "calm", "solid"]):
            meanings.append("A steady flame suggests clear, consistent energy.")

        if any(
            word in desc
            for word in ["flicker", "flickering", "dancing", "wavering", "jumping"]
        ):
            meanings.append(
                "A flickering or dancing flame points to influences; emotional, spiritual, or physical."
            )

        # tall vs low
        if any(word in desc for word in ["tall", "high", "big", "strong"]):
            meanings.append("A tall flame shows strong energy or willpower.")

        if any(word in desc for word in ["low", "small", "weak", "tiny"]):
            meanings.append(
                "A low flame suggests resistance, low energy, or a lack of support."
            )

        # smoke / soot
        if any(word in desc for word in ["smoke", "smoky", "soot", "haze"]):
            meanings.append(
                "Smoke lingers; something is lingering. Attachments, interferences, or energy that needs cleansing."
            )

        # popping / crackling
        if any(
            word in desc
            for word in ["pop", "popping", "crackle", "crackling", "spark", "sparks"]
        ):
            meanings.append(
                "Pop, pop, pop! Someone is talking about you. You may have some conflicts you need to address."
            )

        # colors (optional)
        if "blue" in desc:
            meanings.append(
                "Blue in the flame suggests spiritual or ancestral attention, truth, or protection."
            )
        if "yellow" in desc or "gold" in desc:
            meanings.append(
                "Yellow or gold leans toward joy, confidence, and solar energy."
            )
        if "red" in desc:
            meanings.append("Red is passionate; angry, fiery, deep energy.")
        if "green" in desc:
            meanings.append("Green suggests growth, healing, and nature's energy.")
        if "white" in desc:
            meanings.append(
                "White is pure, clean, and clear. It suggests new beginnings or spiritual energy."
            )
        if "purple" in desc:
            meanings.append(
                "Purple is mystical, magical, and creative. It suggests intuition and spiritual connection."
            )
        if not meanings:
            meanings.append(
                "I wasn't able to detect any specific flame characteristics in your description."
            )

        await ctx.send("🔥 **Flame Reading**\n" + "\n\n".join(meanings))

    # color oracle command ----------------------------------------------

    @commands.command(name="colororacle", aliases=["colorguide", "whatcolor"])
    async def color_oracle(self, ctx):
        """Discover what color energy you need today."""
        color_name = random.choice(list(self.oracle_colors.keys()))
        color_data = self.oracle_colors[color_name]

        embed = discord.Embed(
            title=f"🎨 {color_name.title()}",
            description=f"**{color_data['energy']}**",
            color=0xE91E63,
        )
        embed.add_field(name="Meaning", value=color_data["meaning"], inline=False)
        embed.add_field(name="Guidance", value=color_data["guidance"], inline=False)
        embed.add_field(name="Element", value=color_data["element"], inline=True)
        embed.add_field(name="Chakra", value=color_data["chakra"], inline=True)
        embed.set_footer(
            text=f"Color oracle for {ctx.author.display_name} • Surround yourself with this energy today"
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="whimsy", aliases=["wordoftheday", "randomword", "whimsyword"]
    )
    async def whimsy_word(self, ctx):
        """Receive a whimsical word to inspire your day."""
        whimsy_words = [
            {
                "word": "Serendipity",
                "definition": "Finding something wonderful when you weren't even looking",
                "vibe": "✨ Lucky discoveries await you",
            },
            {
                "word": "Luminescence",
                "definition": "Soft glowing light from within",
                "vibe": "🌟 Your inner light shines bright",
            },
            {
                "word": "Ephemeral",
                "definition": "Beautiful but fleeting, like a sunset",
                "vibe": "🌸 Treasure this fleeting moment",
            },
            {
                "word": "Petrichor",
                "definition": "The earthy scent after rain",
                "vibe": "🌧️ Renewal is coming",
            },
            {
                "word": "Wanderlust",
                "definition": "A strong desire to explore the world",
                "vibe": "🗺️ Adventure calls your name",
            },
            {
                "word": "Solitude",
                "definition": "Peaceful time alone with yourself",
                "vibe": "🕊️ Rest in your own company",
            },
            {
                "word": "Euphoria",
                "definition": "Intense happiness and excitement",
                "vibe": "🎉 Joy is your birthright",
            },
            {
                "word": "Whimsy",
                "definition": "Playful, fanciful behavior",
                "vibe": "🎠 Be delightfully unpredictable",
            },
            {
                "word": "Mellifluous",
                "definition": "Sweet-sounding, flowing like honey",
                "vibe": "🍯 Speak with sweetness today",
            },
            {
                "word": "Ineffable",
                "definition": "Too profound for words",
                "vibe": "💫 Some magic defies language",
            },
            {
                "word": "Ethereal",
                "definition": "Delicate and otherworldly",
                "vibe": "👻 You're made of stardust",
            },
            {
                "word": "Limerence",
                "definition": "The butterflies of new infatuation",
                "vibe": "💕 Let yourself feel deeply",
            },
            {
                "word": "Sonder",
                "definition": "Realizing everyone has a story as vivid as yours",
                "vibe": "🌍 We're all the main character",
            },
            {
                "word": "Halcyon",
                "definition": "Calm, peaceful, and idyllic",
                "vibe": "☮️ Tranquility surrounds you",
            },
            {
                "word": "Resplendent",
                "definition": "Dazzling and radiant",
                "vibe": "💎 You are magnificent",
            },
            {
                "word": "Iridescent",
                "definition": "Shimmering with rainbow colors",
                "vibe": "🌈 Your multifaceted beauty shows",
            },
            {
                "word": "Cascade",
                "definition": "Flowing downward like a waterfall",
                "vibe": "💧 Let it flow naturally",
            },
            {
                "word": "Gossamer",
                "definition": "Delicate like a spider's web",
                "vibe": "🕸️ Strength in gentleness",
            },
            {
                "word": "Vespertine",
                "definition": "Belonging to the evening",
                "vibe": "🌙 Night magic is yours",
            },
            {
                "word": "Pluviophile",
                "definition": "A lover of rain",
                "vibe": "☔ Dance in the downpour",
            },
            {
                "word": "Sillage",
                "definition": "The scent trail left behind",
                "vibe": "🌺 Leave a beautiful impression",
            },
            {
                "word": "Effervescent",
                "definition": "Bubbly and vivacious",
                "vibe": "✨ Your energy sparkles",
            },
            {
                "word": "Reverence",
                "definition": "Deep respect and awe",
                "vibe": "🙏 Honor the sacred in all things",
            },
            {
                "word": "Sonorous",
                "definition": "Deep, rich, and resonant sound",
                "vibe": "🎶 Your voice carries weight",
            },
            {
                "word": "Felicity",
                "definition": "Intense happiness",
                "vibe": "😊 Bliss is available now",
            },
        ]

        chosen = random.choice(whimsy_words)

        embed = discord.Embed(
            title=f"✨ {chosen['word']}",
            description=f"*{chosen['definition']}*",
            color=0xFF69B4,
        )
        embed.add_field(name="Your Vibe Today", value=chosen["vibe"], inline=False)
        embed.set_footer(
            text=f"Whimsy for {ctx.author.display_name} • Let this word guide your day"
        )

        await ctx.send(embed=embed)

    # ----------------------------------------------- SLASH COMMANDS ----------------------------------------------

    # fortune slash command ----------------------------------------------

    @app_commands.command(
        name="fortune", description="Receive a mystical fortune telling"
    )
    async def fortune_slash(self, interaction: discord.Interaction):
        """Slash command for fortune telling."""
        fortune = random.choice(self.fortunes)

        embed = discord.Embed(
            title="✨ Your Fortune", description=fortune, color=0xFFD700
        )
        embed.set_footer(text=f"Fortune told for {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

    # pendulum slash command ----------------------------------------------

    @app_commands.command(
        name="pendulum", description="Ask the pendulum a yes/no question"
    )
    @app_commands.describe(question="Your yes/no question for the pendulum")
    async def pendulum_slash(self, interaction: discord.Interaction, question: str):
        """Slash command for pendulum reading."""
        responses = [
            ("Yes", "The pendulum swings strongly in affirmation.", 0x00FF00),
            ("No", "The pendulum swings clearly in denial.", 0xFF0000),
            ("Maybe", "The pendulum circles uncertainly.", 0xFFFF00),
            (
                "Ask again later",
                "The pendulum is still, the answer is not yet clear.",
                0x808080,
            ),
            ("Uncertain", "The pendulum wavers, the energy is mixed.", 0xFFA500),
        ]

        answer, description, color = random.choice(responses)

        embed = discord.Embed(
            title="🔘 Pendulum Reading",
            description=f"**Question:** {question}\n\n**Answer:** {answer}\n\n*{description}*",
            color=color,
        )
        embed.set_footer(text=f"Reading for {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

    # dice rolling slash command ----------------------------------------------

    @app_commands.command(name="roll", description="Roll dice with standard notation")
    @app_commands.describe(dice="Dice notation (e.g., 2d6, 1d20)")
    async def roll_slash(self, interaction: discord.Interaction, dice: str = "1d6"):
        """Slash command for rolling dice."""
        try:
            rolls, sides = map(int, dice.lower().split("d"))

            if rolls > 100 or sides > 1000:
                await interaction.response.send_message(
                    "❌ Too many dice or sides! Max: 100d1000", ephemeral=True
                )
                return

            results = [random.randint(1, sides) for _ in range(rolls)]
            total = sum(results)

            if len(results) <= 20:
                result_str = ", ".join(map(str, results))
            else:
                result_str = (
                    f"{', '.join(map(str, results[:20]))}... (showing first 20)"
                )

            embed = discord.Embed(title=f"🎲 Rolling {dice}", color=0xE74C3C)
            embed.add_field(name="Results", value=result_str, inline=False)
            embed.add_field(name="Total", value=str(total), inline=False)
            embed.set_footer(text=f"Rolled by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid format! Use format like: `2d6` or `1d20`", ephemeral=True
            )

    # color oracle slash command ----------------------------------------------

    @app_commands.command(
        name="colororacle", description="Discover what color energy you need today"
    )
    async def colororacle_slash(self, interaction: discord.Interaction):
        """Slash command for color oracle."""
        color_name = random.choice(list(self.oracle_colors.keys()))
        color_data = self.oracle_colors[color_name]

        embed = discord.Embed(
            title=f"🎨 {color_name.title()}",
            description=f"**{color_data['energy']}**",
            color=0xE91E63,
        )
        embed.add_field(name="Meaning", value=color_data["meaning"], inline=False)
        embed.add_field(name="Guidance", value=color_data["guidance"], inline=False)
        embed.add_field(name="Element", value=color_data["element"], inline=True)
        embed.add_field(name="Chakra", value=color_data["chakra"], inline=True)
        embed.set_footer(text=f"Color oracle for {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="whimsy", description="Receive a whimsical word to inspire your day"
    )
    async def whimsy_slash(self, interaction: discord.Interaction):
        """Slash command for whimsy word."""
        whimsy_words = [
            {
                "word": "Serendipity",
                "definition": "Finding something wonderful when you weren't even looking",
                "vibe": "✨ Lucky discoveries await you",
            },
            {
                "word": "Luminescence",
                "definition": "Soft glowing light from within",
                "vibe": "🌟 Your inner light shines bright",
            },
            {
                "word": "Ephemeral",
                "definition": "Beautiful but fleeting, like a sunset",
                "vibe": "🌸 Treasure this fleeting moment",
            },
            {
                "word": "Petrichor",
                "definition": "The earthy scent after rain",
                "vibe": "🌧️ Renewal is coming",
            },
            {
                "word": "Wanderlust",
                "definition": "A strong desire to explore the world",
                "vibe": "🗺️ Adventure calls your name",
            },
            {
                "word": "Solitude",
                "definition": "Peaceful time alone with yourself",
                "vibe": "🕊️ Rest in your own company",
            },
            {
                "word": "Euphoria",
                "definition": "Intense happiness and excitement",
                "vibe": "🎉 Joy is your birthright",
            },
            {
                "word": "Whimsy",
                "definition": "Playful, fanciful behavior",
                "vibe": "🎠 Be delightfully unpredictable",
            },
            {
                "word": "Mellifluous",
                "definition": "Sweet-sounding, flowing like honey",
                "vibe": "🍯 Speak with sweetness today",
            },
            {
                "word": "Ineffable",
                "definition": "Too profound for words",
                "vibe": "💫 Some magic defies language",
            },
            {
                "word": "Ethereal",
                "definition": "Delicate and otherworldly",
                "vibe": "👻 You're made of stardust",
            },
            {
                "word": "Limerence",
                "definition": "The butterflies of new infatuation",
                "vibe": "💕 Let yourself feel deeply",
            },
            {
                "word": "Sonder",
                "definition": "Realizing everyone has a story as vivid as yours",
                "vibe": "🌍 We're all the main character",
            },
            {
                "word": "Halcyon",
                "definition": "Calm, peaceful, and idyllic",
                "vibe": "☮️ Tranquility surrounds you",
            },
            {
                "word": "Resplendent",
                "definition": "Dazzling and radiant",
                "vibe": "💎 You are magnificent",
            },
            {
                "word": "Iridescent",
                "definition": "Shimmering with rainbow colors",
                "vibe": "🌈 Your multifaceted beauty shows",
            },
            {
                "word": "Cascade",
                "definition": "Flowing downward like a waterfall",
                "vibe": "💧 Let it flow naturally",
            },
            {
                "word": "Gossamer",
                "definition": "Delicate like a spider's web",
                "vibe": "🕸️ Strength in gentleness",
            },
            {
                "word": "Vespertine",
                "definition": "Belonging to the evening",
                "vibe": "🌙 Night magic is yours",
            },
            {
                "word": "Pluviophile",
                "definition": "A lover of rain",
                "vibe": "☔ Dance in the downpour",
            },
            {
                "word": "Sillage",
                "definition": "The scent trail left behind",
                "vibe": "🌺 Leave a beautiful impression",
            },
            {
                "word": "Effervescent",
                "definition": "Bubbly and vivacious",
                "vibe": "✨ Your energy sparkles",
            },
            {
                "word": "Elysian",
                "definition": "Blissfully peaceful",
                "vibe": "☁️ You deserve serenity",
            },
            {
                "word": "Hiraeth",
                "definition": "Longing for a home that never was",
                "vibe": "🏡 Your heart remembers",
            },
            {
                "word": "Reverie",
                "definition": "A pleasant daydream",
                "vibe": "💭 Let your mind wander",
            },
        ]

        chosen = random.choice(whimsy_words)

        embed = discord.Embed(
            title=f"✨ {chosen['word']}",
            description=f"*{chosen['definition']}*",
            color=0xFF69B4,
        )
        embed.add_field(name="Today's Vibe", value=chosen["vibe"], inline=False)
        embed.set_footer(text=f"Whimsy word for {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(GamesDivinationCog(bot))

