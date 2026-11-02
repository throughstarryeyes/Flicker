import discord
from discord.ext import commands
from discord import app_commands
import random
import json

class GeneratorsCog(commands.Cog, name="Generators"):
    def __init__(self, bot):
        self.bot = bot
        with open('bot/data/correspondences/herbs.json', 'r') as f:
            self.herbs_data = json.load(f)['herbs']
        with open('bot/data/correspondences/crystals.json', 'r') as f:
            self.crystals_data = json.load(f)['crystals']
        with open('bot/data/correspondences/elements.json', 'r') as f:
            self.elements_data = json.load(f)

    @commands.command(name="spell")
    async def generate_spell(self, ctx, *, intention: str = None):
        if not intention:
            intention = random.choice(["protection", "love", "prosperity", "healing", "luck", "baneful"])
        
        intent_map = {
            "love": "love", "romance": "love", "attraction": "love",
            "protection": "protection", "shield": "protection", "defend": "protection",
            "healing": "healing", "health": "healing", "wellness": "healing",
            "prosperity": "prosperity", "wealth": "prosperity", "money": "prosperity", "abundance": "prosperity",
            "luck": "luck", "fortune": "luck", "success": "luck",
            "baneful": "baneful", "hex": "baneful", "curse": "baneful", "revenge": "baneful"
        }
        
        matched_intent = intent_map.get(intention.lower(), None)
        if not matched_intent:
            for key in intent_map:
                if key in intention.lower():
                    matched_intent = intent_map[key]
                    break
        
        if not matched_intent:
            matched_intent = random.choice(["protection", "love", "prosperity", "healing", "luck"])
        
        suitable_herbs = []
        suitable_crystals = []
        
        for name, data in self.herbs_data.items():
            if matched_intent in data['intents']:
                suitable_herbs.append({'name': name, 'data': data})
        
        for name, data in self.crystals_data.items():
            if matched_intent in data['intents']:
                suitable_crystals.append({'name': name, 'data': data})
        
        if not suitable_herbs:
            suitable_herbs = [{'name': name, 'data': data} for name, data in list(self.herbs_data.items())[:5]]
        if not suitable_crystals:
            suitable_crystals = [{'name': name, 'data': data} for name, data in list(self.crystals_data.items())[:5]]
        
        chosen_herb1 = random.choice(suitable_herbs)
        
        other_herbs = [h for h in suitable_herbs if h['name'] != chosen_herb1['name']]
        if other_herbs:
            chosen_herb2 = random.choice(other_herbs)
        else:
            all_herbs = [{'name': name, 'data': data} for name, data in self.herbs_data.items() if name != chosen_herb1['name']]
            chosen_herb2 = random.choice(all_herbs)
        
        chosen_crystal = random.choice(suitable_crystals)
        
        elements = list(set([chosen_herb1['data'].get('element', 'Air'), 
                             chosen_herb2['data'].get('element', 'Water'),
                             chosen_crystal['data'].get('element', 'Earth')]))
        element = random.choice(elements).split('/')[0]
        
        color_map = {
            "love": ["rose pink", "deep red", "soft pink"],
            "protection": ["black", "white", "deep purple"],
            "healing": ["green", "blue", "white"],
            "prosperity": ["gold", "green", "silver"],
            "luck": ["orange", "gold", "green"],
            "baneful": ["black", "dark red", "midnight purple"]
        }
        
        color = random.choice(color_map.get(matched_intent, ["white", "silver", "purple"]))
        
        moons = ["new moon", "waxing crescent", "full moon", "waning gibbous"]
        moon = random.choice(moons)
        
        intro_phrases = [
            f"Here's a powerful spell for {intention}...",
            f"I've crafted this {matched_intent} spell for you.",
            f"The energies align for this {intention} working.",
            f"This spell channels {element} energy for {matched_intent}."
        ]
        
        timing_phrases = [
            f"Best performed during the {moon} for maximum potency",
            f"The {moon} enhances this spell's power",
            f"Cast this ritual under the {moon}",
            f"Optimal timing: {moon} phase"
        ]
        
        affirmations = [
            f"By {element}'s sacred power, my will is done. So mote it be.",
            f"With {element} as my witness, this spell is cast. As above, so below.",
            f"Through {element}'s blessing, my intention manifests. And so it is.",
            f"By the ancient force of {element}, let this be. Blessed be."
        ]
        
        spell = f"""
{random.choice(intro_phrases)}

**Intention:** {intention.title()}

**Timing:** {random.choice(timing_phrases)}

**Gather These:**
• A {color} candle
• {chosen_herb1['name'].title()} ({chosen_herb1['data']['description']})
• {chosen_herb2['name'].title()} ({chosen_herb2['data']['description']})
• {chosen_crystal['name'].title()} ({chosen_crystal['data']['description']})

**Elemental Correspondence:** {element}

**The Working:**
1. Begin by cleansing your space with {element} energy
2. Cast your circle of protection
3. Light the {color} candle while holding your intention clearly in mind
4. Place the {chosen_crystal['name']} before the flame
5. Sprinkle or arrange the {chosen_herb1['name']} and {chosen_herb2['name']} around the crystal
6. Speak your intention aloud three times with conviction
7. Visualize your desired outcome as if already manifested
8. Allow the candle to burn down safely
9. Express gratitude and release your circle

**Seal With:** "{random.choice(affirmations)}"
"""
        
        embed = discord.Embed(
            title="✨ Your Custom Spell",
            description=spell,
            color=0x9B59B6
        )
        embed.set_footer(text=f"Spell woven for {ctx.author.display_name} • Work with pure intention")
        
        ctx.bot.last_spell = {
            'user_id': ctx.author.id,
            'content': spell,
            'intention': intention.title()
        }
        
        await ctx.send(embed=embed)

    @commands.command(name="sigil")
    async def generate_sigil(self, ctx, *, intention: str = None):
        if not intention:
            await ctx.send("✍️ Please provide an intention! Usage: `!sigil <your intention>`")
            return
        
        clean_text = intention.upper().replace(" ", "")
        unique_letters = []
        for letter in clean_text:
            if letter.isalpha() and letter not in unique_letters:
                unique_letters.append(letter)
        
        letter_string = "".join(unique_letters)
        
        sigil_methods = [
            "**Wheel Method:** Use a witches wheel/alphabet to map these letters into a connected symbol",
            "**Pictographic Method:** Draw these letters overlapping and combined into one unified symbol",
            "**Chaos Method:** Create an abstract symbol using the shapes of these letters as inspiration",
            "**Kamea Method:** Use a magic square to connect the numerical values of these letters"
        ]
        
        method = random.choice(sigil_methods)
        
        embed = discord.Embed(
            title="🖋️ Sigil Generator",
            description=f"**Intention:** {intention}",
            color=0x34495E
        )
        embed.add_field(name="Unique Letters", value=letter_string, inline=False)
        embed.add_field(name="Suggested Method", value=method, inline=False)
        embed.add_field(
            name="Instructions",
            value="1. Draw the letters in a creative, overlapping design\n2. Simplify and stylize the symbol\n3. Remove any recognizable letters\n4. Charge the sigil with your energy\n5. Activate it through meditation, burning, or burying",
            inline=False
        )
        embed.set_footer(text=f"Sigil for {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="teablend", aliases=["tea"])
    async def generate_tea(self, ctx, *, purpose: str = None):
        if not purpose:
            purpose = random.choice(["relaxation", "energy", "clarity", "sleep", "healing", "love"])
        
        intent_map = {
            "love": "love", "romance": "love",
            "protection": "protection", "safety": "protection",
            "healing": "healing", "health": "healing", "relaxation": "healing", "sleep": "healing",
            "prosperity": "prosperity", "wealth": "prosperity", "abundance": "prosperity",
            "luck": "luck", "fortune": "luck", "energy": "luck", "clarity": "luck"
        }
        
        matched_intent = intent_map.get(purpose.lower(), None)
        if not matched_intent:
            for key in intent_map:
                if key in purpose.lower():
                    matched_intent = intent_map[key]
                    break
        
        if not matched_intent:
            matched_intent = random.choice(["healing", "love", "protection", "luck"])
        
        tea_safe_herbs = ["chamomile", "lavender", "rose", "mint", "lemon balm", "rosemary", 
                          "jasmine", "hibiscus", "elderflower", "yarrow", "thyme", "basil"]
        
        suitable_herbs = []
        for name, data in self.herbs_data.items():
            if name in tea_safe_herbs and matched_intent in data['intents']:
                suitable_herbs.append({'name': name, 'data': data})
        
        if len(suitable_herbs) < 2:
            suitable_herbs = [{'name': name, 'data': self.herbs_data[name]} 
                            for name in tea_safe_herbs if name in self.herbs_data][:3]
        
        herb1 = random.choice(suitable_herbs)
        herb2 = random.choice([h for h in suitable_herbs if h['name'] != herb1['name']])
        
        base_teas = ["organic green tea", "premium black tea", "delicate white tea", "earthy rooibos"]
        additions = ["raw honey", "fresh lemon", "vanilla extract", "star anise", "cardamom pods", "orange peel"]
        
        base = random.choice(base_teas)
        addition = random.choice(additions)
        
        brew_time = random.choice(["3-5 minutes", "5-7 minutes", "7-10 minutes"])
        temp_map = {
            "healing": "175°F (80°C)",
            "love": "185°F (85°C)",
            "protection": "195°F (90°C)",
            "prosperity": "195°F (90°C)",
            "luck": "185°F (85°C)"
        }
        temp = temp_map.get(matched_intent, "185°F (85°C)")
        
        intro_phrases = [
            f"I've blended this tea specifically for {purpose}.",
            f"This aromatic blend supports {purpose}.",
            f"Here's your personalized {purpose} tea recipe.",
            f"Let this blend help you find {purpose}."
        ]
        
        ritual_phrases = [
            f"As you brew, envision {purpose} infusing each drop.",
            f"While steeping, hold the intention of {purpose} in your heart.",
            f"Breathe in the steam and welcome {purpose} into your being.",
            f"Let the warmth of this blend bring you {purpose}."
        ]
        
        blend = f"""
{random.choice(intro_phrases)}

**Intention:** {purpose.title()}

**Base:** {base.title()}

**Magical Herbs:**
• {herb1['name'].title()} - {herb1['data']['description']}
• {herb2['name'].title()} - {herb2['data']['description']}

**To Enhance:** Add a touch of {addition}

**Preparation:**
• Heat water to {temp}
• Steep for {brew_time}
• Stir clockwise (deosil) while focusing on your intention

**Sacred Ritual:** {random.choice(ritual_phrases)} Express gratitude before your first sip.
"""
        
        embed = discord.Embed(
            title="🍵 Your Enchanted Tea Blend",
            description=blend,
            color=0x8B4513
        )
        embed.set_footer(text=f"Blend crafted for {ctx.author.display_name} • Sip mindfully")
        
        await ctx.send(embed=embed)

    @commands.command(name="ingredients", aliases=["spellingredients", "magicalitems"])
    async def spell_ingredients_list(self, ctx):
        ingredients_text = """
**Common Spell Ingredients:**

**Candles:** White, red, green, blue, purple, black, silver, gold
**Herbs:** Lavender, rosemary, sage, basil, mint, thyme, bay leaves
**Crystals:** Amethyst, rose quartz, clear quartz, black tourmaline, citrine
**Incense:** Sandalwood, frankincense, myrrh, dragon's blood, jasmine
**Oils:** Lavender, rose, cinnamon, peppermint, eucalyptus
**Natural Items:** Salt, water, flowers, feathers, stones, coins
**Moon Water:** Water charged under different moon phases
**Sigils:** Hand-drawn symbols for specific intentions
**Charms:** Small bags filled with herbs and crystals
**Talismans:** Objects consecrated for protection or luck
"""
        
        embed = discord.Embed(
            title="🗂️ Magical Ingredients Reference",
            description=ingredients_text,
            color=0x8E44AD
        )
        embed.set_footer(text="Use !spell <intention> to generate custom spells")
        
        await ctx.send(embed=embed)

    @commands.command(name="makespell", aliases=["analyzespell", "ingredientspell"])
    async def make_spell(self, ctx, *, ingredients: str = None):
        """Analyze ingredients and create a spell based on their correspondences."""
        if not ingredients:
            embed = discord.Embed(
                title="✨ Make Me a Spell",
                description="Provide ingredients and I'll analyze their magical properties!\n\n**Usage:** `!makespell <ingredients>`\n\n**Example:** `!makespell rose, lavender, rose quartz, sage`",
                color=0xE67E22
            )
            await ctx.send(embed=embed)
            return
        
        ingredient_list = [i.strip().lower() for i in ingredients.split(',')]
        
        all_correspondences = {**self.herbs_data, **self.crystals_data, **self.elements_data}
        
        detected = []
        unknown = []
        intent_scores = {}
        
        for ingredient in ingredient_list:
            found = None
            
            if ingredient in all_correspondences:
                found = all_correspondences[ingredient]
            else:
                for name, data in all_correspondences.items():
                    if ingredient in data.get('synonyms', []):
                        found = data
                        break
            
            if found:
                item_type = found.get('type', 'element')
                detected.append({
                    'name': ingredient.title(),
                    'type': item_type,
                    'description': found['description'],
                    'intents': found['intents'],
                    'planet': found.get('planet', 'Unknown'),
                    'element': found.get('element', 'Unknown')
                })
                
                for intent, weight in found['intents'].items():
                    intent_scores[intent] = intent_scores.get(intent, 0) + weight
            else:
                unknown.append(ingredient.title())
        
        if not detected:
            embed = discord.Embed(
                title="✨ No Ingredients Recognized",
                description=f"I couldn't identify any of these ingredients: {', '.join(unknown)}\n\nTry common herbs (rose, sage, lavender) or crystals (amethyst, rose quartz, citrine).",
                color=0xE67E22
            )
            await ctx.send(embed=embed)
            return
        
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent = sorted_intents[0][0] if sorted_intents else "general"
        secondary_intent = sorted_intents[1][0] if len(sorted_intents) > 1 else None
        
        has_conflict = False
        if 'baneful' in intent_scores and 'love' in intent_scores:
            has_conflict = True
        elif 'baneful' in intent_scores and 'healing' in intent_scores:
            has_conflict = True
        
        embed = discord.Embed(
            title=f"✨ {primary_intent.title()} Spell",
            description=f"Based on your ingredients, I've crafted a **{primary_intent}** working.",
            color=0xE67E22
        )
        
        ingredients_text = ""
        for item in detected:
            ingredients_text += f"**{item['name']}** ({item['type'].title()})\n_{item['description']}_\n"
            intents_list = [f"{k.title()} ({v})" for k, v in item['intents'].items()]
            ingredients_text += f"Intent: {', '.join(intents_list)}\n\n"
        
        embed.add_field(name="📦 Your Ingredients", value=ingredients_text, inline=False)
        
        intent_text = f"**Primary:** {primary_intent.title()} ({intent_scores[primary_intent]} points)\n"
        if secondary_intent:
            intent_text += f"**Secondary:** {secondary_intent.title()} ({intent_scores[secondary_intent]} points)"
        embed.add_field(name="🎯 Detected Intent", value=intent_text, inline=False)
        
        if has_conflict:
            embed.add_field(
                name="⚠️ Conflicting Energies Detected",
                value="Your ingredients contain both baneful and beneficial energies. Consider using protection to frame your intent clearly, or separate these into different workings.",
                inline=False
            )
        
        ritual_text = f"Combine these ingredients in a ritual space. Focus on your intent of {primary_intent}. "
        if secondary_intent:
            ritual_text += f"Allow the energy of {secondary_intent} to support your primary goal. "
        ritual_text += "Visualize your desired outcome manifesting as you blend the energies together."
        
        embed.add_field(name="🌙 Ritual Guidance", value=ritual_text, inline=False)
        
        if unknown:
            embed.set_footer(text=f"Unknown ingredients: {', '.join(unknown)}")
        else:
            embed.set_footer(text="All ingredients recognized! ✨")
        
        spell_text = f"{embed.description}\n\n"
        for field in [ingredients_text, intent_text, ritual_text]:
            if field:
                spell_text += field + "\n\n"
        
        ctx.bot.last_spell = {
            'user_id': ctx.author.id,
            'content': spell_text,
            'intention': f"{primary_intent.title()} Spell"
        }
        
        await ctx.send(embed=embed)

    @commands.command(name="savespell")
    async def save_spell_command(self, ctx, *, spell_name: str = None):
        """Save the last generated spell to your personal spellbook."""
        if not spell_name:
            embed = discord.Embed(
                title="📖 Save Spell",
                description="Please provide a name for your spell!\n\n**Usage:** `!savespell <name>`\n\n**Example:** `!savespell Protection Shield`",
                color=0x9B59B6
            )
            await ctx.send(embed=embed)
            return
        
        if not hasattr(ctx.bot, 'last_spell') or not ctx.bot.last_spell:
            embed = discord.Embed(
                title="❌ No Spell to Save",
                description="You need to generate a spell first using `!spell` or `!makespell` before you can save it!",
                color=0xE74C3C
            )
            await ctx.send(embed=embed)
            return
        
        last_spell = ctx.bot.last_spell
        if last_spell['user_id'] != ctx.author.id:
            embed = discord.Embed(
                title="❌ Not Your Spell",
                description="You can only save spells that you generated yourself!",
                color=0xE74C3C
            )
            await ctx.send(embed=embed)
            return
        
        from bot.services.database import save_spell
        
        try:
            await save_spell(
                user_id=ctx.author.id,
                spell_name=spell_name,
                spell_content=last_spell['content'],
                intention=last_spell['intention']
            )
            
            embed = discord.Embed(
                title="✨ Spell Saved!",
                description=f"**{spell_name}** has been added to your personal spellbook.\n\nUse `!myspells` to view all your saved spells.",
                color=0x2ECC71
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Saving Spell",
                description="Something went wrong while saving your spell. Please try again.",
                color=0xE74C3C
            )
            await ctx.send(embed=embed)

    @commands.command(name="myspells", aliases=["spellbook", "savedspells"])
    async def my_spells(self, ctx):
        """View your personal spellbook."""
        from bot.services.database import get_user_spells
        
        try:
            spells = await get_user_spells(ctx.author.id)
            
            if not spells:
                embed = discord.Embed(
                    title="📖 Your Spellbook",
                    description="Your spellbook is empty. Generate spells with `!spell` or `!makespell` and save them with `!savespell <name>`!",
                    color=0x9B59B6
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📖 Your Spellbook",
                description=f"You have **{len(spells)}** saved spell(s).",
                color=0x9B59B6
            )
            
            for spell_id, spell_name, spell_content, intention, created_at in spells[:10]:
                from datetime import datetime
                created = datetime.fromisoformat(created_at)
                date_str = created.strftime("%b %d, %Y")
                
                preview = spell_content[:200] + "..." if len(spell_content) > 200 else spell_content
                
                embed.add_field(
                    name=f"✨ {spell_name}",
                    value=f"*{intention}* • Saved on {date_str}\n{preview}",
                    inline=False
                )
            
            if len(spells) > 10:
                embed.set_footer(text=f"Showing 10 of {len(spells)} spells")
            else:
                embed.set_footer(text=f"{ctx.author.display_name}'s Spellbook")
            
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Loading Spells",
                description="Something went wrong while loading your spellbook. Please try again.",
                color=0xE74C3C
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="spell", description="Generate a custom spell using real magical correspondences")
    @app_commands.describe(intention="Your magical intention (love, protection, healing, prosperity, luck, baneful)")
    async def spell_slash(self, interaction: discord.Interaction, intention: str = None):
        """Slash command for spell generation."""
        await interaction.response.defer()
        
        if not intention:
            intention = random.choice(["protection", "love", "prosperity", "healing", "luck"])
        
        intent_map = {
            "love": "love", "romance": "love", "attraction": "love",
            "protection": "protection", "shield": "protection", "defend": "protection",
            "healing": "healing", "health": "healing", "wellness": "healing",
            "prosperity": "prosperity", "wealth": "prosperity", "money": "prosperity", "abundance": "prosperity",
            "luck": "luck", "fortune": "luck", "success": "luck",
            "baneful": "baneful", "hex": "baneful", "curse": "baneful", "revenge": "baneful"
        }
        
        matched_intent = intent_map.get(intention.lower(), None)
        if not matched_intent:
            for key in intent_map:
                if key in intention.lower():
                    matched_intent = intent_map[key]
                    break
        
        if not matched_intent:
            matched_intent = random.choice(["protection", "love", "prosperity", "healing", "luck"])
        
        suitable_herbs = []
        suitable_crystals = []
        
        for name, data in self.herbs_data.items():
            if matched_intent in data['intents']:
                suitable_herbs.append({'name': name, 'data': data})
        
        for name, data in self.crystals_data.items():
            if matched_intent in data['intents']:
                suitable_crystals.append({'name': name, 'data': data})
        
        if not suitable_herbs:
            suitable_herbs = [{'name': name, 'data': data} for name, data in list(self.herbs_data.items())[:5]]
        if not suitable_crystals:
            suitable_crystals = [{'name': name, 'data': data} for name, data in list(self.crystals_data.items())[:5]]
        
        chosen_herb1 = random.choice(suitable_herbs)
        other_herbs = [h for h in suitable_herbs if h['name'] != chosen_herb1['name']]
        if other_herbs:
            chosen_herb2 = random.choice(other_herbs)
        else:
            all_herbs = [{'name': name, 'data': data} for name, data in self.herbs_data.items() if name != chosen_herb1['name']]
            chosen_herb2 = random.choice(all_herbs)
        
        chosen_crystal = random.choice(suitable_crystals)
        
        elements = list(set([chosen_herb1['data'].get('element', 'Air'), 
                             chosen_herb2['data'].get('element', 'Water'),
                             chosen_crystal['data'].get('element', 'Earth')]))
        element = random.choice(elements).split('/')[0]
        
        color_map = {
            "love": ["rose pink", "deep red", "soft pink"],
            "protection": ["black", "white", "deep purple"],
            "healing": ["green", "blue", "white"],
            "prosperity": ["green", "gold", "silver"],
            "luck": ["orange", "gold", "green"],
            "baneful": ["black", "dark red", "deep purple"]
        }
        candle_color = random.choice(color_map.get(matched_intent, ["white"]))
        
        timings = ["during a full moon", "at midnight", "at dawn", "at dusk", "during a new moon", "on a Tuesday", "on a Friday", "during the waxing moon"]
        timing = random.choice(timings)
        
        actions = ["light your candle and focus on your intention", "arrange the ingredients in a circle", 
                  "hold the crystal and visualize your goal", "chant your intention three times"]
        action = random.choice(actions)
        
        spell_text = f"""**Ingredients:**
• {chosen_herb1['name'].title()} - {chosen_herb1['data'].get('planet', 'N/A')} energy
• {chosen_herb2['name'].title()} - {chosen_herb2['data'].get('planet', 'N/A')} energy
• {chosen_crystal['name'].title()}
• {candle_color.title()} candle

**Instructions:**
Perform this spell {timing}. {action.capitalize()}. Combine your herbs and place them around the crystal. Let the candle burn for at least 20 minutes while focusing on {matched_intent}.

**Element:** {element}
**Best Time:** {timing.capitalize()}"""
        
        embed = discord.Embed(
            title=f"✨ {matched_intent.title()} Spell",
            description=spell_text,
            color=0xE67E22
        )
        embed.set_footer(text=f"Spell generated for {interaction.user.display_name} • Use /savespell to save this spell")
        
        if not hasattr(self.bot, 'last_generated_spells'):
            self.bot.last_generated_spells = {}
        self.bot.last_generated_spells[interaction.user.id] = {
            'name': f"{matched_intent.title()} Spell",
            'content': spell_text,
            'type': 'generated'
        }
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="sigil", description="Generate a sigil from your intention")
    @app_commands.describe(intention="Your magical intention or goal")
    async def sigil_slash(self, interaction: discord.Interaction, intention: str):
        """Slash command for sigil generation."""
        clean_text = intention.upper().replace(" ", "")
        unique_letters = []
        for char in clean_text:
            if char.isalpha() and char not in unique_letters:
                unique_letters.append(char)
        
        sigil_pattern = ''.join(unique_letters)
        
        embed = discord.Embed(
            title="🔯 Your Personal Sigil",
            description=f"**Intention:** {intention}\n\n**Sigil Pattern:** `{sigil_pattern}`",
            color=0x9B59B6
        )
        embed.add_field(
            name="How to Use",
            value="Draw these letters in an artistic way, overlapping and combining them into a unique symbol. Charge it with your energy and keep it secret.",
            inline=False
        )
        embed.set_footer(text=f"Sigil created for {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="myspells", description="View your saved spells")
    async def myspells_slash(self, interaction: discord.Interaction):
        """Slash command to view saved spells."""
        await interaction.response.defer(ephemeral=True)
        
        from bot.services.database import get_user_spells
        spells = await get_user_spells(interaction.user.id)
        
        if not spells:
            await interaction.followup.send("📖 Your spellbook is empty. Generate spells with `/spell` and save them with `/savespell`!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📖 {interaction.user.display_name}'s Spellbook",
            description=f"You have **{len(spells)}** saved spell(s)",
            color=0x9B59B6
        )
        
        for i, (spell_id, spell_name, spell_content, created_at) in enumerate(spells[:10], 1):
            preview = spell_content[:100] + "..." if len(spell_content) > 100 else spell_content
            embed.add_field(
                name=f"{i}. {spell_name}",
                value=preview,
                inline=False
            )
        
        if len(spells) > 10:
            embed.set_footer(text=f"Showing 10 of {len(spells)} spells")
        else:
            embed.set_footer(text=f"Total: {len(spells)} spell(s)")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneratorsCog(bot))
