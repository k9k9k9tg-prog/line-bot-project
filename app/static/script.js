"use strict";

const socket = io();
let unreadCounts = {};
const notificationSound = new Audio('/static/notify.mp3');

socket.on('connect', () => {
    console.log('Socket.IO connected');
});

socket.on('disconnect', () => {
    console.log('Socket.IO disconnected');
});

let selectedUserId = null;
let allMessages = [];

// --- DOM Elements ---
const userListContainer = document.getElementById('user-list-container');
const chatBox = document.getElementById('chat');
const chatUsername = document.getElementById('chat-with-username');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const scenarioSelect = document.getElementById('scenario-dropdown');
const setScenarioBtn = document.getElementById('set-scenario');

// --- Functions ---

/**
 * Updates the unread count badge for a user
 * @param {string} userId 
 */
function updateUnreadBadge(userId) {
    const userItem = userListContainer.querySelector(`[data-user-id="${userId}"]`);
    if (!userItem) return;

    let badge = userItem.querySelector('.badge');
    if (!badge) {
        badge = document.createElement('span');
        badge.classList.add('badge', 'bg-danger', 'ms-auto');
        // This assumes the user name container can hold a badge.
        // Let's adjust buildUserList to make this robust.
        const nameDiv = userItem.querySelector('.fw-bold');
        if(nameDiv) nameDiv.appendChild(badge);
    }

    const count = unreadCounts[userId] || 0;
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = '';
    } else {
        badge.style.display = 'none';
    }
}


/**
 * Creates a message bubble HTML element
 * @param {object} msg - The message object
 * @returns {HTMLDivElement}
 */
function createMessageBubble(msg) {
    const bubbleContainer = document.createElement('div');
    bubbleContainer.classList.add('message-container');

    let avatarUrl = '';
    let displayName = '';
    let isOperatorMessage = false;

    if (msg.type === 'outgoing' || msg.type === 'auto') {
        // オペレーターからのメッセージ or Botの自動返信
        avatarUrl = '/static/default-avatar.png'; // オペレーターのアバター（仮）
        displayName = msg.type === 'auto' ? 'Bot' : 'オペレーター';
        isOperatorMessage = true;
        bubbleContainer.classList.add('operator-message');
    } else if (msg.type === 'incoming') {
        // ユーザーからのメッセージ
        const user = window.userList[msg.user_id];
        avatarUrl = user ? user.picture : '/static/default-avatar.png';
        displayName = user ? user.name : 'Unknown User';
        bubbleContainer.classList.add('user-message');
    } else if (msg.type === 'notify') {
        // 通知メッセージ
        bubbleContainer.classList.add('notify-message');
        const textDiv = document.createElement('div');
        textDiv.classList.add('notify-text');
        textDiv.textContent = msg.text;
        bubbleContainer.appendChild(textDiv);
        return bubbleContainer;
    }

    const avatarDiv = document.createElement('div');
    avatarDiv.classList.add('message-avatar');
    const avatarImg = document.createElement('img');
    avatarImg.src = avatarUrl;
    avatarImg.alt = displayName;
    avatarDiv.appendChild(avatarImg);

    const messageContentDiv = document.createElement('div');
    messageContentDiv.classList.add('message-content');

    const nameSpan = document.createElement('span');
    nameSpan.classList.add('message-name');
    nameSpan.textContent = displayName;
    messageContentDiv.appendChild(nameSpan);

    const textDiv = document.createElement('div');
    textDiv.classList.add('message-text');
    textDiv.textContent = msg.text;
    messageContentDiv.appendChild(textDiv);

    const timeSpan = document.createElement('span');
    timeSpan.classList.add('message-time');
    timeSpan.textContent = new Date(msg.timestamp * 1000).toLocaleTimeString();
    messageContentDiv.appendChild(timeSpan);

    if (isOperatorMessage) {
        bubbleContainer.appendChild(messageContentDiv);
        bubbleContainer.appendChild(avatarDiv);
    } else {
        bubbleContainer.appendChild(avatarDiv);
        bubbleContainer.appendChild(messageContentDiv);
    }

    return bubbleContainer;
}

/**
 * Filters and displays messages for the selected user
 */
