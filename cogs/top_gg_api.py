import logging
import dbl
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)


class TopGGApi(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.dbl_client = dbl.DBLClient(self.bot, self.bot.config["top_gg_api_key"])
        self.update_stats_loop.start()

    @tasks.loop(hours=12.0)
    async def update_stats_loop(self):
        """This function runs every 1 hour to automatically update server count on top.gg"""
        try:
            await self.dbl_client.post_guild_count()
            logger.info(f"Posted server count ({self.dbl_client.guild_count()})")
        except Exception as e:
            logger.exception(f"Failed to post server count\n{type(e).__name__}: {e}")

    @update_stats_loop.before_loop
    async def before_update_stats_loop(self):
        logger.info("Starting update stats loop loop..")
        await self.bot.wait_until_ready()
        logger.info("Update stats loop started!")


def setup(bot):
    bot.add_cog(TopGGApi(bot))
