"""Optional per-site ssg.toml config file."""
import os
import tomllib

CONFIG_FILENAME = "ssg.toml"


class ConfigError(Exception):
    pass


def load_config(site_dir):
    """Return the parsed ssg.toml at site_dir's root, or {} if absent."""
    path = os.path.join(site_dir, CONFIG_FILENAME)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"malformed {path}: {e}") from e
