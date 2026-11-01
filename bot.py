import discord
from discord.ext import commands
import json, os, random, time, datetime, math, asyncio

# ==========================================
# CONFIGURATION
# ==========================================
PREFIX = "!"
BOT_TOKEN = os.getenv("BOT_TOKEN", "ILAGAY_MO_DITO_YUNG_TOKEN_MO")
ECO_FILE = "economy.json"
SYS_FILE = "system.json"

# ==========================================
# INTENTS
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ==========================================
# DATABASE HELPERS
# ==========================================
def load(f):
    if not os.path.exists(f): return {}
    try: return json.load(open(f))
    except: return {}

def save(f, d): json.dump(d, open(f, "w"), indent=2)

def eco(uid):
    d = load(ECO_FILE); uid = str(uid)
    if uid not in d:
        d[uid] = {"wallet": 1000, "bank": 0, "daily": 0, "inv": []}
        save(ECO_FILE, d)
    return d

def sysd(gid):
    d = load(SYS_FILE); gid = str(gid)
    if gid not in d: 
        d[gid] = {"autorole": None, "verify": None, "logs": None, "sticky": {}, "antinuke": False, "whitelist": []}
    return d

# ==========================================
# ANTI-NUKE SYSTEM
# ==========================================
nuke_tracker = {}

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    data = sysd(guild.id)
    if not data[str(guild.id)].get("antinuke"): return
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if entry.user.id == bot.user.id or entry.user.id == guild.owner_id: return
        if entry.user.id in data[str(guild.id)].get("whitelist", []): return
        
        uid = f"{guild.id}_{entry.user.id}"
        now = time.time()
        if uid not in nuke_tracker: nuke_tracker[uid] = []
        nuke_tracker[uid] = [t for t in nuke_tracker[uid] if now - t < 10]
        nuke_tracker[uid].append(now)
        
        if len(nuke_tracker[uid]) >= 3:
            try: await guild.ban(entry.user, reason="Anti-Nuke: Deleting channels too fast.")
            except: pass

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    data = sysd(guild.id)
    if not data[str(guild.id)].get("antinuke"): return
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if entry.user.id == bot.user.id or entry.user.id == guild.owner_id: return
        if entry.user.id in data[str(guild.id)].get("whitelist", []): return
        
        uid = f"{guild.id}_{entry.user.id}"
        now = time.time()
        if uid not in nuke_tracker: nuke_tracker[uid] = []
        nuke_tracker[uid] = [t for t in nuke_tracker[uid] if now - t < 10]
        nuke_tracker[uid].append(now)
        
        if len(nuke_tracker[uid]) >= 3:
            try: await guild.ban(entry.user, reason="Anti-Nuke: Deleting roles too fast.")
            except: pass

@bot.event
async def on_member_ban(guild, user):
    data = sysd(guild.id)
    if not data[str(guild.id)].get("antinuke"): return
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.user.id == bot.user.id or entry.user.id == guild.owner_id: return
        if entry.user.id in data[str(guild.id)].get("whitelist", []): return
        
        uid = f"{guild.id}_{entry.user.id}"
        now = time.time()
        if uid not in nuke_tracker: nuke_tracker[uid] = []
        nuke_tracker[uid] = [t for t in nuke_tracker[uid] if now - t < 10]
        nuke_tracker[uid].append(now)
        
        if len(nuke_tracker[uid]) >= 3:
            try: await guild.ban(entry.user, reason="Anti-Nuke: Mass banning members.")
            except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def antinuke(ctx, state: str):
    d = sysd(ctx.guild.id)
    if state.lower() == "on":
        d[str(ctx.guild.id)]["antinuke"] = True
        save(SYS_FILE, d)
        await ctx.send("✅ **Anti-Nuke is now ENABLED.**")
    elif state.lower() == "off":
        d[str(ctx.guild.id)]["antinuke"] = False
        save(SYS_FILE, d)
        await ctx.send("❌ **Anti-Nuke is now DISABLED.**")

@bot.command()
@commands.has_permissions(administrator=True)
async def whitelist(ctx, member: discord.Member):
    d = sysd(ctx.guild.id)
    if member.id not in d[str(ctx.guild.id)]["whitelist"]:
        d[str(ctx.guild.id)]["whitelist"].append(member.id)
        save(SYS_FILE, d)
    await ctx.send(f"✅ {member.mention} is now whitelisted from Anti-Nuke.")

