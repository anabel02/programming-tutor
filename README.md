# Programming Tutor

## Project Structure

- `data/`: Contains data files such as the database and exercise definitions.
- `src/`: Contains all source code.
  - `database/`: Database models, CRUD operations, and queries.
  - `rag/`: Retrieval-Augmented Generation (RAG) related code.
  - `telegram_bot/`: Telegram bot implementation and services.
  - `utils/`: Utility functions.
- `.env`: Environment variables.
- `requirements.txt`: Project dependencies.

## Setup

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

2. Set up environment variables in .env:
    - **GEMINI_API_KEY**:
        1. Go to the [Google AI Studio](https://aistudio.google.com) website.
        2. Sign in or create an account.
        3. Navigate to the `Get API key` section and generate a new API key.
        4. Copy the API key and add it to your .env file:
            ```plaintext
            GEMINI_API_KEY=your_gemini_api_key_here
            ```
    - **TELEGRAM_BOT_TOKEN**:
        1. Open Telegram and search for the `BotFather`.
        2. Start a chat with `BotFather` and use the `/newbot` command to create a new bot.
        3. Follow the instructions to set up your bot and get the bot token.
        4. Copy the bot token and add it to your [.env](http://_vscodecontentref_/2) file:
            ```plaintext
            TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
            ```

3. Run the main script:
    ```sh
    python src/main.py
    ```