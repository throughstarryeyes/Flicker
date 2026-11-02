import discord
from discord.ext import commands
from discord import app_commands
import json
import random
from itertools import combinations
from typing import Optional, List, Dict, Any


TYPE_FORMAT = {
    "gradient": "Gradient Resonance",
    "primary": "Primary Dyad",
    "secondary": "Secondary Dyad",
    "tertiary": "Tertiary Dyad",
    "conflict": "Polar Conflict",
}


class EmotionOracleCog(commands.Cog, name="Emotion Oracle"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/emotions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.cards: List[Dict[str, Any]] = data["cards"]
            self.raw_syntheses: List[Dict[str, Any]] = data.get("syntheses", [])

        self.synthesis_index: Dict[frozenset, Dict[str, Any]] = {}
        for syn in self.raw_syntheses:
            key = frozenset(syn["parents"])
            self.synthesis_index[key] = syn

    def draw(self, count: int) -> List[Dict[str, Any]]:
        count = max(1, min(count, 10))
        deck = self.cards.copy()
        random.shuffle(deck)
        return deck[:count]

    def safe_text(self, value: Any, fallback: str = "—") -> str:
        if value is None:
            return fallback
        return str(value).strip()

    def find_synthesis(self, card_a: Dict[str, Any], card_b: Dict[str, Any]) -> str:
        key = frozenset({card_a["id"], card_b["id"]})
        syn = self.synthesis_index.get(key)

        if syn:
            category = TYPE_FORMAT.get(syn.get("type", ""), "Synthesis")
            return f"• **{card_a['name']}** + **{card_b['name']}** → **{syn['name']}** *({category})*"

        # failsafe: if no synthesis is found, return a default message
        return f"• **{card_a['name']}** + **{card_b['name']}** → *Undiscovered*"

    # -------------------------------------------------------------
    # PREFIX COMMAND (emotionoracle)
    # -------------------------------------------------------------
    @commands.command(name="emotionoracle", aliases=["wheel", "feel", "emotionwheel", "emotionaloracle", "emotioncard", "emotionreading"])
    async def emotionoracle_prefix(self, ctx, count: int = 1, *, question: Optional[str] = None):
        """Draws 1 to 6 cards. Single draws show full emotion descriptions. Multi-card draws show keywords and synthesis."""
        count = max(1, min(count, 6))
        drawn = self.draw(count)

        # 1. Single Card Pull: Name + Keywords + Sensation
        if count == 1:
            card = drawn[0]
            embed = discord.Embed(
                title=f"🜂 {self.safe_text(card.get('name'))}",
                description="*Emotion Oracle • Single Draw*",
                color=0xDD6B20,
            )
            if question:
                embed.add_field(name="Question / Focus", value=question, inline=False)

            embed.add_field(
                name="Keywords",
                value=self.safe_text(card.get("keywords")),
                inline=False,
            )
            embed.add_field(
                name="What It Feels Like",
                value=self.safe_text(card.get("sensation")),
                inline=False,
            )
            embed.set_footer(text=f"Drawn for {ctx.author.display_name}")
            await ctx.send(embed=embed)
            return

        # multi card pull: name, keywords, synthesis
        embed = discord.Embed(
            title=f"🜂 {count}-Card Emotion Spread",
            description=f"*Focus: \"{question}\"*\n" if question else None,
            color=0xDD6B20,
        )

        for idx, card in enumerate(drawn, 1):
            embed.add_field(
                name=f"{idx}. {self.safe_text(card.get('name'))}",
                value=self.safe_text(card.get("keywords")),
                inline=False,
            )

        # synthesis for each pair of drawn cards
        synergy_lines = [
            self.find_synthesis(a, b) for a, b in combinations(drawn, 2)
        ]

        embed.add_field(
            name="⚡ Emotional Synthesis",
            value="\n".join(synergy_lines),
            inline=False,
        )

        embed.set_footer(text=f"Spread cast for {ctx.author.display_name}")
        await ctx.send(embed=embed)

    # -------------------------------------------------------------
    # Slash Command (/emotionoracle)
    # -------------------------------------------------------------
    @app_commands.command(name="emotionoracle", description="Draws 1 to 6 cards. Single draws show full emotion descriptions. Multi-card draws show keywords and synthesis.")
    @app_commands.describe(
        count="Number of cards to draw (1-6)",
        question="Optional question or focus for the reading"
    )
    async def emotionoracle_slash(self, interaction: discord.Interaction, count: int = 1, question: Optional[str] = None):
        count = max(1, min(count, 6))
        drawn = self.draw(count)

        if count == 1:
            card = drawn[0]
            embed = discord.Embed(
                title=f"🜂 {self.safe_text(card.get('name'))}",
                description="*Emotion Oracle • Single Draw*",
                color=0xDD6B20,
            )
            if question:
                embed.add_field(name="Question / Focus", value=question, inline=False)

            embed.add_field(
                name="Keywords",
                value=self.safe_text(card.get("keywords")),
                inline=False,
            )
            embed.add_field(
                name="What It Feels Like",
                value=self.safe_text(card.get("sensation")),
                inline=False,
            )
            embed.set_footer(text=f"Drawn for {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title=f"🜂 {count}-Card Emotion Spread",
            description=f"*Focus: \"{question}\"*\n" if question else None,
            color=0xDD6B20,
        )

        for idx, card in enumerate(drawn, 1):
            embed.add_field(
                name=f"{idx}. {self.safe_text(card.get('name'))}",
                value=self.safe_text(card.get("keywords")),
                inline=False,
            )

        synergy_lines = [
            self.find_synthesis(a, b) for a, b in combinations(drawn, 2)
        ]

        embed.add_field(
            name="⚡ Emotional Synthesis",
            value="\n".join(synergy_lines),
            inline=False,
        )

        embed.set_footer(text=f"Spread cast for {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(EmotionOracleCog(bot))