Web to Telegram chat with CherryPy based on https://gist.github.com/Lawouach/7698023

## Quickstart
Clone this source code:-

    git clone

Run buildout:-

    python bootstrap.py
    ./bin/buildout

Run the app:-

    ./bin/python app.py --tgtoken=<TELEGRAM_BOT_TOKEN> --tgchat=<TELEGRAM_CHAT_ID>

You need to use BotFather to get the `TELEGRAM_BOT_TOKEN`. `TELEGRAM_CHAT_ID` is where the message from chatbox will be forwarded to the telegram user. 

In order for us to receive reply from Telegram, need to setup webhook for `TELEGRAM_BOT_TOKEN` above. The webhook should point to:-

    https://your-domain:9000/webhook/

Hint: For development and local testing, you may use ngrok or localtunnel.
