import discord
from discord.ext import commands


class CommandPager(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], author_id: int, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.index = 0
        self.author_id = author_id
        self._sync_button_state()

    def _sync_button_state(self):
        self.prev_button.disabled = (self.index <= 0)
        self.next_button.disabled = (self.index >= len(self.pages) - 1)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ only the command invoker can use these buttons.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self._sync_button_state()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self._sync_button_state()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # cog name -> (category_key, title, color)
        self.category_mappings = {
            'Tarot': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'Numerology': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'Runes': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'DreamsAura': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'GamesDivination': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'Lenormand': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'Playing Cards': ('divination', '🔮 Divination Commands', 0x9B59B6),
            'Relationship Oracle': ('divination', '🔮 Divination Commands', 0x9B59B6),

            'Reference': ('reference', '📚 Reference Commands', 0x2ECC71),
            'Generators': ('generators', '✨ Generator Commands', 0xE67E22),
            'Utility': ('utility', '🌙 Utility Commands', 0x3498DB),

            'Moderation': ('moderation', '🛡️ Moderation Commands', 0xE74C3C),
            'Cleanup': ('moderation', '🛡️ Moderation Commands', 0xE74C3C),
            'Kickall': ('moderation', '🛡️ Moderation Commands', 0xE74C3C),

            'Misc': ('misc', '🎭 Misc Commands', 0xF39C12),
            'Hearth': ('misc', '🎭 Misc Commands', 0xF39C12),
            'Personality': ('misc', '🎭 Misc Commands', 0xF39C12),
        }

        self.category_display_names = {
            'Tarot': '🔮 Tarot',
            'Numerology': '🔢 Numerology',
            'Runes': 'ᚱ Runes',
            'DreamsAura': '💭 Dreams & Aura',
            'GamesDivination': '🎲 Games & Divination',
            'Lenormand': '🜂 Lenormand',
            'Playing Cards': '🃏 Playing Cards',
            'Relationship Oracle': '💕 Relationship Oracle',
            'Reference': '📚 Reference',
            'Generators': '✨ Generators',
            'Utility': '🌙 Utility',
            'Moderation': '🛡️ Moderation',
            'Cleanup': '🧹 Cleanup',
            'Kickall': '👢 Kickall',
            'Misc': '🎭 Misc',
            'Hearth': '🏠 Hearth',
            'Personality': '💫 Personality',
        }

    def _is_moderator(self, member: discord.Member) -> bool:
        return (
            member.guild_permissions.manage_messages
            or member.guild_permissions.kick_members
            or member.guild_permissions.ban_members
            or member.guild_permissions.moderate_members
            or member.guild_permissions.administrator
        )

    async def _get_prefix(self, ctx: commands.Context) -> str:
        prefixes = await self.bot.get_prefix(ctx.message)
        return prefixes[0] if isinstance(prefixes, (list, tuple)) else prefixes

    def _is_mod_visible(self, is_moderator: bool, mapped_category: str) -> bool:
        return not (mapped_category == "moderation" and not is_moderator)

    def _paginate_lines(self, lines: list[str], limit: int = 3500) -> list[str]:
        pages = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > limit:
                pages.append(current.strip())
                current = ""
            current += line + "\n"
        if current.strip():
            pages.append(current.strip())
        return pages

    @commands.command(name="help")
    async def custom_help(self, ctx: commands.Context, category: str = None):
        is_moderator = bool(ctx.guild and isinstance(ctx.author, discord.Member) and self._is_moderator(ctx.author))
        prefix = await self._get_prefix(ctx)

        if category:
            category = category.lower()

            commands_in_category = []
            slash_commands_in_category = []
            category_title = ""
            category_color = 0x9B59B6

            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue

                cog_name = cmd.cog_name or "Other"
                mapped_category, title, color = self.category_mappings.get(
                    cog_name, ('misc', '🎭 Misc Commands', 0xF39C12)
                )

                if mapped_category == category and self._is_mod_visible(is_moderator, mapped_category):
                    commands_in_category.append(cmd)
                    category_title = title
                    category_color = color

            for app_cmd in self.bot.tree.get_commands():
                if hasattr(app_cmd, 'cog') and app_cmd.cog:
                    cog_name = app_cmd.cog.qualified_name
                    mapped_category, _, _ = self.category_mappings.get(
                        cog_name, ('misc', '🎭 Misc Commands', 0xF39C12)
                    )
                    if mapped_category == category and self._is_mod_visible(is_moderator, mapped_category):
                        slash_commands_in_category.append(app_cmd)

            if not commands_in_category and not slash_commands_in_category:
                valid_categories = {m[0] for m in self.category_mappings.values()}
                if category not in valid_categories:
                    await ctx.send(f"❌ Unknown category! Use: {', '.join(sorted(valid_categories))}")
                else:
                    await ctx.send("🔒 Moderation commands are only available to server moderators.")
                return

            embed = discord.Embed(title=category_title, color=category_color)

            if slash_commands_in_category:
                slash_names = [f"`/{cmd.name}`" for cmd in slash_commands_in_category[:8]]
                if len(slash_commands_in_category) > 8:
                    slash_names.append("...")
                embed.description = "**Slash commands:** " + ", ".join(slash_names)

            # fields have 1024 char limit per value; keep your original style, but protect it
            for cmd in sorted(commands_in_category, key=lambda c: c.name):
                usage = f"`{prefix}{cmd.name}`"
                if cmd.aliases:
                    aliases = ", ".join(f"`{prefix}{a}`" for a in cmd.aliases)
                    usage += f" (aliases: {aliases})"
                desc = cmd.help or "No description available."
                embed.add_field(name=usage, value=(desc[:1021] + "…") if len(desc) > 1024 else desc, inline=False)

            if category == 'moderation':
                embed.set_footer(text=f"Current prefix: {prefix} • Moderation commands require appropriate permissions")
            else:
                embed.set_footer(text=f"Current prefix: {prefix}")

            await ctx.send(embed=embed)
            return

        # Main help menu
        embed = discord.Embed(
            title="✨ Flicker Commands ✨",
            description=(
                "A magical Discord bot for divination, reference, and more!\n\n"
                f"**Current prefix:** `{prefix}`\n"
                "**🎯 All commands now available as slash commands!**\n"
                "Type `/` in chat to see all slash commands."
            ),
            color=0x9B59B6
        )

        available_categories = set()

        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            cog_name = cmd.cog_name or "Other"
            mapped_category, _, _ = self.category_mappings.get(cog_name, ('misc', '🎭 Misc Commands', 0xF39C12))
            if self._is_mod_visible(is_moderator, mapped_category):
                available_categories.add(mapped_category)

        for app_cmd in self.bot.tree.get_commands():
            if hasattr(app_cmd, 'cog') and app_cmd.cog:
                cog_name = app_cmd.cog.qualified_name
                mapped_category, _, _ = self.category_mappings.get(cog_name, ('misc', '🎭 Misc Commands', 0xF39C12))
                if self._is_mod_visible(is_moderator, mapped_category):
                    available_categories.add(mapped_category)

        category_info = {
            'divination': ('🔮 Divination', 'Tarot, runes, numerology, and mystical games'),
            'reference': ('📚 Reference', 'Herbs, crystals, and magical correspondences'),
            'generators': ('✨ Generators', 'Spells, sigils, and magical creations'),
            'utility': ('🌙 Utility', 'Moon phases, reminders, and helpful tools'),
            'moderation': ('🛡️ Moderation', 'Server management and admin tools'),
            'misc': ('🎭 Misc', 'Fun commands and personality features'),
        }

        for cat_key in ['divination', 'reference', 'generators', 'utility', 'moderation', 'misc']:
            if cat_key in available_categories:
                emoji, name = category_info[cat_key][0].split(' ', 1)
                desc = category_info[cat_key][1]
                embed.add_field(
                    name=f"{emoji} {name}",
                    value=f"`{prefix}help {cat_key}`\n{desc}",
                    inline=True
                )

        embed.add_field(name="\u200b", value=f"**📋 Complete list:** `{prefix}help_all`", inline=False)
        embed.set_footer(text=f"Use {prefix}help <category> for details • Type / to see all slash commands")
        await ctx.send(embed=embed)

    @commands.command(name="help_all", aliases=["commands", "allcommands"])
    async def help_all(self, ctx: commands.Context):
        is_moderator = bool(ctx.guild and isinstance(ctx.author, discord.Member) and self._is_moderator(ctx.author))
        prefix = await self._get_prefix(ctx)

        # group commands by cog
        commands_by_cog: dict[str, list[commands.Command]] = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            cog_name = cmd.cog_name or "Other"

            mapped_category, _, _ = self.category_mappings.get(cog_name, ('misc', '🎭 Misc Commands', 0xF39C12))
            if not self._is_mod_visible(is_moderator, mapped_category):
                continue

            display_name = self.category_display_names.get(cog_name, cog_name)
            commands_by_cog.setdefault(display_name, []).append(cmd)

        # flatten lines
        lines: list[str] = []
        for display_name in sorted(commands_by_cog.keys(), key=str.lower):
            lines.append(f"__{display_name}__")
            for cmd in sorted(commands_by_cog[display_name], key=lambda c: c.name):
                usage = f"`{prefix}{cmd.name}`"
                if cmd.aliases:
                    usage += f" (aliases: {', '.join(cmd.aliases)})"
                desc = cmd.help or "No description available."
                lines.append(f"• {usage} – {desc}")
            lines.append("")

        pages_text = self._paginate_lines(lines, limit=3500)

        embeds: list[discord.Embed] = []
        total = len(pages_text) if pages_text else 1

        for i, text in enumerate(pages_text or ["(No commands found.)"], start=1):
            embed = discord.Embed(
                title="✨ Complete Command List ✨",
                description=text,
                color=0x9B59B6
            )
            embed.set_footer(text=f"Page {i}/{total} • Tip: type / for slash commands")
            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
            return

        view = CommandPager(pages=embeds, author_id=ctx.author.id)
        msg = await ctx.send(embed=embeds[0], view=view)

        async def disable_on_timeout():
            await view.wait()
            try:
                await msg.edit(view=view)
            except Exception:
                pass

        # use create_task rather than bot.loop directly (safer in newer discord.py)
        try:
            self.bot.loop.create_task(disable_on_timeout())
        except Exception:
            # if loop access is weird in your env, just ignore the timeout edit
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))