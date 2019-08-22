from discord import Embed
from helpers import misc


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
