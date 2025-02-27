import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
from discord.ui import View, Select  
import re 
import requests
import aiohttp
import websockets
import json
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(discord.Client):
    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user}")

intents = discord.Intents.default()
bot = MyBot(intents=intents)

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token Discord introuvable !")

if not TOKEN:
    print("❌ ERREUR: Le token Discord est manquant ou vide !")
    print("💡 Vérifie que DISCORD_TOKEN est bien défini dans Railway.")
else:
    print("✅ Token récupéré avec succès !")

# ✅ Configuration des intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True
intents.reactions = True

# ✅ Création du bot
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ✅ IDs du serveur et des salons (à remplacer avec les vrais)
GUILD_ID = 1339249351779684422
CHANNEL_RULES_ID = 1339249352031469605
CHANNEL_ROLES_ID = 1339249352031469607 # ✅ AJOUTE UN ID VALIDE
ROLE_ID = 1339249351779684425
WELCOME_CHANNEL_ID = 1339249352031469606  # ID du salon de bienvenue

# ✅ IDs des rôles
roles_info = {
    "👦🏽- Mineur Garçon": 1339281414968840246,
    "👧🏽 -Mineur Fille": 1339281631491522580,
    "👩- Majeur Fille": 1339281759941955727,
    "🧔-Majeur Homme": 1339282075311935499,
    "Twitch 🎥": 1339282319634337822,
    "YouTube 📺": 1339282410675638392,
    "TikTok 🎶": 1339282470264115344,
    "Giveaways 🎁": 1339282525281058876
}

# Fonction pour extraire proprement l'émoji et le texte du rôle
def extract_emoji_and_label(role_name):
    match = re.match(r"([\U0001F300-\U0001FAD6\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF]+)?\s?(.+)", role_name)
    if match:
        emoji, label = match.groups()
        return emoji, label
    return None, role_name

class RoleSelect(Select):
    def __init__(self):
        options = []
        for role_name, role_id in roles_info.items():
            emoji, label = extract_emoji_and_label(role_name)

            # Vérification si l'émoji est valide pour Discord
            try:
                option = discord.SelectOption(
                    label=label,
                    description=f"Obtenez ou retirez le rôle {label}",
                    emoji=emoji if emoji else None,
                    value=str(role_id)
                )
                options.append(option)
            except discord.errors.HTTPException:
                print(f"⚠️ Erreur avec l'émoji : {emoji} pour le rôle {label}")

        super().__init__(
            placeholder="🎭 Choisissez un rôle...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="role_select"
        )

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)

        if not role:
            await interaction.response.send_message("❌ Rôle introuvable.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                f"❌ {interaction.user.mention}, vous avez retiré le rôle **{role.name}**.",
                ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"✅ {interaction.user.mention}, vous avez reçu le rôle **{role.name}** !",
                ephemeral=True
            )

class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())

