import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import re
from typing import Optional, Tuple, Dict, Any, List


class TarotCog(commands.Cog, name="Tarot"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/tarot_cards.json", "r", encoding="utf-8") as f:
            self.tarot_major = json.load(f)

        with open("bot/data/tarot_minor.json", "r", encoding="utf-8") as f:
            minor_data = json.load(f)
            self.tarot_minor = (
                minor_data.get("wands", [])
                + minor_data.get("cups", [])
                + minor_data.get("swords", [])
                + minor_data.get("pentacles", [])
            )

        self.all_tarot = self.tarot_major + self.tarot_minor

    # ---------- TAROT HELPERS ----------

    def _arcana_label(self, card: Dict[str, Any]) -> str:
        """Normalize arcana label for display."""
        arc = str(card.get("arcana", "")).strip().lower()
        if arc == "major":
            return "Major"
        return "Minor"

    def _safe_text(self, value: Any, fallback: str = "") -> str:
        if value is None:
            return fallback
        return str(value).strip()

    def get_keywords_and_meaning(self, card: Dict[str, Any], is_reversed: bool) -> Tuple[str, str]:
        """Return (keywords, meaning) based on orientation, safely."""
        if is_reversed:
            rk = self._safe_text(card.get("reversed_keywords"))
            rm = self._safe_text(card.get("reversed_meaning"))
            if rk and rm:
                return rk, rm
        # default upright
        return self._safe_text(card.get("keywords")), self._safe_text(card.get("meaning"))

    def build_single_card_embed(
        self,
        *,
        card: Dict[str, Any],
        is_reversed: bool,
        user_display_name: str,
        question: Optional[str] = None,
        is_lookup: bool = False,
    ) -> discord.Embed:
        arcana_type = self._arcana_label(card)
        orientation = "Reversed" if is_reversed else "Upright"
        keywords, meaning = self.get_keywords_and_meaning(card, is_reversed)

        title_suffix = " (Reversed)" if is_reversed else ""
        embed = discord.Embed(
            title=f"🔮 {self._safe_text(card.get('name'))}{title_suffix}",
            description=f"*{arcana_type} Arcana • {orientation}*",
            color=0x9B59B6 if not is_reversed else 0x6A0DAD,
        )

        # Optional but useful: number + correspondences, since you curated them
        number = self._safe_text(card.get("number"))
        if number:
            embed.add_field(name="Number", value=number, inline=True)

        corr = self._safe_text(card.get("correspondences"))
        if corr:
            embed.add_field(name="Correspondences", value=corr, inline=True)

        embed.add_field(name="Keywords", value=keywords or "—", inline=False)
        embed.add_field(name="Meaning", value=meaning or "—", inline=False)

        if question:
            embed.add_field(name="Question", value=question, inline=False)
            embed.set_footer(text="Flicker pulls this card in response to your question.")
        else:
            if is_lookup:
                embed.set_footer(text=f"Card lookup for {user_display_name}")
            else:
                embed.set_footer(
                    text=f"Card drawn for {user_display_name} | Try !tarot 3 or !tarot <card name>"
                )

        return embed

    def build_spread_embed(
        self,
        *,
        drawn_cards: List[Dict[str, Any]],
        user_display_name: str,
        question: Optional[str] = None,
    ) -> discord.Embed:
        num_cards = len(drawn_cards)

        spread_names = {
            2: "Past & Future",
            3: "Past, Present, Future",
            4: "Situation, Challenge, Advice, Outcome",
            5: "You, Situation, Challenge, Past, Outcome",
            6: "Current State, Obstacle, Inner Self, External Influence, Advice, Outcome",
            7: "Past, Present, Future, Advice, Challenge, Opportunity, Hidden Influence",
            8: "Outer Situation, Inner Situation, Past, Present, Future, Advice, Challenge, Outcome",
            9: "Outer Situation, Inner Situation, Past, Present, Future, Advice, Challenge, Outcome, Hidden Influence",
            10: "Outer Situation, Inner Situation, Past, Present, Future, Advice, Challenge, Outcome, Hidden Influence, Subconscious",
            11: "Past, Present, Future, Advice, Challenge, Opportunity, Hidden Influence, Subconscious",
            12: "Past, Present, Future, Advice, Challenge, Opportunity, Hidden Influence, Subconscious, Hidden Influence",
        }
        spread_name = spread_names.get(num_cards, f"{num_cards}-Card Spread")

        embed = discord.Embed(
            title=f"🔮 {spread_name}",
            description=f"Your {num_cards}-card tarot reading",
            color=0x9B59B6,
        )

        if question:
            embed.add_field(name="Question", value=question, inline=False)

        for i, card in enumerate(drawn_cards, 1):
            is_reversed = random.choice([True, False])
            orientation = "↓ Reversed" if is_reversed else "↑ Upright"
            arcana = self._arcana_label(card)

            keywords, _ = self.get_keywords_and_meaning(card, is_reversed)
            keywords = self._safe_text(keywords)
            if len(keywords) > 120:
                keywords = keywords[:117] + "..."

            card_info = f"*{arcana} Arcana {orientation}*\n{keywords or '—'}"
            embed.add_field(
                name=f"{i}. {self._safe_text(card.get('name'))}{' (R)' if is_reversed else ''}",
                value=card_info,
                inline=False,
            )

        embed.set_footer(
            text=f"{num_cards}-card spread for {user_display_name} | No duplicate cards drawn"
        )
        return embed

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
            noise_words = {"tarot", "spread"}
            words = [w for w in text_without_number.split() if w.lower() not in noise_words]
            text_without_number = " ".join(words).strip()

        if text_without_number:
            lowered = text_without_number.lower()

            # exact match first
            matches = [c for c in self.all_tarot if lowered == self._safe_text(c.get("name")).lower()]
            if not matches:
                matches = [c for c in self.all_tarot if lowered in self._safe_text(c.get("name")).lower()]

            if matches:
                search_query = lowered
                question = None
                num_cards = 0  # sentinel: lookup mode
            else:
                question = text_without_number
                search_query = None

        return question, search_query, num_cards

    def _find_card_by_query(self, search_query: str) -> Optional[Dict[str, Any]]:
        matches = [
            card for card in self.all_tarot
            if search_query in self._safe_text(card.get("name")).lower()
        ]
        return matches[0] if matches else None

    def _draw_cards(self, num_cards: int) -> List[Dict[str, Any]]:
        deck_copy = self.all_tarot.copy()
        random.shuffle(deck_copy)
        return deck_copy[:num_cards]

    # ---------- PREFIX TAROT COMMAND ----------

    @commands.command(name="tarot")
    async def pull_tarot(self, ctx, *, query: str = None):
        question, search_query, num_cards = self._parse_query(query)

        # ----- lookup by name -----
        if search_query:
            card = self._find_card_by_query(search_query)
            if not card:
                await ctx.send(
                    f"❌ No tarot card found matching '{query}'. Try !tarot to pull a random card!"
                )
                return

            is_reversed = random.choice([True, False])
            embed = self.build_single_card_embed(
                card=card,
                is_reversed=is_reversed,
                user_display_name=ctx.author.display_name,
                is_lookup=True,
            )
            await ctx.send(embed=embed)
            return

        # ----- random pulls -----
        if num_cards < 1:
            num_cards = 1
        num_cards = min(num_cards, 12)

        drawn_cards = self._draw_cards(num_cards)

        if num_cards == 1:
            card = drawn_cards[0]
            is_reversed = random.choice([True, False])
            embed = self.build_single_card_embed(
                card=card,
                is_reversed=is_reversed,
                user_display_name=ctx.author.display_name,
                question=question,
                is_lookup=False,
            )
            await ctx.send(embed=embed)
        else:
            embed = self.build_spread_embed(
                drawn_cards=drawn_cards,
                user_display_name=ctx.author.display_name,
                question=question,
            )
            await ctx.send(embed=embed)

    # ---------- SLASH TAROT COMMAND ----------

    @app_commands.command(name="tarot", description="Pull tarot cards for a reading")
    @app_commands.describe(card_count="Number of cards to pull (1-10)")
    async def tarot_slash(self, interaction: discord.Interaction, card_count: int = 1):
        await interaction.response.defer()

        num_cards = min(max(card_count, 1), 10)
        drawn_cards = self._draw_cards(num_cards)

        if num_cards == 1:
            card = drawn_cards[0]
            is_reversed = random.choice([True, False])
            embed = self.build_single_card_embed(
                card=card,
                is_reversed=is_reversed,
                user_display_name=interaction.user.display_name,
                question=None,
                is_lookup=False,
            )
            await interaction.followup.send(embed=embed)
        else:
            embed = self.build_spread_embed(
                drawn_cards=drawn_cards,
                user_display_name=interaction.user.display_name,
                question=None,
            )
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TarotCog(bot))