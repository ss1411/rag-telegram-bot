import logging
from telegram import Update  # [web:3]
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from config import TELEGRAM_BOT_TOKEN
from rag import MiniRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rag = MiniRAG()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Hi! I am a Mini-RAG bot.\n"
        "Use /ask <your question> to query the knowledge base.\n"
        "Use /help to see this message again."
    )
    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/ask <query> - Ask a question answered from local docs.\n"
        "/help - Show this help message."
    )


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a question after /ask.")
        return
    query = " ".join(context.args)
    await update.message.reply_text("Thinking...")
    try:
        answer = rag.answer(query)
        await update.message.reply_text(answer)
    except Exception as e:
        logger.exception("Error in /ask")
        await update.message.reply_text("Something went wrong while answering your question.")


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("ask", ask))

    application.run_polling()


if __name__ == "__main__":
    main()
