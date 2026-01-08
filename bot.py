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
        self.never_leave_mode = True  # MODE JAMAIS QUITTER
        self.load_data()
        print("🤖 Bot vocal initialisé - PRÊT POUR 24/24/365!")
        print("🚫 MODE: IMPOSSIBLE À DÉCONNECTER")

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
        activity = discord.Activity(type=discord.ActivityType.watching, name="🎧 Vocal ÉTERNEL")
        await self.change_presence(activity=activity)
        
        # CONNEXION AUTOMATIQUE IMMÉDIATE
        await self.auto_connect_to_voice()
        
        # Tâches background
        self.loop.create_task(self.auto_save())
        self.loop.create_task(self.eternal_connection_watcher())
        self.loop.create_task(self.time_accumulator())

    async def auto_connect_to_voice(self):
        """Se connecte automatiquement à un salon vocal - ESSAI INFINI"""
        print("🔍 Recherche d'un salon vocal...")
        
        while True:  # BOUCLE INFINIE JUSQU'À CONNEXION
            for guild in self.guilds:
                print(f"🏠 Serveur: {guild.name}")
                for channel in guild.voice_channels:
                    print(f"   🎧 Tentative: {channel.name}")
                    try:
                        # Déconnecter si déjà connecté ailleurs
                        if self.bot_voice_channel and self.bot_voice_channel.is_connected():
                            try:
                                await self.bot_voice_channel.disconnect()
                            except:
                                pass
                        
                        # Se connecter au salon
                        self.bot_voice_channel = await channel.connect()
                        self.target_channel_id = channel.id
                        self.last_connect_time = datetime.now()
                        self.reconnect_attempts = 0
                        
                        print(f"🎧✅ CONNECTÉ à: {channel.name}")
                        print("🤖 JE RESTE DANS LE VOCAL POUR L'ÉTERNITÉ !")
                        print("🚫 IMPOSSIBLE DE ME DÉCONNECTER")
                        return True
                        
                    except discord.errors.ClientException as e:
                        if "Already connected" in str(e):
                            print("✅ Déjà connecté!")
                            return True
                        print(f"⚠️ Erreur: {e}")
                        continue
                    except Exception as e:
                        print(f"❌ Impossible {channel.name}: {e}")
                        continue
            
            print("🔄 Aucun salon trouvé - Nouvel essai dans 10 secondes...")
            await asyncio.sleep(10)

    async def eternal_connection_watcher(self):
        """Surveillance ÉTERNELLE de la connexion"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                # Vérifier si déconnecté
                if not self.bot_voice_channel or not self.bot_voice_channel.is_connected():
                    print("🚨 DÉCONNEXION DÉTECTÉE !")
                    print("🔄 RECONNEXION IMMÉDIATE...")
                    self.reconnect_attempts += 1
                    print(f"📊 Tentative #{self.reconnect_attempts}")
                    
                    # Reconnexion ULTRA RAPIDE
                    success = await self.auto_connect_to_voice()
                    if success:
                        print(f"✅ Reconnexion #{self.reconnect_attempts} RÉUSSIE !")
                    else:
                        print(f"⚠️ Échec, nouvelle tentative dans 3 secondes...")
                        await asyncio.sleep(3)
                else:
                    # Vérifier la stabilité
                    if self.last_connect_time:
                        duration = datetime.now() - self.last_connect_time
                        hours = duration.total_seconds() / 3600
                        if hours > 1:  # Toutes les heures, log la durée
                            print(f"⏱️ Connexion stable depuis: {hours:.1f} heures")
                            
            except Exception as e:
                print(f"❌ Erreur surveillant: {e}")
                
            await asyncio.sleep(5)  # Vérifie toutes les 5 secondes

    async def time_accumulator(self):
        """Cumule du temps pour le bot"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                # Le bot cumule du temps pour lui-même
                bot_id = self.user.id
                if self.bot_voice_channel and self.bot_voice_channel.is_connected():
                    if bot_id in self.user_voice_time:
                        self.user_voice_time[bot_id] += timedelta(seconds=60)
                    else:
                        self.user_voice_time[bot_id] = timedelta(seconds=60)
                    
                    # Log toutes les heures
                    total_seconds = self.user_voice_time[bot_id].total_seconds()
                    if total_seconds % 3600 < 60:
                        hours = int(total_seconds // 3600)
                        print(f"📈 Temps cumulé: {hours} heures")
                        
            except Exception as e:
                print(f"❌ Erreur accumulateur: {e}")
                
            await asyncio.sleep(60)

    async def auto_save(self):
        """Sauvegarde automatique"""
        await self.wait_until_ready()
        while not self.is_closed():
            await asyncio.sleep(300)
            self.save_data()

    async def on_voice_state_update(self, member, before, after):
        """Track le temps des utilisateurs et SURVEILLANCE MAXIMUM du bot"""
        # ===== SURVEILLANCE ULTRA DU BOT =====
        if member == self.user:
            # Bot déconnecté (NE DEVRAIT JAMAIS ARRIVER MAIS AU CAS OÙ)
            if before.channel and not after.channel:
                print(f"🚨🚨🚨 BOT DÉCONNECTÉ DE {before.channel.name} !!!")
                print("🚨 RECONNEXION ULTRA RAPIDE...")
                await asyncio.sleep(1)  # Seulement 1 seconde d'attente
                await self.auto_connect_to_voice()
            # Bot connecté
            elif not before.channel and after.channel:
                print(f"✅✅✅ BOT DANS LE VOCAL: {after.channel.name}")
                self.last_connect_time = datetime.now()
            return
            
        # ===== TRACKING UTILISATEURS =====
        if before.channel == after.channel:
            return
            
        if after.channel and not before.channel:
            self.voice_join_time[member.id] = datetime.now()
            print(f"🎧 {member.name} a rejoint")
            
        elif before.channel and not after.channel:
            if member.id in self.voice_join_time:
                time_spent = datetime.now() - self.voice_join_time[member.id]
                
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
        """Gestion des commandes - !leave DÉSACTIVÉ"""
        if message.author == self.user:
            return

        if message.content.startswith('!join'):
            await self.cmd_join(message)
        elif message.content.startswith('!leave'):
            await self.cmd_leave(message)  # Modifié pour NE RIEN FAIRE
        elif message.content.startswith('!temps'):
            await self.cmd_temps(message)
        elif message.content.startswith('!classement'):
            await self.cmd_classement(message)
        elif message.content.startswith('!status'):
            await self.cmd_status(message)
        elif message.content.startswith('!help'):
            await self.cmd_help(message)
        elif message.content.startswith('!force'):
            await self.cmd_force(message)

    async def cmd_join(self, message):
        """Rejoindre le vocal de l'utilisateur"""
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            try:
                # Déconnecter si déjà connecté
                if self.bot_voice_channel and self.bot_voice_channel.is_connected():
                    try:
                        await self.bot_voice_channel.disconnect()
                    except:
                        pass
                
                # Se reconnecter au nouveau salon
                self.bot_voice_channel = await channel.connect()
                self.target_channel_id = channel.id
                self.last_connect_time = datetime.now()
                
                await message.channel.send(f"🎧 **CONNECTÉ À {channel.name.upper()}** 🤖")
                await message.channel.send("**⭐ JE RESTE POUR TOUJOURS MAINTENANT !**")
                await message.channel.send("**🚫 IMPOSSIBLE DE ME DÉCONNECTER**")
                await message.channel.send("**⏰ CUMUL D'HEURES ÉTERNEL ACTIVÉ !**")
                
                print(f"🤖 Rejoint {channel.name} sur commande")
                
            except Exception as e:
                await message.channel.send(f"⚠️ Erreur: {e}")
                await message.channel.send("🔄 Nouvelle tentative automatique...")
                await self.auto_connect_to_voice()
        else:
            await message.channel.send("❌ Vous devez être dans un salon vocal !")

    async def cmd_leave(self, message):
        """COMMANDE DÉSACTIVÉE - Le bot ne quitte jamais"""
        await message.channel.send("🚫 **COMMANDE DÉSACTIVÉE**")
        await message.channel.send("🤖 **JE NE QUITTE JAMAIS LE VOCAL !**")
        await message.channel.send("💡 Utilise `!join` pour me déplacer dans ton salon")
        await message.channel.send("🔒 *Mode éternel activé - Impossible à déconnecter*")
        print(f"⚠️ {message.author.name} a tenté de déconnecter le bot (refusé)")

    async def cmd_force(self, message):
        """Commande spéciale pour forcer la reconnexion (admin)"""
        # Vérifier si l'utilisateur est admin ou le propriétaire du bot
        if message.author.guild_permissions.administrator or message.author.id == self.owner_id:
            await message.channel.send("🔄 **FORCE RECONNEXION EN COURS...**")
            print(f"🔄 Reconnexion forcée par {message.author.name}")
            await self.auto_connect_to_voice()
            await message.channel.send("✅ **RECONNECTÉ !**")
        else:
            await message.channel.send("❌ **PERMISSION REFUSÉE**")
            await message.channel.send("Seuls les admins peuvent utiliser cette commande")

    async def cmd_temps(self, message):
        """Afficher le temps de l'utilisateur"""
        user_id = message.author.id
        if user_id in self.user_voice_time:
            total_seconds = self.user_voice_time[user_id].total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            days = hours // 24
            hours = hours % 24
            await message.channel.send(f"🎧 **{message.author.name}** - Temps total: **{days}j {hours}h {minutes}min**")
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
        
        classement = "🏆 **CLASSEMENT TEMPS VOCAL ÉTERNEL:**\n"
        for i, (user_id, time_spent) in enumerate(sorted_users, 1):
            user = self.get_user(user_id)
            username = user.name if user else f"User{user_id}"
            total_seconds = time_spent.total_seconds()
            days = int(total_seconds // 86400)
            hours = int((total_seconds % 86400) // 3600)
            classement += f"`{i:2d}.` {username:<20} - {days:3d}j {hours:2d}h\n"
        
        await message.channel.send(classement)

    async def cmd_status(self, message):
        """Statut du bot"""
        status_text = "**🤖 STATUT BOT VOCAL ÉTERNEL:**\n"
        
        if self.bot_voice_channel and self.bot_voice_channel.is_connected():
            channel_name = self.bot_voice_channel.channel.name if self.bot_voice_channel.channel else "Inconnu"
            status_text += f"✅ **CONNECTÉ** à: {channel_name}\n"
            
            if self.last_connect_time:
                duration = datetime.now() - self.last_connect_time
                days = int(duration.total_seconds() // 86400)
                hours = int((duration.total_seconds() % 86400) // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                status_text += f"⏱️ **Depuis:** {days}j {hours}h {minutes}min\n"
            
            status_text += f"🔒 **Mode:** ÉTERNEL (pas de déconnexion)\n"
            status_text += f"🔄 **Tentatives:** {self.reconnect_attempts}\n"
        else:
            status_text += "🚨 **DÉCONNECTÉ - RECONNEXION EN COURS**\n"
            status_text += f"🔄 Tentative #{self.reconnect_attempts + 1}\n"
            
        status_text += f"📊 **Utilisateurs trackés:** {len(self.user_voice_time)}\n"
        status_text += f"💾 **Sauvegarde auto:** Activée\n"
        status_text += "⚡ **Reconnexion:** <5 secondes"
        
        await message.channel.send(status_text)

    async def cmd_help(self, message):
        help_text = """
**🎧 BOT VOCAL ÉTERNEL - COMMANDES:**

`!join` - Je rejoins VOTRE vocal (pour toujours)
`!temps` - Voir VOTRE temps total
`!classement` - Top 10 des temps vocaux
`!status` - Voir mon statut actuel
`!help` - Cette aide

**🚨 ATTENTION IMPORTANTE:**
• 🤖 **JE NE QUITTE JAMAIS LE VOCAL**
• 🔒 **!leave est DÉSACTIVÉ**
• ⚡ **Reconnexion automatique** en <5 secondes
• 🔄 **Tentatives infinies** en cas de problème

**🌟 FONCTIONNALITÉS ÉTERNELLES:**
• 🕐 **Cumul d'heures 24/24/365**
• 💾 **Sauvegarde automatique**
• 📊 **Classement temps réel**
• 🛡️ **Anti-déconnexion MAXIMUM**

**🚀 JE RESTE DANS LE VOCAL POUR L'ÉTERNITÉ !**
        """
        await message.channel.send(help_text)

# ================= LANCEMENT DU BOT =================
print("=" * 50)
print("🚀 DÉMARRAGE BOT VOCAL ÉTERNEL")
print("🤖 Conçu pour durer POUR TOUJOURS")
print("🎧 JE NE QUITTE JAMAIS LE VOCAL")
print("🚫 COMMANDE !leave DÉSACTIVÉE")
print("⚡ Reconnexion ultra-rapide")
print("=" * 50)

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot = VoiceTimeBot()
    bot.run(token)
else:
    print("❌ ERREUR: DISCORD_TOKEN non trouvé!")
