import discord
from discord.ext import commands
import json, os, random, time, datetime

PREFIX = "!"
BOT_TOKEN = "MTU2NTk3Mzg4NjY2MTU1ODM1Mw.GlsO_2.Ev_CEdtuwmDYZqtb2M1CogbrfKvDNqRstrSrgk"
ECO = "economy.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

def get_eco(uid):
    d = json.load(open(ECO)) if os.path.exists(ECO) else {}
    u = str(uid)
    if u not in d:
        d[u] = {"wallet": 1000, "bank": 0, "daily": 0, "warns": 0}
        json.dump(d, open(ECO, "w"), indent=2)
    return d[u]

def save_eco(uid, data):
    d = json.load(open(ECO)) if os.path.exists(ECO) else {}
    d[str(uid)] = data
    json.dump(d, open(ECO, "w"), indent=2)

async def find_member(ctx, query):
    if not query: return None
    if query.isdigit(): return ctx.guild.get_member(int(query))
    if query.startswith("<@"): 
        try: return await commands.MemberConverter().convert(ctx, query)
        except: pass
    return discord.utils.find(lambda m: query.lower() in m.name.lower() or query.lower() in m.display_name.lower(), ctx.guild.members)

# ==========================================
# HELP UI
# ==========================================
class HelpMenu(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Moderation", emoji="🛡️", value="mod"),
            discord.SelectOption(label="Economy", emoji="💰", value="eco"),
            discord.SelectOption(label="Gambling", emoji="🎲", value="gam"),
            discord.SelectOption(label="Fun & RP", emoji="🎉", value="fun"),
            discord.SelectOption(label="Utility", emoji="🔧", value="util"),
        ]
        super().__init__(placeholder="Choose a category...", options=opts)

    async def callback(self, i: discord.Interaction):
        await i.response.defer()
        e = discord.Embed(color=discord.Color.from_rgb(43,45,49))
        v = self.values[0]
        if v == "mod":
            e.title = "🛡️ Moderation"
            e.description = "`/ban` `/kick` `/warn` `/timeout` `/purge` `/lock` `/unlock`\n*(Gumagana rin as `!ban`, etc.)*"
        elif v == "eco":
            e.title = "💰 Economy"
            e.description = "`/balance` `/daily` `/work` `/slots`\n*(Gumagana rin as `!balance`, etc.)*\n\nMay 100+ jobs na pwedeng i-type as `!fish`, `!hunt`, `!mine`."
        elif v == "gam":
            e.title = "🎲 Gambling"
            e.description = "`/slots` `/coinflip` `/dice`\n*(Gumagana rin as `!slots`, etc.)*\n\nMay 30+ games na pwedeng i-type as `!crash`, `!mines`, `!baccarat`."
        elif v == "fun":
            e.title = "🎉 Fun & RP"
            e.description = "`!hug` `!slap` `!kiss` `!punch` `!bite` `!cuddle`\n`!cat` `!dog` `!fox`\n*May 100+ actions at animals!*"
        elif v == "util":
            e.title = "🔧 Utility"
            e.description = "`!ping` `!serverinfo` `!userinfo` `!avatar` `!calc`\n`!8ball` `!roll` `!choose`"
        await i.edit_original_response(embed=e, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpMenu())
        self.add_item(discord.ui.Button(label="Support", style=discord.ButtonStyle.link, url="https://discord.gg/6W4thfs7x"))

@bot.hybrid_command(name="help", aliases=["commands"], description="Show the interactive help menu")
async def help_cmd(ctx):
    e = discord.Embed(title="Doraemon Help", description=f"**{len(bot.commands)} Total Commands Loaded**\n\nChoose a category below:", color=discord.Color.from_rgb(43,45,49))
    if bot.user.avatar: e.set_thumbnail(url=bot.user.avatar.url)
    await ctx.send(embed=e, view=HelpView())

# ==========================================
# ERROR HANDLER (Silent on Missing Permissions)
# ==========================================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=discord.Embed(description=f"❌ **Missing arguments.** Example: `/ban user`", color=discord.Color.red()))
    elif isinstance(error, commands.MissingPermissions):
        pass # Tahimik lang kapag walang permission (para hindi malaman na may hidden command)
    elif isinstance(error, commands.CommandNotFound):
        pass

# ==========================================
# HIDDEN ADMIN COMMAND (Dito mo ilalagay ang pera)
# ==========================================
@bot.command(name="addcash", aliases=["ac"])
@commands.has_permissions(administrator=True)
async def addcash(ctx, target: str = None, amount: int = 0):
    if not target or amount <= 0: return await ctx.send("❌ **Usage:** `!addcash @user 1000`")
    member = await find_member(ctx, target)
    if not member: return await ctx.send(f"❌ **Not found:** `{target}`")
    
    u = get_eco(member.id)
    u["wallet"] += amount
    save_eco(member.id, u)
    
    await ctx.send(f"💰 Added **${amount:,}** to {member.mention}'s wallet.")
    try: await ctx.message.delete() # Binubura yung command para walang bakas
    except: pass

