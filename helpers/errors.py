from discord.errors import DiscordException


class RoleNotFound(DiscordException):
    def __init__(self, message):
        self.message = message


class DefaultGuildRoleNotSet(DiscordException):
    def __init__(self, message):
        self.message = message


class DatabaseMissingData(DiscordException):
    def __init__(self, message):
        self.message = message
