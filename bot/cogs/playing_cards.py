import discord
from discord.ext import commands
import json
import random
import re
from typing import Optional, Dict, Any, List, Tuple


class PlayingCardCog(commands.Cog, name="Playing Cards"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/playing_cards.json", "r", encoding="utf-8") as f:
            self.cards: List[Dict[str, Any]] = json.load(f)

        # quick lookup map for normalized "rank|suit"
        self._index = {}
        for c in self.cards:
            norm = self._normalize_card_query(self._safe_text(c.get("name"), ""))
            if norm:
                self._index[norm] = c

    def _safe_text(self, value: Any, fallback: str = "") -> str:
        if value is None:
            return fallback
        return str(value).strip()

    def _draw(self, n: int) -> List[Dict[str, Any]]:
        deck = self.cards.copy()
        random.shuffle(deck)
        return deck[:n]

    def _normalize_card_query(self, raw: str) -> Optional[str]:
        """
        Normalize user input to something like:
        '3|hearts', 'q|spades', '10|diamonds', 'a|clubs'
        Accepts: "three hearts", "3 of hearts", "queen spades", "Q spades", etc.
        """
        if not raw:
            return None

        s = raw.lower().strip()
        s = s.replace("of", " ")
        s = re.sub(r"\s+", " ", s)

        word_to_rank = {
            "ace": "a", "a": "a", "1": "a",
            "two": "2", "2": "2",
            "three": "3", "3": "3",
            "four": "4", "4": "4",
            "five": "5", "5": "5",
            "six": "6", "6": "6",
            "seven": "7", "7": "7",
            "eight": "8", "8": "8",
            "nine": "9", "9": "9",
            "ten": "10", "10": "10",
            "jack": "j", "j": "j",
            "queen": "q", "q": "q",
            "king": "k", "k": "k",
        }

        suit_alias = {
            "hearts": "hearts", "heart": "hearts", "♥": "hearts",
            "diamonds": "diamonds", "diamond": "diamonds", "♦": "diamonds",
            "clubs": "clubs", "club": "clubs", "♣": "clubs",
            "spades": "spades", "spade": "spades", "♠": "spades",
        }

        parts = s.split()
        if len(parts) < 2:
            return None

        rank = None
        suit = None

        for p in parts:
            if p in word_to_rank and rank is None:
                rank = word_to_rank[p]
            if p in suit_alias and suit is None:
                suit = suit_alias[p]

        if rank and suit:
            return f"{rank}|{suit}"
        return None

    def _find_card_by_query(self, search_query: str) -> Optional[Dict[str, Any]]:
        # Try normalized lookup first
        norm = self._normalize_card_query(search_query)
        if norm and norm in self._index:
            return self._index[norm]

        # fallback: name substring match
        matches = [
            card for card in self.cards
            if search_query in self._safe_text(card.get("name")).lower()
        ]
        return matches[0] if matches else None

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
            noise_words = {"card", "cards", "spread", "playingcard", "playingcards", "deck"}
            words = [w for w in text_without_number.split() if w.lower() not in noise_words]
            text_without_number = " ".join(words).strip()

        if text_without_number:
            lowered = text_without_number.lower()

            # Check if it's a card lookup
            if self._find_card_by_query(lowered):
                search_query = lowered
                question = None
                num_cards = 0  # sentinel: lookup mode
            else:
                question = text_without_number
                search_query = None

        return question, search_query, num_cards

    @commands.command(name="card", aliases=["playingcard", "pcard", "playingcards"])
    async def playing_card(self, ctx, *, query: str = None):
        question, search_query, num_cards = self._parse_query(query)

        # ----- lookup by name -----
        if search_query:
            card = self._find_card_by_query(search_query)
            if not card:
                await ctx.send(
                    f"❌ No playing card found matching '{query}'. Try !card to pull a random card!"
                )
                return

            embed = discord.Embed(
                title=f"🂠 {self._safe_text(card.get('name'))}",
                description="*Playing Cards • Lookup*",
                color=0x2E8B57,
            )
            embed.add_field(name="Keywords", value=self._safe_text(card.get("keywords")) or "—", inline=False)
            embed.add_field(name="Meaning", value=self._safe_text(card.get("meaning")) or "—", inline=False)

            if card.get("correspondences"):
                embed.add_field(name="Correspondences", value=self._safe_text(card.get("correspondences")), inline=False)

            embed.set_footer(text=f"Playing card lookup for {ctx.author.display_name}")
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
                title=f"🂠 {self._safe_text(card.get('name'))}",
                description="*Playing Cards • Draw*",
                color=0x2E8B57,
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
                    text=f"Card drawn for {ctx.author.display_name} | Try !card 3 or !card <card name>"
                )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🂠 {num_cards}-Card Spread",
            description="Keywords-only spread",
            color=0x2E8B57,
        )
        if question:
            embed.add_field(name="Question", value=question, inline=False)

        for i, card in enumerate(drawn, 1):
            embed.add_field(
                name=f"{i}. {self._safe_text(card.get('name'))}",
                value=self._safe_text(card.get("keywords")) or "—",
                inline=False,
            )

        embed.set_footer(text=f"{num_cards}-card spread for {ctx.author.display_name}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PlayingCardCog(bot))
