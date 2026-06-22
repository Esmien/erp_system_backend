import sys

from loguru import logger

from backend.core.config import settings


def setup_logger():
    """
    Настраивает loguru: вывод в консоль и в файл с ротацией.
    """
    # Удаляем стандартный обработчик
    logger.remove()

    # Настройка вывода в консоль
    logger.add(
        sys.stdout,
        level=settings.logger.LOG_LEVEL,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    )

    # Вывод в файл с ротацией
    # rotation="10 MB" - создаст новый файл, когда старый весит 10МБ
    # compression="zip" - старые логи будут сжиматься
    # retention="10 days" - храним логи за последние 10 дней
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level=settings.logger.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=settings.logger.LOG_SERIALIZE,
    )

    logger.info("Логгер успешно инициализирован.")
