from alerts.telegram_bot import (
    send_message
)

from utils.logger import (
    logger
)


def main():

    logger.info(
        "Engine started"
    )

    send_message(
        "🚀 FII-DII Sector Intelligence Engine Started Successfully"
    )


if __name__ == "__main__":
    main()