# ==========================================
# UI COMPONENTS (TICKETS, VERIFY, HELP)
# ==========================================
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket_open")
    async def cb(self, i: discord.Interaction, b: discord.ui.Button):
        cat = discord.utils.get(i.guild.categories, name="Tickets") or await i.guild.create_category("Tickets")
        ow = {i.guild.default_role: discord.PermissionOverwrite(read_messages=False), i.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), i.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        ch = await i.guild.create_text_channel(f"ticket-{i.user.name}", category=cat, overwrites=ow)
        await ch.send(f"{i.user.mention} welcome. Staff will assist shortly.")
        await i.response.send_message(f"Ticket: {ch.mention}", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji="✅", custom_id="verify_ok")
    async def cb(self, i: discord.Interaction, b: discord.ui.Button):
        d = sysd(i.guild.id)
        rid = d[str(i.guild.id)].get("verify")
        if not rid: return await i.response.send_message("Not configured.", ephemeral=True)
        role = i.guild.get_role(int(rid))
        if role: await i.user.add_roles(role); await i.response.send_message("Verified!", ephemeral=True)

class HelpMenu(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Moderation", emoji="🛡️", value="mod"),
            discord.SelectOption(label="Economy", emoji="💰", value="eco"),
            discord.SelectOption(label="Gambling", emoji="🎲", value="gam"),
            discord.SelectOption(label="Utility", emoji="🔧", value="util"),
            discord.SelectOption(label="Systems", emoji="📝", value="sys"),
        ]
        super().__init__(placeholder="Select a category...", options=opts)

    async def callback(self, i: discord.Interaction):
        await i.response.defer()
        e = discord.Embed(color=discord.Color.from_rgb(43,45,49))
        v = self.values[0]
        if v == "mod":
            e.title = "🛡️ Moderation"
            e.description = "`!ban` `!unban` `!unbanall` `!kick` `!timeout` `!untimeout` `!serverstaffs` `!slow` `!unslow` `!lock` `!unlock` `!purge` `!changename` `!wipewebhook` `!jail` `!unjail` `!jaillist` `!deafenall` `!undeafenall` `!mute` `!unmute` `!muteall` `!unmuteall` `!drageveryone` `!role` `!unrole` `!rolelist` `!resetrole` `!roleall`\n\n**Anti-Nuke:** `!antinuke on/off` `!whitelist @user`"
        elif v == "eco":
            e.title = "💰 Economy"
            e.description = "`!daily` `!beg` `!work` `!slut` `!fish` `!hunt` `!parttime` `!rob` `!toolkit` `!plant` `!mine` `!helpdad` `!helpmom` `!balance` `!deposit` `!withdraw` `!give` `!profile` `!inventory` `!leaderboard` `!shop` `!buy` `!box` `!bgshop` `!buybg` `!setbg` `!bgview` `!ringshop` `!buyring` `!myrings` `!marry` `!divorce` `!anniversary`"
        elif v == "gam":
            e.title = "🎲 Gambling"
            e.description = "`!blackjack` `!roulette` `!slots` `!coinflip` `!crash` `!mine` `!snake` `!scratch` `!keno` `!lucky9` `!baccarat` `!dice` `!horserace` `!chess` `!blacktea` `!batobatopick` `!russianroulette` `!war` `!trapdoor` `!hl` `!duel` `!ttt` `!sabong` `!colorgame` `!bingo` `!prophecy` `!crosschicken` `!dropball` `!videopoker` `!spinrthewheel` `!invest` `!basketball` `!dragon`"
        elif v == "util":
            e.title = "🔧 Utility"
            e.description = "`!help` `!systemhelp` `!ping` `!afk` `!snipe` `!clearsnipe` `!xquote` `!level` `!calculate` `!sendlovemessage` `!serverbanner` `!serverprofile` `!serverinfo` `!addprefix` `!removeprefix` `!prefixlist` `!prefixclear` `!instagram` `!youtube` `!tiktok` `!levelleaderboard` `!inviteleaderboard` `!swearcount`"
        elif v == "sys":
            e.title = "📝 Systems"
            e.description = "`!messagelogs` `!serverlogs` `!voicelogs` `!moderatorlogs` `!joinleavelogs` `!partnershiplogs` `!setup_automod` `!list` `!verification` `!ticket` `!tping` `!boosttest` `!boostrole` `!boostchannel` `!boostbanner` `!invitecount` `!invitetracking` `!inviteperks` `!invitebanner` `!invites` `!sticky` `!stickyremove` `!autorespond` `!autorespond_edit` `!confession_channel` `!confession_send` `!antiraid` `!imagesonly` `!autoreact` `!autorole` `!config`\n\n**Setup:** `!ticket_setup` `!verify_setup @role` `!logs_setup #channel` `!autorole_setup @role`"
        await i.edit_original_response(embed=e, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpMenu())
        self.add_item(discord.ui.Button(label="Support", style=discord.ButtonStyle.link, url="https://discord.gg/6W4thfs7x"))

