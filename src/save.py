import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain.embeddings import BedrockEmbeddings

from src.configure import S3_BUCKET, CHROMA_DIR, PDF_DIR, BEDROCK_EMBED_MODEL
from src.aws_utils import baixar_arquivos_s3, setup_logger

def carregar_documentos(pasta_local: str):
    docs = []
    if not os.path.exists(pasta_local):
        os.makedirs(pasta_local, exist_ok=True)

    for arquivo in os.listdir(pasta_local):
        if arquivo.endswith(".pdf"):
            caminho = os.path.join(pasta_local, arquivo)
            loader = PyPDFLoader(caminho)
            docs.extend(loader.load())

    return docs

def criar_chroma(docs, persist_dir: str):
    embeddings = BedrockEmbeddings(model_id=BEDROCK_EMBED_MODEL)

    vectordb = Chroma.from_documents(
        docs,
        embedding = embeddings,
        persist_directory = persist_dir
    )
    vectordb.persist()
    return vectordb

if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Iniciando ingestão de documentos jurídicos.")

    logger.info(f"Baixando PDFs do bucket {S3_BUCKET}...")
    baixar_arquivos_s3(S3_BUCKET, "dataset/", PDF_DIR)

    logger.info("Carregando documentos.")
    documentos = carregar_documentos(PDF_DIR)

    if not documentos:
        logger.warning("Nenhum documento encontrado em %s", PDF_DIR)
    else:
        logger.info("Criando base vetorial com Chroma...")
        criar_chroma(documentos, CHROMA_DIR)
        logger.info("Ingestão concluída. Base salva em: %s", CHROMA_DIR)
