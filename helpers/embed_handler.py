from discord import Embed, Colour, Member
from helpers import misc


def _simple_embed(message: str, title: str, color: Colour) -> Embed:
    embed = Embed(title=title, description=message, color=color)
    return embed


def info_embed(message: str, member: Member, title: str = Embed.Empty) -> Embed:
    embed = Embed(title=title, description=message, color=member.top_role.colour)
    return embed


def success_embed(message: str, member: Member) -> Embed:
    return _simple_embed(message, "Success", member.top_role.colour)


def warning_embed(message: str) -> Embed:
    return _simple_embed(message, "Warning", Colour.dark_gold())


def failure_embed(message: str) -> Embed:
    return _simple_embed(message, "Failure", Colour.red())


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
