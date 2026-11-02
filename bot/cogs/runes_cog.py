import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import math
from itertools import combinations


class RunesCog(commands.Cog, name="Runes"):
    def __init__(self, bot):
        self.bot = bot
        with open("bot/data/runes.json", "r", encoding="utf-8") as f:
            self.runes = json.load(f)

        # Optional named layouts. Coordinates are on a 0..100 "cloth".
        # (You can add more later without touching the cast logic.)
        self.named_patterns = {
            "line": [(10, 50), (30, 50), (50, 50), (70, 50), (90, 50)],
            "cross": [(50, 20), (50, 40), (50, 60), (50, 80), (30, 50), (70, 50)],
            "triangle": [(50, 20), (30, 70), (70, 70), (50, 45)],
            "diamond": [(50, 20), (30, 50), (50, 80), (70, 50), (50, 50)],
            "scatter": [],  # special: forces random placement (no cluster bias)
        }

    # -----------------------------
    # Helpers: selecting runes
    # -----------------------------

    def _draw_unique_runes(self, count: int) -> list[dict]:
        count = max(1, min(count, 10))
        pool = self.runes.copy()
        random.shuffle(pool)
        return pool[:count]

    # -----------------------------
    # Helpers: layout + geometry
    # -----------------------------

    def _clamp(self, v: float, lo: float = 0.0, hi: float = 100.0) -> float:
        return max(lo, min(hi, v))

    def _dist(self, a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _generate_positions(self, n: int, pattern: str | None = None) -> list[tuple[float, float]]:
        """
        If pattern is given and exists, use it (trim/extend as needed).
        If not, generate a random cast with a chance of clustering.
        """
        n = max(1, min(n, 10))

        if pattern:
            key = pattern.lower().strip()
            if key in self.named_patterns and key != "scatter":
                coords = self.named_patterns[key]
                # If they request more than the template length, fill remaining randomly.
                out = coords[:n]
                while len(out) < n:
                    out.append((random.uniform(10, 90), random.uniform(10, 90)))
                return out

            # "scatter" explicitly: no cluster bias
            if key == "scatter":
                return [(random.uniform(10, 90), random.uniform(10, 90)) for _ in range(n)]

        # -------- Random cast with cluster bias --------
        # Choose 1–3 clusters, weighted toward 1–2. More runes = more likely 2–3.
        if n <= 3:
            k = 1
        elif n <= 6:
            k = random.choices([1, 2], weights=[35, 65])[0]
        else:
            k = random.choices([1, 2, 3], weights=[25, 55, 20])[0]

        # Pick cluster centers (avoid extreme edges)
        centers = [(random.uniform(20, 80), random.uniform(20, 80)) for _ in range(k)]

        # Spread factor: smaller = tighter clusters
        tightness = random.uniform(6.0, 16.0)

        positions = []
        for i in range(n):
            cx, cy = random.choice(centers)

            # Nudge spread depending on how "many centers" there are
            jitter = tightness * (1.0 + (0.15 * (k - 1)))

            x = self._clamp(random.gauss(cx, jitter))
            y = self._clamp(random.gauss(cy, jitter))
            positions.append((x, y))

        return positions

    def _proximity_groups(self, runes_with_pos: list[tuple[dict, tuple[float, float]]]) -> list[list[int]]:
        """
        Build groups of indices where runes are "close" (graph components).
        """
        n = len(runes_with_pos)
        if n <= 1:
            return [[0]] if n == 1 else []

        # Distance threshold scales slightly with count
        # (More runes = tighter threshold so it doesn't say everything is close.)
        threshold = 18.0 if n <= 4 else 15.0 if n <= 7 else 13.0

        # adjacency list
        adj = {i: set() for i in range(n)}
        for (i, (_, pi)), (j, (_, pj)) in combinations(enumerate(runes_with_pos), 2):
            if self._dist(pi, pj) <= threshold:
                adj[i].add(j)
                adj[j].add(i)

        # connected components
        seen = set()
        comps = []
        for i in range(n):
            if i in seen:
                continue
            stack = [i]
            comp = []
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                comp.append(cur)
                stack.extend(list(adj[cur] - seen))
            comps.append(sorted(comp))
        return comps

    def _describe_distribution(self, positions: list[tuple[float, float]]) -> str:
        """
        Human description: clustered/spread + top/bottom/left/right bias.
        """
        n = len(positions)
        if n == 0:
            return "No runes cast."

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        cx = sum(xs) / n
        cy = sum(ys) / n

        # spread measure: average pairwise distance
        if n == 1:
            spread = 0.0
        else:
            dists = [self._dist(a, b) for a, b in combinations(positions, 2)]
            spread = sum(dists) / len(dists)

        # interpret spread
        # On a 0..100 cloth, typical:
        # - ~10-18 = clustered
        # - ~18-30 = mixed
        # - 30+ = scattered
        if spread < 18:
            spread_text = "The runes fell in a **tight cluster**."
        elif spread < 30:
            spread_text = "The runes are **somewhat clustered**, with a few drifting apart."
        else:
            spread_text = "The runes are **widely scattered** across the cloth."

        # direction bias
        horiz = ""
        vert = ""

        if cx <= 42:
            horiz = "leaning **left**"
        elif cx >= 58:
            horiz = "leaning **right**"
        else:
            horiz = "**centered** left-to-right"

        if cy <= 42:
            vert = "clustered toward the **top**"
        elif cy >= 58:
            vert = "clustered toward the **bottom**"
        else:
            vert = "**centered** top-to-bottom"

        return f"{spread_text}\nOverall, the cast is {vert} and {horiz}."

    # -----------------------------
    # Commands: single rune
    # -----------------------------

    @commands.command(name="rune", aliases=["runes"])
    async def pull_rune(self, ctx):
        rune = random.choice(self.runes)

        embed = discord.Embed(
            title=f"{rune['symbol']} {rune['name']}",
            description=f"*{rune['meaning']}*",
            color=0x8B4513,
        )
        embed.add_field(name="Keywords", value=rune["keywords"], inline=False)
        embed.add_field(name="Interpretation", value=rune["interpretation"], inline=False)
        embed.set_footer(text=f"Rune cast for {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @app_commands.command(name="rune", description="Cast a rune and receive its wisdom")
    async def rune_slash(self, interaction: discord.Interaction):
        rune = random.choice(self.runes)

        embed = discord.Embed(
            title=f"{rune['symbol']} {rune['name']}",
            description=f"*{rune['meaning']}*",
            color=0x8B4513,
        )
        embed.add_field(name="Keywords", value=rune["keywords"], inline=False)
        embed.add_field(name="Interpretation", value=rune["interpretation"], inline=False)
        embed.set_footer(text=f"Rune cast for {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

    # -----------------------------
    # Commands: rune spread
    # -----------------------------

    @commands.command(name="runespread", aliases=["spreadrune", "runecast", "cast"])
    async def rune_spread(self, ctx, count: int = 3, *, pattern: str = None):
        """
        Usage:
          !runespread
          !runespread 5
          !runespread 6 cross
          !runespread 8 scatter
        """
        count = max(1, min(int(count), 10))
        pattern_clean = pattern.strip() if pattern else None

        drawn = self._draw_unique_runes(count)
        positions = self._generate_positions(count, pattern_clean)

        runes_with_pos = list(zip(drawn, positions))

        # analysis text
        distribution = self._describe_distribution(positions)
        comps = self._proximity_groups(runes_with_pos)

        # proximity summary (only mention meaningful clusters)
        clusters = [c for c in comps if len(c) >= 2]
        proximity_lines = []
        if clusters:
            for c in clusters:
                names = ", ".join([runes_with_pos[i][0]["name"] for i in c])
                proximity_lines.append(f"• **Close together:** {names}")
        else:
            proximity_lines.append("• No runes landed especially close together; each one stands on its own.")

        proximity_text = "\n".join(proximity_lines)
        if len(proximity_text) > 1000:
            proximity_text = proximity_text[:997] + "…"

        # embed
        title = "ᚱ Rune Spread"
        if pattern_clean:
            title += f" - {pattern_clean.title()}"

        embed = discord.Embed(
            title=title,
            description=f"Your **{count}**-rune cast\n\n{distribution}",
            color=0x8B4513,
        )

        embed.add_field(name="Cast pattern", value=proximity_text, inline=False)

        # Show runes in order; include a tiny location tag for flavor
        for idx, (r, (x, y)) in enumerate(runes_with_pos, 1):
            # location words (very light-touch)
            lr = "left" if x < 45 else "right" if x > 55 else "center"
            tb = "top" if y < 45 else "bottom" if y > 55 else "middle"
            loc = f"{tb}-{lr}"

            value = (
                f"*{r['meaning']}*  (`{loc}`)\n"
                f"**Keywords:** {r['keywords']}\n"
                f"{r['interpretation']}"
            )

            # Discord embed field values have limits; keep it tidy
            if len(value) > 950:
                value = value[:947] + "…"

            embed.add_field(
                name=f"{idx}. {r['symbol']} {r['name']}",
                value=value,
                inline=False,
            )

        embed.set_footer(text=f"Rune spread for {ctx.author.display_name} • No reversals, just the cast")
        await ctx.send(embed=embed)

    @app_commands.command(name="runespread", description="Cast multiple runes with a spatial spread")
    @app_commands.describe(
        count="How many runes to cast (1–10)",
        pattern="Optional: line, cross, triangle, diamond, scatter",
    )
    async def runespread_slash(self, interaction: discord.Interaction, count: int = 3, pattern: str = None):
        await interaction.response.defer()

        count = max(1, min(int(count), 10))
        pattern_clean = pattern.strip() if pattern else None

        drawn = self._draw_unique_runes(count)
        positions = self._generate_positions(count, pattern_clean)
        runes_with_pos = list(zip(drawn, positions))

        distribution = self._describe_distribution(positions)
        comps = self._proximity_groups(runes_with_pos)
        clusters = [c for c in comps if len(c) >= 2]

        proximity_lines = []
        if clusters:
            for c in clusters:
                names = ", ".join([runes_with_pos[i][0]["name"] for i in c])
                proximity_lines.append(f"• **Close together:** {names}")
        else:
            proximity_lines.append("• No runes landed especially close together — each one stands on its own.")

        proximity_text = "\n".join(proximity_lines)
        if len(proximity_text) > 1000:
            proximity_text = proximity_text[:997] + "…"

        title = "ᚱ Rune Spread"
        if pattern_clean:
            title += f" — {pattern_clean.title()}"

        embed = discord.Embed(
            title=title,
            description=f"Your **{count}**-rune cast\n\n{distribution}",
            color=0x8B4513,
        )

        embed.add_field(name="Cast pattern", value=proximity_text, inline=False)

        for idx, (r, (x, y)) in enumerate(runes_with_pos, 1):
            lr = "left" if x < 45 else "right" if x > 55 else "center"
            tb = "top" if y < 45 else "bottom" if y > 55 else "middle"
            loc = f"{tb}-{lr}"

            value = (
                f"*{r['meaning']}*  (`{loc}`)\n"
                f"**Keywords:** {r['keywords']}\n"
                f"{r['interpretation']}"
            )
            if len(value) > 950:
                value = value[:947] + "…"

            embed.add_field(
                name=f"{idx}. {r['symbol']} {r['name']}",
                value=value,
                inline=False,
            )

        embed.set_footer(text=f"Rune spread for {interaction.user.display_name} • No reversals, just the cast")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RunesCog(bot))
