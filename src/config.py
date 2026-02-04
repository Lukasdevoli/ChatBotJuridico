import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PASTA_DATASET = "dataset"
PASTA_PERSISTENTE_DB = "vector_db"
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP", "ChatbotJuridicoLog")
AWS_PROFILE = os.getenv("AWS_PROFILE")


MODELO_EMBEDDINGS = "amazon.titan-embed-text-v1"

MODELO_LLM = "amazon.titan-text-express-v1"

BOT_TOKEN = os.getenv("BOT_TOKEN")
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
