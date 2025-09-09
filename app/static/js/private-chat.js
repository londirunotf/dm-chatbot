/**
 * プライベートチャット機能
 */

// グローバル変数
let isLoading = false;
let lastMessageId = null;
let autoScrollEnabled = true;
let currentSettings = {
    fontSize: 2,
    highContrast: false
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 [Private-chat.js] DOMContentLoaded started');
    initializePrivateChat();
    loadSettings();
    // 初回ロード時に履歴を表示
    loadChatMessages();
    console.log('🔧 [Private-chat.js] DOMContentLoaded completed');
});

/**
 * プライベートチャット初期化
 */
function initializePrivateChat() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const fileInput = document.getElementById('fileInput');
    
    // メッセージ入力の文字数カウント
    messageInput.addEventListener('input', function() {
        updateCharCount(this.value.length);
        adjustTextareaHeight(this);
        updateSendButtonState();
    });
    
    // Enter キーでの送信（Ctrl+Enter または Shift+Enter）
    messageInput.addEventListener('keydown', handleKeyDown);
    
    // 送信ボタンのクリックイベント
    sendButton.addEventListener('click', sendMessage);
    
    // ファイルアップロードの処理
    fileInput.addEventListener('change', handleFileUpload);
    
    // スクロール検知
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.addEventListener('scroll', function() {
        const isAtBottom = this.scrollTop + this.clientHeight >= this.scrollHeight - 100;
        autoScrollEnabled = isAtBottom;
    });
    
    // CSRFトークンの設定
    const csrfToken = document.querySelector('meta[name=csrf-token]').getAttribute('content');
    if (csrfToken) {
        // すべてのAJAXリクエストにCSRFトークンを含める
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (options.method && options.method.toUpperCase() !== 'GET') {
                options.headers = {
                    ...options.headers,
                    'X-CSRFToken': csrfToken
                };
            }
            return originalFetch(url, options);
        };
    }
}

/**
 * チャットメッセージをロード
 */
async function loadChatMessages() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        const response = await fetch('/api/get_messages');
        const data = await response.json();
        
        if (response.ok && data.messages) {
            displayMessages(data.messages);
            
            // 新しいメッセージがあった場合の処理
            const latestMessage = data.messages[data.messages.length - 1];
            if (latestMessage && latestMessage.id !== lastMessageId) {
                if (lastMessageId !== null) {
                    showNotification('新しいメッセージが届きました', 'info');
                }
                lastMessageId = latestMessage.id;
            }
        } else if (data.error) {
            console.error('メッセージ取得エラー:', data.error);
            if (response.status === 401) {
                showNotification('セッションが無効です。再ログインしてください。', 'error');
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 2000);
            }
        }
    } catch (error) {
        console.error('メッセージ取得でエラーが発生しました:', error);
    } finally {
        isLoading = false;
    }
}

/**
 * メッセージを表示
 */
function displayMessages(messages) {
    const chatMessages = document.getElementById('chatMessages');
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    
    // ウェルカムメッセージ以外をクリア
    const existingMessages = chatMessages.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // メッセージがない場合はウェルカムメッセージを表示
    if (messages.length === 0) {
        if (welcomeMessage) {
            welcomeMessage.style.display = 'block';
        }
        return;
    }
    
    // ウェルカムメッセージを非表示
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    // メッセージを追加
    messages.forEach(message => {
        const messageElement = createMessageElement(message);
        chatMessages.appendChild(messageElement);
    });
    
    // 自動スクロール
    if (autoScrollEnabled) {
        scrollToBottom();
    }
}

/**
 * 単一メッセージを表示に追加
 */
function addMessageToDisplay(message) {
    const chatMessages = document.getElementById('chatMessages');
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    
    // ウェルカムメッセージを非表示
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    // メッセージ要素を作成して追加
    const messageElement = createMessageElement(message);
    chatMessages.appendChild(messageElement);
    
    // 自動スクロール
    if (autoScrollEnabled) {
        scrollToBottom();
    }
}

/**
 * メッセージ要素を作成
 */