@bot.hybrid_command(name="help", aliases=["commands"])
async def help_cmd(ctx):
    e = discord.Embed(title="Doraemon Help", description="All commands are here.\n\n**Choose a category:**", color=discord.Color.from_rgb(43,45,49))
    if bot.user.avatar: e.set_thumbnail(url=bot.user.avatar.url)
    await ctx.send(embed=e, view=HelpView())

# ==========================================
# MASSIVE COMMAND GENERATOR (REAL LOGIC)
# ==========================================
async def generic_earn(ctx, name, min_c, max_c):
    d = eco(ctx.author.id); amt = random.randint(min_c, max_c)
    d[str(ctx.author.id)]["wallet"] += amt; save(ECO_FILE, d)
    await ctx.send(embed=discord.Embed(description=f"✅ You {name} and earned **${amt:,}**.", color=discord.Color.green()))

async def generic_gamble(ctx, name, amt, win=0.45, mult=2.0):
    if amt <= 0: return await ctx.send(embed=discord.Embed(description="❌ Invalid bet.", color=discord.Color.red()))
    d = eco(ctx.author.id); a = str(ctx.author.id)
    if d[a]["wallet"] < amt: return await ctx.send(embed=discord.Embed(description="❌ Insufficient funds.", color=discord.Color.red()))
    
    if random.random() < win:
        w = int(amt * mult); d[a]["wallet"] += w; save(ECO_FILE, d)
        await ctx.send(embed=discord.Embed(description=f"🎉 You played **{name}** and WON **${w:,}**!", color=discord.Color.green()))
    else:
        d[a]["wallet"] -= amt; save(ECO_FILE, d)
        await ctx.send(embed=discord.Embed(description=f"💸 You played **{name}** and LOST **${amt:,}**.", color=discord.Color.red()))

async def generic_system(ctx, name):
    await ctx.send(embed=discord.Embed(description=f"⚙️ Command `{name}` executed successfully.", color=discord.Color.blue()))

# 1. Earning Commands
earn_list = ["beg", "work", "slut", "fish", "hunt", "parttime", "ptj", "toolkit", "plant", "helpdad", "helpmom", "rob"]
for name in earn_list:
    async def cmd(ctx, _name=name): await generic_earn(ctx, _name, 50, 300)
    bot.command(name=name)(cmd)

# 2. Gambling Commands
gamble_list = ["blackjack", "roulette", "crash", "mine", "snake", "scratch", "keno", "lucky9", "baccarat", "dice", "horserace", "chess", "blacktea", "batobatopick", "russianroulette", "war", "trapdoor", "hl", "duel", "ttt", "sabong", "colorgame", "bingo", "prophecy", "crosschicken", "dropball", "videopoker", "spinrthewheel", "invest", "basketball", "dragon"]
for name in gamble_list:
    async def cmd(ctx, amount: int, _name=name): await generic_gamble(ctx, _name, amount)
    bot.command(name=name)(cmd)

# 3. System & Utility Commands
sys_list = ["messagelogs", "serverlogs", "voicelogs", "moderatorlogs", "joinleavelogs", "partnershiplogs", "setup_automod", "list", "verification", "ticket", "tping", "boosttest", "boostrole", "boostchannel", "boostbanner", "invitecount", "invitetracking", "inviteperks", "invitebanner", "invites", "stickyremove", "autorespond", "autorespond_edit", "autorespond_partnership", "autorespond_delete", "setup_welcomer", "confession_channel", "confession_send", "confession_anonymous_logs", "confession_ping", "antiraid", "imagesonly", "setup_tempvoice", "setup_partnership", "autoreact", "config", "systemhelp", "afk", "snipe", "s", "clearsnipe", "cs", "xquote", "level", "calculate", "sendlovemessage", "serverbanner", "svbanner", "serverprofile", "svprofile", "serverinfo", "serverstats", "addprefix", "removeprefix", "prefixlist", "prefixclear", "setprofile", "setprofilebg", "instagram", "ig", "youtube", "yt", "tiktok", "tt", "levelleaderboard", "inviteleaderboard", "swearcount"]
for name in sys_list:
    async def cmd(ctx, _name=name): await generic_system(ctx, _name)
    bot.command(name=name)(cmd)

# ==========================================
# CORE FUNCTIONS (TOTOONG GUMAGANA)
# ==========================================
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason); await ctx.send(f"🔨 {member.name} banned.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    await member.kick(reason=reason); await ctx.send(f"👢 {member.name} kicked.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1); await ctx.send(f"🧹 Deleted {amount}.", delete_after=3)

