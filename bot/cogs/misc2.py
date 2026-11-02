import discord
from discord import app_commands
from discord.ext import commands

class Misc2Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """tinker zone 2: do not delete"""

    @commands.command(name="tarot2")
    async def tarotbetter(self, ctx):
        """Display a better tarot reading."""
        # Placeholder for better tarot reading logic
        embed = discord.Embed(title="tarot placeholder", 
                              description="this is where the tarot reading will be",
                              color=0x00ff00
                              )
        embed.set_footer(text="footer text here.")
        await ctx.send(embed=embed)
        
    @commands.command(name="crystaloracle", aliases=["coracle", "crystalcard"])
    async def crystaloracle(self, ctx):
        """Display a crystal oracle reading."""
        # embed placeholder for crystal oracle logic
        embed = discord.Embed(title="crystal oracle placeholder",
                              description="crystal oracle description here",
                              color=0xffffff)
        embed.set_footer(text="footer text here. | made with magic by saturn")
        await ctx.send(embed=embed)
        
    @commands.command(name="moonoracle", aliases=["mooncard", "moonreading"])
    async def moonoracle(self, ctx):
        """Display a moon oracle reading for phases of the moon."""
        #embed placeholder for moon oracle logic
        embed = discord.Embed(title="moon oracle placeholder",
                              description="moon oracle description here",
                              color=0x000000)
        embed.set_footer(text="footer text here | made with magic by saturn")
        await ctx.send(embed=embed)
        
    @commands.command(name="sunmoonandstars", aliases=["smsoracle", "sunmoonstars", "sms", "sunmoonandstarsoracle"])
    async def sunmoonandstars(self, ctx):
        """Saturn's personal oracle deck."""
        # embed placeholder for sms oracle logic
        embed = discord.Embed(title="sun moon and stars oracle placeholder",
                              description= "description here",
                              color=0xFFF000)
        embed.set_footer(text="footer text here | made with magic by saturn")
        await ctx.send(embed=embed)

async def setup(bot):
    print("tinker cog 2 being loaded...")
    await bot.add_cog(Misc2Cog(bot))
