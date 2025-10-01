import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

S3_BUCKET = os.getenv("S3_BUCKET", "bucket-juridico")

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
PDF_DIR = os.getenv("PDF_DIR", "./data_pdfs")

BEDROCK_EMBED_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v1")
BEDROCK_LLM_MODEL = os.getenv("BEDROCK_LLM_MODEL", "anthropic.claude-v2")

LOG_GROUP = os.getenv("LOG_GROUP", "ChatbotJuridico")
