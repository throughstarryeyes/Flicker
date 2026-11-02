import discord
from discord.ext import commands
import json

class NumerologyCog(commands.Cog, name="Numerology"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/numerology_detailed.json", "r") as f:
            self.numerology_detailed = json.load(f)["numbers"]

    # ---------- NUMEROLOGY HELPERS ----------

    def extract_digits(self, raw: str) -> list[int]:
        return [int(c) for c in raw if c.isdigit()]

    def get_entry(self, n: int) -> dict | None:
        return self.numerology_detailed.get(str(n))

    def is_master(self, n: int) -> bool:
        entry = self.get_entry(n)
        if not entry:
            return False
        return bool(entry.get("is master", False))

    def reduce_number(self, n: int) -> int:
        """Reduce unless it's a master number."""
        if self.is_master(n):
            return n

        while n > 9 and not self.is_master(n):
            n = sum(int(d) for d in str(n))
            if self.is_master(n):
                break
        return n

    # --------- meaning formatting ----------

    def full_meaning(self, n: int) -> str:
        """Full essay for master + single digit + core."""
        e = self.get_entry(n)
        if not e:
            return "No meaning found."

        lines = []
        if e.get("is master"):
            lines.append("*Master number energy.*")
        if e.get("keywords"):
            lines.append(f"**Keywords:** {e['keywords']}")
        if e.get("strengths"):
            lines.append(f"**Strengths:** {e['strengths']}")
        if e.get("challenges"):
            lines.append(f"**Challenges:** {e['challenges']}")
        if e.get("life_theme"):
            lines.append(f"**Life theme:** {e['life_theme']}")
        if e.get("career"):
            lines.append(f"**Career:** {e['career']}")
        if e.get("love"):
            lines.append(f"**Love:** {e['love']}")

        return "\n".join(lines)

    def keyword_only(self, n: int) -> str:
        """Short summary for multi-digit non-master."""
        e = self.get_entry(n)
        if not e:
            return "No meaning found."
        return f"**Keywords:** {e.get('keywords', 'No keywords available.')}"

    # numerology lifepath command ----------------------------------------------

    @commands.command(name="lifepath")
    async def lifepath(self, ctx, birthdate: str = None):
        if not birthdate:
            await ctx.send(
                "🔢 Please provide your birthdate! Usage: `!numerology MM/DD/YYYY` or `!numerology MMDDYYYY`"
            )
            return

        try:
            numbers = "".join(filter(str.isdigit, birthdate))

            if len(numbers) != 8:
                await ctx.send("❌ Please use format MM/DD/YYYY or MMDDYYYY")
                return

            total = sum(int(digit) for digit in numbers)

            while total > 9 and total not in [11, 22, 33]:
                total = sum(int(digit) for digit in str(total))

            num_data = self.numerology_detailed.get(str(total))
            if not num_data:
                await ctx.send("❌ Unable to find numerology data for this number.")
                return

            embed = discord.Embed(
                title=f"🔢 Life Path Number: {total}",
                description=f"**{num_data['keywords']}**",
                color=0x3498DB,
            )
            embed.add_field(
                name="✨ Strengths", value=num_data["strengths"], inline=False
            )
            embed.add_field(
                name="⚠️ Challenges", value=num_data["challenges"], inline=False
            )
            embed.add_field(
                name="🎯 Life Theme", value=num_data["life_theme"], inline=False
            )
            embed.add_field(
                name="💼 Career Path", value=num_data["career"], inline=True
            )
            embed.add_field(
                name="💕 Love & Relationships", value=num_data["love"], inline=True
            )
            embed.set_footer(text=f"Lifepath reading for {ctx.author.display_name}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error calculating numerology: {e}")

    # numerology spread command ----------------------------------------------

    @commands.command(name="numerology", aliases=["num", "numbers"])
    async def numerology_cmd(self, ctx, *, numbers: str):
        digits = self.extract_digits(numbers)

        if not digits:
            return await ctx.send("No numbers found in your input.")

        unique_digits = sorted(set(digits))

        embed = discord.Embed(
            title="🔢 Numerology Reading",
            description=f"Input: `{numbers}`",
            color=discord.Color.blurple(),
        )

        # ---------- digit influences (keywords only so it doesn't become a novel) ----------
        digit_blocks = []
        for d in unique_digits:
            # always use short version here
            digit_blocks.append(f"**{d}**\n{self.keyword_only(d)}")

        digit_text = "\n\n".join(digit_blocks)
        if len(digit_text) > 1000:
            digit_text = digit_text[:997] + "…"

        embed.add_field(name="Digit influences", value=digit_text, inline=False)

        # ---------- core number ----------
        raw_value = int("".join(str(d) for d in digits))

        if self.is_master(raw_value):
            # if the *whole number* is a master (e.g. 11, 22, 33)
            core = raw_value
        else:
            # otherwise use sum-of-digits reduction w/ master handling
            core = self.reduce_number(sum(digits))

        # core formatting using your rule:
        # - if master -> essay
        # - elif single digit -> essay
        # - else -> keywords
        if self.is_master(core) or core < 10:
            core_text = self.full_meaning(core)
        else:
            core_text = self.keyword_only(core)

        if len(core_text) > 1000:
            core_text = core_text[:997] + "…"

        embed.add_field(name=f"Core number: {core}", value=core_text, inline=False)

        await ctx.send(embed=embed)

    # lo shu grid command ----------------------------------------------

    @commands.command(name="loshu", aliases=["numbermatrix", "matrix"])
    async def lo_shu_grid(self, ctx, birthdate: str = None):
        """Lo Shu Grid / Number Matrix analysis from birthdate.

        Usage: !loshu MM/DD/YYYY or !loshu MMDDYYYY
        """
        if not birthdate:
            await ctx.send(
                "🔢 Please provide your birthdate!\nUsage: `!loshu MM/DD/YYYY` or `!loshu 03151990`"
            )
            return

        digits_only = "".join(filter(str.isdigit, birthdate))

        if len(digits_only) < 6:
            await ctx.send(
                "❌ Please provide a valid birthdate with at least month, day, and year!"
            )
            return

        grid = {str(i): 0 for i in range(1, 10)}

        for digit in digits_only:
            if digit in grid:
                grid[digit] += 1

        grid_visual = f"""
```
 {grid['4'] or '·'} | {grid['9'] or '·'} | {grid['2'] or '·'}
───┼───┼───
 {grid['3'] or '·'} | {grid['5'] or '·'} | {grid['7'] or '·'}
───┼───┼───
 {grid['8'] or '·'} | {grid['1'] or '·'} | {grid['6'] or '·'}
```"""

        missing = [num for num, count in grid.items() if count == 0]
        repeated = [(num, count) for num, count in grid.items() if count > 1]

        meanings = {
            "1": "Self, ego, communication",
            "2": "Intuition, sensitivity, emotions",
            "3": "Creativity, mental agility, memory",
            "4": "Practicality, stability, planning",
            "5": "Balance, emotional control, logic",
            "6": "Home, family, nurturing",
            "7": "Spirituality, introspection, wisdom",
            "8": "Ambition, materialism, discipline",
            "9": "Idealism, humanitarianism, purpose",
        }

        analysis = ""

        if missing:
            analysis += "\n**Missing Numbers:**\n"
            for num in missing[:3]:
                analysis += f"• **{num}** - May lack {meanings[num].lower()}\n"

        if repeated:
            analysis += "\n**Strong Numbers:**\n"
            for num, count in repeated[:3]:
                analysis += (
                    f"• **{num}** (×{count}) - Enhanced {meanings[num].lower()}\n"
                )

        if not missing and not repeated:
            analysis = "\n✨ **Balanced Grid** - All numbers present once! This indicates a well-rounded personality."

        embed = discord.Embed(
            title="🔢 Lo Shu Grid Analysis",
            description=f"Your personal number matrix:{grid_visual}",
            color=0xF39C12,
        )
        embed.add_field(
            name="Analysis", value=analysis or "See your grid above!", inline=False
        )
        embed.set_footer(
            text=f"Lo Shu Grid for {ctx.author.display_name} • Ancient Chinese numerology"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(NumerologyCog(bot))

