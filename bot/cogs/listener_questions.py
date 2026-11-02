import asyncio
from discord.ext import commands

VERIFICATION_CATEGORY_ID = 1438235003518718065
SPEAKEASY_CATEGORY_ID = 1438235528037404816


class QuestionsListener(commands.Cog, name="QuestionsListener"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not hasattr(channel, "category_id"):
            return

        if channel.category_id == VERIFICATION_CATEGORY_ID:
            await asyncio.sleep(1)

            verification_questions = (
                "1. What do you want us to call you?\n\n"
                "2. How old are you?\n\n"
                "3. Where did you find this server? if you were invited by someone, put their username!\n\n"
                "4. Why do you want to join Stars and Cards?\n\n"
                "5. If you're currently practicing, what does your craft look like?\n\n"
                "6. If you're still exploring, what areas of the occult are you most interested in applying to your practice?\n\n"
                "7. Do you agree to abide by the rules?"
            )

            try:
                await channel.send(verification_questions)
                print(f"✅ Sent verification questions to channel: {channel.name}")
            except Exception as e:
                print(f"❌ Failed to send verification questions: {e}")

        elif channel.category_id == SPEAKEASY_CATEGORY_ID:
            await asyncio.sleep(1)

            speakeasy_questions = (
                "welcome to the S&C speakeasy! if you would like to offer your services here, please fill out the questions below. if a question does not apply to you, please put n/a!\n\n"
                "**note: you will need to provide a sample/mock service for the category you are applying for. if you are applying for both roles, you will need to provide examples of both services. if you are not comfortable with such, please let us know so we can end the application here.**\n\n"
                "1. What year were you born in?\n\n"
                "2. How long have you been practicing divination?\n\n"
                "3. How long have you been practicing spellwork?\n\n"
                "4. What types of divination/spellwork do you practice? What types of divination/spellwork do you offer?\n\n"
                "5. How would you handle a situation where a client asks for an unethical or disallowed service?\n\n"
                "6. How would you handle a situation where a client asks for a service you cannot perform (either because of server rules, personal preference, or skill level)?\n\n"
                "7. What is the most challenging service you have offered? Why was it challenging?\n\n"
                "8. Do you want to offer paid services here? If so, why?\n\n"
                "9. Do you agree to abide by the servicer rules?\n\n"
                "once you complete these questions, please ping `@staff` so we can move on to the sample services!"
            )

            try:
                await channel.send(speakeasy_questions)
                print(f"✅ Sent speakeasy application questions to channel: {channel.name}")
            except Exception as e:
                print(f"❌ Failed to send speakeasy questions: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(QuestionsListener(bot))