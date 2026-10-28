"""The effective Mermaid config, shared by the browser preview and mmdc."""

import json
import os


class ConfigError(Exception):
    """The user's Mermaid config file can't be used."""


def load_effective_config(default_json: str, user_path: str) -> dict:
    """The bundled default, or the user's file in its place (no merging)."""
    if not user_path:
        return json.loads(default_json)
    path = os.path.expanduser(user_path)
    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise ConfigError("mermaid_config file not found: " + path) from None
    except (OSError, ValueError) as e:
        raise ConfigError("mermaid_config file can't be read as JSON: {} ({})".format(path, e)) from None
    if not isinstance(config, dict):
        raise ConfigError("mermaid_config file must hold a JSON object: " + path)
    return config
