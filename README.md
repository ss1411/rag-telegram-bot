# rag-telegram-bot
Telegram bot that does Retrieval-Augmented Generation (RAG) over local documents 

## Tech stack

Bot: python-telegram-bot.​
Embeddings: sentence-transformers/all-MiniLM-L6-v2.​
Vector store: sqlite-vec on SQLite.​
LLM: OpenAI GPT.

## Setup instructions
- 
- Create a Telegram bot with BotFather and get TELEGRAM_BOT_TOKEN.​
- Install dependencies: pip install -r requirements.txt.
- Put your .md or .txt docs into data/. 
- Set environment variables in .env:
- TELEGRAM_BOT_TOKEN=...
- LLM_BACKEND=openai
- OPENAI_API_KEY=...
- Start bot: python app.py.

1. One time setup:
```powershell
# 1. Create and activate venv (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```
Create a .env file in project root (where app.py is present) and add key-values as per .env.example

- To get TELEGRAM_BOT_TOKEN, talk to @BotFather in Telegram and use /newbot to create a bot, then copy the token
- Run the telegram bot from project root:
```powershell
python app.py
```
This calls ApplicationBuilder().token(...).build() and starts application.run_polling(), so the bot keeps running and listening for commands

3. How to run app:
Bot username: mini_rag_bot
Bot name: mini-rag-bot
- start the bot: /start then /help

examples:

```text
/ask What are my responsibilities as an employee under the information security policy?
```

```text
/ask How are company laptops tracked and what happens at end of life?
```

```text
/ask What steps must I follow when resigning from the company?
```

Flow: bot --> embed your question --> retrieve the most relevant chunks via sqlite-vec --> send them to the LLM --> response

## Workflow

Textual architecture explanation:
Telegram user → Bot → /ask → RAG: embed query → sqlite-vec search → context + prompt → LLM → answer back to user.​

# Example Screenshots

Images for below are included in output/
1. /start welcome
2. /ask with successful RAG answer