function displayMessagesForUser() {
    if (!selectedUserId) {
        chatBox.innerHTML = '<div class="text-center text-muted mt-3">ユーザーを選択してください</div>';
        return;
    }

    chatBox.innerHTML = '';
    
    // selectedUserIdに関連する全てのメッセージと通知メッセージを表示
    const userMessages = allMessages.filter(
        (msg) => (msg.user_id === selectedUserId) || (msg.type === 'notify')
    );
    
    userMessages.forEach((msg) => {
        chatBox.appendChild(createMessageBubble(msg));
    });

    // Scroll to the bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Fetches messages for a specific user and displays them
 * @param {string} userId
 */
async function fetchMessagesAndDisplay(userId) {
    if (!userId) {
        allMessages = [];
        displayMessagesForUser();
        return;
    }
    try {
        const response = await fetch(`/messages?user_id=${userId}`);
        allMessages = await response.json();
        displayMessagesForUser();
    } catch (error) {
        console.error('Failed to fetch messages:', error);
    }
}

/**
 * Handles selecting a user from the list
 * @param {string} userId 
 * @param {HTMLElement} element 
 */
function selectUser(userId, element) {
    selectedUserId = userId;

    // Reset unread count for the selected user
    unreadCounts[userId] = 0;
    updateUnreadBadge(userId);

    // Update active class on user list
    document.querySelectorAll('#user-list-container .list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    element.classList.add('active');

    // Update chat header
    const user = window.userList[userId];
    chatUsername.textContent = user ? user.name : 'Unknown User';

    // Enable chat input
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.focus();

    // Fetch and display messages for the selected user
    fetchMessagesAndDisplay(userId);
}

/**
 * Builds the user list panel from window.userList
 */
function buildUserList() {
    userListContainer.innerHTML = '';
    if (Object.keys(window.userList).length === 0) {
        userListContainer.innerHTML = '<div class="p-3 text-muted">ユーザーがいません</div>';
        return;
    }

    Object.entries(window.userList).forEach(([userId, user]) => {
        const userItem = document.createElement('a');
        userItem.href = '#';
        userItem.classList.add('list-group-item', 'list-group-item-action', 'd-flex', 'align-items-center');
        userItem.dataset.userId = userId;

        const avatar = document.createElement('img');
        avatar.src = user.picture || '/static/default-avatar.png';
        avatar.classList.add('user-avatar', 'me-3');

        const nameContainer = document.createElement('div');
        nameContainer.classList.add('d-flex', 'w-100', 'justify-content-between', 'align-items-center');

        const nameDiv = document.createElement('div');
        nameDiv.textContent = user.name;
        nameDiv.classList.add('fw-bold');

        const badge = document.createElement('span');
        badge.classList.add('badge', 'bg-danger');
        badge.style.display = 'none'; // Initially hidden

        nameContainer.appendChild(nameDiv);
        nameContainer.appendChild(badge);

        userItem.appendChild(avatar);
        userItem.appendChild(nameContainer);

        userItem.addEventListener('click', (e) => {
            e.preventDefault();
            selectUser(userId, userItem);
        });

        userListContainer.appendChild(userItem);
        updateUnreadBadge(userId); // Initial badge state
    });
}

/**
 * Sends a message to the selected user via Socket.IO
 */
function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !selectedUserId) return;

    socket.emit('send_message', { 
        user_id: selectedUserId, 
        text: text 
    });
    
    messageInput.value = '';
}


// --- Event Listeners ---

document.addEventListener('DOMContentLoaded', async () => {
    
    async function fetchUsers() {
        try {
            const response = await fetch('/users');
            window.userList = await response.json();
        } catch (error) {
            console.error('Failed to fetch users:', error);
            window.userList = {}; // fallback to empty list
        }
    }

    await fetchUsers();
    buildUserList();

    // Listen for new messages from the server
    socket.on('new_message', (msg) => {
        // Append the new message directly to the chat window if it's for the selected user
        if (msg.user_id === selectedUserId || msg.type === 'notify') {
            // Also add to the main message list to avoid needing a re-fetch
            allMessages.push(msg); 
            chatBox.appendChild(createMessageBubble(msg));
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        // Handle unread count and notification for other users
        if (msg.user_id !== selectedUserId && msg.type === 'incoming') {
            if (window.userList[msg.user_id]) {
                unreadCounts[msg.user_id] = (unreadCounts[msg.user_id] || 0) + 1;
                updateUnreadBadge(msg.user_id);
                notificationSound.play().catch(e => console.error("Audio play failed:", e));
            }
        }
    });

    // Listen for new users
    socket.on('new_user', (user) => {
        window.userList[user.line_user_id] = {
            name: user.display_name,
            picture: user.picture_url
        };
        buildUserList();
    });

    // Listen for message sending errors
    socket.on('message_error', (data) => {
        console.error('Message error:', data.error);
        alert(`メッセージの送信に失敗しました: ${data.error}`);
    });

    // Select first user by default
    const firstUserEl = userListContainer.querySelector('.list-group-item');
    if (firstUserEl) {
        selectUser(firstUserEl.dataset.userId, firstUserEl);
    } else {
        // If no user, clear the chatbox
        fetchMessagesAndDisplay(null);
    }

    // User search functionality
    const searchInput = document.getElementById('user-search-input');
    searchInput.addEventListener('keyup', () => {
        const searchTerm = searchInput.value.toLowerCase();
        document.querySelectorAll('#user-list-container .list-group-item').forEach(item => {
            const userName = item.textContent.toLowerCase();
            if (userName.includes(searchTerm)) {
                item.style.display = 'flex'; // Use flex to match bootstrap's d-flex
            } else {
                item.style.display = 'none';
            }
        });
    });

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    setScenarioBtn.addEventListener('click', () => {
        const name = scenarioSelect.value;
        fetch('/set_scenario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name }),
        })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'ok') {
                alert('シナリオを適用しました。');
                window.currentScenario = name;
            } else {
                alert('シナリオの適用に失敗しました。');
            }
        });
    });
});