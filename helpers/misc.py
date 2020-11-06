import os
import logging
from pathlib import Path

import timeago as timesince
from discord import Embed, Colour


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
    for _ in range(0, progress):
        constructed += element_full
    for _ in range(progress, size):
        constructed += element_emtpy
    constructed += limiters
    if message is None:
        constructed = f"{constructed} {percent:.2f}%"
    else:
        constructed = f"{constructed} {message}"
    return constructed


def get_top_role_color(member):
    """
    Tries to get member top role color and if fails return Embed.Empty - This makes it work in DMs.
    If the top role has default role color then returns green color (marking success)
    """
    try:
        color = member.top_role.color
        if color == Colour.default():
            return Colour.green()
        else:
            return member.top_role.color
    except AttributeError:
        # Fix for DMs
        return Embed.Empty


def construct_embed(author, description=None, **kwargs):
    embed = Embed(description=description, color=get_top_role_color(author))
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


def maximize_size(message: str):
    return (message[:1980] + "...too long") if len(message) > 1980 else message


def tail(n=1):
    """
    Tail a file and get X lines from the end
    Source(modified to work): https://stackoverflow.com/a/57277212/11311072
    """
    with open("logs/log.txt", "r", errors="backslashreplace") as f:
        assert n >= 0
        pos, lines = n + 1, []

        # set file pointer to end

        f.seek(0, os.SEEK_END)

        is_file_small = False

        while len(lines) <= n:
            try:
                f.seek(f.tell() - pos, os.SEEK_SET)
            except ValueError:
                # lines greater than file seeking size
                # seek to start
                f.seek(0, os.SEEK_SET)
                is_file_small = True
            finally:
                lines = f.readlines()
                if is_file_small:
                    break

            pos += 1

        lines.reverse()
        return lines


# Embeds are not monospaced so we need to use spaces to make different lines "align"
# But discord doesn't like spaces and strips them down, however it doesn't do that with zero
# width space.
# Remember that when copy pasting it will copy ZWS too and can cause problems because the
# copied string is visually identical BUT it's not the same!
# Example copy pasting from help command will result in "Command not found." even tho it's
# visually the same command string! So in short in help command don't do this format:
# prefix + command_name as copy pasting will not work, however just command_name name is fine.
embed_space = "\u200b "