# ==========================================
# HYBRID MODERATION (Slash & Prefix)
# ==========================================
@bot.hybrid_command(name="ban", description="Ban a user")
@commands.has_permissions(ban_members=True)
async def ban(ctx, target: str, reason: str = "No reason"):
    member = await find_member(ctx, target)
    if not member: return await ctx.send(f"❌ **Not found:** `{target}`")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 **{member.name}** banned.")

@bot.hybrid_command(name="kick", description="Kick a user")
@commands.has_permissions(kick_members=True)
async def kick(ctx, target: str, reason: str = "No reason"):
    member = await find_member(ctx, target)
    if not member: return await ctx.send(f"❌ **Not found:** `{target}`")
    await member.kick(reason=reason)
    await ctx.send(f"👢 **{member.name}** kicked.")

@bot.hybrid_command(name="warn", description="Warn a user")
@commands.has_permissions(kick_members=True)
async def warn(ctx, target: str, reason: str = "No reason"):
    member = await find_member(ctx, target)
    if not member: return await ctx.send(f"❌ **Not found:** `{target}`")
    u = get_eco(member.id); u["warns"] += 1; save_eco(member.id, u)
    await ctx.send(f"⚠️ **{member.name}** warned ({u['warns']}/3).")

@bot.hybrid_command(name="purge", description="Delete messages")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"🧹 Deleted {amount}.", delete_after=3)

@bot.hybrid_command(name="lock", description="Lock channel")
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel locked.")

@bot.hybrid_command(name="unlock", description="Unlock channel")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 Channel unlocked.")

# ==========================================
# HYBRID ECONOMY & GAMBLING
# ==========================================
@bot.hybrid_command(name="daily", description="Claim your daily reward")
async def daily(ctx):
    u = get_eco(ctx.author.id)
    if time.time() - u["daily"] < 86400: return await ctx.send("⏳ Claimed na.")
    u["daily"] = time.time(); u["wallet"] += 500; save_eco(ctx.author.id, u)
    await ctx.send("💰 +$500!")

@bot.hybrid_command(name="balance", description="Check your wallet")
async def balance(ctx):
    u = get_eco(ctx.author.id); await ctx.send(f"💵 Wallet: ${u['wallet']:,}")

@bot.hybrid_command(name="slots", description="Play the slot machine")
async def slots(ctx, amount: int = 0):
    u = get_eco(ctx.author.id)
    if amount <= 0 or u["wallet"] < amount: return await ctx.send("❌ Invalid bet.")
    items = ["🍎","🍌","🍒","💎"]; s = [random.choice(items) for _ in range(3)]; line = " | ".join(s)
    if s[0]==s[1]==s[2]:
        w = amount*10 if s[0]=="💎" else amount*5; u["wallet"] += w; save_eco(ctx.author.id, u)
        await ctx.send(f"{line}\n🎉 JACKPOT **${w}**!")
    elif s[0]==s[1] or s[1]==s[2] or s[0]==s[2]:
        w = amount*2; u["wallet"] += w; save_eco(ctx.author.id, u)
        await ctx.send(f"{line}\n✨ Won **${w}**!")
    else:
        u["wallet"] -= amount; save_eco(ctx.author.id, u)
        await ctx.send(f"{line}\n💸 Lost **${amount}**.")

@bot.hybrid_command(name="coinflip", description="Flip a coin")
async def coinflip(ctx, choice: str, amount: int):
    u = get_eco(ctx.author.id)
    if amount <= 0 or u["wallet"] < amount: return await ctx.send("❌ Invalid bet.")
    res = random.choice(["H","T"])
    if choice.lower()[0].upper() == res:
        u["wallet"] += amount; save_eco(ctx.author.id, u)
        await ctx.send(f"🪙 It's **{res}**! Won **${amount}**.")
    else:
        u["wallet"] -= amount; save_eco(ctx.author.id, u)
        await ctx.send(f"🪙 It's **{res}**! Lost **${amount}**.")

