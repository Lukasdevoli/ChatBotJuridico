from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from src.configure import TELEGRAM_TOKEN
from src.rag_chain import criar_chain
from src.aws_utils import setup_logger

logger = setup_logger()


qa = criar_chain()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Usuário {user.username} iniciou conversa.")
    await update.message.reply_text(
        f"Olá, {user.first_name}! \n"
        f"Sou o Chatbot Jurídico. Me pergunte algo sobre os documentos carregados."
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pergunta = update.message.text
    user = update.effective_user

    logger.info(f"Pergunta de {user.username}: {pergunta}")

    try:
        resultado = qa({"query": pergunta})

        resposta = resultado["result"]
        fontes = [doc.metadata.get("source") for doc in resultado["source_documents"]]

        await update.message.reply_text(resposta)

        logger.info(f"Resposta: {resposta} | Fontes: {fontes}")

    except Exception as e:
        logger.error(f"Erro ao responder: {e}")
        await update.message.reply_text("Ocorreu um erro ao processar sua pergunta.")

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TOKEN não definido nas variáveis de ambiente!")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    logger.info("Bot do Telegram iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
