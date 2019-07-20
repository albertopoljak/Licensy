#####################
# Credits to Kimchi #
#####################
import traceback
import asyncio
import json
import os
from datetime import datetime, timedelta
from dateutil import parser
import discord
from discord.ext.commands import Bot

############################
# Bot Config (config.json) #
############################
with open("config.json") as (f):
    data = json.load(f)
BOT_TOKEN = data["token"]
BOT_PREFIX = data["prefix"]
ROLE_TO_ASSIGN = data["role_to_assign"]
LICENSE_DURATION_DAYS = data["license_duration_days"]

client = Bot(command_prefix=BOT_PREFIX)


#########################
# Functions For License #
#########################
def key_grab(key):
    f = open("license list.txt", 'r')
    for line in f:
        clean = line.split("\n")
        key.append(clean[0])
    
    f.close()


def key_remove(key):
    os.remove("license list.txt")
    f = open('license list.txt', "a")
    for ELEM in key:
        f.write(ELEM + '\n')

    f.close()


#######################
# Startup Code [Main] #
#######################
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=data['BotStatus']))
    print("The MemberLicense Discord Bot is online")


#####################
# Commands / Source #
#####################

# Check if license not expired / Remove roles from those who have expired licenses
@client.command()
async def start(ctx):
    try:
        
        # Announce start
        await ctx.send("The filtering process has started. "
                       "Will be checking for expired licenses periodically (30 min intervals).")

        while True:
            f = open("licensed users.txt", "r")
            lines = f.readlines()

            f.close()

            f = open("licensed users.txt", "w")
            for line in lines:
                info = line.split(";")
                
                id_num = int(info[0])
                member = ctx.guild.get_member(id_num)
                expiration_date = parser.parse(info[1])

                # Debug Console
                print("User: " + str(member))
                print("Expiration Date: " + str(expiration_date))
                print("Today's Date: " + str(datetime.now()))
                print("-----------------------")

                # If Expired
                if expiration_date < datetime.now():
                    role = discord.utils.get(member.guild.roles, name=ROLE_TO_ASSIGN)
                    await member.remove_roles(role)
                    await member.send("Your license has expired for the following role: " + ROLE_TO_ASSIGN)
                else:
                    f.write(str(id_num) + ";" + str(expiration_date) + "\n")
        
            f.close()

            await asyncio.sleep(1800)

    except Exception as e:
        print(traceback.format_exc())


# Redeem License Command
@client.command(pass_context=True)
async def redeem(ctx, license):
    await ctx.message.delete()

    keys = []
    key_grab(keys)

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
            role = discord.utils.get(member.guild.roles, name=ROLE_TO_ASSIGN)

            # Add Role
            await member.add_roles(role)

            # Direct Message User and Remove Key
            await ctx.author.send(f"Your license has been verified for the following "
                                  f"role: {ROLE_TO_ASSIGN} for {LICENSE_DURATION_DAYS} Days.")
            key_remove(keys)

            f = open("licensed users.txt", "a+")
            id_num = member.id
            expiration_date = datetime.now() + timedelta(days=int(LICENSE_DURATION_DAYS))
            f.write(str(id_num) + ";" + str(expiration_date) + "\n")
            f.close()

        # Bot Error Exception
        except Exception as e:
            print(e)
            await ctx.send(f"An error has occurred while adding the role. "
                           f"Try checking if there is a role for: {ROLE_TO_ASSIGN}")


client.run(BOT_TOKEN)