# ==========================================
# MASSIVE GENERATOR (Prefix only for the remaining 200+)
# ==========================================
async def mass_exec(ctx, *args):
    cmd = ctx.command.name
    jobs = "beg work slut fish hunt mine plant chop dig explore search crime stream deliver clean code hack scam heist rob helpdad helpmom parttime toolkit bake cook drive guard fight nurse teach build paint sing dance act write read study garden sweep wash iron fix sell trade invest stock crypto tailor plumber electrician carpenter welder farmer fisherman miner lumberjack pilot sailor soldier police firefighter doctor teacher lawyer judge chef butcher artist writer actor director musician programmer engineer scientist astronaut janitor security".split()
    games = "blackjack roulette crash mines snake scratch keno lucky9 baccarat dice horserace chess blacktea batobatopick russianroulette war trapdoor hl duel ttt sabong colorgame bingo prophecy crosschicken dropball videopoker spinrthewheel basketball dragon".split()
    acts = "hug slap kiss punch bite cuddle dance cry laugh wave smile poke tickle highfive pat stare kill hold pout blush scream sigh smug smirk snuggle spank stomp trip wag wink yawn yeet lick nuzzle peck pinch shush toss tuck twerk whisper worship boop bonk feed glomp handhold hide nom kick_rp".split()
    animals = "cat dog fox panda koala bird raccoon kangaroo whale dolphin duck penguin lion tiger bear wolf eagle shark snake frog bunny hamster mouse monkey cow pig sheep goat horse chicken ant bee butterfly caterpillar centipede cockroach crab crocodile deer dodo elephant flamingo giraffe gorilla hedgehog hippo jellyfish leopard lizard lobster mammoth meerkat octopus ostrich otter parrot peacock pelican porcupine rabbit rat rhino seahorse seal sloth squirrel swan toad turkey turtle unicorn walrus wombat zebra".split()
    misc = "afk snipe xquote calc roll choose rate fact joke quote meme serverinfo userinfo avatar banner say embed announce roast compliment insult truth dare wyr neverhaveiever paranoia wouldyourather ship simp sus dadjoke pun showerthought progfact catfact dogfact numberfact spacefact historyfact sciencefact mathfact randomfact advice motivation horoscope fortune 8ball rps".split()
    
    if cmd in jobs:
        u = get_eco(ctx.author.id); amt = random.randint(50, 300)
        u["wallet"] += amt; save_eco(ctx.author.id, u); await ctx.send(f"✅ You {cmd} and earned **${amt:,}**.")
    elif cmd in games:
        if not args or not str(args[0]).isdigit(): return await ctx.send(f"❌ Usage: `!{cmd} <amount>`")
        amt = int(args[0]); u = get_eco(ctx.author.id)
        if amt <= 0 or u["wallet"] < amt: return await ctx.send("❌ Kulang funds.")
        if random.random() < 0.45:
            w = int(amt * 2); u["wallet"] += w; save_eco(ctx.author.id, u); await ctx.send(f"🎉 Played **{cmd}** and WON **${w:,}**!")
        else:
            u["wallet"] -= amt; save_eco(ctx.author.id, u); await ctx.send(f"💸 Played **{cmd}** and LOST **${amt:,}**.")
    elif cmd in acts:
        if not args: return await ctx.send(f"❌ Tag someone to {cmd}!")
        await ctx.send(f"✨ **{ctx.author.name}** {cmd}s {args[0]}!")
    elif cmd in animals:
        await ctx.send(f"Here is a random **{cmd}**! 🐾")
    else:
        await ctx.send(f"⚙️ Command `{cmd}` executed.")

all_cmds = "beg work slut fish hunt mine plant chop dig explore search crime stream deliver clean code hack scam heist rob helpdad helpmom parttime toolkit bake cook drive guard fight nurse teach build paint sing dance act write read study garden sweep wash iron fix sell trade invest stock crypto tailor plumber electrician carpenter welder farmer fisherman miner lumberjack pilot sailor soldier police firefighter doctor teacher lawyer judge chef butcher artist writer actor director musician programmer engineer scientist astronaut janitor security blackjack roulette crash mines snake scratch keno lucky9 baccarat dice horserace chess blacktea batobatopick russianroulette war trapdoor hl duel ttt sabong colorgame bingo prophecy crosschicken dropball videopoker spinrthewheel basketball dragon hug slap kiss punch bite cuddle dance cry laugh wave smile poke tickle highfive pat stare kill hold pout blush scream sigh smug smirk snuggle spank stomp trip wag wink yawn yeet lick nuzzle peck pinch shush toss tuck twerk whisper worship boop bonk feed glomp handhold hide nom kick_rp cat dog fox panda koala bird raccoon kangaroo whale dolphin duck penguin lion tiger bear wolf eagle shark snake frog bunny hamster mouse monkey cow pig sheep goat horse chicken ant bee butterfly caterpillar centipede cockroach crab crocodile deer dodo elephant flamingo giraffe gorilla hedgehog hippo jellyfish leopard lizard lobster mammoth meerkat octopus ostrich otter parrot peacock pelican porcupine rabbit rat rhino seahorse seal sloth squirrel swan toad turkey turtle unicorn walrus wombat zebra afk snipe xquote calc roll choose rate fact joke quote meme serverinfo userinfo avatar banner say embed announce roast compliment insult truth dare wyr neverhaveiever paranoia wouldyourather ship simp sus dadjoke pun showerthought progfact catfact dogfact numberfact spacefact historyfact sciencefact mathfact randomfact advice motivation horoscope fortune 8ball rps".split()

for name in all_cmds:
    if name not in bot.all_commands:
        bot.command(name=name)(mass_exec)

@bot.event
async def on_ready():
    print(f"[+] ONLINE: {bot.user} | {len(bot.commands)} Commands")
    await bot.change_presence(activity=discord.Streaming(name="Protecting Server", url="https://www.twitch.tv/discord"))
    try: await bot.tree.sync()
    except: pass

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
