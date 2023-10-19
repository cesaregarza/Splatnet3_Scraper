from __future__ import annotations

import configparser
import copy

from splatnet3_scraper.constants import (
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    TOKENS,
)
from splatnet3_scraper.query.configuration.callbacks import (
    f_token_url_callback,
    log_level_callback,
    session_token_callback,
)
from splatnet3_scraper.query.configuration.config_option import ConfigOption


class ConfigOptionHandler:
    """Manages a collection of configuration options.

    This class is used to manage a collection of configuration options. The
    ``_OPTIONS`` attribute contains essential options that are tightly coupled
    with the library. The ``_ADDITIONAL_OPTIONS`` attribute is used to store
    any additional attributes that the user may need. When first initialized,
    the class will create a reference dictionary that maps the option names to
    the option objects. This is used to look up options by name, including any
    deprecated names an option may have.
    """

    _BASE_OPTIONS = (
        ConfigOption(
            name=TOKENS.SESSION_TOKEN,
            default=None,
            callback=session_token_callback,
            section="Tokens",
            env_var="SESSION_TOKEN",
        ),
        ConfigOption(
            name=TOKENS.GTOKEN,
            default=None,
            section="Tokens",
            env_var="GTOKEN",
        ),
        ConfigOption(
            name=TOKENS.BULLET_TOKEN,
            default=None,
            section="Tokens",
            env_var="BULLET_TOKEN",
        ),
        ConfigOption(
            name="user_agent",
            default=DEFAULT_USER_AGENT,
            section="Options",
            env_var="SPLATNET3_USER_AGENT",
        ),
        ConfigOption(
            name="f_token_url",
            default=DEFAULT_F_TOKEN_URL,
            callback=f_token_url_callback,
            section="Options",
            deprecated_names=["f_gen", "ftoken_url"],
            env_var="F_TOKEN_URL",
        ),
        ConfigOption(
            name="export_path",
            default="",
            section="Options",
        ),
        ConfigOption(
            name="language",
            default="en-US",
            section="Options",
            env_var="SPLATNET3_LANGUAGE",
        ),
        ConfigOption(
            name="country",
            default="US",
            section="Options",
            env_var="SPLATNET3_COUNTRY",
        ),
        ConfigOption(
            "log_level",
            default="INFO",
            section="Logging",
            callback=log_level_callback,
            env_var="LOG_LEVEL",
        ),
        ConfigOption(
            "log_file",
            default=None,
            section="Logging",
            env_var="LOG_FILE",
        ),
    )

    def __init__(self, prefix: str | None = None) -> None:
        """Initializes the class.

        This method initializes the class and sets up the additional options
        attribute. It also builds the option reference dictionary.
        """
        # Make a copy of the base options so that we don't modify the original
        # class attribute
        self._OPTIONS = copy.deepcopy(self._BASE_OPTIONS)
        self._ADDITIONAL_OPTIONS: list[ConfigOption] = []
        self.unknown_options: list[tuple[str, str]] = []
        self.option_reference = self.build_option_reference()
        self.prefix = prefix
        if prefix is not None:
            self.assign_prefix_to_options(prefix)

    def build_option_reference(self) -> dict[str, ConfigOption]:
        """Builds the option reference dictionary.

        This method builds the option reference dictionary. It maps the option
        names to the option objects. It also maps any deprecated names to the
        option objects.

        Returns:
            dict[str, ConfigOption]: The option reference dictionary.
        """
        reference = {option.name: option for option in self.OPTIONS}
        deprecated_reference = {}
        for option in self.OPTIONS:
            if isinstance(option.deprecated_names, str):
                deprecated_reference[option.deprecated_names] = option
                continue
            for deprecated_name in option.deprecated_names or []:
                deprecated_reference[deprecated_name] = option
        return {**reference, **deprecated_reference}

    def assign_prefix_to_options(self, prefix: str) -> None:
        """Assigns a prefix to the options.

        Does NOT assign the prefix to the object itself.

        Args:
            prefix (str): The prefix to assign to the options.
        """
        for option in self.OPTIONS:
            option.set_prefix(prefix)

    @property
    def OPTIONS(self) -> list[ConfigOption]:
        """The list of options.

        Returns the list of set options as well as any additional options that
        have been added.

        Returns:
            list[ConfigOption]: The list of options.
        """
        return list(self._OPTIONS) + self._ADDITIONAL_OPTIONS

    @property
    def SUPPORTED_OPTIONS(self) -> list[str]:
        """The list of supported options.

        Returns the list of supported options as well as any additional options
        that have been added.

        Returns:
            list[str]: The list of supported options.
        """
        return list(self.option_reference.keys())

    @property
    def SECTIONS(self) -> list[str]:
        """The list of sections.

        Returns the list of sections that the options are in.

        Returns:
            list[str]: The list of sections.
        """
        return list(set(option.section for option in self.OPTIONS))

    @property
    def tokens(self) -> dict[str, str]:
        """The tokens.

        Returns:
            dict[str, str]: The tokens.
        """
        return {
            TOKENS.SESSION_TOKEN: self.get_value(TOKENS.SESSION_TOKEN),
            TOKENS.GTOKEN: self.get_value(TOKENS.GTOKEN),
            TOKENS.BULLET_TOKEN: self.get_value(TOKENS.BULLET_TOKEN),
        }

    def add_options(self, options: ConfigOption | list[ConfigOption]) -> None:
        """Add options to the list of additional options.

        Args:
            options (ConfigOption | list[ConfigOption]): The list of options to
                add.
        """
        if not isinstance(options, list):
            options = [options]
        self._ADDITIONAL_OPTIONS.extend(options)
        self.option_reference = self.build_option_reference()
        if self.prefix is not None:
            self.assign_prefix_to_options(self.prefix)

    def get_option(self, name: str) -> ConfigOption:
        """Gets an option from the option reference dictionary.

        Args:
            name (str): The name of the option to get.

        Raises:
            ValueError: If the option is not defined.

        Returns:
            ConfigOption: The option that was retrieved.
        """
        name = name.lower()
        try:
            return self.option_reference[name]
        except KeyError:
            raise KeyError(f"Option {name} is not supported.")

    def get_value(self, name: str) -> str | None:
        """Gets the value of an option.

        Args:
            name (str): The name of the option to get.

        Returns:
            str | None: The value of the option.
        """
        return self.get_option(name).get_value()

    def set_value(self, name: str, value: str | None) -> None:
        """Sets the value of an option.

        Args:
            name (str): The name of the option to set.
            value (str | None): The value to set the option to.
        """
        self.get_option(name).set_value(value)

    def get_section(self, section: str) -> list[ConfigOption]:
        """Gets all the options in a section.

        Args:
            section (str): The section to get the options from.

        Returns:
            list[ConfigOption]: The list of options in the section.
        """
        return [option for option in self.OPTIONS if option.section == section]

    def read_from_configparser(self, config: configparser.ConfigParser) -> None:
        """Reads the config from a ConfigParser object and sets the values in
        the handler.

        Args:
            config (configparser.ConfigParser): The ConfigParser object to read
                the config from.
        """
        for section in config.sections():
            for option in config.options(section):
                value = config.get(section, option)
                try:
                    self.set_value(option, value)
                except KeyError:
                    self.unknown_options.append((option, value))

    def read_from_dict(self, config: dict[str, str]) -> None:
        """Reads the config from a dictionary and sets the values in the
        handler.

        Args:
            config (dict[str, str]): The dictionary to read the config from.
        """
        for option, value in config.items():
            try:
                self.set_value(option, value)
            except KeyError:
                self.unknown_options.append((option, value))

    def save_to_configparser(
        self, config: configparser.ConfigParser | None = None
    ) -> configparser.ConfigParser:
        """Saves the config to a ConfigParser object.

        Args:
            config (configparser.ConfigParser | None): The ConfigParser object
                to save the config to. If None, a new ConfigParser object will
                be created.

        Returns:
            configparser.ConfigParser: The ConfigParser object with the config
                saved to it.
        """
        if config is None:
            config = configparser.ConfigParser()
        for option in self.OPTIONS:
            if option.value is None:
                continue
            if not config.has_section(option.section):
                config.add_section(option.section)
            config.set(option.section, option.name, option.value)

        if not config.has_section("Unknown"):
            config.add_section("Unknown")
        for option, value in self.unknown_options:
            config.set("Unknown", option, value)
        return config
