from typing import Union
from discord import Embed, Colour, Member, User
from helpers import misc


def simple_embed(message: str, title: str, color: Colour) -> Embed:
    embed = Embed(title=title, description=message, color=color)
    return embed


def info(message: str, member: Union[Member, User, None], title: str = Embed.Empty) -> Embed:
    """
    Constructs info embed with custom title and description.
    Color depends on passed member top role color.
    :param message: embed description
    :param member: member/user object to get the color of it's top role from
    :param title: title of embed
    :return: Embed object
    """
    embed = Embed(title=title, description=message, color=misc.get_top_role_color(member))
    return embed


def success(message: str, member: Union[Member, User, None]) -> Embed:
    """
    Constructs success embed with fixed title:Success and color depending
    on passed member top role color.
    :param message: embed description
    :param member: member object to get the color of it's top role from,
                   usually our bot member object from the specific guild.
    :return: Embed object
    """
    return simple_embed(message, "Success", misc.get_top_role_color(member))


def warning(message: str) -> Embed:
    """
    Constructs warning embed with fixed title:Warning and color:gold
    :param message: embed description
    :return: Embed object
    """
    return simple_embed(message, "Warning", Colour.dark_gold())


def failure(message: str) -> Embed:
    """
    Constructs failure embed with fixed title:Failure and color:red
    :param message: embed description
    :return: Embed object
    """
    return simple_embed(message, "Failure", Colour.red())