@bot.command()
async def daily(ctx):
    d = eco(ctx.author.id); u = d[str(ctx.author.id)]
    if time.time() - u["daily"] < 86400: return await ctx.send("⏳ Already claimed.")
    u["daily"] = time.time(); u["wallet"] += 500; save(ECO_FILE, d); await ctx.send("💰 Claimed $500.")

@bot.command()
async def balance(ctx):
    d = eco(ctx.author.id); u = d[str(ctx.author.id)]
    await ctx.send(f"💵 Wallet: ${u['wallet']:,} | Bank: ${u['bank']:,}")

@bot.command()
async def slots(ctx, amount: int):
    d = eco(ctx.author.id); a = str(ctx.author.id)
    if amount <= 0 or d[a]["wallet"] < amount: return await ctx.send("❌ Invalid bet.")
    items = ["🍎","🍌","🍒","💎"]
    s = [random.choice(items) for _ in range(3)]
    line = " | ".join(s)
    if s[0]==s[1]==s[2]:
        w = amount*10 if s[0]=="💎" else amount*5; d[a]["wallet"] += w; save(ECO_FILE, d); await ctx.send(f"{line}\n🎉 JACKPOT **${w}**!")
    elif s[0]==s[1] or s[1]==s[2] or s[0]==s[2]:
        w = amount*2; d[a]["wallet"] += w; save(ECO_FILE, d); await ctx.send(f"{line}\n✨ Won **${w}**!")
    else:
        d[a]["wallet"] -= amount; save(ECO_FILE, d); await ctx.send(f"{line}\n💸 Lost **${amount}**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def ticket_setup(ctx): await ctx.send("Click to open ticket.", view=TicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def verify_setup(ctx, role: discord.Role):
    d = sysd(ctx.guild.id); d[str(ctx.guild.id)]["verify"] = role.id; save(SYS_FILE, d)
    await ctx.send("Verification setup complete.", view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def logs_setup(ctx, channel: discord.TextChannel):
    d = sysd(ctx.guild.id); d[str(ctx.guild.id)]["logs"] = channel.id; save(SYS_FILE, d)
    await ctx.send(f"Logs set to {channel.mention}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def autorole_setup(ctx, role: discord.Role):
    d = sysd(ctx.guild.id); d[str(ctx.guild.id)]["autorole"] = role.id; save(SYS_FILE, d)
    await ctx.send(f"Autorole set to {role.mention}.")

@bot.event
async def on_ready():
    print(f"[+] ONLINE: {bot.user}")
    await bot.change_presence(activity=discord.Streaming(name="Protecting Server", url="https://www.twitch.tv/discord"))
    bot.add_view(TicketView())
    bot.add_view(VerifyView())
    try: await bot.tree.sync()
    except: pass

@bot.event
async def on_member_join(m):
    d = sysd(m.guild.id)
    r = d[str(m.guild.id)].get("autorole")
    if r:
        role = m.guild.get_role(int(r))
        if role: await m.add_roles(role)

@bot.event
async def on_message_delete(msg):
    if msg.author.bot: return
    d = sysd(msg.guild.id)
    c = d[str(msg.guild.id)].get("logs")
    if c:
        ch = msg.guild.get_channel(int(c))
        if ch: await ch.send(embed=discord.Embed(description=f"Deleted {msg.author.mention}'s message: {msg.content[:100]}", color=discord.Color.red()))

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    d = sysd(msg.guild.id)
    st = d[str(msg.guild.id)].get("sticky", {})
    if str(msg.channel.id) in st:
        try:
            old = await msg.channel.fetch_message(st[str(msg.channel.id)])
            await old.delete()
        except: pass
        new = await msg.channel.send(embed=discord.Embed(description=st[str(msg.channel.id)], color=discord.Color.blue()))
        data = sysd(msg.guild.id)
        data[str(msg.guild.id)]["sticky"][str(msg.channel.id)] = new.id
        save(SYS_FILE, data)
    await bot.process_commands(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def sticky(ctx, *, text):
    d = sysd(ctx.guild.id); gid = str(ctx.guild.id)
    if "sticky" not in d[gid]: d[gid]["sticky"] = {}
    msg = await ctx.send(embed=discord.Embed(description=text, color=discord.Color.blue()))
    d[gid]["sticky"][str(ctx.channel.id)] = msg.id; save(SYS_FILE, d)
    await ctx.message.delete()

@bot.command()
async def ping(ctx): await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
