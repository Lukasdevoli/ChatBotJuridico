import boto3
import logging
import watchtower
from src.configure import LOG_GROUP

s3_client = boto3.client("s3")

def baixar_arquivos_s3(bucket: str, prefix: str, destino: str):
    import os
    if not os.path.exists(destino):
        os.makedirs(destino)
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    for obj in response.get("Contents", []):
        nome_arquivo = obj["Key"].split("/")[-1]
        if nome_arquivo.endswith(".pdf"):
            caminho = os.path.join(destino, nome_arquivo)
            s3_client.download_file(bucket, obj["Key"], caminho)

def setup_logger():
    logger = logging.getLogger("chatbot-juridico")
    logger.setLevel(logging.INFO)
    handler = watchtower.CloudWatchLogHandler(log_group=LOG_GROUP)
    logger.addHandler(handler)
    return logger
