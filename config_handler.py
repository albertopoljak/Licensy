import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigHandler:
    """
    Class that handles interaction with config json files.
    Values can be accessed with bracket notation self[key]
    """
    CONFIG_DIR = Path("")

    def __init__(self, config_name: str):
        """
        :param config_name: name of the config file without the suffix.
        """
        self._path = ConfigHandler.CONFIG_DIR / (config_name + ".json")
        self._config = self._load_config()

    def __repr__(self):
        return f"{json.dumps(self._config, indent=4, sort_keys=True)}"

    def _load_config(self) -> dict:
        """
        Loads config and checks fo validity of json file.
        :return: dict loaded json data
        """
        try:
            with open(self._path) as cfg:
                data = json.load(cfg)
                return data
        except FileNotFoundError as e:
            logger.critical(f"Config json file was not found: {self._path} : {e}")
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
        self._config = self._load_config()

    def __getitem__(self, key: str):
        return self._get_key(key)

    def _get_key(self, key: str):
        try:
            return self._config[key]
        except KeyError as e:
            error_message = f"Key '{key}' not found in json config! {e}"
            logger.critical(error_message)
            raise KeyError(error_message)

    def update_key(self, key: str, value):
        try:
            self._config[key] = value
            with open(self._path, "w") as cfg:
                json.dump(self._config, cfg, indent=4, sort_keys=True)
        except TypeError as e:
            logger.critical(f"Unable to serialize the object {e}")
        except Exception as e:
            logger.critical(f"Unable to update json key {key} to value {value}: {e}")
