import os
import time
import psutil
import discord
import logging
from datetime import datetime
from discord.ext import commands
from helpers.misc import construct_load_bar_string, construct_embed, time_ago

logger = logging.getLogger(__name__)
up_time_start_time = datetime.now()


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.developers = []
        # Fetch developers only once, at start
        self.bot.loop.create_task(self.set_developers())
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def ping(self, ctx):
        """
        Show bot ping.

        """
        before = time.monotonic()
        message = await ctx.send("Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f":ping_pong:   |   {int(ping)}ms")

    @commands.command()
    async def invite(self, ctx):
        """
        Shows bot invite link.

        """
        invite_link = ("(https://discordapp.com/api/oauth2/authorize?client_id=604057722878689324&permissions="
                       "268504064&redirect_uri=https%3A%2F%2Fdiscordapp.com%2Foauth2%2Fauthorize%3Fclient_id%"
                       "3D604057722878689324%26scope%3Dbot&scope=bot)")
        embed = discord.Embed(description=f"**Use this [URL]{invite_link} to invite me.**")
        await ctx.send(embed=embed)

    @commands.command()
    async def support(self, ctx):
        """
        Shows invite to the support server.

        """
        support_server_invite = "https://discord.gg/eNZNQUk"
        description = f"**Join here [Support server]({support_server_invite}) for questions, suggestions and support.**"
        embed = discord.Embed(description=description)
        await ctx.send(embed=embed)

    @commands.command(aliases=["stats", "status", "server"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def about(self, ctx):
        """
        Show bot/server information.

        """
        last_boot = time_ago(datetime.now() - up_time_start_time)

        server_count = len(ctx.bot.guilds)

        avg_members = round(len(self.bot.users) / len(self.bot.guilds))
        avg_members_string = f"{avg_members} users/server"

        commands_loaded = len(self.bot.commands)

        bot_ram_usage = self.process.memory_full_info().rss / 1024 ** 2
        bot_ram_usage = f"{bot_ram_usage:.2f} MB"
        bot_ram_usage_field = construct_load_bar_string(self.process.memory_percent(), bot_ram_usage)

        virtual_memory = psutil.virtual_memory()
        server_ram_usage = f"{virtual_memory.used/1024/1024:.0f} MB"
        server_ram_usage_field = construct_load_bar_string(virtual_memory.percent, server_ram_usage)

        cpu_count = psutil.cpu_count()

        bot_cpu_usage = self.process.cpu_percent()
        if bot_cpu_usage > 100:
            bot_cpu_usage = bot_cpu_usage / cpu_count
        bot_cpu_usage_field = f"{bot_cpu_usage}%"

        server_cpu_usage = psutil.cpu_percent()
        if server_cpu_usage > 100:
            server_cpu_usage = server_cpu_usage / cpu_count
        server_cpu_usage_field = construct_load_bar_string(server_cpu_usage)

        io_counters = self.process.io_counters()
        io_read_bytes = f"{io_counters.read_bytes/1024/1024:.3f}MB"
        io_write_bytes = f"{io_counters.write_bytes/1024/1024:.3f}MB"
        io_count = f"{io_counters.read_count}/{io_counters.write_count}"

        footer = "[Invite](https://example.org)" \
                 " | [Support](https://example.org)" \
                 " | [Vote](https://example.org)" \
                 " | [Website](https://example.org)"

        field_content = f"**Bot ram usage:** {bot_ram_usage_field}\n" \
                        f"**Server RAM usage:** {server_ram_usage_field}\n" \
                        f"**Server swap usage:** {psutil.swap_memory().percent}%\n" \
                        f"**Server cores:** {cpu_count}\n" \
                        f"**Bot CPU usage:** {bot_cpu_usage_field}\n" \
                        f"**Server CPU usage:** {server_cpu_usage_field}\n" \
                        f"**IO (r/w/c):** {io_read_bytes} , {io_write_bytes} , {io_count}\n" \
                        f"\n**Links:\n**" + footer

        fields = {"Last boot": last_boot,
                  "Developers": "\n".join(self.developers),
                  "Library": "discord.py",
                  "Servers": server_count,
                  "Average users:": avg_members_string,
                  "Commands": commands_loaded,
                  "Server info": field_content,
                  }
        embed = construct_embed(author=ctx.me, **fields)
        await ctx.send(embed=embed)

    async def set_developers(self):
        """
        Sets self.developers as a list of user mentions.
        Users represent developers loaded from config.

        """
        # Absolutely needed, otherwise we will try to fetch_user
        # before the bot is connected to discord thus getting an exception
        await self.bot.wait_until_ready()
        developer_ids = self.bot.config.get_developers().values()
        developers = []
        for value_id in developer_ids:
            developer = await self.bot.fetch_user(value_id)
            developers.append(developer.mention)
        if not developers:
            logger.critical("Developers ({developer_ids}) could not be found on discord!")
            self.developers = ["Unknown"]
        else:
            self.developers = developers


def setup(bot):
    bot.add_cog(Information(bot))
