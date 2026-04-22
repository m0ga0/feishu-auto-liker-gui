from loguru import logger

from .gui import App


def main():
    logger.remove()
    logger.add("rpa_bot.log", rotation="10 MB", level="INFO")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()