import discord
from discord.ext import commands
import json
import random
import re
from typing import Optional, Dict, Any, List, Tuple


class RelationshipOracleCog(commands.Cog, name="Relationship Oracle"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/relationship_oracle.json", "r", encoding="utf-8") as f:
            self.cards: List[Dict[str, Any]] = json.load(f)

    def _safe_text(self, value: Any, fallback: str = "") -> str:
        if value is None:
            return fallback
        return str(value).strip()

    def _find_card_by_query(self, search_query: str) -> Optional[Dict[str, Any]]:
        matches = [
            card for card in self.cards
            if search_query in self._safe_text(card.get("name")).lower()
        ]
        return matches[0] if matches else None

    def _draw(self, n: int) -> List[Dict[str, Any]]:
        deck = self.cards.copy()
        random.shuffle(deck)
        return deck[:n]

    def _parse_query(self, query: Optional[str]) -> Tuple[Optional[str], Optional[str], int]:
        """
        Returns (question, search_query, num_cards)
        - search_query is set when user is looking up a card name
        - question is set when user wrote a question (possibly with a number)
        - num_cards is 1..10 for spreads
        """
        question = None
        search_query = None
        num_cards = 1

        if query is None:
            return None, None, 1

        query = query.strip()
        if not query:
            return None, None, 1

        match = re.search(r"\d+", query)
        text_without_number = query

        if match:
            num_cards = min(int(match.group()), 10)
            before = query[: match.start()].strip()
            after = query[match.end():].strip()
            text_without_number = " ".join([p for p in (before, after) if p]).strip()
        else:
            num_cards = 1
            text_without_number = query

        if text_without_number:
            noise_words = {"card", "cards", "spread", "oracle", "relationship", "loveoracle"}
            words = [w for w in text_without_number.split() if w.lower() not in noise_words]
            text_without_number = " ".join(words).strip()

        if text_without_number:
            lowered = text_without_number.lower()

            # exact match first
            matches = [c for c in self.cards if lowered == self._safe_text(c.get("name")).lower()]
            if not matches:
                matches = [c for c in self.cards if lowered in self._safe_text(c.get("name")).lower()]

            if matches:
                search_query = lowered
                question = None
                num_cards = 0  # sentinel: lookup mode
            else:
                question = text_without_number
                search_query = None

        return question, search_query, num_cards

    @commands.command(name="loveoracle", aliases=["reloracle", "relationshiporacle"])
    async def loveoracle(self, ctx, *, query: str = None):
        question, search_query, num_cards = self._parse_query(query)

        # ----- lookup by name -----
        if search_query:
            card = self._find_card_by_query(search_query)
            if not card:
                await ctx.send(
                    f"❌ No relationship oracle card found matching '{query}'. Try !loveoracle to pull a random card!"
                )
                return

            embed = discord.Embed(
                title=f"💞 {self._safe_text(card.get('name'))}",
                description="*Relationship Oracle • Lookup*",
                color=0xC71585,
            )
            embed.add_field(name="Keywords", value=self._safe_text(card.get("keywords")) or "—", inline=False)
            embed.add_field(name="Meaning", value=self._safe_text(card.get("meaning")) or "—", inline=False)

            if card.get("correspondences"):
                embed.add_field(name="Correspondences", value=self._safe_text(card.get("correspondences")), inline=False)

            embed.set_footer(text=f"Relationship oracle lookup for {ctx.author.display_name}")
            await ctx.send(embed=embed)
            return

        # ----- random pulls -----
        if num_cards < 1:
            num_cards = 1
        num_cards = min(num_cards, 10)

        drawn = self._draw(num_cards)

        if num_cards == 1:
            card = drawn[0]
            embed = discord.Embed(
                title=f"💞 {self._safe_text(card.get('name'))}",
                description="*Relationship Oracle • Draw*",
                color=0xC71585,
            )
            if question:
                embed.add_field(name="Question", value=question, inline=False)
            embed.add_field(name="Keywords", value=self._safe_text(card.get("keywords")) or "—", inline=False)
            embed.add_field(name="Meaning", value=self._safe_text(card.get("meaning")) or "—", inline=False)

            if card.get("correspondences"):
                embed.add_field(name="Correspondences", value=self._safe_text(card.get("correspondences")), inline=False)

            if question:
                embed.set_footer(text="Flicker pulls this card in response to your question.")
            else:
                embed.set_footer(
                    text=f"Card drawn for {ctx.author.display_name} | Try !loveoracle 3 or !loveoracle <card name>"
                )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"💞 {num_cards}-Card Relationship Spread",
            description=" ",
            color=0xC71585,
        )
        if question:
            embed.add_field(name="Question", value=question, inline=False)

        for i, card in enumerate(drawn, 1):
            embed.add_field(
                name=f"{i}. {self._safe_text(card.get('name'))}",
                value=self._safe_text(card.get("keywords")) or "—",
                inline=False,
            )

        embed.set_footer(text=f"{num_cards}-card relationship spread for {ctx.author.display_name}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RelationshipOracleCog(bot))