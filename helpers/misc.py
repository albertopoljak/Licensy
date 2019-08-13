import os
import logging
from pathlib import Path
from discord import Embed
import timeago as timesince

logger = logging.getLogger(__name__)


def construct_load_bar_string(percent, message=None, size=None):
    if size is None:
        size = 10
    else:
        if size < 8:
            size = 8

    limiters = "|"
    element_emtpy = "▱"
    element_full = "▰"
    constructed = ""

    if percent > 100:
        percent = 100
    progress = int(round(percent / size))

    constructed += limiters
    for x in range(0, progress):
        constructed += element_full
    for x in range(progress, size):
        constructed += element_emtpy
    constructed += limiters
    if message is None:
        constructed = f"{constructed} {percent:.2f}%"
    else:
        constructed = f"{constructed} {message}"
    return constructed


def construct_embed(description=None, author=None, **kwargs):
    embed = Embed(description=description, color=author.top_role.color)
    if author is not None:
        embed.set_author(name=author.display_name, icon_url=author.avatar_url)

    for field_name, field_content in kwargs.items():
        embed.add_field(name=field_name, value=field_content, inline=True)

    return embed


def time_ago(target):
    return timesince.format(target)


def check_create_directory(directory_path: str):
    """
    Creates directory if it doesn't exist
    :param directory_path: str example 'dir/"
    """
    if not Path(directory_path).is_dir():
        logger.info(f"Creating directory {directory_path}")
        os.mkdir(directory_path)
