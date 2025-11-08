import discord
import asyncio
import os
import json
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.voice_states = True
intents.messages = True
intents.message_content = True

class VoiceTimeBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.user_voice_time = {}
        self.voice_join_time = {}
        self.load_data()

    def save_data(self):
        """Sauvegarde les données dans un fichier JSON"""
        try:
            save_data = {}
            for user_id, timedelta_obj in self.user_voice_time.items():
                save_data[str(user_id)] = timedelta_obj.total_seconds()
            
            with open('voice_data.json', 'w') as f:
                json.dump(save_data, f)
            print("💾 Données sauvegardées avec succès")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")

    def load_data(self):
        """Charge les données depuis le fichier JSON"""
        try:
            with open('voice_data.json', 'r') as f:
                data = json.load(f)
                for user_id, seconds in data.items():
                    self.user_voice_time[int(user_id)] = timedelta(seconds=seconds)
            print(f"📂 Données chargées: {len(self.user_voice_time)} utilisateurs")
        except FileNotFoundError:
            print("📂 Aucune donnée trouvée, démarrage frais")
            self.user_voice_time = {}
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            self.user_voice_time = {}

    async def on_voice_state_update(self, member, before, after):
        """Gère les connexions/déconnexions vocales"""
        # Ignorer les mute/déafen
        if before.channel == after.channel:
            return
            
        # Rejoint un canal vocal
        if after.channel and not before.channel:
            self.voice_join_time[member.id] = datetime.now()
            print(f"🎧 {member.name} a rejoint {after.channel.name}")
            
        # Quitte un canal vocal
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
                
                print(f"🚪 {member.name} a quitté après {time_spent}. Total: {hours}h {minutes}min")
                del self.voice_join_time[member.id]
                self.save_data()

    async def on_ready(self):
        """Quand le bot est prêt"""
        print(f'✅ Bot connecté en tant que {self.user}')
        print(f'👥 Sur {len(self.guilds)} serveur(s)')
        print(f'📊 {len(self.user_voice_time)} utilisateurs suivis')
        
        # Mettre le statut
        activity = discord.Activity(type=discord.ActivityType.watching, name="le temps en vocal 🎧")
        await self.change_presence(activity=activity)
        
        # Tâche de sauvegarde automatique
        self.loop.create_task(self.auto_save())

    async def auto_save(self):
        """Sauvegarde automatique toutes les 5 minutes"""
        await self.wait_until_ready()
        while not self.is_closed():
            await asyncio.sleep(300)  # 5 minutes
            self.save_data()

    async def on_message(self, message):
        """Gère les commandes messages"""
        if message.author == self.user:
            return

        if message.content.startswith('!temps'):
            await self.cmd_temps(message)

        elif message.content.startswith('!classement'):
            await self.cmd_classement(message)
            
        elif message.content.startswith('!help'):
            await self.cmd_help(message)

    async def cmd_temps(self, message):
        """Commande !temps"""
        user_id = message.author.id
        if user_id in self.user_voice_time:
            total_seconds = self.user_voice_time[user_id].total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            await message.channel.send(f"🎧 **{message.author.name}** - Temps vocal: **{hours}h {minutes}min**")
        else:
            await message.channel.send(f"❌ **{message.author.name}**, aucun temps vocal enregistré")

    async def cmd_classement(self, message):
        """Commande !classement"""
        if not self.user_voice_time:
            await message.channel.send("📊 Aucune donnée de classement disponible")
            return
            
        sorted_users = sorted(self.user_voice_time.items(), 
                            key=lambda x: x[1].total_seconds(), 
                            reverse=True)[:10]
        
        classement = "🏆 **Classement des temps en vocal :**\n"
        for i, (user_id, time_spent) in enumerate(sorted_users, 1):
            user = self.get_user(user_id)
            username = user.name if user else f"User{user_id}"
            total_seconds = time_spent.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            classement += f"`{i:2d}.` {username:<20} - {hours:3d}h {minutes:2d}min\n"
        
        await message.channel.send(classement)

    async def cmd_help(self, message):
        """Commande !help"""
        help_text = """
**🎧 Commandes du Bot Vocal:**
`!temps` - Voir votre temps total en vocal
`!classement` - Voir le top 10 des temps vocaux
`!help` - Affiche ce message

Le bot track automatiquement votre temps passé en vocal !
        """
        await message.channel.send(help_text)

# Lancer le bot
if __name__ == "__main__":
    bot = VoiceTimeBot()
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("❌ ERREUR: DISCORD_TOKEN non trouvé!")
        print("💡 Assurez-vous de l'avoir configuré dans Railway")
    else:
        bot.run(token)
