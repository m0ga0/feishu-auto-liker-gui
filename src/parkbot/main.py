from loguru import logger

from parkbot.gui import App
from parkbot.infra import get_settings_repository, get_message_repository


def main():
    app_settings_repo = get_settings_repository()
    message_repo = get_message_repository()
    internal_settings = app_settings_repo.internal.get()

    logger.remove()
    logger.add(
        internal_settings.logging_dir,
        level=internal_settings.logging_level,
        rotation="10 MB",
    )

    app = App(app_settings_repo=app_settings_repo, message_repo=message_repo)
    app.mainloop()


if __name__ == "__main__":
    main()
