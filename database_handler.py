import logging
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Union

from helpers import misc
from helpers import licence_helper
from helpers.errors import DefaultGuildRoleNotSet, DatabaseMissingData


logger = logging.getLogger(__name__)


class DatabaseHandler:
    DB_PATH = "databases/"
    DB_EXTENSION = ".sqlite3"

    @classmethod
    async def create_instance(cls, db_name: str = "main"):
        """"
        Can't use await in __init__ so we create a factory pattern.
        To correctly create this object you need to call :
            await DatabaseHandler.create_instance()

        """
        self = DatabaseHandler()
        self.db_name = db_name
        self.connection = await self._get_connection()
        logger.info("Connection to database established.")
        return self

    def __init__(self):
        self.db_name = None
        self.connection = None

    async def _get_connection(self) -> aiosqlite.core.Connection:
        """
        Returns a connection to the db, if db doesn't exist create new
        :return: aiosqlite.core.Connection
        """
        path = DatabaseHandler._construct_path(self.db_name)
        if Path(path).is_file():
            conn = await aiosqlite.connect(path)
            return conn
        else:
            logger.warning("Database not found! Creating fresh ...")
            misc.check_create_directory(DatabaseHandler.DB_PATH)
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
                           "PREFIX TEXT CHECK(PREFIX IS NULL OR LENGTH(PREFIX) <= 5), "
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
        logger.info("Database successfully created!")
        return conn

    async def update_database(self, query: str, *args):
        await self.connection.execute(query, args)
        await self.connection.commit()

    # TABLE GUILDS #######################################################################
    async def setup_new_guild(self, guild_id: int, default_prefix: str):
        insert_guild_query = "INSERT INTO GUILDS(GUILD_ID, PREFIX) VALUES(?,?)"
        await self.update_database(insert_guild_query, guild_id, default_prefix)

    async def get_guild_prefix(self, guild_id: int) -> str:
        query = "SELECT PREFIX FROM GUILDS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def get_all_guild_ids(self):
        """
        :return: a tuple of all guild ids (ints)

        """
        query = "SELECT GUILD_ID FROM GUILDS"
        async with self.connection.execute(query) as cursor:
            results = await cursor.fetchall()
            return tuple(int(guild_id[0]) for guild_id in results)

    async def change_guild_prefix(self, guild_id: int, prefix: str):
        """
        :param guild_id: int id of guild to change the prefix to in the database
        :param prefix: str prefix to change to. Length is limited by table GUILDS layout (max 5 chars)
        :raise: IntegrityError if the prefix has too many chars (max 5)
        """
        query = "UPDATE GUILDS SET PREFIX=? WHERE GUILD_ID=?"
        await self.update_database(query, prefix, guild_id)

    async def change_default_guild_role(self, guild_id: int, role_id: int):
        query = "UPDATE GUILDS SET DEFAULT_LICENSE_ROLE_ID=? WHERE GUILD_ID=?"
        await self.update_database(query, role_id, guild_id)

    async def change_default_license_expiration(self, guild_id: int, expiration_hours: int):
        query = "UPDATE GUILDS SET DEFAULT_LICENSE_DURATION_HOURS=? WHERE GUILD_ID=?"
        await self.update_database(query, expiration_hours, guild_id)

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
                raise DefaultGuildRoleNotSet("Default guild license not set!\n\n"
                                             "For more information call command:\n"
                                             "{prefix}help default_role\n\n"
                                             "If still in doubt call:\n"
                                             "{prefix}help")

    async def get_default_guild_license_duration_hours(self, guild_id: int) -> int:
        """
        Gets the default license duration from specific guild.
        :return: int representing hours of license duration

        """
        query = "SELECT DEFAULT_LICENSE_DURATION_HOURS FROM GUILDS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            #
            if not row:
                # License duration has default value.
                # So if this is None it means the guild is not found in database.
                raise DatabaseMissingData(f"Guild {guild_id} not found in database!")
            return int(row[0])

    async def get_guild_info(self, guild_id: int) -> Tuple[str, str, int]:
        """
        :param guild_id:
        :return: tuple(str prefix, str role_id, int expiration hours)
        """
        query = "SELECT * FROM GUILDS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            # ('guild_id', 'prefix', 0, None, 'role_id', hours)
            return row[1], row[4], row[5]

    # TABLE LICENSED_MEMBERS #############################################################

    async def add_new_licensed_member(self, member_id: int, guild_id: int,
                                      expiration_date: datetime, licensed_role_id: int):
        query = "INSERT INTO LICENSED_MEMBERS(MEMBER_ID, GUILD_ID, EXPIRATION_DATE, LICENSED_ROLE_ID) VALUES(?,?,?,?)"
        await self.update_database(query, member_id, guild_id, expiration_date, licensed_role_id)

    async def delete_licensed_member(self, member_id: int, licensed_role_id: int):
        """
        Called when member licensed role has expired
        The member row is deleted from table LICENSED_MEMBERS.
        MEMBER_ID and LICENSED_ROLE_ID are unique so we only need that to differentiate

        """
        delete_query = "DELETE FROM LICENSED_MEMBERS WHERE MEMBER_ID=? AND LICENSED_ROLE_ID=?"
        await self.update_database(delete_query, member_id, licensed_role_id)

    async def get_member_license_expiration_date(self, member_id: int, licensed_role_id: int) -> str:
        query = "SELECT EXPIRATION_DATE FROM LICENSED_MEMBERS WHERE MEMBER_ID=? AND LICENSED_ROLE_ID=?"
        async with self.connection.execute(query, (member_id, licensed_role_id)) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                return row[0]
            else:
                raise DatabaseMissingData(f"ID {member_id} doesn't exists in database table LICENSED_MEMBERS.")

    async def get_member_data(self, guild_id: int, member_id: int) -> List[Tuple]:
        """
        Return type:
        [(), ()...]
        Note that returned LICENSED_ROLE_ID is string
        """
        query = "SELECT LICENSED_ROLE_ID, EXPIRATION_DATE FROM LICENSED_MEMBERS WHERE GUILD_ID=? AND MEMBER_ID=?"
        async with self.connection.execute(query, (guild_id, member_id)) as cursor:
            results = await cursor.fetchall()
            if results is not None:
                return results
            else:
                raise DatabaseMissingData(f"No active licenses for member {member_id} in guild {guild_id}.")

    async def get_guild_licensed_roles_total_count(self, guild_id: int) -> int:
        query = "SELECT COUNT(*) FROM LICENSED_MEMBERS WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_licensed_roles_total_count(self) -> int:
        query = "SELECT COUNT(*) FROM LICENSED_MEMBERS"
        async with self.connection.execute(query) as cursor:
            result = await cursor.fetchone()
            return result[0]

    # TABLE GUILD_LICENSES ###############################################################

    async def get_license_data(self, license: str) -> Union[Tuple[int, int], None]:
        """
        Returns licensed role id that the param license is linked to
        :param license: license the role is linked to
        :return: tuple(int guild id, int license role id)

        """
        query = "SELECT GUILD_ID, LICENSED_ROLE_ID FROM GUILD_LICENSES WHERE LICENSE=?"
        async with self.connection.execute(query, (license,)) as cursor:
            row = await cursor.fetchone()
            # TODO: Temporal quick fix. Refactor
            if row is None:
                return None
            else:
                return int(row[0]), int(row[1])

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
        licenses = licence_helper.generate_multiple(number)
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
        But if deleting from withing the guild better to call is_valid_license beforehand
        to prevent deletion of other guild licenses in other guilds.
        :param license: license to delete

        """
        delete_query = "DELETE FROM GUILD_LICENSES WHERE LICENSE=?"
        await self.update_database(delete_query, license)

    async def get_guild_licenses(self, number: int, guild_id: int, license_role_id: int) -> list:
        """
        Returns list of licenses that are linked to license_role_id role and their duration time.
        :param number: int larger than 0, max number of licenses to return
        :param guild_id: int guild id. Needed to differentiate guilds even though licenses are unique
                         for example to avoid members activating a valid license from one guild into
                         another guild (where linked roles don't exist).
        :param license_role_id: we get only those licenses that are linked to this role id
        :return: List of tuples in format [('license', license_duration_int_hours)]

        """
        query = """SELECT LICENSE, LICENSE_DURATION_HOURS FROM GUILD_LICENSES
                   WHERE GUILD_ID=? AND LICENSED_ROLE_ID=? LIMIT ?"""
        async with self.connection.execute(query, (guild_id, license_role_id, number)) as cursor:
            return await cursor.fetchall()

    async def get_guild_license_total_count(self, guild_id: int) -> int:
        query = "SELECT COUNT(*) FROM GUILD_LICENSES WHERE GUILD_ID=?"
        async with self.connection.execute(query, (guild_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_stored_license_total_count(self) -> int:
        query = "SELECT COUNT(*) FROM GUILD_LICENSES"
        async with self.connection.execute(query) as cursor:
            result = await cursor.fetchone()
            return result[0]

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

    async def get_random_licenses(self, guild_id: int, amount: int):
        query = """SELECT LICENSE, LICENSED_ROLE_ID, LICENSE_DURATION_HOURS FROM GUILD_LICENSES
                   WHERE GUILD_ID=? ORDER BY RANDOM() LIMIT ?"""
        async with self.connection.execute(query, (guild_id, amount)) as cursor:
            return await cursor.fetchall()

    async def remove_all_stored_guild_licenses(self, guild_id: int):
        query = "DELETE FROM GUILD_LICENSES WHERE GUILD_ID=?"
        await self.update_database(query, guild_id)

    # ALL TABLES #########################################################################

    async def remove_all_guild_data(self, guild_id: int, guild_table_too=False):
        queries = ["DELETE FROM LICENSED_MEMBERS WHERE GUILD_ID=?",
                   "DELETE FROM GUILD_LICENSES WHERE GUILD_ID=?"]
        if guild_table_too:
            queries.append("DELETE FROM GUILDS WHERE GUILD_ID=?")
        for query in queries:
            await self.connection.execute(query, (guild_id,))

        await self.connection.commit()

    async def remove_all_guild_role_data(self, role_id: int):
        queries = ["DELETE FROM LICENSED_MEMBERS WHERE LICENSED_ROLE_ID=?",
                   "DELETE FROM GUILD_LICENSES WHERE LICENSED_ROLE_ID=?"]
        for query in queries:
            await self.connection.execute(query, (role_id,))

        await self.connection.commit()
