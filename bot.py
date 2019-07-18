#Credits to Kimchi
import discord
from discord.ext.commands import Bot
import asyncio, json, requests
import os, time, re, subprocess

# Bot Config (config.json)
with open("config.json") as (f):
    data = json.load(f)
BOT_TOKEN = data["token"]
BOT_PREFIX = data["prefix"]
ROLE_TO_ASSIGN = data["role_to_assign"]

client = Bot(command_prefix = BOT_PREFIX)

def keyGrab(key):
    f = open("license list.txt", 'r')
    for line in f:
        clean = line.split("\n")
        key.append(clean[0])
    
    f.close()

def keyRemove(key):
    os.remove("license list.txt")
    f = open('license list.txt', "a")
    for ELEM in key:
        f.write(ELEM + '\n')

    f.close()

@client.event
async def on_ready():
    await client.change_presence(activity= discord.Game(name = data['BotStatus']))
    print ("The MemberLicense Discord Bot is online")

"""""""""
Commands
"""""""""
# Redeem License Command
@client.command(pass_context = True)
async def redeem(ctx, license):
    await ctx.message.delete()

    keys = []
    keyGrab(keys)

    # If Invalid Key
    if license not in keys:
        return await (client.say("The license key you entered is not valid/deactivated."))
    
    # If Valid Key
    if license in keys:
        keys.remove(license)

        member = ctx.message.author
        if member == client.user:
            return
        
        try:
            role = discord.utils.get(member.guild.roles, name = ROLE_TO_ASSIGN)
            await member.add_roles(role)
            await ctx.author.send("Your license has been verified for the following role: " + ROLE_TO_ASSIGN)
            keyRemove(keys)
        except Exception as e:
            print (e)
            await ctx.send("An error has occured while adding the role. Try checking if there is a role for: " + ROLE_TO_ASSIGN)


client.run(BOT_TOKEN)
