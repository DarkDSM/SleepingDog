import discord
import asyncio
import os
import json
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# ================= SERVEUR WEB POUR RESTER ACTIF =================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot Vocal 24/24/365 - TOUJOURS ACTIF!"

@app.route('/ping')
def ping():
    return "pong"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# Démarrer le serveur web
print("🌐 Lancement du serveur web...")
web_thread = Thread(target=run_web)
web_thread.daemon = True
web_thread.start()

# ================= BOT VOCAL 24/24/365 =================

intents = discord.Intents.default()
intents.voice_states = True
intents.messages = True
intents.message_content = True

class VoiceTimeBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.user_voice_time = {}
        self.voice_join_time = {}
        self.bot_voice_channel = None
        self.target_channel_id = None
        self.last_connect_time = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.is_manually_disconnecting = False  # Pour éviter la reconnexion auto quand on quitte manuellement
        self.load_data()
        print("🤖 Bot vocal initialisé - Prêt pour 24/24!")

    def save_data(self):
        """Sauvegarde les données"""
        try:
            save_data = {}
            for user_id, timedelta_obj in self.user_voice_time.items():
                save_data[str(user_id)] = timedelta_obj.total_seconds()
            
            with open('voice_data.json', 'w') as f:
                json.dump(save_data, f)
            print("💾 Données sauvegardées")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")

    def load_data(self):
        """Charge les données"""
        try:
            with open('voice_data.json', 'r') as f:
                data = json.load(f)
                for user_id, seconds in data.items():
                    self.user_voice_time[int(user_id)] = timedelta(seconds=seconds)
            print(f"📂 {len(self.user_voice_time)} utilisateurs chargés")
        except FileNotFoundError:
            print("📂 Démarrage frais - Nouveau fichier de données")
            self.user_voice_time = {}
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")

    async def on_ready(self):
        print(f'✅ BOT CONNECTÉ: {self.user}')
        print(f'👥 Serveurs: {len(self.guilds)}')
        
        # Statut
        activity = discord.Activity(type=discord.ActivityType.watching, name="🎧 Vocal 24/24/365")
        await self.change_presence(activity=activity)
        
        # CONNEXION AUTOMATIQUE IMMÉDIATE
        await self.auto_connect_to_voice()
        
        # Tâches background
        self.loop.create_task(self.auto_save())
        self.loop.create_task(self.connection_watcher())
        self.loop.create_task(self.time_accumulator())
        self.loop.create_task(self.emergency_reconnector())

    async def auto_connect_to_voice(self):
        """Se connecte automatiquement à un salon vocal"""
        print("🔍 Recherche d'un salon vocal...")
        
        for guild in self.guilds:
            print(f"🏠 Serveur: {guild.name}")
            for channel in guild.voice_channels:
                print(f"   🎧 Salon: {channel.name}")
                try:
                    # Déconnecter si déjà connecté ailleurs
                    if self.bot_voice_channel and self.bot_voice_channel.is_connected():
                        await self.bot_voice_channel.disconnect()
                    
                    # Se connecter au salon
                    self.bot_voice_channel = await channel.connect()
                    self.target_channel_id = channel.id
                    self.last_connect_time = datetime.now()
                    self.reconnect_attempts = 0  # Réinitialiser les tentatives
                    
                    print(f"🎧✅ CONNECTÉ à: {channel.name}")
                    print("🤖 JE RESTE DANS LE VOCAL 24H/24 MAINTENANT !")
                    print("⏰ Cumul d'heures COMMENCÉ !")
                    return True
                    
                except Exception as e:
                    print(f"❌ Impossible {channel.name}: {e}")
                    continue
        
        print("⚠️ Aucun salon vocal trouvé - Attente manuelle !join")
        return False

    async def connection_watcher(self):
        """Surveille la connexion vocale en permanence"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                # Vérifier si déconnecté
                if not self.bot_voice_channel or not self.bot_voice_channel.is_connected():
                    if not self.is_manually_disconnecting:
                        print("🔁 DÉCONNEXION DÉTECTÉE - Reconnexion immédiate...")
                        self.reconnect_attempts += 1
                        success = await self.auto_connect_to_voice()
                        if success:
                            print("✅ Reconnexion réussie !")
                        else:
                            print(f"⚠️ Échec reconnexion (tentative {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                else:
                    # Vérifier la stabilité
                    duration = datetime.now() - self.last_connect_time if self.last_connect_time else timedelta(0)
                    hours = duration.total_seconds() / 3600
                    if hours > 1:  # Toutes les heures, log la durée
                        print(f"⏱️ Connexion stable depuis: {hours:.1f} heures")
                        self.reconnect_attempts = 0  # Réinitialiser après une heure stable
                        
            except Exception as e:
                print(f"❌ Erreur surveillant: {e}")
                
            await asyncio.sleep(15)  # Vérifie toutes les 15 secondes

    async def emergency_reconnector(self):
        """Reconnecteur d'urgence - vérifie périodiquement même si le watcher rate quelque chose"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                # Vérification supplémentaire toutes les 60 secondes
                await asyncio.sleep(60)
                
                if self.is_manually_disconnecting:
                    continue
                    
                # Si pas connecté et pas en mode manuel
                if not self.bot_voice_channel or not self.bot_voice_channel.is_connected():
                    print("🚨 RECONNECTEUR D'URGENCE - Tentative de reconnexion...")
                    await self.auto_connect_to_voice()
                    
            except Exception as e:
                print(f"❌ Erreur reconnecteur: {e}")

    async def time_accumulator(self):
        """Cumule du temps pour le bot (simulation d'activité)"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                # Le bot cumule du temps pour lui-même
                bot_id = self.user.id
                if self.bot_voice_channel and self.bot_voice_channel.is_connected():
                    if bot_id in self.user_voice_time:
                        self.user_voice_time[bot_id] += timedelta(seconds=60)  # +1 minute
                    else:
                        self.user_voice_time[bot_id] = timedelta(seconds=60)
                    
                    # Log toutes les heures
                    total_seconds = self.user_voice_time[bot_id].total_seconds()
                    if total_seconds % 3600 < 60:  # Toutes les heures
                        hours = int(total_seconds // 3600)
                        print(f"📈 Temps cumulé: {hours} heures")
                        
            except Exception as e:
                print(f"❌ Erreur accumulateur: {e}")
                
            await asyncio.sleep(60)  # Toutes les 60 secondes

    async def auto_save(self):
        """Sauvegarde automatique toutes les 5 minutes"""
        await self.wait_until_ready()
        while not self.is_closed():
            await asyncio.sleep(300)  # 5 minutes
            self.save_data()

    async def on_voice_state_update(self, member, before, after):
        """Track le temps des utilisateurs réels et surveille les déconnexions du bot"""
        # ===== SURVEILLANCE DU BOT =====
        if member == self.user:
            # Bot déconnecté involontairement
            if before.channel and not after.channel and not self.is_manually_disconnecting:
                print(f"⚠️ BOT DÉCONNECTÉ DU VOCAL: {before.channel.name}")
                print("🔄 Reconnexion automatique dans 3 secondes...")
                await asyncio.sleep(3)
                if not self.is_manually_disconnecting:  # Vérifier à nouveau
                    await self.auto_connect_to_voice()
            # Bot connecté
            elif not before.channel and after.channel:
                print(f"✅ BOT RECONNECTÉ À: {after.channel.name}")
                self.is_manually_disconnecting = False
                self.last_connect_time = datetime.now()
            return
            
        # ===== TRACKING UTILISATEURS =====
        if before.channel == after.channel:
            return
            
        # User rejoint le vocal
        if after.channel and not before.channel:
            self.voice_join_time[member.id] = datetime.now()
            print(f"🎧 {member.name} a rejoint le vocal")
            
        # User quitte le vocal
        elif before.channel and not after.channel:
            if member.id in self.voice_join_time:
                time_spent = datetime.now() - self.voice_join_time[member.id]
                
                # Mettre à jour le temps total
                if member.id in self.user_voice_time:
                    self.user_voice_time[member.id] += time_spent
                else:
                    self.user_voice_time[member.id] = time_spent
                
                total_seconds = self.user_voice_time[member.id].total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                
                print(f"🚪 {member.name} a quitté - Total: {hours}h {minutes}min")
                del self.voice_join_time[member.id]
                self.save_data()

    async def on_message(self, message):
        """Gestion des commandes"""
        if message.author == self.user:
            return

        if message.content.startswith('!join'):
            await self.cmd_join(message)
        elif message.content.startswith('!leave'):
            await self.cmd_leave(message)
        elif message.content.startswith('!temps'):
            await self.cmd_temps(message)
        elif message.content.startswith('!classement'):
            await self.cmd_classement(message)
        elif message.content.startswith('!status'):
            await self.cmd_status(message)
        elif message.content.startswith('!help'):
            await self.cmd_help(message)

    async def cmd_join(self, message):
        """Rejoindre le vocal de l'utilisateur"""
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            try:
                self.is_manually_disconnecting = False  # Réinitialiser pour la reconnexion
                
                # Déconnecter si déjà connecté
                if self.bot_voice_channel and self.bot_voice_channel.is_connected():
                    await self.bot_voice_channel.disconnect()
                
                # Se reconnecter au nouveau salon
                self.bot_voice_channel = await channel.connect()
                self.target_channel_id = channel.id
                self.last_connect_time = datetime.now()
                self.reconnect_attempts = 0
                
                await message.channel.send(f"🎧 **CONNECTÉ À {channel.name.upper()}** 🤖")
                await message.channel.send("**⭐ JE RESTE 24H/24 MAINTENANT !**")
                await message.channel.send("**⏰ CUMUL D'HEURES ACTIVÉ !**")
                await message.channel.send("**🔒 ANTI-DÉCONNEXION ACTIVÉ - JE NE PARTIRAI JAMAIS !**")
                
                print(f"🤖 Rejoint {channel.name} sur commande")
                
            except Exception as e:
                await message.channel.send(f"❌ Erreur: {e}")
        else:
            await message.channel.send("❌ Vous devez être dans un salon vocal !")

    async def cmd_leave(self, message):
        """Quitter le vocal (manuellement)"""
        self.is_manually_disconnecting = True  # Empêcher la reconnexion auto
        if self.bot_voice_channel:
            await self.bot_voice_channel.disconnect()
            self.bot_voice_channel = None
            self.target_channel_id = None
            await message.channel.send("🚪 **DÉCONNECTÉ DU VOCAL**")
            await message.channel.send("⚠️ **Mode manuel: Je ne me reconnecterai pas automatiquement**")
            print("🤖 Déconnecté manuellement - Mode manuel activé")
        else:
            await message.channel.send("❌ Je ne suis dans aucun vocal")
        # Réactiver la reconnexion auto après 30 secondes si pas rejoint manuellement
        await asyncio.sleep(30)
        if self.is_manually_disconnecting:
            self.is_manually_disconnecting = False
            print("🔄 Mode manuel désactivé - Reconnexion auto réactivée")

    async def cmd_temps(self, message):
        """Afficher le temps de l'utilisateur"""
        user_id = message.author.id
        if user_id in self.user_voice_time:
            total_seconds = self.user_voice_time[user_id].total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            await message.channel.send(f"🎧 **{message.author.name}** - Temps total: **{hours}h {minutes}min**")
        else:
            await message.channel.send(f"❌ **{message.author.name}**, vous n'avez pas encore de temps enregistré")

    async def cmd_classement(self, message):
        """Afficher le classement"""
        if not self.user_voice_time:
            await message.channel.send("📊 Aucune donnée de temps enregistrée")
            return
            
        sorted_users = sorted(self.user_voice_time.items(), 
                            key=lambda x: x[1].total_seconds(), 
                            reverse=True)[:10]
        
        classement = "🏆 **CLASSEMENT TEMPS VOCAL 24/24:**\n"
        for i, (user_id, time_spent) in enumerate(sorted_users, 1):
            user = self.get_user(user_id)
            username = user.name if user else f"User{user_id}"
            total_seconds = time_spent.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            classement += f"`{i:2d}.` {username:<20} - {hours:3d}h {minutes:2d}min\n"
        
        await message.channel.send(classement)

    async def cmd_status(self, message):
        """Statut du bot"""
        status_text = "**🤖 STATUT BOT VOCAL 24/24:**\n"
        
        if self.bot_voice_channel and self.bot_voice_channel.is_connected():
            channel_name = self.bot_voice_channel.channel.name if self.bot_voice_channel.channel else "Inconnu"
            status_text += f"✅ **CONNECTÉ** à: {channel_name}\n"
            
            if self.last_connect_time:
                duration = datetime.now() - self.last_connect_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                status_text += f"⏱️ **Depuis:** {hours}h {minutes}min\n"
            
            status_text += f"🔒 **Anti-déconnexion:** ACTIF\n"
            status_text += f"🔄 **Tentatives reconnexion:** {self.reconnect_attempts}\n"
        else:
            status_text += "❌ **DÉCONNECTÉ**\n"
            if self.is_manually_disconnecting:
                status_text += "⚠️ **Mode manuel activé** (pas de reconnexion auto)\n"
            else:
                status_text += "🔄 **Reconnexion auto en cours...**\n"
            
        status_text += f"📊 **Utilisateurs trackés:** {len(self.user_voice_time)}\n"
        status_text += f"💾 **Prochaine sauvegarde:** <5 min\n"
        status_text += "🔧 **Système:** Anti-déco MAXIMUM activé"
        
        await message.channel.send(status_text)

    async def cmd_help(self, message):
        help_text = """
**🎧 BOT VOCAL 24H/24 - COMMANDES:**

`!join` - Je rejoins VOTRE vocal (reste 24h/24)
`!leave` - Je quitte le vocal (manuellement)
`!temps` - Voir VOTRE temps total
`!classement` - Top 10 des temps vocaux
`!status` - Voir mon statut actuel
`!help` - Cette aide

**🌟 NOUVELLES FONCTIONNALITÉS:**
• 🤖 **ANTI-DÉCONNEXION MAXIMUM** - Je ne pars JAMAIS seul
• 🔒 **Double système de surveillance** (watcher + reconnecteur)
• 🚨 **Reconnexion automatique** en 3 secondes max
• ⚠️ **Mode manuel** pour !leave (empêche reconnexion auto 30s)
• 🔄 **10 tentatives max** avant pause

**🚀 CONFIGURÉ POUR DURER À VIE - JE NE PARTIRAI JAMAIS !**
        """
        await message.channel.send(help_text)

# ================= LANCEMENT DU BOT =================
print("=" * 50)
print("🚀 DÉMARRAGE BOT VOCAL 24/24/365")
print("🤖 Conçu pour durer À VIE")
print("🎧 Reste dans le vocal 24h/24 - ANTI-DÉCO MAXIMUM")
print("⏰ Cumule des heures automatiquement")
print("🔒 Système anti-déconnexion ACTIVÉ")
print("=" * 50)

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot = VoiceTimeBot()
    bot.run(token)
else:
    print("❌ ERREUR: DISCORD_TOKEN non trouvé!")
    print("💡 Configurez-le dans Railway/Replit Secrets")
