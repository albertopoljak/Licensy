import os
import time
import psutil
import logging
import discord
from discord.ext import commands, tasks
from helpers.misc import construct_load_bar_string, construct_embed, time_ago, embed_space
from helpers.licence_helper import get_current_time
from helpers.embed_handler import info

logger = logging.getLogger(__name__)


class BotInformation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.developers = []
        # Fetch developers only once, at start
        self.bot.loop.create_task(self._set_developers())
        self.process = psutil.Process(os.getpid())
        self.activity = 0
        self.activity_loop.start()
        self.patreon_link = "https://www.patreon.com/Licensy"
        self.github_source = "https://github.com/albertopoljak/Licensy"
        self.top_gg_vote_link = "https://discordbots.org/bot/604057722878689324"

    @tasks.loop(seconds=300.0)
    async def activity_loop(self):
        if self.activity == 0:
            await self.bot.change_presence(activity=discord.Game(name="Roles!"))
            self.activity = 1
        elif self.activity == 1:
            msg = f"{len(self.bot.guilds)} guilds!"
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=msg))
            self.activity = 0

    @activity_loop.before_loop
    async def before_activity_loop(self):
        logger.info("Starting activity loop..")
        await self.bot.wait_until_ready()
        logger.info("Activity loop started!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # If bot is mentioned in message (both in guild and DM) show it's prefix
        if message.mentions and not message.author.bot and self.bot.user in message.mentions:
            if message.guild is None:
                prefix = self.bot.config["default_prefix"]
                msg = f"My prefix here is **{prefix}**"
                await message.channel.send(embed=info(msg, None))
            else:
                prefix = await self.bot.main_db.get_guild_prefix(message.guild.id)
                msg = f"My prefix in this guild is **{prefix}**"
                await message.channel.send(embed=info(msg, message.guild.me))

    @commands.command()
    async def ping(self, ctx):
        """
        Show bot ping.

        First value is REST API latency.
        Second value is Discord Gateway latency.

        """
        before = time.monotonic()
        message = await ctx.send(embed=info("Pong", ctx.me))
        ping = (time.monotonic() - before) * 1000
        content = (f":ping_pong:   |   {int(ping)}ms\n"
                   f":timer:   |   {self.bot.latency * 1000:.0f}ms")
        await message.edit(embed=info(content, ctx.me, title="Results:"))

    @commands.command()
    async def invite(self, ctx):
        """
        Shows bot invite link.

        """
        invite_link = self._get_bot_invite_link()
        description = f"Use this **[invite link]({invite_link})** to invite me."
        await ctx.send(embed=info(description, ctx.me, title="Invite me :)"))

    @commands.command()
    async def donate(self, ctx):
        """
        Support development!
        """
        await ctx.send(embed=info(self.patreon_link, ctx.me, title="Thank you :)"))

    def _get_bot_invite_link(self):
        perms = discord.Permissions()
        perms.update(manage_roles=True, read_messages=True, send_messages=True, manage_messages=True)
        return discord.utils.oauth_url(self.bot.user.id, permissions=perms)

    @commands.command()
    async def support_server(self, ctx):
        """
        Shows invite to the support server.

        """
        description = (f"Join **[support server]({self.bot.config['support_channel_invite']})** "
                       f"for questions, suggestions and support.")
        await ctx.send(embed=info(description, ctx.me, title="Ask away!"))

    @commands.command()
    async def vote(self, ctx):
        """
        Vote bot on top.gg (bot list).
        """
        await ctx.send(embed=info(self.top_gg_vote_link, ctx.me, title="Thank you."))

    @commands.command(aliases=["git", "github"])
    async def source(self, ctx):
        """
        Link to source code on Github.
        """
        await ctx.send(embed=info(self.github_source, ctx.me, title="Source code"))

    @commands.command()
    async def uptime(self, ctx):
        """
        Time since boot.
        """
        await ctx.send(embed=info(self.last_boot(), ctx.me, title="Booted:"))

    @commands.command(aliases=["stats", "status", "server"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def about(self, ctx):
        """
        Show bot information (stats/links/etc).

        """
        avg_members = round(len(self.bot.users) / len(self.bot.guilds))
        avg_members_string = f"{avg_members} users/server"

        active_licenses = await self.bot.main_db.get_licensed_roles_total_count()
        stored_licenses = await self.bot.main_db.get_stored_license_total_count()

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
                  f" | [Donate]({self.patreon_link})"
                  f" | [Support server]({self.bot.config['support_channel_invite']})"
                  f" | [Vote]({self.top_gg_vote_link})"
                  f" | [Github]({self.github_source})")

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
                  "Total users": len(self.bot.users),
                  "Commands": len(self.bot.commands),
                  "Active licenses:": active_licenses,
                  "Stored licenses:": stored_licenses,
                  "Server info": field_content,
                  }

        embed = construct_embed(ctx.me, **fields)
        await ctx.send(embed=embed)

    async def _set_developers(self):
        """
        Sets self.developers as a list of user mentions.
        Users represent developers loaded from config.

        """
        # Absolutely needed, otherwise we will try to fetch_user
        # before the bot is connected to discord thus getting an exception
        await self.bot.wait_until_ready()
        developer_ids = self.bot.config["developers"].values()
        developers = []
        for value_id in developer_ids:
            developer = await self.bot.fetch_user(value_id)
            developers.append(developer.mention)
        if not developers:
            logger.critical(f"Developers ({developer_ids}) could not be found on discord!")
            self.developers = ["Unknown"]
        else:
            self.developers = developers

    def last_boot(self) -> str:
        """
        :return: str last boot time

        """
        return time_ago(get_current_time() - self.bot.up_time_start_time)


def setup(bot):
    bot.add_cog(BotInformation(bot))
