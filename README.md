# Programming Tutor

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
        4. Copy the bot token and add it to your .env file:
            ```plaintext
            TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
            ```
    - **DB_URI**: 
    
        The `DB_URI` variable is used to define the connection string to your database. Follow these steps to configure it:

        1. Choose a database engine. Make sure you have your preferred database engine installed and configured.

        2. The `DB_URI` variable must follow the SQLAlchemy connection string format. Here are some examples:

            - **PostgreSQL**:
            ```plaintext
            postgresql://username:password@localhost/database_name
            ```

            - **MySQL**:
            ```plaintext
            mysql+pymysql://username:password@localhost/database_name
            ```

        3. Open the `.env` file and add the following line with your connection string:
            ```plaintext
            DB_URI=your_database_connection_string_here
            ```


3. Run the main script:
    ```sh
    python src/main.py
    ```
