import os
import discord
from discord.ext import commands
import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Configurações do bot e do Spotify
bot_token = os.getenv('DISCORD_BOT_TOKEN')
spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Inicializa o Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret))

# Inicializa o bot
bot = commands.Bot(command_prefix='!')

# Lista de reprodução
playlist = []

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

def search_youtube(query):
    ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            get = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        except Exception:
            return False
    return {'source': get['formats'][0]['url'], 'title': get['title']}

def search_spotify(query):
    result = sp.search(query, type='track', limit=1)
    if result['tracks']['items']:
        track = result['tracks']['items'][0]
        return {'source': track['external_urls']['spotify'], 'title': track['name']}
    return None

@bot.command()
async def play(ctx, *, query):
    channel = ctx.author.voice.channel
    if not channel:
        await ctx.send('Você precisa estar em um canal de voz para tocar música.')
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        voice_client = await channel.connect()

    song = search_youtube(query) or search_spotify(query)
    if not song:
        await ctx.send('Música não encontrada.')
        return

    playlist.append(song)
    await ctx.send(f'Adicionado à playlist: {song["title"]}')
    
    if not voice_client.is_playing():
        play_next(ctx, voice_client)

def play_next(ctx, voice_client):
    if playlist:
        song = playlist.pop(0)
        voice_client.play(discord.FFmpegPCMAudio(song['source']), after=lambda e: play_next(ctx, voice_client))
        coro = ctx.send(f'Tocando agora: {song["title"]}')
        fut = discord.compat.create_task(coro, name="send current song")
    else:
        coro = ctx.send('A playlist está vazia.')
        fut = discord.compat.create_task(coro, name="send empty playlist")

@bot.command()
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Música pulada.')

@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send('Música pausada.')

@bot.command()
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send('Música retomada.')

@bot.command()
async def queue(ctx):
    if playlist:
        message = '\n'.join([song['title'] for song in playlist])
        await ctx.send(f'Playlist:\n{message}')
    else:
        await ctx.send('A playlist está vazia.')

@bot.command()
async def clear(ctx):
    global playlist
    playlist = []
    await ctx.send('A playlist foi limpa.')

bot.run(bot_token)
