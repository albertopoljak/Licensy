import logging
import discord
from discord.ext import commands
from helpers.embed_handler import info
from helpers.misc import embed_space, get_top_role_color

logger = logging.getLogger(__name__)


class PrettyHelpCommand(commands.MinimalHelpCommand):
    def get_ending_note(self):
        command_name = self.invoked_with
        return ("Type {0}{1} <command> for more info on a command.\n"
                "You can also type {0}{1} <category> for more info on a category.").format(self.clean_prefix, command_name)

    def get_opening_note(self):
        if self.context.guild is None or self.context.author.guild_permissions.administrator:
            return
        else:
            return "Commands that you have no permission for are hidden."

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            max_length = 19
            outputs = [f"`  {c.name}{embed_space * (max_length - len(c.name))}{c.short_doc}`" for c in commands]
            joined = "\n".join(outputs)
            self.paginator.add_line(f"\n**__{heading}__**")
            self.paginator.add_line(joined)

    async def send_pages(self):
        empty = discord.Embed.Empty
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(title=empty, description=page, color=get_top_role_color(self.context.me))
            await destination.send(embed=embed)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = PrettyHelpCommand()
        bot.help_command.cog = self
        self.github_permissions_link = "https://github.com/albertopoljak/Licensy#permissions-needed"
        self.github_bot_quick_start = "https://github.com/albertopoljak/Licensy#quickstart-bot-usage"

    def cog_unload(self):
        """
        Revert to default help command in case cog is unloaded

        """
        self.bot.help_command = self._original_help_command

    @commands.command()
    async def faq(self, ctx):
        """
        Show common Q/A about bot and it's usage.

        """
        disclaimer = ("Disclaimer: Bot is currently in alpha phase.\n"
                      "Please let me know which features/improvements you want so I can focus on those.\n"
                      f"Type `{ctx.prefix}support` for invite to support server.")

        bot_faq = ("**1. If bot gets kicked/banned do I lose all my data?**\n"
                   "All of the guild data is immediately deleted from the database.\n\n"

                   "**2. What happens if I delete a role or remove it manually from a member?**\n"
                   "If that role is tied to any licenses/active subscriptions "
                   "they are immediately deleted/canceled from the database.\n\n"

                   "**3. What is the precision of role expiration?**\n"
                   "Bot checks for expired licenses on startup and each 60 seconds after startup.\n\n"

                   "**4. Who can view/generate guild licenses?**\n"
                   "Only those who have role administrator in the guild.\n\n"

                   "**5. How are licenses generated, are they unique?**\n"
                   "They are completely unique, comprised of 30 randomly generated characters.\n\n"
                   
                   "**6. Can I generate licenses for roles other than default guild role?**\n"
                   f"Use `{ctx.prefix}generate` command with custom arguments.\n"
                   f"See **[github link]({self.github_bot_quick_start})** for example "
                   f"or just call `{ctx.prefix}help generate` for more info.\n\n"

                   "**7. What's the maximum for role expire time?**\n"
                   "Maximum time for expiry date is 12 months.\n\n"

                   "**8. How many stored licenses per guild?**\n"
                   "Limit for stored (unactivated) licenses is "
                   f"{self.bot.config.get_maximum_unused_guild_licences()} per guild.\n\n"
                   
                   "**9. How many activated licenses per member?**\n"
                   "Members can have unlimited subscriptions active at the same time! "
                   "(only limited by the Discord role limit per member which is 250).\n\n"

                   "**10. What are the bot permissions for?**\n"
                   f"To avoid repeating see **[github link]({self.github_permissions_link})** where permissions "
                   "are explained in detail.\n\n"

                   "**11. What if I deny any of those permissions when inviting the bot?**\n"
                   "Bot was over-engineered to deal with all sorts of exceptions but I don't guarantee the bot "
                   "will function properly or at all in that case.\n\n"
                   
                   "**12. Does the bot get updated? Will it affect usage?**\n"
                   "There will be no breaking changes in updates, only improvements. "
                   "During the update you will see that bot has changed status to 'Update' or is offline. "
                   "During that time the bot may stop responding to commands, but this is only for <5 minutes. "
                   "After that everything is back to normal."
                   )
        await ctx.send(embed=info(bot_faq, ctx.me, title=disclaimer))

    @commands.command()
    async def quickstart(self, ctx):
        """
        Shortly explains first time bot usage.

        """
        description = (f"To avoid repeating see **[github link]({self.github_bot_quick_start})** where quickstart "
                       f"is explained in detail.")
        await ctx.send(embed=info(description, ctx.me, title="Quickstart :)"))


def setup(bot):
    bot.add_cog(Help(bot))
