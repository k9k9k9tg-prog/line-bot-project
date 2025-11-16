from flask import Flask, request, jsonify, render_template
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os, json, time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPERATOR_ID = os.getenv("OPERATOR_ID")  # 管理者のLINE ID

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

USER_FILE = "users.json"
MESSAGE_FILE = "messages.json"

# 永続化読み込み
try:
    with open(USER_FILE, "r", encoding="utf-8") as f:
        user_list = json.load(f)
except:
    user_list = {}

try:
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        messages = json.load(f)
except:
    messages = []

# シナリオ管理（5ステップ例）
scenarios = {
    "default": [
        "こんにちは！まずはお名前を教えてください。",
        "今日はどんなご用件でしょうか？",
        "詳しくお聞きしてもよろしいですか？",
        "ありがとうございます。確認します。",
        "すべてのステップが終了しました。オペレーターに接続します。"
    ]
}

user_progress = {}  # user_id -> 現在のステップ

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        events = parser.parse(body, signature)
    except:
        return "Error", 400

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_id = event.source.user_id

            # ユーザー名・アイコン取得
            try:
                profile = line_bot_api.get_profile(user_id)
                user_list[user_id] = {
                    "name": profile.display_name,
                    "picture": profile.picture_url or ""
                }
            except:
                user_list[user_id] = {
                    "name": user_id,
                    "picture": ""
                }

            with open(USER_FILE, "w", encoding="utf-8") as f:
                json.dump(user_list, f, ensure_ascii=False, indent=2)

            # 受信メッセージ追加
            messages.append({
                "user_id": user_id,
                "text": event.message.text,
                "type": "incoming",
                "timestamp": int(time.time())
            })

            # シナリオ返信
            step = user_progress.get(user_id, 0)
            scenario = scenarios["default"]

            if step < len(scenario):
                reply_text = scenario[step]
                user_progress[user_id] = step + 1
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                messages.append({
                    "user_id": user_id,
                    "text": reply_text,
                    "type": "auto",
                    "timestamp": int(time.time())
                })

            # ステップ完了 → オペレーター通知
            if user_progress[user_id] >= len(scenario):
                notify_text = f"{user_list.get(user_id, {}).get('name', user_id)} がシナリオを完了しました。"
                line_bot_api.push_message(OPERATOR_ID, TextSendMessage(text=notify_text))
                messages.append({
                    "user_id": OPERATOR_ID,
                    "text": notify_text,
                    "type": "notify",
                    "timestamp": int(time.time())
                })

            # メッセージ保存
            with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

    return "OK"

# 管理画面
@app.route("/admin")
def admin():
    return render_template("admin.html", user_list=user_list)

# 最新チャット
@app.route("/messages")
def get_messages():
    filtered = [m for m in messages if m.get("type") in ["incoming", "outgoing", "auto", "notify"]]
    return jsonify(filtered)

# メッセージ送信（管理者用）
@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    user_id = data.get("user_id")
    text = data.get("text")
    if not user_id or not text:
        return jsonify({"error": "user_id と text が必要"}), 400

    line_bot_api.push_message(user_id, TextSendMessage(text=text))
    messages.append({
        "user_id": user_id,
        "text": text,
        "type": "outgoing",
        "timestamp": int(time.time())
    })
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
