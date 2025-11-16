# app/main.py
from flask import Flask, request
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os

load_dotenv()  # .env を読み込む

app = Flask(__name__)

CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# 変数が無ければ起動前に気づけるように
if CHANNEL_SECRET is None or CHANNEL_ACCESS_TOKEN is None:
    raise ValueError("LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN を .env に設定してください")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    # 本来は parser.parse で署名チェック & parse
    events = parser.parse(body, signature)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            # シンプルに受け取ったテキストを返す
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"受け取った: {event.message.text}")
            )
    return "OK"

if __name__ == "__main__":
    # ホスト0.0.0.0で待つ（Docker内で公開するため）
    app.run(host="0.0.0.0", port=8000)
