from loguru import logger

from parkbot.gui import App
from parkbot.infra import get_settings_repository


def main():
    app_settings = get_settings_repository()
    internal_settings = app_settings.internal.get()

    logger.remove()
    logger.add(
        internal_settings.logging_dir,
        level=internal_settings.logging_level,
        rotation="10 MB",
    )

    app = App(app_settings=app_settings)
    app.mainloop()


if __name__ == "__main__":
    main()
