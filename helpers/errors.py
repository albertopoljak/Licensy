from discord.errors import DiscordException


class RoleNotFound(DiscordException):
    def __init__(self, message):
        self.message = message
