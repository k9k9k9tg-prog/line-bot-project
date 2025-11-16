let lastNotifyTimestamp = 0;
const audio = new Audio("/static/notify.mp3");

// DOM読み込み後
document.addEventListener("DOMContentLoaded", () => {
    // 通知許可
    if ("Notification" in window) {
        if (Notification.permission === "default") {
            Notification.requestPermission();
        }
    }
    refreshMessages(true);
    setInterval(() => refreshMessages(false), 2000);

    // 送信ボタン
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

// メッセージ取得・描画
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
            if (m.type === "incoming" || m.type === "notify") {
                container.classList.add("left");   // ユーザー・通知は左
            } else if (m.type === "outgoing" || m.type === "auto") {
                container.classList.add("right");  // 自分・シナリオ返信は右
            }

            // アイコン
            const img = document.createElement("img");
            img.className = "avatar";
            if (container.classList.contains("left")) {
                img.src = (m.user_id in window.userList) ? window.userList[m.user_id].picture || "/static/default-avatar.png" : "/static/default-avatar.png";
                container.appendChild(img); // 左はアイコンを左に
            }

            // 名前
            const nameSpan = document.createElement("span");
            nameSpan.className = "name";
            if (m.type === "outgoing" || m.type === "auto") nameSpan.textContent = "あなた";
            else if (m.type === "notify") nameSpan.textContent = "通知";
            else if (m.user_id in window.userList) nameSpan.textContent = window.userList[m.user_id].name;
            else nameSpan.textContent = m.user_id;
            bubble.appendChild(nameSpan);

            // メッセージテキスト
            const textSpan = document.createElement("span");
            textSpan.textContent = m.text;
            bubble.appendChild(textSpan);

            container.appendChild(bubble);

            // 右側のアイコン（自分・シナリオ）
            if (container.classList.contains("right")) {
                const rightImg = document.createElement("img");
                rightImg.className = "avatar";
                rightImg.src = "/static/default-avatar.png";
                container.appendChild(rightImg);
            }

            chat.appendChild(container);

            // 通知
            if (m.type === "notify" && (fullNotify || m.timestamp > lastNotifyTimestamp)) {
                showNotification(m.text);
                lastNotifyTimestamp = m.timestamp;
            }
        });

        chat.scrollTop = chat.scrollHeight;
    });
}

// Notification API
function showNotification(text) {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") {
        new Notification("LINE Operator 通知", { body: text });
        audio.play().catch(e => console.log(e));
    }
}
