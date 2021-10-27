"""
Script to backup your guild data if you need to keep it safe or to migrate.
If you need different functionality you're free to download it and modify it however you want.
Example usage:
Backup(JSONBackup()).backup(123456789)
above will get you naive dates (without timezone). If you know timezone of server the bot is in you can use:
Backup(JSONBackup()).backup(123456789, server_timezone=timezone(timedelta(hours=-8)))
"""
import json
import sqlite3
from typing import Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class BackupAdapter(ABC):
    @abstractmethod
    def format(self, data: dict) -> str:
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        ...

    @abstractmethod
    def save(self, data: Any, *, file_name: str) -> None:
        ...


class JSONBackup(BackupAdapter):
    def format(self, data: dict) -> Any:
        return json.dumps(data, indent=2)

    @property
    def file_extension(self) -> str:
        return "json"

    def save(self, data: str, *, file_name: str) -> None:
        with open(file_name + self.file_extension, "w") as f:
            f.write(data)


class SqliteBackup(BackupAdapter):
    def format(self, data: dict) -> dict:
        return data

    @property
    def file_extension(self) -> str:
        return "sqlite3"

    def save(self, data: dict, *, file_name: str) -> None:
        self._create_db_tables(file_name=file_name)
        self._save_db_data(file_name, data)

    @classmethod
    def _create_db_tables(cls, *,  file_name: str):
        con = sqlite3.connect(file_name)
        cur = con.cursor()
        cur.execute("CREATE TABLE GUILDS"
                    "("
                    "GUILD_ID TEXT PRIMARY KEY, "
                    "PREFIX TEXT CHECK(PREFIX IS NULL OR LENGTH(PREFIX) <= 5), "
                    "ENABLE_LOG_CHANNEL TINYINT DEFAULT 0, "
                    "LOG_CHANNEL_ID TEXT, "
                    "DEFAULT_LICENSE_ROLE_ID TEXT, "
                    "DEFAULT_LICENSE_DURATION_HOURS UNSIGNED BIG INT DEFAULT 720"
                    ")"
                    )

        cur.execute("CREATE TABLE LICENSED_MEMBERS"
                    "("
                    "MEMBER_ID TEXT,"
                    "GUILD_ID TEXT,"
                    "EXPIRATION_DATE DATE,"
                    "LICENSED_ROLE_ID TEXT,"
                    "UNIQUE(MEMBER_ID, LICENSED_ROLE_ID)"
                    ")"
                    )

        cur.execute("CREATE TABLE GUILD_LICENSES"
                    "("
                    "LICENSE TEXT PRIMARY KEY,"
                    "GUILD_ID TEXT,"
                    "LICENSED_ROLE_ID TEXT,"
                    "LICENSE_DURATION_HOURS UNSIGNED BIG INT"
                    ")"
                    )

        con.commit()
        con.close()

    @classmethod
    def _save_db_data(cls, file_name: str,  data: dict):
        con = sqlite3.connect(file_name)
        cur = con.cursor()

        cur.execute(
            "INSERT INTO GUILDS("
            "GUILD_ID,"
            "PREFIX,"
            "ENABLE_LOG_CHANNEL,"
            "LOG_CHANNEL_ID,"
            "DEFAULT_LICENSE_ROLE_ID,"
            "DEFAULT_LICENSE_DURATION_HOURS"
            ") VALUES(?,?,?,?,?,?)",
            (*data["GUILDS"].values(),),
        )

        for licensed_member_sub_dict in data["LICENSED_MEMBERS"].values():
            licensed_member_data = [*licensed_member_sub_dict.values()]
            cur.execute(
                "INSERT INTO LICENSED_MEMBERS("
                "MEMBER_ID,"
                "GUILD_ID,"
                "EXPIRATION_DATE,"
                "LICENSED_ROLE_ID"
                ") VALUES(?,?,?,?)",
                (*licensed_member_data,),
            )

        for guild_license_sub_dict in data["GUILD_LICENSES"].values():
            guild_license_data = [*guild_license_sub_dict.values()]
            cur.execute(
                "INSERT INTO GUILD_LICENSES("
                "LICENSE,"
                "GUILD_ID,"
                "LICENSED_ROLE_ID,"
                "LICENSE_DURATION_HOURS"
                ") VALUES(?,?,?,?)",
                (*guild_license_data,),
            )

        con.commit()
        con.close()


class Backup:
    DATABASE = "main.sqlite3"

    def __init__(self, backup_format: BackupAdapter):
        self._conn = sqlite3.connect(self.DATABASE)
        self._backup_format = backup_format

    def backup(self, guild_id: int, *, file_name: str = "backup", server_timezone: timezone = None):
        """
        :param guild_id: int ID you want to backup from the database
        :param file_name: str of file name to save backup data to. Defaults to "backup"
        :param server_timezone: optional timezone. Licensy backend code saves dates as naive datetimes (><) but if you
        pass this param then extracted datetimes will be converted to this timezone. If not passed extracted dates will
        be naive.
        """
        licensed_members = self.get_licensed_members_table(guild_id)
        if server_timezone is not None:
            self._naive_dates_to_tz(licensed_members, server_timezone)

        data = {
            "GUILDS": self.get_guild_table(guild_id),
            "LICENSED_MEMBERS": licensed_members,
            "GUILD_LICENSES": self.get_guild_licenses_table(guild_id)
        }
        formatted_data = self._backup_format.format(data)
        self._backup_format.save(formatted_data, file_name=f"{file_name}_{guild_id}.{self._backup_format.file_extension}")

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

    def get_licensed_members_table(self, guild_id: int,) -> Dict[int, Dict[str, Any]]:
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

    @classmethod
    def _naive_dates_to_tz(cls, licensed_members_data: dict, server_timezone: timezone):
        for sub_dict in licensed_members_data.values():
            naive_datetime = datetime.strptime(sub_dict["EXPIRATION_DATE"], "%Y-%m-%d %H:%M:%S.%f")
            proper_datetime = naive_datetime.replace(tzinfo=server_timezone)
            sub_dict["EXPIRATION_DATE"] = str(proper_datetime)
