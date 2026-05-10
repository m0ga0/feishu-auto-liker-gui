class AppError(Exception):
    """Base class for application errors."""

    pass


class ConfigError(AppError):
    """Configuration related errors."""

    pass
