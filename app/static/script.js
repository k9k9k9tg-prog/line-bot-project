// ====== script.js ======
let lastNotifyTimestamp = 0;
const audio = new Audio("/static/notify.mp3");

// ページ読み込み後
document.addEventListener("DOMContentLoaded", () => {
    // 通知許可
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }

    // 初回メッセージ取得
    refreshMessages(true);
    setInterval(() => refreshMessages(false), 2000);

    // メッセージ送信
    const sendBtn = document.getElementById("send-btn");
    sendBtn.addEventListener("click", () => {
        const userId = document.getElementById("user-select").value;
        const text = document.getElementById("message-input").value.trim();
        if (!text) return;

        fetch("/send_message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, text: text })
        })
        .then(res => res.json())
        .then(r => {
            if (r.status === "ok") document.getElementById("message-input").value = "";
        });
    });
});

// メッセージ取得・チャット更新
function refreshMessages(fullNotify = false) {
    fetch("/messages")
        .then(res => res.json())
        .then(data => {
            const chat = document.getElementById("chat");
            if (!chat) return;
            chat.innerHTML = "";

            data.forEach(m => {
                const container = document.createElement("div");
                container.className = "bubble-container";

                const bubble = document.createElement("div");
                bubble.className = "bubble";

                // 左右判定
                if (m.type === "incoming") {
                    container.classList.add("left");
                } else if (m.type === "auto") {
                    container.classList.add("right");
                } else if (m.type === "outgoing") {
                    container.classList.add("right");
                } else if (m.type === "notify") {
                    container.classList.add("center");
                }

                // アイコン
                const img = document.createElement("img");
                img.className = "avatar";
                if (m.type === "incoming") {
                    img.src = window.userList[m.user_id]?.picture || "/static/default-avatar.png";
                } else if (m.type === "auto") {
                    img.src = "/static/bot-avatar.png";
                } else if (m.type === "outgoing") {
                    img.src = "/static/default-avatar.png";
                } else {
                    img.style.display = "none"; // notifyはアイコンなし
                }
                container.appendChild(img);

                // 名前
                const nameSpan = document.createElement("span");
                nameSpan.className = "name";
                if (m.type === "incoming") {
                    nameSpan.textContent = window.userList[m.user_id]?.name || m.user_id;
                } else if (m.type === "auto") {
                    nameSpan.textContent = "チャットボット";
                } else if (m.type === "outgoing") {
                    nameSpan.textContent = "あなた";
                } else if (m.type === "notify") {
                    nameSpan.textContent = "通知";
                }
                bubble.appendChild(nameSpan);

                // メッセージ本文
                const textSpan = document.createElement("span");
                textSpan.textContent = m.text;
                bubble.appendChild(textSpan);

                container.appendChild(bubble);
                chat.appendChild(container);

                // 通知
                if (m.type === "notify" && (fullNotify || m.timestamp > lastNotifyTimestamp)) {
                    showNotification(m.text);
                    lastNotifyTimestamp = m.timestamp;
                }
            });

            chat.scrollTop = chat.scrollHeight;
        })
        .catch(err => console.log("メッセージ取得エラー:", err));
}

// Notification API
function showNotification(text) {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") {
        new Notification("LINE Operator 通知", { body: text });
        audio.play().catch(e => console.log(e));
    }
}
