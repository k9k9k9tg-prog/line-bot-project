from flask import Flask, request, jsonify, render_template_string
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# LINE Webhook受信
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        events = parser.parse(body, signature)
    except Exception as e:
        print("Webhook parse error:", e)
        return "Error", 400

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.message.text)
            )
    return "OK"

# 管理画面
@app.route("/admin")
def admin():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>LINE Operator</title></head>
    <body>
    <h2>LINE オペレーター</h2>
    <input type="text" id="user_id" placeholder="ユーザーID"><br><br>
    <button onclick="sendMessage('こんにちは！')">こんにちは！</button>
    <script>
    function sendMessage(text) {
        const userId = document.getElementById("user_id").value;
        if(!userId){ alert("ユーザーIDを入力してください"); return; }
        fetch("/send_message", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({user_id:userId,text:text})
        }).then(res=>res.json()).then(data=>alert(JSON.stringify(data))).catch(err=>alert(err));
    }
    </script>
    </body>
    </html>
    """
    return render_template_string(html)

# 外部からメッセージ送信
@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    user_id = data.get("user_id")
    text = data.get("text")
    if not user_id or not text:
        return jsonify({"error": "user_id と text が必要"}), 400
    line_bot_api.push_message(user_id, TextSendMessage(text=text))
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
