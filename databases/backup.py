"""
Script to backup your guild data if you need to keep it safe or to migrate.

If you need different functionality you're free to download it and modify it however you want.
"""
import json
import sqlite3
from typing import Dict, Any
from abc import ABC, abstractmethod


class BackupAdapter(ABC):
    @abstractmethod
    def format(self, data: dict) -> str:
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        ...


class JSONBackup(BackupAdapter):
    def format(self, data: dict) -> str:
        return json.dumps(data, indent=2)

    @property
    def file_extension(self) -> str:
        return ".json"


class Backup:
    DATABASE = "main.sqlite3"

    def __init__(self, backup_format: BackupAdapter):
        self._conn = sqlite3.connect(self.DATABASE)
        self._backup_format = backup_format

    def backup(self, guild_id: int, *, file_name: str = "backup"):
        data = {
            "GUILDS": self.get_guild_table(guild_id),
            "LICENSED_MEMBERS": self.get_licensed_members_table(guild_id),
            "GUILD_LICENSES": self.get_guild_licenses_table(guild_id)
        }
        text_format = self._backup_format.format(data)
        self._save(text_format, file_name=file_name)

    def _save(self, text: str, *, file_name: str) -> None:
        with open(file_name + self._backup_format.file_extension, "w") as f:
            f.write(text)

    def get_guild_table(self, guild_id) -> Dict[str, Any]:
        """
        Return format:
        {
            'GUILD_ID': 'id',
            'PREFIX': 'prefix',
            'ENABLE_LOG_CHANNEL': int,
            'LOG_CHANNEL_ID': Union[None, 'id'],
            'DEFAULT_LICENSE_ROLE_ID': Union[None, 'id'],
            'DEFAULT_LICENSE_DURATION_HOURS': int
        }
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM GUILDS WHERE GUILD_ID=?", (guild_id,))
        values = tuple(*cursor.fetchall())
        col_names = next(zip(*cursor.description))
        return {col_name: value for col_name, value in zip(col_names, values)}

    def get_licensed_members_table(self, guild_id: int) -> Dict[int, Dict[str, Any]]:
        """
        Bot was done in a way that timezone is not saved -.-
        So you'll get datetime but need to know what timezone your server/PC that is hosting the bot is in.

        {
            0: {
                "MEMBER_ID": "id",
                "GUILD_ID": "id",
                "EXPIRATION_DATE": "NAIVE datetime in format 2021-02-14 08:40:06.459694",
                "LICENSED_ROLE_ID": "id"
            },
            1:{...},
            2:{...},
            ...
            N:{...}
        }
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM LICENSED_MEMBERS WHERE GUILD_ID=?", (guild_id,))
        col_names = next(zip(*cursor.description))
        return_data = {}
        for i, row in enumerate(cursor.fetchall()):
            return_data[i] = {col_name: value for col_name, value in zip(col_names, row)}
        return return_data

    def get_guild_licenses_table(self, guild_id: int) -> Dict[int, Dict[str, Any]]:
        """
        Return data:
        {
            0:{
                "LICENSE": "string",
                "GUILD_ID": "id",
                "LICENSED_ROLE_ID": "id",
                "LICENSE_DURATION_HOURS": int
            },
            1:{...},
            2:{...},
            ...
            N:{...}
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM GUILD_LICENSES WHERE GUILD_ID=?", (guild_id,))
        col_names = next(zip(*cursor.description))
        return_data = {}
        for i, row in enumerate(cursor.fetchall()):
            return_data[i] = {col_name: value for col_name, value in zip(col_names, row)}
        return return_data
