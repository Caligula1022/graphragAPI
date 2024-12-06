import logging

# 配置全局 logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def get_logger(name: str = __name__):
    return logging.getLogger(name)