function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.message_type}`;
    messageDiv.dataset.messageId = message.id;
    
    // アバター要素
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    const senderInfo = getSenderInfo(message);
    avatarDiv.innerHTML = senderInfo.icon;
    
    // メッセージ情報コンテナ
    const infoDiv = document.createElement('div');
    infoDiv.className = 'message-info';
    
    // メッセージヘッダー（バブル外）
    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    headerDiv.innerHTML = `
        <span class="message-sender">${senderInfo.name}</span>
    `;
    
    // メッセージコンテンツ（バブル内）
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // メッセージテキスト
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = message.content;
    contentDiv.appendChild(textDiv);
    
    // 時刻表示（バブル右下）
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(message.timestamp);
    contentDiv.appendChild(timeDiv);
    
    // 添付ファイル（バブル内）
    if (message.file_name) {
        const attachmentDiv = document.createElement('div');
        attachmentDiv.className = 'message-attachment';
        attachmentDiv.innerHTML = `📎 ${message.file_name}`;
        contentDiv.appendChild(attachmentDiv);
    }
    
    // 構造を組み立て
    infoDiv.appendChild(headerDiv);
    infoDiv.appendChild(contentDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(infoDiv);
    
    return messageDiv;
}

/**
 * 送信者情報を取得
 */
function getSenderInfo(message) {
    switch (message.message_type) {
        case 'user':
            return {
                icon: window.currentUser.is_admin ? '👨‍💼' : '👤',
                name: window.currentUser.display_name
            };
        case 'staff':
            return {
                icon: '👨‍💼',
                name: message.staff_name || 'サポートスタッフ'
            };
        case 'bot':
            return {
                icon: '🤖',
                name: '自動回答システム'
            };
        default:
            return {
                icon: '❓',
                name: '不明'
            };
    }
}

/**
 * メッセージ送信
 */
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || isLoading) {
        return;
    }
    
    if (message.length > 1000) {
        showNotification('メッセージが長すぎます（1000文字以内）', 'error');
        return;
    }
    
    try {
        isLoading = true;
        updateSendButtonState(true);
        
        const response = await fetch('/api/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            messageInput.value = '';
            updateCharCount(0);
            adjustTextareaHeight(messageInput);
            
            // 送信したユーザーメッセージを即座に表示に追加
            const userMessage = {
                id: Date.now() + '_user', // 一時的なID
                message_type: 'user',
                content: message,
                timestamp: new Date().toISOString(),
                is_escalated: false
            };
            addMessageToDisplay(userMessage);
            
            // ボット回答がある場合は即座に追加
            if (data.type === 'faq_answer' || data.type === 'escalation') {
                const botMessage = {
                    id: Date.now() + '_bot',
                    message_type: 'bot',
                    content: data.message,
                    timestamp: new Date().toISOString(),
                    is_escalated: data.type === 'escalation'
                };
                
                // 少し遅延を入れてボット回答を表示（リアルな感じにするため）
                setTimeout(() => {
                    addMessageToDisplay(botMessage);
                }, 500);
            }
            
            showNotification('メッセージを送信しました', 'success');
        } else {
            showNotification(data.error || '送信に失敗しました', 'error');
            
            if (response.status === 401) {
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 2000);
            }
        }
    } catch (error) {
        console.error('送信エラー:', error);
        showNotification('送信でエラーが発生しました', 'error');
    } finally {
        isLoading = false;
        updateSendButtonState(false);
    }
}

/**
 * キーボードイベントハンドラ
 */
function handleKeyDown(event) {
    if (event.key === 'Enter') {
        if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            sendMessage();
        } else if (!event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }
}

/**
 * テキストエリアの高さ調整
 */
function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    const maxHeight = 120;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = newHeight + 'px';
}

/**
 * 文字数カウント更新
 */
function updateCharCount(count) {
    const charCountElement = document.querySelector('.char-count');
    const statusElement = document.querySelector('.status-text');
    
    if (charCountElement) {
        charCountElement.textContent = `${count}/1000`;
        
        // 警告色の設定
        charCountElement.className = 'char-count';
        if (count > 900) {
            charCountElement.classList.add('error');
        } else if (count > 700) {
            charCountElement.classList.add('warning');
        }
    }
    
    if (statusElement) {
        if (count === 0) {
            statusElement.textContent = 'メッセージを入力してください';
        } else if (count > 1000) {
            statusElement.textContent = '文字数制限を超えています';
        } else {
            statusElement.textContent = '送信可能です';
        }
    }
}

/**
 * 送信ボタンの状態更新
 */
function updateSendButtonState(loading = false) {
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    
    const hasMessage = messageInput.value.trim().length > 0 && messageInput.value.length <= 1000;
    
    sendButton.disabled = loading || !hasMessage || isLoading;
    
    // アイコンの表示切り替え
    const enabledIcon = sendButton.querySelector('.send-icon-enabled');
    const disabledIcon = sendButton.querySelector('.send-icon-disabled');
    if (enabledIcon && disabledIcon) {
        if (sendButton.disabled || loading) {
            enabledIcon.style.display = 'none';
            disabledIcon.style.display = 'inline-block';
        } else {
            enabledIcon.style.display = 'inline-block';
            disabledIcon.style.display = 'none';
        }
    }
}

/**
 * ファイルアップロード処理
 */
function handleFileUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    // ファイルサイズチェック（16MB）
    if (file.size > 16 * 1024 * 1024) {
        showNotification('ファイルサイズが大きすぎます（16MB以内）', 'error');
        input.value = '';
        return;
    }
    
    // TODO: ファイルアップロード機能の実装
    showNotification('ファイルアップロード機能は今後実装予定です', 'info');
    input.value = '';
}

/**
 * クイックテキスト挿入
 */
function insertQuickText(text) {
    const messageInput = document.getElementById('messageInput');
    const currentValue = messageInput.value;
    const newValue = currentValue ? currentValue + ' ' + text : text;
    
    messageInput.value = newValue;
    messageInput.focus();
    updateCharCount(newValue.length);
    adjustTextareaHeight(messageInput);
    updateSendButtonState();
}

/**
 * FAQ参照を挿入
 */
// insertFAQReference関数は削除（自動入力機能を廃止）

/**
 * FAQ検索
 */
function searchFAQ(query) {
    const faqItems = document.querySelectorAll('.faq-item');
    const normalizedQuery = query.toLowerCase().trim();
    
    faqItems.forEach(item => {
        const title = item.querySelector('.faq-title').textContent.toLowerCase();
        const preview = item.querySelector('.faq-preview').textContent.toLowerCase();
        
        const matches = title.includes(normalizedQuery) || preview.includes(normalizedQuery);
        item.style.display = matches || normalizedQuery === '' ? 'block' : 'none';
    });
}

/**
 * 設定パネルの切り替え
 */
function toggleSettings() {
    const settingsPanel = document.getElementById('settingsPanel');
    settingsPanel.classList.toggle('hidden');
}

/**
 * フォントサイズ変更
 */
function changeFontSize(size) {
    const sizeMap = {
        1: { label: '小', value: '12px' },
        2: { label: '標準', value: '14px' },
        3: { label: '大', value: '16px' },
        4: { label: '特大', value: '18px' }
    };
    
    const sizeInfo = sizeMap[size];
    if (sizeInfo) {
        document.documentElement.style.setProperty('--base-font-size', sizeInfo.value);
        document.getElementById('fontSizeLabel').textContent = sizeInfo.label;
        currentSettings.fontSize = parseInt(size);
        saveSettings();
    }
}

/**
 * ハイコントラストモード切り替え
 */
function toggleHighContrast() {
    const isEnabled = document.getElementById('highContrastMode').checked;
    document.body.classList.toggle('high-contrast', isEnabled);
    currentSettings.highContrast = isEnabled;
    saveSettings();
}

/**
 * 設定を保存
 */
function saveSettings() {
    localStorage.setItem('privateChatSettings', JSON.stringify(currentSettings));
}

/**
 * 設定を読み込み
 */
function loadSettings() {
    try {
        const saved = localStorage.getItem('privateChatSettings');
        if (saved) {
            const settings = JSON.parse(saved);
            currentSettings = { ...currentSettings, ...settings };
            
            // 設定を適用
            document.getElementById('fontSizeSlider').value = currentSettings.fontSize;
            changeFontSize(currentSettings.fontSize);
            
            document.getElementById('highContrastMode').checked = currentSettings.highContrast;
            if (currentSettings.highContrast) {
                document.body.classList.add('high-contrast');
            }
        }
    } catch (error) {
        console.error('設定読み込みエラー:', error);
    }
}

/**
 * 通知表示
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notifications');
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    }[type] || 'ℹ️';
    
    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;
    
    container.appendChild(notification);
    
    // 5秒後に自動削除
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

/**
 * 確認ダイアログ表示
 */
function showConfirm(title, message, onConfirm) {
    const dialog = document.getElementById('confirmDialog');
    const titleElement = document.getElementById('confirmTitle');
    const messageElement = document.getElementById('confirmMessage');
    const yesButton = document.getElementById('confirmYes');
    const noButton = document.getElementById('confirmNo');
    
    titleElement.textContent = title;
    messageElement.textContent = message;
    
    const handleYes = () => {
        dialog.classList.add('hidden');
        onConfirm();
        cleanup();
    };
    
    const handleNo = () => {
        dialog.classList.add('hidden');
        cleanup();
    };
    
    const cleanup = () => {
        yesButton.removeEventListener('click', handleYes);
        noButton.removeEventListener('click', handleNo);
    };
    
    yesButton.addEventListener('click', handleYes);
    noButton.addEventListener('click', handleNo);
    
    dialog.classList.remove('hidden');
}

/**
 * 時刻フォーマット
 */
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 最下部にスクロール
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * アクセシビリティ機能の初期化
 */
function initializeAccessibility() {
    // フォーカス管理
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const settingsPanel = document.getElementById('settingsPanel');
            if (!settingsPanel.classList.contains('hidden')) {
                toggleSettings();
            }
        }
    });
    
    // スクリーンリーダー対応
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.setAttribute('aria-live', 'polite');
    chatMessages.setAttribute('aria-label', 'チャットメッセージ一覧');
}


// エクスポート（他のスクリプトからも使用可能）
window.privateChat = {
    sendMessage,
    loadChatMessages,
    showNotification,
    showConfirm,
    toggleSettings,
    searchFAQ,
    insertQuickText
};