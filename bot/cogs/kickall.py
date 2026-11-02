import discord
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from discord import app_commands
from discord.ext import commands

EXEMPT_ROLES_PATH = Path("bot/data/exemptroles.json")
LASTMSG_PATH = Path("bot/data/lastmessagetime.json")


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class KickallCog(commands.Cog, name="Kickall"):
    def __init__(self, bot):
        self.bot = bot
        self.dry_run = False
        self.delay_seconds = 1.0

        # guild_id -> [role_ids]
        self.exempt_roles_by_guild: dict[str, list[int]] = load_json(
            EXEMPT_ROLES_PATH, {}
        )

    # ---------- exempt role + inactivity helpers ----------

    def get_saved_exempt_role_ids(self, guild: discord.Guild) -> set[int]:
        """Return saved exempt role IDs for this guild from exemptroles.json."""
        raw = self.exempt_roles_by_guild.get(str(guild.id), [])
        return {int(r) for r in raw}

    def _load_last_message_map(self, guild: discord.Guild) -> dict[str, str]:
        """
        Load last-message timestamps for this guild from lastmessagetime.json.
        Returns: { user_id(str) -> iso_timestamp(str) }
        """
        data = load_json(LASTMSG_PATH, {})
        return data.get(str(guild.id), {})

    def _is_inactive(self, guild: discord.Guild, member: discord.Member, days: int) -> bool:
        """
        Inactivity based on last message in this guild.

        - If days <= 0: never treated as inactive.
        - If member joined after cutoff: treated as active (even if silent).
        - If no last-message record and joined before cutoff: treated as inactive.
        - If last-message timestamp is older than cutoff: inactive.
        """
        if days <= 0:
            return False

        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        # New members shouldn't be kicked just for being quiet
        if member.joined_at and member.joined_at > cutoff:
            return False

        guild_map = self._load_last_message_map(guild)
        ts = guild_map.get(str(member.id))

        # Never spoke, and they've been around long enough → treat as inactive
        if ts is None:
            return True

        try:
            last_dt = datetime.fromisoformat(ts.replace("Z", ""))
        except Exception:
            # Bad timestamp, assume inactive to be safe
            return True

        return last_dt <= cutoff

    async def _kickall_logic(
        self,
        guild: discord.Guild,
        author: discord.abc.User,
        extra_exempt_roles=None,
        inactive_days: int = 0,
        response_callback=None,
        preview_only: bool = False
    ):
        """
        Shared logic for kickall/kicklist command (both prefix and slash versions).

        - Uses saved exempt roles from exemptroles.json.
        - Uses extra_exempt_roles (role objects) passed in from commands.
        - If inactive_days == 0 and no exempt roles at all → refuses to run.
        """
        if extra_exempt_roles is None:
            extra_exempt_roles = []

        # Saved exempt roles for this guild
        saved_ids = self.get_saved_exempt_role_ids(guild)
        # Extra exempt roles from command invocation
        extra_ids = {r.id for r in extra_exempt_roles if r is not None}
        roles_to_keep = saved_ids | extra_ids

        # Safety: MUST have exempt roles unless you're filtering by inactivity
        if inactive_days <= 0 and not roles_to_keep:
            msg = (
                "❌ No exempt roles configured for this server, and no exempt roles were "
                "provided.\n"
                "Set exempt roles first (via your config / JSON), or use an inactivity "
                "filter like `!kickall 30` to only remove inactive members."
            )
            if response_callback:
                await response_callback(msg)
            return

        members_to_kick: list[discord.Member] = []

        for member in guild.members:
            # basic protection
            if member.bot:
                continue
            if member.id == guild.owner_id:
                continue
            if member.id == author.id:
                continue
            if self.bot.user and member.id == self.bot.user.id:
                continue
            if member.guild_permissions.administrator:
                continue

            # role-based protection
            member_role_ids = {r.id for r in member.roles}
            if roles_to_keep.intersection(member_role_ids):
                continue

            # inactivity filter (if set)
            if inactive_days > 0 and not self._is_inactive(guild, member, inactive_days):
                continue

            members_to_kick.append(member)

        if not members_to_kick:
            filter_desc = f" (inactive {inactive_days}+ days)" if inactive_days > 0 else ""
            msg = f"✅ No members found to kick{filter_desc}. Everyone is exempt or protected."
            if response_callback:
                await response_callback(msg)
            return

        # Format member list with basic info
        preview_lines = []
        for m in members_to_kick[:50]:
            joined_str = m.joined_at.strftime('%Y-%m-%d') if m.joined_at else 'Unknown'
            role_count = len(m.roles) - 1  # minus @everyone
            preview_lines.append(f"- {m} (`{m.id}`) • Joined: {joined_str} • Roles: {role_count}")

        filter_info = f" (inactive {inactive_days}+ days)" if inactive_days > 0 else ""
        msg = (
            f"Found **{len(members_to_kick)}** members{filter_info}.\n"
            f"First 50:\n" + "\n".join(preview_lines)
        )

        if response_callback:
            await response_callback(msg)

        # If preview only, stop here
        if preview_only:
            return

        if self.dry_run:
            if response_callback:
                await response_callback("🚧 DRY RUN is ON — no one was kicked.")
            return

        kicked = 0
        for member in members_to_kick:
            try:
                reason = f"Mass kick by {author} using kickall"
                if inactive_days > 0:
                    reason += f" (inactive {inactive_days}+ days)"
                await member.kick(reason=reason)
                kicked += 1
                await asyncio.sleep(self.delay_seconds)
            except Exception as e:
                print(f"Failed to kick {member} ({member.id}): {e}")

        if response_callback:
            await response_callback(f"✅ Done. Kicked **{kicked}** members.")

    def _save_exempt_roles_for_guild(self, guild: discord.Guild, ids: set[int]) -> None:
        """Persist this guild's exempt role IDs to exemptroles.json."""
        self.exempt_roles_by_guild[str(guild.id)] = list(ids)
        save_json(EXEMPT_ROLES_PATH, self.exempt_roles_by_guild)

    # ---------- SLASH COMMANDS (kickall / kicklist) ----------

    @app_commands.command(
        name="kickall",
        description="Kick members, respecting exempt roles + optional inactivity filter."
    )
    @app_commands.describe(
        exempt_role_1="Additional role to exempt from kicking (optional)",
        exempt_role_2="Second exempt role (optional)",
        exempt_role_3="Third exempt role (optional)",
        exempt_role_4="Fourth exempt role (optional)",
        inactive_days="Only kick members inactive for this many days (0 = all eligible)"
    )
    @app_commands.default_permissions(kick_members=True)
    async def kickall_slash(
        self,
        interaction: discord.Interaction,
        exempt_role_1: discord.Role | None = None,
        exempt_role_2: discord.Role | None = None,
        exempt_role_3: discord.Role | None = None,
        exempt_role_4: discord.Role | None = None,
        inactive_days: int = 0
    ):
        """
        Kick members in bulk.

        - Uses saved exempt roles from exemptroles.json.
        - You *may* add extra exempt roles.
        - If inactive_days == 0 and no exempt roles exist at all, it refuses to run.
        """
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None:
            await interaction.followup.send("❌ This command can only be used in a server.", ephemeral=True)
            return

        extra_exempt = [
            r for r in [exempt_role_1, exempt_role_2, exempt_role_3, exempt_role_4]
            if r is not None
        ]

        async def send_response(content):
            await interaction.followup.send(content, ephemeral=True)

        await self._kickall_logic(
            interaction.guild,
            interaction.user,
            extra_exempt_roles=extra_exempt,
            inactive_days=inactive_days,
            response_callback=send_response,
            preview_only=False,
        )

    @app_commands.command(
        name="kicklist",
        description="Preview who would be kicked with current filters/settings."
    )
    @app_commands.describe(
        exempt_role_1="Additional role to exempt from kicking (optional)",
        exempt_role_2="Second exempt role (optional)",
        exempt_role_3="Third exempt role (optional)",
        exempt_role_4="Fourth exempt role (optional)",
        inactive_days="Only show members inactive for this many days (0 = all eligible)"
    )
    @app_commands.default_permissions(kick_members=True)
    async def kicklist_slash(
        self,
        interaction: discord.Interaction,
        exempt_role_1: discord.Role | None = None,
        exempt_role_2: discord.Role | None = None,
        exempt_role_3: discord.Role | None = None,
        exempt_role_4: discord.Role | None = None,
        inactive_days: int = 0
    ):
        """Preview who would be kicked without actually performing the kick."""
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None:
            await interaction.followup.send("❌ This command can only be used in a server.", ephemeral=True)
            return

        extra_exempt = [
            r for r in [exempt_role_1, exempt_role_2, exempt_role_3, exempt_role_4]
            if r is not None
        ]

        async def send_response(content):
            await interaction.followup.send(content, ephemeral=True)

        await self._kickall_logic(
            interaction.guild,
            interaction.user,
            extra_exempt_roles=extra_exempt,
            inactive_days=inactive_days,
            response_callback=send_response,
            preview_only=True,
        )

    # ---------- PREFIX COMMANDS (kickall / kicklist) ----------

    @commands.command(name="kickall", aliases=["purge_now"])
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kickall_prefix(self, ctx: commands.Context, inactive_days: int = 0):
        """
        Kick members in bulk.

        Uses:
            !kickall           → Kick all eligible members (with saved/extra exempt roles)
            !kickall 30        → Kick only members inactive for 30+ days

        Saved exempt roles from exemptroles.json are always respected.
        """
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        async def send_response(content):
            await ctx.send(content)

        await self._kickall_logic(
            ctx.guild,
            ctx.author,
            extra_exempt_roles=[],
            inactive_days=inactive_days,
            response_callback=send_response,
            preview_only=False,
        )

    @commands.command(name="kicklist")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kicklist_prefix(self, ctx: commands.Context, inactive_days: int = 0):
        """
        Preview who would be kicked without actually kicking them.

        Uses:
            !kicklist          → Preview all eligible members (respects exempt roles)
            !kicklist 30       → Preview members inactive for 30+ days
        """
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        async def send_response(content):
            await ctx.send(content)

        await self._kickall_logic(
            ctx.guild,
            ctx.author,
            extra_exempt_roles=[],
            inactive_days=inactive_days,
            response_callback=send_response,
            preview_only=True,
        )

    # ---------- EXEMPT ROLE MANAGEMENT ----------

    @commands.group(name="exempt", invoke_without_command=True)
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def exempt_group(self, ctx: commands.Context):
        """Show current exempt roles used by kickall/kicklist in this server."""
        ids = self.get_saved_exempt_role_ids(ctx.guild)
        if not ids:
            await ctx.send(
                "No exempt roles configured for this server.\n"
                "Use `!exempt add @role` to start adding some."
            )
            return

        lines = []
        for rid in ids:
            role = ctx.guild.get_role(rid)
            if role is not None:
                lines.append(f"- {role.mention} (`{role.id}`)")
            else:
                lines.append(f"- *(deleted role)* `{rid}`")

        await ctx.send("Current exempt roles:\n" + "\n".join(lines))

    @exempt_group.command(name="add")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def exempt_add(self, ctx: commands.Context, *, role: discord.Role):
        """Add a role to the exempt list for this server."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        ids = self.get_saved_exempt_role_ids(ctx.guild)
        if role.id in ids:
            await ctx.send(f"{role.mention} is already in the exempt list.")
            return

        ids.add(role.id)
        self._save_exempt_roles_for_guild(ctx.guild, ids)
        await ctx.send(f"✅ Added {role.mention} to the exempt list.")

    @exempt_group.command(name="remove")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def exempt_remove(self, ctx: commands.Context, *, role: discord.Role):
        """Remove a role from the exempt list for this server."""
        ids = self.get_saved_exempt_role_ids(ctx.guild)
        if role.id not in ids:
            await ctx.send("That role is not currently in the exempt list.")
            return

        ids.discard(role.id)
        self._save_exempt_roles_for_guild(ctx.guild, ids)
        await ctx.send(f"✅ Removed {role.mention} from the exempt list.")

    @exempt_group.command(name="clear")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def exempt_clear(self, ctx: commands.Context):
        """Clear all exempt roles for this server."""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        self._save_exempt_roles_for_guild(ctx.guild, set())
        await ctx.send("✅ Cleared all exempt roles for this server.")


async def setup(bot):
    await bot.add_cog(KickallCog(bot))
