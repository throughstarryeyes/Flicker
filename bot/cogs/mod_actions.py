import discord
from datetime import timedelta
from discord import app_commands
from discord.ext import commands


class ModActionsCog(commands.Cog, name="Moderation"):
    def __init__(self, bot):
        self.bot = bot

    # ---------- PREFIX COMMANDS ----------

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.kick(reason=f"{reason} (By {ctx.author})")
            await ctx.send(f"✅ Kicked {member.mention}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Failed to kick {member.mention}: {e}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.ban(reason=f"{reason} (By {ctx.author})")
            await ctx.send(f"✅ Banned {member.mention}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Failed to ban {member.mention}: {e}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{reason} (By {ctx.author})")
            await ctx.send(f"✅ Unbanned {user.name}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Failed to unban user: {e}")

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute_member(self, ctx, member: discord.Member, duration: int = 60, *, reason: str = "No reason provided"):
        try:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=f"{reason} (By {ctx.author})")
            await ctx.send(f"✅ Muted {member.mention} for {duration} minutes. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Failed to mute {member.mention}: {e}")

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute_member(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.send(f"✅ Unmuted {member.mention}")
        except Exception as e:
            await ctx.send(f"❌ Failed to unmute {member.mention}: {e}")

    # ---------- SLASH COMMANDS ----------

    @app_commands.command(name="ping", description="Check bot latency and responsiveness")
    async def ping_slash(self, interaction: discord.Interaction):
        """Check bot latency (slash command)"""
        latency_ms = round(self.bot.latency * 1000, 2)
        await interaction.response.send_message(f"🏓 Pong! Latency: **{latency_ms}ms**")

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    @app_commands.default_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command to kick a member."""
        try:
            await member.kick(reason=f"{reason} (By {interaction.user})")
            await interaction.response.send_message(f"✅ Kicked {member.mention}. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick {member.mention}: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for banning")
    @app_commands.default_permissions(ban_members=True)
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command to ban a member."""
        try:
            await member.ban(reason=f"{reason} (By {interaction.user})")
            await interaction.response.send_message(f"✅ Banned {member.mention}. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to ban {member.mention}: {e}", ephemeral=True)

    @app_commands.command(name="mute", description="Mute (timeout) a member")
    @app_commands.describe(member="The member to mute", duration="Duration in minutes", reason="Reason for muting")
    @app_commands.default_permissions(moderate_members=True)
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: int = 60, reason: str = "No reason provided"):
        """Slash command to mute a member."""
        try:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=f"{reason} (By {interaction.user})")
            await interaction.response.send_message(f"✅ Muted {member.mention} for {duration} minutes. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to mute {member.mention}: {e}", ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute (remove timeout from) a member")
    @app_commands.describe(member="The member to unmute")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member):
        """Slash command to unmute a member."""
        try:
            await member.timeout(None)
            await interaction.response.send_message(f"✅ Unmuted {member.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to unmute {member.mention}: {e}", ephemeral=True)

    @app_commands.command(
        name="verify",
        description="Verify a user by adding and/or removing roles."
    )
    @app_commands.describe(
        member="User to verify",
        add_role="Role to add (optional)",
        remove_role="Role to remove (optional)",
        reason="Optional reason (for audit log)"
    )
    @app_commands.default_permissions(manage_roles=True)
    async def verify_slash(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        add_role: discord.Role | None = None,
        remove_role: discord.Role | None = None,
        reason: str | None = None
    ):
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None:
            await interaction.followup.send("❌ This command can only be used in a server.", ephemeral=True)
            return

        if add_role is None and remove_role is None:
            await interaction.followup.send(
                "❌ You must specify at least one role to add or remove.",
                ephemeral=True
            )
            return

        # Basic sanity: don't let people verify the bot, owner, or themselves (optional)
        if self.bot.user and member.id == self.bot.user.id:
            await interaction.followup.send("❌ I can't verify myself.", ephemeral=True)
            return

        me = interaction.guild.me  # type: ignore
        if me is None:
            await interaction.followup.send("❌ Could not resolve my member object in this guild.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.followup.send("❌ I need **Manage Roles** permission to do that.", ephemeral=True)
            return

        # Helper to check role hierarchy
        def role_manageable(role: discord.Role) -> bool:
            # Can't manage @everyone or roles >= bot's top role
            if role.is_default():
                return False
            return role < me.top_role

        # Validate roles against bot hierarchy
        if add_role and not role_manageable(add_role):
            await interaction.followup.send(
                f"❌ I can't add {add_role.mention} because it's above (or equal to) my top role.",
                ephemeral=True
            )
            return

        if remove_role and not role_manageable(remove_role):
            await interaction.followup.send(
                f"❌ I can't remove {remove_role.mention} because it's above (or equal to) my top role.",
                ephemeral=True
            )
            return

        # Validate invoker hierarchy too (prevents mods giving/removing roles above themselves)
        invoker = interaction.user
        if isinstance(invoker, discord.Member):
            if add_role and add_role >= invoker.top_role and invoker != interaction.guild.owner:
                await interaction.followup.send(
                    f"❌ You can't add {add_role.mention} because it's above (or equal to) your top role.",
                    ephemeral=True
                )
                return
            if remove_role and remove_role >= invoker.top_role and invoker != interaction.guild.owner:
                await interaction.followup.send(
                    f"❌ You can't remove {remove_role.mention} because it's above (or equal to) your top role.",
                    ephemeral=True
                )
                return

        changes = []
        audit_reason = reason or f"Verified by {interaction.user}"

        try:
            if add_role and add_role not in member.roles:
                await member.add_roles(add_role, reason=audit_reason)
                changes.append(f"➕ Added {add_role.mention}")
            elif add_role:
                changes.append(f"ℹ️ {add_role.mention} was already present")

            if remove_role and remove_role in member.roles:
                await member.remove_roles(remove_role, reason=audit_reason)
                changes.append(f"➖ Removed {remove_role.mention}")
            elif remove_role:
                changes.append(f"ℹ️ {remove_role.mention} was not on the user")
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to modify that user/role.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"❌ Verify failed: `{e}`", ephemeral=True)
            return

        summary = "\n".join(changes) if changes else "No changes were made."
        await interaction.followup.send(
            f"✅ Verified {member.mention}.\n{summary}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ModActionsCog(bot))
