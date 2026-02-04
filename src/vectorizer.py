import os
import boto3
import logging
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_aws import BedrockEmbeddings
from src.config import (
    PASTA_DATASET, PASTA_PERSISTENTE_DB, MODELO_EMBEDDINGS, CHUNK_SIZE, 
    CHUNK_OVERLAP, S3_BUCKET_NAME, AWS_REGION_NAME
)

logger = logging.getLogger(__name__)
session = boto3.Session()

def extrair_id_processo_do_caminho(caminho_arquivo):
    try:
        partes = caminho_arquivo.split(os.sep)
        if len(partes) > 1:
            return partes[1]
    except Exception:
        pass
    return None

def baixar_arquivos_do_s3():
    if not S3_BUCKET_NAME:
        logger.warning("Nome do bucket S3 não foi definido. Pulando download.")
        return
    logger.info(f"Iniciando download recursivo de ficheiros do bucket S3: {S3_BUCKET_NAME}")
    try:
        s3_resource = session.resource('s3', region_name=AWS_REGION_NAME)
        bucket = s3_resource.Bucket(S3_BUCKET_NAME)
        arquivos_baixados = 0
        for obj in bucket.objects.all():
            caminho_local = os.path.join(PASTA_DATASET, obj.key)
            if obj.key.endswith('/'):
                os.makedirs(caminho_local, exist_ok=True)
                continue
            diretorio_pai = os.path.dirname(caminho_local)
            os.makedirs(diretorio_pai, exist_ok=True)
            if obj.key.endswith('.pdf'):
                bucket.download_file(obj.key, caminho_local)
        logger.info(f"Download de {arquivos_baixados} ficheiro(s) concluído.")
    except Exception as e:
        logger.error(f"Erro ao baixar ficheiros do S3: {e}", exc_info=True)
        raise

def criar_base_vetorial():
    try:
        baixar_arquivos_do_s3()
        bedrock_client = session.client(service_name='bedrock-runtime', region_name=AWS_REGION_NAME)
        bedrock_embeddings = BedrockEmbeddings(client=bedrock_client, model_id=MODELO_EMBEDDINGS)
        if not os.path.exists(PASTA_DATASET) or not os.listdir(PASTA_DATASET):
            logger.error(f"A pasta '{PASTA_DATASET}' está vazia.")
            return
        loader = PyPDFDirectoryLoader(PASTA_DATASET)
        documentos = loader.load()
        logger.info(f"{len(documentos)} páginas carregadas.")
        
        # ADICIONAR AS ETIQUETAS
        for doc in documentos:
            caminho_fonte = doc.metadata.get('source')
            if caminho_fonte:
                id_processo = extrair_id_processo_do_caminho(caminho_fonte)
                if id_processo:
                    doc.metadata['id_processo'] = id_processo

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        docs_split = text_splitter.split_documents(documentos)
        logger.info(f"Documentos divididos em {len(docs_split)} chunks.")
        
        Chroma.from_documents(
            docs_split,
            bedrock_embeddings,
            persist_directory=PASTA_PERSISTENTE_DB
        )
        logger.info(f"Base de dados reconstruída com sucesso em '{PASTA_PERSISTENTE_DB}'.")
    except Exception as e:
        logger.error(f"Falha na criação da base vetorial: {e}", exc_info=True)