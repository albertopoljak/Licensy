import os
import time
import psutil
import discord
import logging
from datetime import datetime
from discord.ext import commands
from helpers.misc import construct_load_bar_string, construct_embed, time_ago, embed_space
from helpers.embed_handler import info_embed, success_embed

logger = logging.getLogger(__name__)


class BotInformation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.developers = []
        # Fetch developers only once, at start
        self.bot.loop.create_task(self.set_developers())
        self.process = psutil.Process(os.getpid())
        self.support_server_invite = self.bot.config.get_support_channel_invite()

    @commands.command()
    async def ping(self, ctx):
        """
        Show bot ping.

        First value is  time needed to send message & edit message.
        Second value is the actual latency between bot and discord.

        """
        before = time.monotonic()
        message = await ctx.send(embed=info_embed("Pong", ctx.me))
        ping = (time.monotonic() - before) * 1000
        content = (f":ping_pong:   |   {int(ping)}ms\n"
                   f":timer:   |   {self.bot.latency * 1000:.0f}ms")
        await message.edit(embed=info_embed(content, ctx.me, title="Results:"))

    @commands.command()
    async def invite(self, ctx):
        """
        Shows bot invite link.

        """
        invite_link = self._get_bot_invite_link()
        description = f"Use this **[invite]({invite_link})** to invite me."
        await ctx.send(embed=info_embed(description, ctx.me, title="Invite me :)"))

    def _get_bot_invite_link(self):
        perms = discord.Permissions()
        perms.update(manage_roles=True, read_messages=True, send_messages=True, manage_messages=True)
        return discord.utils.oauth_url(self.bot.user.id, permissions=perms)

    @commands.command()
    async def support(self, ctx):
        """
        Shows invite to the support server.

        """
        description = f"Join **[support server]({self.support_server_invite})** for questions, suggestions and support."
        await ctx.send(embed=info_embed(description, ctx.me, title="Ask away!"))

    @commands.command(aliases=["stats", "status", "server"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def about(self, ctx):
        """
        Show bot/server information.

        """
        avg_members = round(len(self.bot.users) / len(self.bot.guilds))
        avg_members_string = f"{avg_members} users/server"

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
        bot_cpu_usage_field = construct_load_bar_string(bot_cpu_usage)

        server_cpu_usage = psutil.cpu_percent()
        if server_cpu_usage > 100:
            server_cpu_usage = server_cpu_usage / cpu_count
        server_cpu_usage_field = construct_load_bar_string(server_cpu_usage)

        io_counters = self.process.io_counters()
        io_read_bytes = f"{io_counters.read_bytes/1024/1024:.3f}MB"
        io_write_bytes = f"{io_counters.write_bytes/1024/1024:.3f}MB"

        footer = (f"[Invite]({self._get_bot_invite_link()})"
                  f" | [Support]({self.support_server_invite})"
                  f" | [Vote](https://discordbots.org/bot/604057722878689324)"
                  f" | [Website](https://github.com/albertopoljak/Licensy)")

        # The weird numbers is just guessing number of spaces so the lines align
        # Needed since embeds are not monospaced font
        field_content = (f"**Bot RAM usage:**{embed_space*7}{bot_ram_usage_field}\n"
                         f"**Server RAM usage:**{embed_space}{server_ram_usage_field}\n"
                         f"**Bot CPU usage:**{embed_space*9}{bot_cpu_usage_field}\n"
                         f"**Server CPU usage:**{embed_space*3}{server_cpu_usage_field}\n"
                         f"**IO (r/w):** {io_read_bytes} / {io_write_bytes}\n"
                         f"\n**Links:\n**" + footer)

        # If called immediately after startup it will fail since developers are not yet loaded
        developers = self.developers if self.developers else ["loading.."]
        fields = {"Last boot": self.last_boot(),
                  "Developers": "\n".join(developers),
                  "Library": "discord.py",
                  "Servers": len(self.bot.guilds),
                  "Average users:": avg_members_string,
                  "Commands": len(self.bot.commands),
                  "Server info": field_content,
                  }

        embed = construct_embed(ctx.me, **fields)
        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx):
        """
        Time since boot.

        """
        await ctx.send(embed=info_embed(self.last_boot(), ctx.me, title="Booted:"))

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

    def last_boot(self) -> str:
        """
        :return: str last boot time

        """
        return time_ago(datetime.now() - self.bot.up_time_start_time)

    @commands.command()
    async def users(self, ctx):
        """
        Shows total count of users in all guilds.

        """
        await ctx.send(embed=success_embed(f"Serving {len(self.bot.users)} users!", ctx.me))


def setup(bot):
    bot.add_cog(BotInformation(bot))
