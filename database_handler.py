import aiosqlite
from pathlib import Path
from datetime import datetime
from helpers import licence_generator
from helpers.errors import DefaultGuildRoleNotSet


class DatabaseHandler:
    DB_PATH = "databases/"
    DB_EXTENSION = ".sqlite3"

    @classmethod
    async def create(cls, db_name: str = "main", db_backup_prefix: str = "backup"):
        """"
        Can't use await in __init__ so we create a factory pattern.
        To correctly create this object you need to call :
            await DatabaseHandler.create()

        """
        self = DatabaseHandler()
        self.db_name = db_name
        self.db_backup_prefix = db_backup_prefix
        self.connection = await self._get_connection()
        print("Connection to database established.")
        return self

    def __init__(self):
        self.db_name = None
        self.db_backup_prefix = None
        self.connection = None

    async def _get_connection(self) -> aiosqlite.core.Connection:
        """
        Returs a connection to the db, if db doesn't exist create new
        :return: aiosqlite.core.Connection
        """
        path = DatabaseHandler._construct_path(self.db_name)
        if Path(path).is_file():
            conn = await aiosqlite.connect(path)
            return conn
        else:
            print("Database not found! Creating fresh ...")
            return await DatabaseHandler._create_database(path)

    @staticmethod
    def _construct_path(db_name: str) -> str:
        return DatabaseHandler.DB_PATH + db_name + DatabaseHandler.DB_EXTENSION

    @staticmethod
    async def _create_database(path: str) -> aiosqlite.core.Connection:
        """
        :param path: path where database will be created, including file name and extension
        :return: aiosqlite.core.Connection
        """
        conn = await aiosqlite.connect(path)
        await conn.execute("CREATE TABLE GUILDS "
                           "("
                           "GUILD_ID TEXT PRIMARY KEY, "
                           "PREFIX TEXT CHECK(PREFIX IS NULL OR LENGTH(PREFIX) <= 3), "
                           "ENABLE_LOG_CHANNEL TINYINT DEFAULT 0, "
                           "LOG_CHANNEL_ID TEXT, "
                           "DEFAULT_LICENSE_ROLE_ID TEXT, "
                           "DEFAULT_LICENSE_DURATION_HOURS UNSIGNED BIG INT DEFAULT 720"
                           ")"
                           )

        await conn.execute("CREATE TABLE LICENSED_MEMBERS "
                           "("
                           "MEMBER_ID TEXT, "
                           "GUILD_ID TEXT, "
                           "EXPIRATION_DATE DATE, "
                           "LICENSED_ROLE_ID TEXT, "
                           "UNIQUE(MEMBER_ID, LICENSED_ROLE_ID)"
                           ")"
                           )

        await conn.execute("CREATE TABLE GUILD_LICENSES "
                           "("
                           "LICENSE TEXT PRIMARY KEY, "
                           "GUILD_ID TEXT, "
                           "LICENSED_ROLE_ID TEXT, "
                           "LICENSE_DURATION_HOURS UNSIGNED BIG INT"
                           ")"
                           )

        await conn.commit()
        print("Database successfully created!")
        return conn

    # TABLE GUILDS #######################################################################

    async def get_guild_prefix(self, guild_id: int) -> str:
        query = "SELECT PREFIX FROM GUILDS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def change_guild_prefix(self, guild_id: int, prefix: str):
        query = "UPDATE GUILDS SET PREFIX=? WHERE GUILD_ID=?"
        await self.connection.execute(query, (prefix, guild_id))
        await self.connection.commit()

    async def get_default_guild_license_role_id(self, guild_id: int) -> int:
        """
        Gets the default license role id from specific guild.
        This role will be used as link when no role argument is passed in 'generate' command
        :return: int default license role id
        :raise: DefaultGuildRoleNotSet if it's None

        """
        query = "SELECT DEFAULT_LICENSE_ROLE_ID FROM GUILDS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            try:
                return int(row[0])
            except TypeError:
                raise DefaultGuildRoleNotSet("Default guild license not set!")

    async def get_default_guild_license_duration_hours(self, guild_id: int) -> int:
        """
        Gets the default license duration from specific guild.
        :return: int representing hours of license duration

        """
        query = "SELECT DEFAULT_LICENSE_DURATION_HOURS FROM GUILDS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return int(row[0])

    # TABLE LICENSED_MEMBERS #############################################################

    async def add_new_licensed_member(self, member_id: int, guild_id: int,
                                      expiration_date: datetime, licensed_role_id: int):
        """
        :param member_id:
        :param guild_id:
        :param expiration_date:
        :param licensed_role_id:
        :return:

        """
        query = "INSERT INTO LICENSED_MEMBERS(MEMBER_ID, GUILD_ID, EXPIRATION_DATE, LICENSED_ROLE_ID) VALUES(?,?,?,?)"
        await self.connection.execute(query, (member_id, guild_id, expiration_date, licensed_role_id))
        await self.connection.commit()

    async def delete_licensed_member(self, member_id: int, licensed_role_id: int):
        """
        Called when member licensed role has expired
        The member row is deleted from table LICENSED_MEMBERS.
        MEMBER_ID and LICENSED_ROLE_ID are unique so we only need that to differentiate

        """
        delete_query = "DELETE FROM LICENSED_MEMBERS WHERE MEMBER_ID=? AND LICENSED_ROLE_ID=?"
        await self.connection.execute(delete_query, (member_id, licensed_role_id))
        await self.connection.commit()

    async def get_member_license_expiration_date(self, member_id: int, licensed_role_id: int) -> str:
        query = "SELECT EXPIRATION_DATE FROM LICENSED_MEMBERS WHERE MEMBER_ID=? AND LICENSED_ROLE_ID=?"
        async with self.connection.execute(query, (member_id, licensed_role_id)) as cursor:
            row = await cursor.fetchone()
            return row[0]

    # TABLE GUILD_LICENSES ###############################################################

    async def get_license_role_id(self, license: str) -> int:
        """
        Returns licensed role id that the param license is linked to
        :param license: license the role is linked to
        :return: int license role id

        """
        query = "SELECT LICENSED_ROLE_ID FROM GUILD_LICENSES WHERE LICENSE=?"
        async with self.connection.execute(query, (license,)) as cursor:
            row = await cursor.fetchone()
            return int(row[0])

    async def get_license_duration_hours(self, license):
        """
        :param license: It's unique so no need to pass any additional argument
        :return: int representing license duration in hours
        """
        query = "SELECT LICENSE_DURATION_HOURS FROM GUILD_LICENSES WHERE LICENSE=?"
        async with self.connection.execute(query, (license,)) as cursor:
            row = await cursor.fetchone()
            return int(row[0])

    async def generate_guild_licenses(self, number: int, guild_id: int,
                                      license_role_id: int, license_duration: int) -> list:
        """
        :param number: int larger than 0, number of licenses to generate
        :param guild_id: int guild id. Needed to differentiate guilds even though licenses are unique
                         for example to avoid members activating a valid license from one guild into
                         another guild (where linked roles don't exist).
        :param license_role_id: role to link to the license
        :param license_duration: int representing license duration in hours
        :return: list of all generated licenses

        """
        licenses = licence_generator.generate(number)
        query = """INSERT INTO GUILD_LICENSES(LICENSE, GUILD_ID, LICENSED_ROLE_ID, LICENSE_DURATION_HOURS) 
                   VALUES(?,?,?,?)"""
        for license in licenses:
            await self.connection.execute(query, (license, guild_id, license_role_id, license_duration))
        await self.connection.commit()
        return licenses

    async def delete_license(self, license: str):
        """
        Called for example when member has redeemed license.
        The license is deleted from table GUILD_LICENSES.
        Guild ID is not needed since licenses are unique.
        :param license: license to delete

        """
        delete_query = "DELETE FROM GUILD_LICENSES WHERE LICENSE=?"
        await self.connection.execute(delete_query, (license,))
        await self.connection.commit()

    async def get_guild_licenses(self, number: int, guild_id: int, license_role_id: int) -> list:
        """
        Returns list of licenses that are linked to license_role_id role.
        :param number: int larger than 0, max number of licenses to return
        :param guild_id: int guild id. Needed to differentiate guilds even though licenses are unique
                         for example to avoid members activating a valid license from one guild into
                         another guild (where linked roles don't exist).
        :param license_role_id: we get only those licenses that are linked to this role id
        :return: list of licenses

        """
        licenses = []
        query = """SELECT LICENSE, LICENSE_DURATION_HOURS FROM GUILD_LICENSES
                   WHERE GUILD_ID=? AND LICENSED_ROLE_ID=? LIMIT ?"""
        async with self.connection.execute(query, (guild_id, license_role_id, number)) as cursor:
            rows = await cursor.fetchall()
            # rows format:
            # [('license1', license_duration_int_hours)]
            for row in rows:
                licenses.append(row[0])

        return licenses

    async def is_valid_license(self, license: str, guild_id: int) -> bool:
        """
        :param license: License to check
        :param guild_id: int guild id. Needed to differentiate guilds even though licenses are unique
                         for example to avoid members activating a valid license from one guild into
                         another guild (where linked roles don't exist).
        :return: True if license is valid, False otherwise

        """
        query = "SELECT LICENSE FROM GUILD_LICENSES WHERE LICENSE=? AND GUILD_ID=?"
        async with self.connection.execute(query, (license, guild_id)) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                return True
        return False
