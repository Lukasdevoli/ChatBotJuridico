import logging
import boto3
import traceback
import re
import chromadb
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from langchain.vectorstores import Chroma
from langchain_aws import BedrockEmbeddings
from langchain_community.chat_models import BedrockChat
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from src.config import (
    BOT_TOKEN,
    PASTA_PERSISTENTE_DB,
    MODELO_EMBEDDINGS,
    MODELO_LLM,
    LLM_TEMPERATURE,
    AWS_REGION_NAME,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

session = boto3.Session()
bedrock_client = session.client(
    service_name="bedrock-runtime", region_name=AWS_REGION_NAME
)
bedrock_embeddings = BedrockEmbeddings(
    client=bedrock_client, model_id=MODELO_EMBEDDINGS
)
llm = BedrockChat(
    client=bedrock_client,
    model_id=MODELO_LLM,
    model_kwargs={"maxTokenCount": 2048, "temperature": LLM_TEMPERATURE},
)

db = Chroma(
    persist_directory=PASTA_PERSISTENTE_DB, embedding_function=bedrock_embeddings
)
retriever = db.as_retriever(search_kwargs={"k": 5})

PROMPT_TEMPLATE = """
Você é um Assistente jurídico do Squad1, especialista em RAG. 
Sua principal diretriz é RESPONDER COM BASE APENAS NO CONTEXTO FORNECIDO e com a MÁXIMA FIDELIDADE ao texto de origem.
Se a PERGUNTA tiver um ID de processo, priorize a informação específica daquele ID.
A sua resposta deve ser a frase ou trecho mais LITERALMENTE correspondente encontrado no CONTEXTO. 
Se a resposta não puder ser encontrada no CONTEXTO, diga "Não encontrei essa informação nos documentos."

CONTEXTO: {context}

PERGUNTA: {question}

ASSISTENTE JURÍDICO SQUAD1:
"""
PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE, input_variables=["context", "question"]
)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=False,
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o Assistente Jurídico do Squad1. Faça sua pergunta sobre um processo. Para buscar informações detalhadas, inclua o ID do processo na pergunta (ex: RE1463299)."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Mensagem recebida: {user_message}")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    try:
        match = re.search(r"(RE\d+|ARE\d+|ED\d+)", user_message, re.IGNORECASE)

        if match:
            id_processo_encontrado = match.group(0).upper()
            logger.info(
                f"ID detectado: {id_processo_encontrado}. Usando busca de Acesso Direto."
            )

            query_vector = bedrock_embeddings.embed_query(user_message)

            client = chromadb.PersistentClient(path=PASTA_PERSISTENTE_DB)
            collection = client.get_collection(name="langchain")

            results = collection.query(
                query_embeddings=[query_vector],
                n_results=8,
                where={"id_processo": id_processo_encontrado},
            )

            documentos_encontrados = results.get("documents", [[]])[0]
            if not documentos_encontrados:
                await update.message.reply_text(
                    f"Não encontrei informações específicas para o processo {id_processo_encontrado} nos documentos."
                )
                return

            contexto_combinado = "\n---\n".join(documentos_encontrados)
            prompt_final = PROMPT.format(
                context=contexto_combinado, question=user_message
            )
            resposta_final = llm.invoke(prompt_final)

            # --- LIMPEZA DE OUTPUT ---
            clean_content = resposta_final.content
            marcador_limpeza = "ASSISTENTE JURÍDICO SQUAD1:"
            if marcador_limpeza in clean_content:
                clean_content = clean_content.split(marcador_limpeza)[-1].strip()

            if clean_content.startswith("Bot:"):
                clean_content = clean_content[4:].strip()

            await update.message.reply_text(clean_content)

        else:
            # LÓGICA FINAL: Exige o ID, pois a busca geral é instável.
            logger.info("Nenhum ID de processo detectado. Solicitando o ID.")
            await update.message.reply_text(
                "Para buscar informações, por favor, inclua o ID completo do processo (ex: RE1463299) na sua pergunta. A busca sem o ID pode ser imprecisa."
            )

    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {e}", exc_info=True)
        traceback.print_exc()
        await update.message.reply_text("Ocorreu um erro ao buscar a resposta.")


def main() -> None:
    if not BOT_TOKEN:
        logger.error("TOKEN DO BOT NÃO ENCONTRADO!")
        return
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logging.info("Iniciando o bot em modo Polling...")
    print("\n✅ Bot online em modo Polling! (Não precisa de HTTPS)\n")
    application.run_polling()


if __name__ == "__main__":
    main()
