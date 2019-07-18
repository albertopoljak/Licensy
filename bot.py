#Credits to Kimchi
import discord
from discord.ext.commands import Bot
import asyncio, json
import os, time, re, subprocess
from datetime import datetime, timedelta
from dateutil import parser
import traceback

# Bot Config (config.json)
with open("config.json") as (f):
    data = json.load(f)
BOT_TOKEN = data["token"]
BOT_PREFIX = data["prefix"]
ROLE_TO_ASSIGN = data["role_to_assign"]
LICENSE_DURATION_DAYS = data["license_duration_days"]

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

# Check if license not expired / Remove roles from those who have expired licenses
@client.command()
async def start(ctx):
    try:
        while True:
            f = open("licensed users.txt", "r")
            lines = f.readlines()

            f.close()

            f = open("licensed users.txt" , "w")
            for line in lines:
                info = line.split(";")
                
                idnum = int(info[0])
                member = ctx.guild.get_member(idnum)
                expirationDate = parser.parse(info[1])

                # Debug Console
                print ("User: " + str(member))
                print ("Expiration Date: " +str(expirationDate))
                print ("Today's Date: " + str(datetime.now()))
                print ("-----------------------")

                if (expirationDate < datetime.now()):
                    role = discord.utils.get(member.guild.roles, name = ROLE_TO_ASSIGN)
                    await member.remove_roles(role)
                else:
                    f.write(str(idnum) + ";" + str(expirationDate) + "\n")
        
            f.close()

            await asyncio.sleep(1800)

    except Exception as e:
        print(traceback.format_exc())

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
        return await ctx.send("The license key you entered is not valid/deactivated.")
    
    # If Valid Key
    if license in keys:
        keys.remove(license)

        member = ctx.message.author
        if member == client.user:
            return
        
        try:
            role = discord.utils.get(member.guild.roles, name = ROLE_TO_ASSIGN)

            # Add Role
            await member.add_roles(role)

            #Direct Message User and Remove Key
            
            await ctx.author.send("Your license has been verified for the following role: " + ROLE_TO_ASSIGN + " for " + LICENSE_DURATION_DAYS + " Days.")
            keyRemove(keys)

            f = open("licensed users.txt", "a+")
            idnum = member.id
            expirationDate = datetime.now() + timedelta(days = int(LICENSE_DURATION_DAYS))
            f.write(str(idnum) + ";" + str(expirationDate) + "\n")

            f.close()


        
        # Bot Error Exception
        except Exception as e:
            print (e)
            await ctx.send("An error has occured while adding the role. Try checking if there is a role for: " + ROLE_TO_ASSIGN)


client.run(BOT_TOKEN)