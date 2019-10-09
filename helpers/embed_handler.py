from discord import Embed, Colour, Member
from helpers import misc


def simple_embed(message: str, title: str, color: Colour) -> Embed:
    embed = Embed(title=title, description=message, color=color)
    return embed


def info_embed(message: str, member: Member, title: str = Embed.Empty) -> Embed:
    """
    Constructs success embed with custom title and description.
    Color depends on passed member top role color.
    :param message: embed description
    :param member: member object to get the color of it's top role from
    :param title: title of embed
    :return: Embed object

    """
    embed = Embed(title=title, description=message, color=misc.get_top_role_color(member))
    return embed


def success_embed(message: str, member: Member) -> Embed:
    """
    Constructs success embed with fixed title:Success and color depending
    on passed member top role color.
    This will be used quite common so no sense to hard-code green colour since
    we want most of the messages the bot sends to be the color of it's top role.
    :param message: embed description
    :param member: member object to get the color of it's top role from,
                   usually our bot member object from the specific guild.
    :return: Embed object

    """
    return simple_embed(message, "Success", misc.get_top_role_color(member))


def warning_embed(message: str) -> Embed:
    """
    Constructs warning embed with fixed title:Warning and color:gold
    :param message: embed description
    :return: Embed object

    """
    return simple_embed(message, "Warning", Colour.dark_gold())


def failure_embed(message: str) -> Embed:
    """
    Constructs failure embed with fixed title:Failure and color:red
    :param message: embed description
    :return: Embed object

    """
    return simple_embed(message, "Failure", Colour.red())


def log_embed(*messages, ctx=None, title="Log"):
    embed = Embed(title=title)
    for index, message in enumerate(messages):
        embed.add_field(name=f"Message {index+1}:", value=message, inline=True)
    if ctx is not None:
        footer = f"Guild: {ctx.guild.id}    Author: {ctx.author}"
        embed.set_footer(text=footer)
    return embed


def traceback_embed(traceback_last):
    # Allow passing both list and string
    if type(traceback_last) is list:
        traceback_last = " ".join(traceback_last)
    description = misc.maximize_size(traceback_last)
    embed = Embed(title="Traceback", description=description)
    return embed
