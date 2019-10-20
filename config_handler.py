import logging
import json

logger = logging.getLogger(__name__)


class ConfigHandler:
    CONFIG_PATH = "config.json"

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Loads config and checks fo validity of json file.
        :return: dict loaded json data
        """
        try:
            with open(ConfigHandler.CONFIG_PATH) as cfg:
                data = json.load(cfg)
                return data
        except FileNotFoundError as e:
            logger.critical(f"Config json file was not found: {ConfigHandler.CONFIG_PATH} : {e}")
        except ValueError as e:
            logger.critical(f"Invalid config json: {e}")
        except KeyError as e:
            logger.critical(f"Invalid json config configuration: {e}")
        except Exception as e:
            logger.critical(f"Can't load json config: {e}")

    def reload_config(self):
        """
        Reloads config.
        If you change the config manually while the bot is running you need to call this method
        so the values are updated in memory.
        """
        self.config = self._load_config()

    def get_description(self) -> str:
        return self.get_key("bot_description")

    def get_default_prefix(self) -> str:
        return self.get_key("default_prefix")

    def get_developers(self) -> dict:
        return self.get_key("developers")

    def get_developer_log_channel_id(self) -> int:
        return int(self.get_key("developer_log_channel_id"))

    def get_support_channel_invite(self) -> str:
        return self.get_key("support_channel_invite")

    def get_maximum_unused_guild_licences(self) -> int:
        return self.get_key("maximum_unused_guild_licences")

    def get_top_gg_api_key(self) -> str:
        return self.get_key("top_gg_api_key")

    def get_token(self) -> str:
        return self.get_key("token")

    def get_key(self, key):
        try:
            return self.config[key]
        except KeyError as e:
            error_message = f"Key '{key}' not found in json config! {e}"
            logger.critical(error_message)
            raise KeyError(error_message)

    def update_key(self, key, value):
        try:
            self.config[key] = value
            with open(ConfigHandler.CONFIG_PATH, "w") as cfg:
                # key vars are used to prettify outputted json
                json.dump(self.config, cfg, indent=4, sort_keys=True)
        except KeyError as e:
            logger.critical(f"Key '{key}' not found in json config! Can't update config! {e}")
        except TypeError as e:
            logger.critical(f"Unable to serialize the object {e}")
        except Exception as e:
            logger.critical(f"Unable to update json key {key} to value {value}: {e}")
