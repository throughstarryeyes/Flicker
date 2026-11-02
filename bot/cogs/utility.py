import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from dateutil import parser
from astral import LocationInfo
from astral.sun import sun
from astral.moon import phase
import sys
sys.path.append('.')
from bot.services.database import store_secret, add_reminder, get_due_reminders

class UtilityCog(commands.Cog, name="Utility"):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @commands.command(name="secret", aliases=["tellmeasecret"])
    async def tell_secret(self, ctx, *, secret: str = None):
        if not secret:
            await ctx.send("🤫 Tell me a secret! Usage: `!secret <your secret>`")
            return
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        await store_secret(ctx.author.id, secret)
        
        try:
            await ctx.author.send("your secret is safe with me :star:")
        except:
            pass
        
        await ctx.send(f"Your secret disappears into the void...", delete_after=5)

    @commands.command(name="remind", aliases=["reminder", "remindme"])
    async def set_reminder(self, ctx, time_str: str, *, message: str = "Reminder!"):
        try:
            now = datetime.now()
            
            if time_str.endswith('m'):
                minutes = int(time_str[:-1])
                due_time = now + timedelta(minutes=minutes)
            elif time_str.endswith('h'):
                hours = int(time_str[:-1])
                due_time = now + timedelta(hours=hours)
            elif time_str.endswith('d'):
                days = int(time_str[:-1])
                due_time = now + timedelta(days=days)
            else:
                try:
                    due_time = parser.parse(time_str)
                    if due_time < now:
                        due_time = due_time.replace(year=now.year + 1)
                except:
                    await ctx.send("❌ Invalid time format! Use: `10m`, `2h`, `1d`, or a date like `Dec 25 3pm`")
                    return
            
            await add_reminder(ctx.author.id, ctx.channel.id, due_time, message)
            
            time_until = due_time - now
            hours, remainder = divmod(int(time_until.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_desc = []
            if hours > 0:
                time_desc.append(f"{hours}h")
            if minutes > 0:
                time_desc.append(f"{minutes}m")
            if not time_desc:
                time_desc.append(f"{seconds}s")
            
            await ctx.send(f"⏰ Reminder set for {' '.join(time_desc)} from now!")
            
        except Exception as e:
            await ctx.send(f"❌ Error setting reminder: {e}")

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        try:
            reminders = await get_due_reminders()
            for reminder_id, user_id, channel_id, message in reminders:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        user = self.bot.get_user(user_id)
                        await channel.send(f"⏰ {user.mention} Reminder: {message}")
                except Exception as e:
                    print(f"Failed to send reminder: {e}")
        except Exception as e:
            print(f"Error checking reminders: {e}")

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @commands.command(name="moonphase", aliases=["moon"])
    async def moon_phase(self, ctx):
        try:
            now = datetime.now()
            moon_phase_value = phase(now)
            
            if moon_phase_value < 1:
                phase_name = "New Moon"
                emoji = "🌑"
                meaning = "New beginnings, setting intentions, planting seeds"
            elif moon_phase_value < 6.5:
                phase_name = "Waxing Crescent"
                emoji = "🌒"
                meaning = "Growth, manifestation, building energy"
            elif moon_phase_value < 8.5:
                phase_name = "First Quarter"
                emoji = "🌓"
                meaning = "Action, decision-making, overcoming obstacles"
            elif moon_phase_value < 13.5:
                phase_name = "Waxing Gibbous"
                emoji = "🌔"
                meaning = "Refinement, editing, perfecting your plans"
            elif moon_phase_value < 15.5:
                phase_name = "Full Moon"
                emoji = "🌕"
                meaning = "Completion, celebration, release, divination"
            elif moon_phase_value < 20.5:
                phase_name = "Waning Gibbous"
                emoji = "🌖"
                meaning = "Gratitude, sharing, teaching what you've learned"
            elif moon_phase_value < 22.5:
                phase_name = "Last Quarter"
                emoji = "🌗"
                meaning = "Letting go, breaking habits, forgiveness"
            else:
                phase_name = "Waning Crescent"
                emoji = "🌘"
                meaning = "Rest, reflection, surrender, preparation"
            
            embed = discord.Embed(
                title=f"{emoji} Current Moon Phase",
                description=f"**{phase_name}**",
                color=0x808080
            )
            embed.add_field(name="Energy", value=meaning, inline=False)
            embed.add_field(name="Moon Age", value=f"{moon_phase_value:.1f} days", inline=True)
            embed.set_footer(text=f"Moon phase for {now.strftime('%B %d, %Y')}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting moon phase: {e}")

    @commands.command(name="planets", aliases=["planetpositions"])
    async def planet_positions(self, ctx):
        """Show current positions of all major planets."""
        try:
            from skyfield.api import load
            
            ts = load.timescale()
            planets_data = load('de421.bsp')
            
            earth = planets_data['earth']
            now = ts.now()
            
            planet_list = [
                ('Mercury', 'mercury barycenter', '☿'),
                ('Venus', 'venus barycenter', '♀'),
                ('Mars', 'mars barycenter', '♂'),
                ('Jupiter', 'jupiter barycenter', '♃'),
                ('Saturn', 'saturn barycenter', '♄')
            ]
            
            positions_text = ""
            
            for name, id_name, symbol in planet_list:
                try:
                    planet = planets_data[id_name]
                    astrometric = earth.at(now).observe(planet)
                    lat, lon, dist = astrometric.ecliptic_latlon()
                    
                    zodiac_signs = [
                        'Aries', 'Taurus', 'Gemini', 'Cancer', 
                        'Leo', 'Virgo', 'Libra', 'Scorpio',
                        'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
                    ]
                    
                    degree = lon.degrees % 360
                    sign_index = int(degree / 30)
                    sign_degree = degree % 30
                    
                    positions_text += f"{symbol} **{name}**: {zodiac_signs[sign_index]} {sign_degree:.1f}°\n"
                except:
                    positions_text += f"{symbol} **{name}**: Position unavailable\n"
            
            embed = discord.Embed(
                title="🪐 Current Planet Positions",
                description=positions_text,
                color=0x4B0082
            )
            embed.set_footer(text=f"Planetary positions for {datetime.now().strftime('%B %d, %Y')}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error calculating planet positions: {e}\nThe bot may be downloading ephemeris data - try again in a moment!")

    @commands.command(name="retrograde", aliases=["mercury", "mercuryretrograde"])
    async def check_retrograde(self, ctx, planet_name: str = "mercury"):
        """Check if a planet is currently in retrograde."""
        try:
            from skyfield.api import load
            import numpy as np
            
            planet_name = planet_name.lower()
            
            planet_mapping = {
                'mercury': ('Mercury', 'mercury barycenter', '☿'),
                'venus': ('Venus', 'venus barycenter', '♀'),
                'mars': ('Mars', 'mars barycenter', '♂'),
                'jupiter': ('Jupiter', 'jupiter barycenter', '♃'),
                'saturn': ('Saturn', 'saturn barycenter', '♄')
            }
            
            if planet_name not in planet_mapping:
                await ctx.send(f"❌ Unknown planet! Try: mercury, venus, mars, jupiter, or saturn")
                return
            
            name, id_name, symbol = planet_mapping[planet_name]
            
            ts = load.timescale()
            planets_data = load('de421.bsp')
            
            earth = planets_data['earth']
            planet = planets_data[id_name]
            
            now_time = datetime.now()
            days_back = 5
            days_forward = 5
            
            date_range = [now_time + timedelta(days=i) for i in range(-days_back, days_forward + 1)]
            times = [ts.utc(d.year, d.month, d.day) for d in date_range]
            
            lon_degrees = []
            for t in times:
                astrometric = earth.at(t).observe(planet)
                lat, lon, dist = astrometric.ecliptic_latlon()
                lon_degrees.append(lon.degrees)
            
            lon_change = np.diff(lon_degrees)
            
            lon_change = np.array([(diff + 180) % 360 - 180 for diff in lon_change])
            
            current_retrograde = lon_change[days_back - 1] < -0.01
            
            if current_retrograde:
                status = f"**YES** - {name} is currently in retrograde"
                color = 0xFF6B6B
                advice = f"{name} retrograde brings introspection and review. Great time to re-evaluate, revise, and reflect!"
            else:
                status = f"**NO** - {name} is currently direct (not retrograde)"
                color = 0x6BCF7F
                advice = f"{name} is moving forward! This is a time for action and progress in {name}'s domains."
            
            embed = discord.Embed(
                title=f"{symbol} {name} Retrograde Check",
                description=status,
                color=color
            )
            embed.add_field(name="Energy", value=advice, inline=False)
            embed.set_footer(text=f"Retrograde status for {datetime.now().strftime('%B %d, %Y')}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error checking retrograde: {e}\nThe bot may be downloading ephemeris data - try again in a moment!")
    
    @app_commands.command(name="moonphase", description="Check the current phase of the moon")
    async def moonphase_slash(self, interaction: discord.Interaction):
        """Slash command for moon phase."""
        try:
            today = datetime.now().date()
            moon_phase_value = phase(today)
            
            phase_names = {
                (0, 1): "🌑 New Moon",
                (1, 7): "🌒 Waxing Crescent",
                (7, 8): "🌓 First Quarter",
                (8, 14): "🌔 Waxing Gibbous",
                (14, 15): "🌕 Full Moon",
                (15, 21): "🌖 Waning Gibbous",
                (21, 22): "🌗 Last Quarter",
                (22, 28): "🌘 Waning Crescent"
            }
            
            phase_name = "🌑 New Moon"
            for (start, end), name in phase_names.items():
                if start <= moon_phase_value < end:
                    phase_name = name
                    break
            
            embed = discord.Embed(
                title=f"{phase_name}",
                description=f"Current moon illumination: **{moon_phase_value:.1f}** days into lunar cycle",
                color=0x5865F2
            )
            embed.set_footer(text=f"Moon phase for {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error checking moon phase: {e}", ephemeral=True)
    
    @app_commands.command(name="planets", description="View current planetary positions in zodiac signs")
    async def planets_slash(self, interaction: discord.Interaction):
        """Slash command for planetary positions."""
        await interaction.response.defer()
        
        try:
            from skyfield.api import load
            from datetime import timezone
            
            eph = load('de421.bsp')
            ts = load.timescale()
            now_utc = datetime.now(timezone.utc)
            t = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute)
            
            earth = eph['earth']
            planets_data = {
                'Sun': eph['sun'],
                'Moon': eph['moon'],
                'Mercury': eph['mercury'],
                'Venus': eph['venus'],
                'Mars': eph['mars barycenter'],
                'Jupiter': eph['jupiter barycenter'],
                'Saturn': eph['saturn barycenter']
            }
            
            zodiac_signs = [
                'Aries ♈', 'Taurus ♉', 'Gemini ♊', 'Cancer ♋',
                'Leo ♌', 'Virgo ♍', 'Libra ♎', 'Scorpio ♏',
                'Sagittarius ♐', 'Capricorn ♑', 'Aquarius ♒', 'Pisces ♓'
            ]
            
            embed = discord.Embed(
                title="🪐 Current Planetary Positions",
                color=0x5865F2
            )
            
            for planet_name, planet_body in planets_data.items():
                astrometric = earth.at(t).observe(planet_body)
                ra, dec, distance = astrometric.radec()
                ecliptic_lon = astrometric.apparent().ecliptic_latlon()[1].degrees
                
                zodiac_index = int(ecliptic_lon / 30)
                degree_in_sign = ecliptic_lon % 30
                
                sign = zodiac_signs[zodiac_index]
                embed.add_field(
                    name=planet_name,
                    value=f"{sign} ({degree_in_sign:.1f}°)",
                    inline=True
                )
            
            embed.set_footer(text=f"Positions calculated for {interaction.user.display_name}")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error calculating positions: {e}")

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
