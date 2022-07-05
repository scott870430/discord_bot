import time
import json
import argparse

import discord
from discord.ext import commands
import discord_slash

from youtube_cmd import *
import pc_bot

parser = argparse.ArgumentParser()
parser.add_argument("--no-musicbot", help="do NOT use music robot",
    action="store_false", default=True)
parser.add_argument("--no-pcbot", help="\"不\"使用報刀機器人",
    action="store_false", default=True)

args = parser.parse_args()


with open('input.json', 'r', encoding="utf-8") as f:
    input_json = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
slash = discord_slash.SlashCommand(bot, sync_commands=True)
clear_channel = input_json["clear_channel"]


if args.no_musicbot:
    bot.add_cog(Music(bot))

if args.no_pcbot:
    google_sheet_url = input_json["google_sheet_url"]
    authorize_file = input_json["authorize_file"]
    bot.add_cog(pc_bot.Pc_bot(bot, google_sheet_url, authorize_file))



'''
@bot.event
async def on_message(message):
    #排除自己的訊息，避免陷入無限循環
    if message.author == bot.user:
        return
    print(message.content)
'''


@bot.event
async def on_ready():
    print(f'目前登入身份：{bot.user}')

@bot.command()
async def hello(ctx):
    await ctx.send(f"!Hi <@{ctx.author.id}>")

@bot.event
async def on_member_join(member):
   await self.bot.get_channel(idchannel).send(f"{ member.name } has joined")

@bot.event
async def on_member_remove(member):
   await self.bot.get_channel(idchannel).send(f"{ member.name } has left")

@slash.slash(name='clear', description='remove all message in the channel')
async def clear(ctx):    
    channel = ctx.channel
    if str(channel) in clear_channel:
        await ctx.send('開始清理')
    else:
        await ctx.send('頻道錯誤')
        return

    start = time.time()
    messages = await channel.history(limit=10).flatten()
    # while
    while len(messages):
        for m in messages:
            await m.delete()
        messages = await channel.history(limit=10).flatten()

    end = time.time()
    await ctx.channel.send('清理結束')


with open('discord_token.json', 'r') as f:
    dis_j = json.load(f)
    discord_token = dis_j["discord_token"]


bot.run(discord_token)