@bot.command()
async def roles(ctx):
    """Envoie le menu des rôles dans le salon défini."""
    await ctx.send("🛠️ La commande `roles` a bien été exécutée ! Vérification en cours...")

    channel = bot.get_channel(CHANNEL_ROLES_ID)

    if not channel:
        await ctx.send("❌ Salon de rôles introuvable. Vérifiez `CHANNEL_ROLES_ID` et les permissions.")
        return

    # Suppression des anciens messages
    async for message in channel.history(limit=10):
        if message.author == bot.user:
            await message.delete()

    embed = discord.Embed(
        title="🎭 **Choisissez vos rôles !**",
        description="🔹 Sélectionnez un rôle dans le menu déroulant ci-dessous pour l'obtenir ou le retirer.\n"
                    "🔹 Vous pouvez changer de rôle à tout moment !",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Système de rôles interactif 🎭")

    view = RoleView()
    await channel.send(embed=embed, view=view)
    await ctx.send("✅ Message de sélection des rôles envoyé avec succès !")

# ------------------------- ÉVÉNEMENT : BOT PRÊT -------------------------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} est connecté !")

    # ✅ Enregistrer la vue après que le bot soit prêt
    asyncio.create_task(register_views())

    # ✅ Envoie automatique du règlement
    guild = bot.get_guild(GUILD_ID)
    if guild:
        await send_rules_channel(guild)

async def register_views():
    await bot.wait_until_ready()  # ✅ Attend que le bot soit totalement prêt
    bot.add_view(RoleView())  # ✅ Ajoute la vue proprement

# ------------------------- MESSAGE DE RÈGLEMENT -------------------------
async def send_rules_channel(guild):
    channel = guild.get_channel(CHANNEL_RULES_ID)
    if channel:
        embed = discord.Embed(title="📜 Règlement du Serveur", color=discord.Color.red())
        embed.add_field(name="1️⃣ Respect", value="Respectez tous les membres.", inline=False)
        embed.add_field(name="2️⃣ Pas de spam", value="Évitez le spam et la pub.", inline=False)
        embed.add_field(name="3️⃣ Contenu approprié", value="Pas de contenu inapproprié.", inline=False)
        embed.set_footer(text="Réagissez ✅ pour accepter le règlement et obtenir le rôle 👥 - Membres")

        message = await channel.send(embed=embed)
        await message.add_reaction("✅")
        print("📜 Message de règlement envoyé.")
    else:
        print("❌ Le salon de règlement n'a pas été trouvé.")

# ------------------------- AJOUT DE RÔLE VIA RÉACTION -------------------------
# ✅ ID du salon des logs
LOGS_CHANNEL_ID = 1339249352824328286

async def log_reaction_action(action, member):
    """Envoie un message dans le salon de logs quand quelqu'un ajoute ou retire la réaction."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if logs_channel:
        embed = discord.Embed(
            title="📜 Log de Réaction",
            description=f"{member.mention} {action} la réaction ✅ au règlement.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"ID: {member.id}")
        await logs_channel.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:
        return  # Ignore les réactions en MP

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    if payload.channel_id == CHANNEL_RULES_ID and str(payload.emoji) == "✅":
        member = guild.get_member(payload.user_id)
        role = guild.get_role(ROLE_ID)

        if member and role and not member.bot:
            try:
                await member.add_roles(role)
                print(f"✅ {member} a accepté le règlement et reçu le rôle {role.name}.")
                await log_reaction_action("a ajouté", member)
            except discord.Forbidden:
                print("❌ Permission refusée pour ajouter le rôle.")
            except discord.HTTPException as e:
                print(f"❌ Erreur HTTP : {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id is None:
        return  # Ignore les réactions en MP

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    if payload.channel_id == CHANNEL_RULES_ID and str(payload.emoji) == "✅":
        member = guild.get_member(payload.user_id)
        role = guild.get_role(ROLE_ID)

        if member and role and not member.bot:
            try:
                await member.remove_roles(role)
                print(f"❌ {member} a retiré la réaction et perdu le rôle {role.name}.")
                await log_reaction_action("a retiré", member)
            except discord.Forbidden:
                print("❌ Permission refusée pour retirer le rôle.")
            except discord.HTTPException as e:
                print(f"❌ Erreur HTTP : {e}")


# ------------------------- COMMANDES -------------------------
@bot.command()
async def ping(ctx):
    """Répond avec 'Pong !'."""
    await ctx.send("🏓 Pong !")

@bot.command()
async def test_role(ctx, member: discord.Member):
    """Ajoute un rôle manuellement à un membre."""
    role = ctx.guild.get_role(ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ {member.mention} a reçu le rôle {role.name}.")
        except discord.Forbidden:
            await ctx.send("❌ Le bot n'a pas la permission d'ajouter ce rôle.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Erreur HTTP : {e}")
    else:
        await ctx.send("❌ Le rôle n'existe pas.")

@bot.command()
async def exclure(ctx, user: discord.Member, *, reason="Aucune raison spécifiée"):
    """Exclut un utilisateur du serveur avec notification et log."""
    allowed_roles = {
        1339249351788335279,  # Admins
        1339249351788335277,  # Modérateurs
        1339249351788335276,  # Modérateurs Test
    }

    if not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return

    # 📩 Envoi du MP avant l'exclusion
    try:
        embed_mp = discord.Embed(
            title="📜 Vous avez été exclu",
            description=f"Vous avez été **exclu** du serveur **{ctx.guild.name}** par {ctx.author.mention}.",
            color=discord.Color.red()
        )
        embed_mp.add_field(name="📌 Raison :", value=reason, inline=False)
        embed_mp.set_footer(text="Si vous pensez que c'est une erreur, vous pouvez contacter : jielzer1xe_.\n"
                                 "Vous pouvez rejoindre le serveur à nouveau ici : https://discord.gg/mbPRghyN")

        await user.send(embed=embed_mp)
    except discord.Forbidden:
        await ctx.send("⚠️ Impossible d'envoyer un message privé à cet utilisateur.")

    # 🚪 Exclusion de l'utilisateur
        await user.kick(reason=reason)



    # 📝 Logs dans le salon 💾・logs-discord
    log_channel = bot.get_channel(1339249352824328286)
    if log_channel:
        embed_logs = discord.Embed(
            title="🚨 Exclusion d'un membre",
            description=f"**{user.mention}** a été exclu du serveur.",
            color=discord.Color.orange()
        )
        embed_logs.add_field(name="👤 Utilisateur :", value=f"{user} ({user.id})", inline=False)
        embed_logs.add_field(name="👮‍♂️ Exclu par :", value=f"{ctx.author.mention}", inline=False)
        embed_logs.add_field(name="📌 Raison :", value=reason, inline=False)
        embed_logs.set_footer(text=f"Date : {ctx.message.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
        
        await log_channel.send(embed=embed_logs)

@bot.command()
async def bannir(ctx, user: discord.Member, *, reason="Aucune raison spécifiée"):
    """Bannit un utilisateur du serveur avec logs et message privé."""
    
    # Rôles autorisés à utiliser la commande
    allowed_roles = [1339249351788335279, 1339249351788335277, 1339249351788335276]  # IDs des rôles

    if not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return
    
    try:
        # 📩 Message privé à l'utilisateur avant le bannissement
        embed_mp = discord.Embed(title="📜 Vous avez été banni", color=discord.Color.red())
        embed_mp.add_field(name="🚪 Serveur", value="**Serveur de jielzer1xe_**", inline=False)
        embed_mp.add_field(name="📌 Raison", value=f"```{reason}```", inline=False)
        embed_mp.add_field(
            name="⚠️ Si vous pensez que c'est une erreur",
            value="Vous pouvez contacter : **jielzer1xe_**",
            inline=False
        )
        
        try:
            await user.send(embed=embed_mp)  # Envoie du MP avant le ban
        except discord.HTTPException:
            pass  # Ignore si le MP ne peut pas être envoyé
        
        # 🚪 Bannissement de l'utilisateur
        await user.ban(reason=reason)

        # 📝 Logs dans le salon "💾・logs-discord"
        logs_channel = bot.get_channel(1339249352824328286)  # ID du salon logs
        if logs_channel:
            embed_logs = discord.Embed(title="🔨 Bannissement", color=discord.Color.red())
            embed_logs.add_field(name="👤 Utilisateur", value=user.mention, inline=False)
            embed_logs.add_field(name="👮‍♂️ Modérateur", value=ctx.author.mention, inline=False)
            embed_logs.add_field(name="📌 Raison", value=f"```{reason}```", inline=False)
            embed_logs.set_footer(text=f"ID utilisateur : {user.id}")
            await logs_channel.send(embed=embed_logs)

    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de bannir cet utilisateur.")
    except Exception as e:
        await ctx.send(f"❌ Erreur inattendue : {e}")

@bot.command()
async def debannir(ctx, user_id: int):
    """Débannit un utilisateur à partir de son ID avec logs et MP."""
    allowed_roles = ["🛡️ - Admins", "🛠️ - Modérateurs", "🔎 - Modérateurs Test"]
    if not any(role.name in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return

    try:
        # Récupérer la liste des bannis
        banned_users = [entry async for entry in ctx.guild.bans()]
        user = discord.utils.find(lambda u: u.user.id == user_id, banned_users)

        if user:
            await ctx.guild.unban(user.user)

            # Message privé à l'utilisateur
            try:
                embed = discord.Embed(title="🔓 Vous avez été débanni", color=discord.Color.green())
                embed.add_field(name="📌 Serveur :", value=f"**{ctx.guild.name}**", inline=False)
                embed.add_field(name="👤 Débanni par :", value=ctx.author.mention, inline=False)
                await user.user.send(embed=embed)
            except:
                pass  # Si l'utilisateur ne peut pas recevoir de MP

            # Logs dans le salon
            log_channel = bot.get_channel(1339249352824328286)  # ID du salon logs
            if log_channel:
                embed_log = discord.Embed(title="📜 Un utilisateur a été débanni", color=discord.Color.green())
                embed_log.add_field(name="👤 Utilisateur :", value=f"{user.user.mention} ({user.user.id})", inline=False)
                embed_log.add_field(name="🔧 Staff :", value=ctx.author.mention, inline=False)
                await log_channel.send(embed=embed_log)

        else:
            await ctx.send("❌ Utilisateur non trouvé dans la liste des bannis.")

    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de débannir des utilisateurs.")
    except Exception as e:
        await ctx.send(f"❌ Erreur inattendue : {e}")

@bot.command()
async def bannis(ctx):
    """Affiche la liste des utilisateurs bannis avec leur ID et raison de ban."""
    allowed_roles = [1339249351788335279, 1339249351788335277, 1339249351788335276]
    
    # Vérification des rôles
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return

    try:
        banned_users = [entry async for entry in ctx.guild.bans()]
        
        if not banned_users:
            await ctx.send("✅ Aucun utilisateur n'est actuellement banni.")
            return

        # Création d'un embed propre
        embed = discord.Embed(title="📜 Liste des utilisateurs bannis", color=discord.Color.red())

        for entry in banned_users:
            user = entry.user
            reason = entry.reason if entry.reason else "Aucune raison spécifiée"
            embed.add_field(
                name=f"👤 {user.name}#{user.discriminator} ({user.id})",
                value=f"📌 **Raison** : {reason}",
                inline=False
            )

        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de voir la liste des bannis.")
    except Exception as e:
        await ctx.send(f"❌ Erreur inattendue : {e}")
@bot.event
async def on_member_join(member):
    guild = member.guild
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    # Récupération des invitations pour voir celle utilisée
    invites = await guild.invites()
    invite_used = None
    for invite in invites:
        if invite.uses > 0:  # Vérifie si l'invitation a été utilisée
            invite_used = invite
            break

    # Date de création du compte
    account_creation_date = member.created_at.strftime("%d/%m/%Y")

    # Nombre total de membres
    total_members = guild.member_count

    # Création de l'embed de bienvenue
    embed = discord.Embed(title="Bienvenue sur JL Community", color=discord.Color.blue())
    embed.description = (
        f"{member.mention} vient de nous rejoindre grâce à "
        f"{f'lien d’invitation **{invite_used.code}**' if invite_used else 'un lien inconnu'}.\n"
        f"📅 **Son compte a été créé le** : {account_creation_date}.\n"
        f"👤 **C'est la première fois qu'il nous rejoint.**\n"
        f"📌 **Nous sommes maintenant {total_members} membres !**"
     )

    # Ajout de la photo de profil du membre
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    await channel.send(embed=embed)              

@bot.command()
async def clear(ctx, limit: int = 100):
    """Supprime un nombre de messages spécifié."""
    
    allowed_roles = [
        1339249351788335279,  # ID du rôle "🛡️ - Admins"
        1339249351788335277,  # ID du rôle "🛠️ - Modérateurs"
        1339249351788335276   # ID du rôle "🔎 - Modérateurs Test"
    ]
    
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=limit)
        log_channel = bot.get_channel(1339249352824328286)  # ID du salon 💾・logs-discord
        
        # Message de confirmation dans le salon
        await ctx.send(f"✅ {len(deleted)} messages supprimés.", delete_after=5)
        
        # Envoi du log
        if log_channel:
            embed = discord.Embed(
                title="🗑️ Suppression de messages",
                description=f"{ctx.author.mention} a supprimé `{len(deleted)}` messages dans {ctx.channel.mention}.",
                color=discord.Color.orange(),
                timestamp=ctx.message.created_at
            )
            embed.set_footer(text=f"ID de {ctx.author}", icon_url=ctx.author.avatar.url)
            await log_channel.send(embed=embed)
    
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de supprimer des messages.")
    except Exception as e:
        await ctx.send(f"❌ Erreur inattendue : {e}")

ticket_categories = {
    "🔧 Support": "Besoin d'aide avec un problème ?",
    "💡 Suggestions": "Proposez une idée pour améliorer le serveur !",
    "⚠️ Signalement": "Signalez un comportement inapproprié."
}

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=key, description=value)
            for key, value in ticket_categories.items()
        ]
        super().__init__(placeholder="Fais un choix", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        category = discord.utils.get(guild.categories, id=1339249352681459811)  # ID de la catégorie "🎫・tickets"
        if not category:
            await interaction.response.send_message("Catégorie des tickets non trouvée.", ephemeral=True)
            return

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                discord.utils.get(guild.roles, name="🛡️ - Admins"): discord.PermissionOverwrite(view_channel=True, send_messages=True),
                discord.utils.get(guild.roles, name="🛠️ - Modérateurs"): discord.PermissionOverwrite(view_channel=True, send_messages=True),
                discord.utils.get(guild.roles, name="🔎 - Modérateurs Test"): discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
        )

        staff_role = discord.utils.get(guild.roles, id=1343603906768408597)  # ID du rôle "🛠️ Équipe Staff"
        embed = discord.Embed(
            title="Ticket Ouvert",
            description=f"{member.mention} a ouvert un ticket pour {self.values[0]}.",
            color=discord.Color.green()
        )
        embed.add_field(name="Support", value=f"{staff_role.mention}, un membre a besoin d'aide !", inline=False)
        await ticket_channel.send(embed=embed)
        await interaction.response.send_message(f"Votre ticket a été créé : {ticket_channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketSelect())

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    await bot.wait_until_ready()

@bot.command()
async def setup_ticket(ctx):
    channel = ctx.channel
    embed = discord.Embed(title="Tickets", description="Utilisez ce menu pour créer un ticket et contacter le staff.", color=discord.Color.green())
    await channel.purge()
    await channel.send(embed=embed, view=TicketView())
    await ctx.send("Message de ticket envoyé.", delete_after=5)

@bot.command()
async def close(ctx):
    if ctx.channel.category and ctx.channel.category.id == 1339249352681459811:
        await ctx.send("Fermeture du ticket dans 5 secondes...")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("Cette commande ne peut être utilisée que dans un salon de ticket.")

@bot.command()
async def lien(ctx):
    embed = discord.Embed(title="📌 Mes Réseaux Sociaux", color=discord.Color.blue())
    embed.add_field(name="📺 Twitch", value="[jlzer1xe](https://www.twitch.tv/jlzer1xe)", inline=False)
    embed.add_field(name="🎵 TikTok", value="[jl_zer1xe](https://www.tiktok.com/@jl_zer1xe)", inline=False)
    embed.add_field(name="▶️ YouTube", value="[jlzer1xe](https://www.youtube.com/@jlzer1xe)", inline=False)
    embed.set_footer(text="N'hésite pas à me suivre pour ne rien rater !")

    await ctx.send(embed=embed)
    # Liste de blagues
blagues = [
    "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon ils tombent dans le bateau.",
    "Quel est le comble pour un électricien ? Ne pas être au courant.",
    "Pourquoi est-ce que les poissons n'aiment pas l'ordinateur ? Parce qu'ils ont peur des hameçons.",
    "Quelle est la meilleure punition pour un électricien ? Le mettre au courant.",
    "Pourquoi Napoléon n'a jamais déménagé ? Parce qu'il avait un Bonaparte."
]

@bot.command()
async def blague(ctx):
    """Envoie une blague aléatoire sous forme d'embed."""
    blague = random.choice(blagues)
    print(f"Blague sélectionnée : {blague}")  # Vérifie dans la console

    embed = discord.Embed(title="😂 Blague du jour", description=blague, color=discord.Color.blue())
    embed.set_footer(text=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, membre: discord.Member = None):
    """Affiche l'avatar du membre mentionné ou du demandeur."""
    membre = membre or ctx.author  # Si aucun membre n'est mentionné, prendre l'auteur
    embed = discord.Embed(title=f"Avatar de {membre.name}", color=discord.Color.blue())
    embed.set_image(url=membre.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    """Le bot rejoint le salon vocal de l'utilisateur."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"✅ Je viens de rejoindre {channel.mention} !")
    else:
        await ctx.send("❌ Tu dois être dans un salon vocal pour utiliser cette commande.")

@bot.command()
async def leave(ctx):
    """Commande pour que le bot quitte le salon vocal s'il est seul."""
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("👋 Déconnecté du salon vocal.")
    else:
        await ctx.send("❌ Le bot n'est pas dans un salon vocal.")

async def check_voice_channel():
    """Vérifie si le bot est seul dans un salon vocal et le fait quitter après 60 secondes."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            voice_client = guild.voice_client
            if voice_client and voice_client.is_connected():
                channel = voice_client.channel
                members = [m for m in channel.members if not m.bot]

                if len(members) == 0:
                    await asyncio.sleep(60)
                    if len([m for m in channel.members if not m.bot]) == 0:
                        await voice_client.disconnect()
                        print(f"Déconnecté du salon vocal {channel.name} car il était vide.")
        await asyncio.sleep(30)

async def setup_hook():
    bot.loop.create_task(check_voice_channel())

bot.setup_hook = setup_hook

@bot.command()
async def play(ctx, url: str):
    """Lit une musique depuis un lien YouTube."""
    if not ctx.author.voice:
        await ctx.send("❌ Tu dois être dans un salon vocal pour utiliser cette commande !")
        return
    
    voice_client = ctx.voice_client
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()
    elif voice_client.is_playing():
        await ctx.send("🎵 Une musique est déjà en cours ! Utilise `!stop` pour l'arrêter.")
        return
    
    await ctx.send("🔍 Recherche de la musique...")

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
            title = info.get("title", "Musique inconnue")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération de la musique : {e}")
        return
    
    embed = discord.Embed(title="🎶 Lecture en cours", description=f"**{title}**", color=discord.Color.blue())
    embed.set_footer(text=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    def after_play(error):
        if error:
            print(f"Erreur lors de la lecture : {error}")
    
    voice_client.play(discord.FFmpegPCMAudio(audio_url), after=after_play)

@bot.command()
async def stop(ctx):
    """Arrête la musique et fait quitter le bot du salon vocal."""
    voice_client = ctx.voice_client
    if voice_client:
        voice_client.stop()
        await voice_client.disconnect()
        await ctx.send("🛑 Musique arrêtée, bot déconnecté.")
    else:
        await ctx.send("❌ Le bot n'est pas dans un salon vocal.")

@bot.command()
async def cmds(ctx):
    """Affiche la liste des commandes disponibles sous forme d'embed."""
    embed = discord.Embed(title="📜 Liste des Commandes", description="Voici toutes les commandes disponibles :", color=discord.Color.blue())

    embed.add_field(name="🛠️ Modération", value=(
        "`!roles` → Gérer les rôles\n"
        "`!ping` → Répond avec 🏓 Pong !\n"
        "`!test_role @membre` → Ajoute un rôle manuellement\n"
        "`!exclure @membre [raison]` → Exclut un membre\n"
        "`!bannir @membre [raison]` → Bannit un membre\n"
        "`!debannir ID_membre` → Débannit un membre\n"
        "`!bannis` → Liste des utilisateurs bannis\n"
        "`!clear` → Supprime des messages\n"
    ), inline=False)

    embed.add_field(name="🎫 Tickets", value=(
        "`!setup_ticket` → Crée un message interactif pour ouvrir des tickets\n"
        "`!close` → Ferme un ticket après 5 secondes\n"
    ), inline=False)

    embed.add_field(name="📌 Réseaux Sociaux", value="`!lien` → Affiche les liens vers mes réseaux sociaux", inline=False)

    embed.add_field(name="🎭 Fun", value=(
        "`!blague` → Envoie une blague aléatoire\n"
        "`!avatar [@membre]` → Affiche un avatar\n"
    ), inline=False)

    embed.add_field(name="🎵 Musique", value=(
        "`!join` → Le bot rejoint le salon vocal\n"
        "`!leave` → Le bot quitte le salon vocal\n"
        "`!play <URL YouTube>` → Joue une musique\n"
        "`!stop` → Arrête la musique\n"
    ), inline=False)

    embed.set_footer(text=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

# ------------------------- ÉVÉNEMENT : BOT PRÊT -------------------------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} est connecté !")
    
    # ✅ Ajoute la vue avec un event loop sécurisé
    asyncio.create_task(register_views())

    # ✅ Envoie automatique du règlement
    guild = bot.get_guild(GUILD_ID)
    if guild:
        await send_rules_channel(guild)

async def register_views():
    await bot.wait_until_ready()  # ✅ Attend que le bot soit totalement prêt
    bot.add_view(RoleView())  # ✅ Ajoute la vue proprement

for guild in bot.guilds:
    for channel in guild.text_channels:
        print(f"{repr(channel.name)} - {channel.id}")

# ------------------------- LANCEMENT DU BOT -------------------------

if TOKEN is None:
    print("❌ Erreur : DISCORD_TOKEN est introuvable ! Assurez-vous qu'il est bien défini dans votre environnement.")
    exit(1)  # Arrête le programme proprement
else:
    print("✅ Token récupéré avec succès.")

bot = discord.Client(intents=discord.Intents.default())

bot.run(TOKEN)
