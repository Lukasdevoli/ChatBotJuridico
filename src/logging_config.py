import logging
import sys
import watchtower
from src.config import ENVIRONMENT, CLOUDWATCH_LOG_GROUP, AWS_REGION_NAME


def setup_logging():
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    if ENVIRONMENT == "production":
        print(f"Ambiente de produção. Logs para CloudWatch: {CLOUDWATCH_LOG_GROUP}")
        try:
            cw_handler = watchtower.CloudWatchLogHandler(
                log_group_name=CLOUDWATCH_LOG_GROUP, region_name=AWS_REGION_NAME
            )
            cw_handler.setFormatter(log_formatter)
            root_logger.addHandler(cw_handler)
            logging.info("Logging para CloudWatch configurado.")
        except Exception as e:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
            logging.error(f"Falha ao configurar CloudWatch: {e}. Usando console.")
    else:
        print("Ambiente de desenvolvimento. Logs para o console.")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
