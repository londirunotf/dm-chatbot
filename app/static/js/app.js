class ChatApp {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.setupMobileHandlers();
        this.loadMessages();
        this.setupCSRF();
        this.setupAutoSave();
        this.isTyping = false;
        this.typingTimeout = null;
    }

    initializeElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.fileButton = document.getElementById('fileButton');
        this.fileInput = document.getElementById('fileInput');
        this.chatMessages = document.getElementById('chatMessages');
        this.charCount = document.getElementById('charCount');
        this.faqModal = document.getElementById('faqModal');
        this.modalClose = document.querySelector('.modal-close');
        this.useFaqButton = document.getElementById('useFaqButton');
        
        // FAQ要素
        this.faqItems = document.querySelectorAll('.faq-item');
    }

    setupCSRF() {
        this.csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    }

    attachEventListeners() {
        // メッセージ送信
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 入力状態の表示
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.showTypingIndicator();
        });

        // フォーカス時の処理
        this.messageInput.addEventListener('focus', () => {
            this.messageInput.parentElement.classList.add('focused');
        });
        this.messageInput.addEventListener('blur', () => {
            this.messageInput.parentElement.classList.remove('focused');
        });

        // ファイル選択
        this.fileButton.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', () => this.handleFileSelect());

        // FAQ関連 - ダブルクリックでモーダル表示（グローバル関数を使用）
        this.faqItems.forEach(item => {
            item.addEventListener('dblclick', () => {
                if (window.showFaqModal) {
                    window.showFaqModal(item.dataset.faqId);
                } else {
                    this.showFaqModal(item.dataset.faqId);
                }
            });
        });

        // クイックFAQアクセスボタン
        const quickFaqButtons = document.querySelectorAll('.quick-faq-btn');
        quickFaqButtons.forEach(btn => {
            btn.addEventListener('click', () => this.handleQuickFaqClick(btn));
        });

        // モーダル制御（グローバル関数を優先）
        if (this.modalClose) {
            this.modalClose.addEventListener('click', () => {
                if (window.closeFaqModal) {
                    window.closeFaqModal();
                } else {
                    this.closeFaqModal();
                }
            });
        }
        if (this.faqModal) {
            this.faqModal.addEventListener('click', (e) => {
                if (e.target === this.faqModal) {
                    if (window.closeFaqModal) {
                        window.closeFaqModal();
                    } else {
                        this.closeFaqModal();
                    }
                }
            });
        }
        if (this.useFaqButton) {
            this.useFaqButton.addEventListener('click', () => this.useFaqAnswer());
        }

        // アクセシビリティ: Escapeキーでモーダルを閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.faqModal && this.faqModal.style.display === 'block') {
                if (window.closeFaqModal) {
                    window.closeFaqModal();
                } else {
                    this.closeFaqModal();
                }
            }
        });
    }

    updateCharCount() {
        const length = this.messageInput.value.length;
        this.charCount.textContent = length;
        
        // 文字数による状態管理
        if (length > 1000) {
            this.charCount.style.color = 'red';
            this.sendButton.disabled = true;
            this.charCount.textContent += ' (上限超過)';
        } else if (length > 800) {
            this.charCount.style.color = 'orange';
            this.sendButton.disabled = false;
        } else {
            this.charCount.style.color = '#666';
            this.sendButton.disabled = false;
        }

        // 送信ボタンの状態更新
        const isEmpty = length === 0;
        this.sendButton.disabled = isEmpty || length > 1000;
        this.sendButton.style.opacity = this.sendButton.disabled ? '0.5' : '1';
        
        // アイコンの表示切り替え
        const enabledIcon = this.sendButton.querySelector('.send-icon-enabled');
        const disabledIcon = this.sendButton.querySelector('.send-icon-disabled');
        if (enabledIcon && disabledIcon) {
            if (this.sendButton.disabled) {
                enabledIcon.style.display = 'none';
                disabledIcon.style.display = 'inline-block';
            } else {
                enabledIcon.style.display = 'inline-block';
                disabledIcon.style.display = 'none';
            }
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.sendButton.disabled) return;

        // UI更新
        const userMessageElement = this.addUserMessage(message);
        this.messageInput.value = '';
        this.updateCharCount();
        this.sendButton.disabled = true;
        this.hideTypingIndicator();
        
        // メッセージ送信中表示
        this.showBotTyping();
        
        // メッセージステータス追加
        this.addMessageStatus(userMessageElement, 'sending');

        try {
            const response = await fetch('/api/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            this.hideBotTyping();
            
            if (response.ok) {
                this.addMessageStatus(userMessageElement, 'sent');
                setTimeout(() => {
                    this.addBotMessage(data);
                }, 300);
            } else {
                this.addMessageStatus(userMessageElement, 'error');
                this.addErrorMessage(data.error || 'エラーが発生しました');
            }
        } catch (error) {
            console.error('送信エラー:', error);
            this.hideBotTyping();
            this.addMessageStatus(userMessageElement, 'error');
            this.addErrorMessage('通信エラーが発生しました。インターネット接続を確認してください。');
        } finally {
            this.sendButton.disabled = false;
        }
    }

    addUserMessage(content) {
        const messageElement = this.createMessageElement('user', content);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        return messageElement;
    }

    addBotMessage(data) {
        let content;
        let messageType = 'bot';

        if (data.type === 'faq_answer') {
            content = `<strong>FAQ: ${data.faq_title}</strong><br><br>${data.message}`;
        } else if (data.type === 'escalation') {
            content = data.message;
            messageType = 'staff';
        } else {
            content = data.message;
        }

        const messageElement = this.createMessageElement(messageType, content, data.timestamp);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    addErrorMessage(content) {
        const messageElement = this.createMessageElement('bot', `エラー: ${content}`);
        messageElement.querySelector('.message-bubble').style.backgroundColor = '#ffebee';
        messageElement.querySelector('.message-bubble').style.color = '#c62828';
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    createMessageElement(type, content, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = timestamp ? 
            new Date(timestamp).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }) :
            new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

        bubbleDiv.appendChild(contentDiv);
        bubbleDiv.appendChild(timeDiv);
        messageDiv.appendChild(bubbleDiv);

        return messageDiv;
    }

    async loadMessages() {
        try {
            const response = await fetch('/api/get_messages');
            const data = await response.json();

            if (response.ok && data.messages.length > 0) {
                // ウェルカムメッセージを削除
                const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
                if (welcomeMessage) {
                    welcomeMessage.remove();
                }

                // メッセージを表示
                data.messages.forEach(msg => {
                    if (msg.message_type === 'user') {
                        this.addUserMessageFromData(msg);
                    } else {
                        this.addBotMessageFromData(msg);
                    }
                });
            }
        } catch (error) {
            console.error('メッセージ読み込みエラー:', error);
        }
    }

    addUserMessageFromData(msg) {
        const messageElement = this.createMessageElement('user', msg.content, msg.timestamp);
        this.chatMessages.appendChild(messageElement);
    }

    addBotMessageFromData(msg) {
        let content = msg.content;
        if (msg.faq_id) {
            const faq = window.faqData?.find(f => f.id === msg.faq_id);
            if (faq) {
                content = `<strong>FAQ: ${faq.title}</strong><br><br>${content}`;
            }
        }

        const messageType = msg.message_type === 'staff' ? 'staff' : 'bot';
        const messageElement = this.createMessageElement(messageType, content, msg.timestamp);
        this.chatMessages.appendChild(messageElement);
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showFaqModal(faqId) {
        const faq = window.faqData?.find(f => f.id == faqId);
        if (!faq) return;

        document.getElementById('faqModalTitle').textContent = faq.title;
        document.getElementById('faqModalQuestion').textContent = faq.question;
        document.getElementById('faqModalAnswer').innerHTML = faq.answer.replace(/\n/g, '<br>');
        
        this.currentFaq = faq;
        this.faqModal.style.display = 'block';
        
        // アクセシビリティ: モーダルにフォーカス
        this.modalClose.focus();
    }

    closeFaqModal() {
        this.faqModal.style.display = 'none';
        this.currentFaq = null;
    }

    useFaqAnswer() {
        if (this.currentFaq) {
            // FAQ回答をチャットに表示
            const content = `<strong>FAQ: ${this.currentFaq.title}</strong><br><br>${this.currentFaq.answer}`;
            const messageElement = this.createMessageElement('bot', content);
            this.chatMessages.appendChild(messageElement);
            this.scrollToBottom();
            this.closeFaqModal();
        }
    }

    handleQuickFaqClick(button) {
        const searchTerm = button.dataset.search;
        if (!searchTerm) return;

        // FAQ検索を実行
        if (window.faqSearchManager) {
            // FAQ検索を実行し、FAQサイドバーを表示（モバイルの場合）
            this.showFAQSidebar();
            window.faqSearchManager.searchFAQ(searchTerm);
            
            // ボタンのフィードバック
            button.style.transform = 'scale(0.95)';
            setTimeout(() => {
                button.style.transform = '';
            }, 150);

            // ユーザーにフィードバックメッセージを表示
            const feedbackContent = `「${searchTerm}」に関するFAQを表示しています。左側のFAQリストをご確認ください。`;
            const messageElement = this.createMessageElement('bot', feedbackContent);
            this.chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }
    }

    handleFileSelect() {
        const file = this.fileInput.files[0];
        if (file) {
            // ファイルサイズチェック（16MB）
            if (file.size > 16 * 1024 * 1024) {
                this.showNotification('ファイルサイズが大きすぎます。16MB以下のファイルを選択してください。', 'error');
                this.fileInput.value = '';
                return;
            }

            // 現在はファイル名のみ表示（実装は後で）
            const fileName = file.name;
            const fileSize = this.formatFileSize(file.size);
            this.messageInput.value += `\n[添付ファイル: ${fileName} (${fileSize})]`;
            this.updateCharCount();
            this.showNotification(`ファイルが添付されました: ${fileName}`, 'success');
        }
    }

    // ユーザビリティ向上のための新機能
    setupAutoSave() {
        // 入力内容の自動保存
        setInterval(() => {
            const content = this.messageInput.value;
            if (content.trim()) {
                localStorage.setItem('chatDraft', content);
            }
        }, 5000);

        // ページ読み込み時に下書きを復元
        const savedDraft = localStorage.getItem('chatDraft');
        if (savedDraft) {
            this.messageInput.value = savedDraft;
            this.updateCharCount();
        }

        // 送信時に下書きをクリア
        const originalSendMessage = this.sendMessage.bind(this);
        this.sendMessage = async function() {
            localStorage.removeItem('chatDraft');
            return originalSendMessage();
        };
    }

    showTypingIndicator() {
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        this.isTyping = true;
        this.typingTimeout = setTimeout(() => {
            this.isTyping = false;
        }, 1000);
    }

    hideTypingIndicator() {
        this.isTyping = false;
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
    }

    showBotTyping() {
        const typingElement = document.createElement('div');
        typingElement.className = 'bot-message typing-indicator';
        typingElement.innerHTML = `
            <div class="message-bubble typing-bubble">
                <div class="message-content">
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideBotTyping() {
        const typingIndicator = this.chatMessages.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    addMessageStatus(messageElement, status) {
        let statusElement = messageElement.querySelector('.message-status');
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.className = 'message-status';
            messageElement.querySelector('.message-bubble').appendChild(statusElement);
        }

        statusElement.className = `message-status ${status}`;
        switch (status) {
            case 'sending':
                statusElement.innerHTML = '⏳';
                statusElement.title = '送信中...';
                break;
            case 'sent':
                statusElement.innerHTML = '✅';
                statusElement.title = '送信完了';
                break;
            case 'error':
                statusElement.innerHTML = '❌';
                statusElement.title = '送信エラー';
                break;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // 通知コンテナが存在しない場合は作成
        let notificationContainer = document.querySelector('.notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        notificationContainer.appendChild(notification);
        
        // 3秒後に自動削除
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    setupMobileHandlers() {
        // モバイル対応：FAQサイドバー制御
        const faqToggleBtn = document.getElementById('faqToggleBtn');
        const faqCloseBtn = document.getElementById('faqCloseBtn');
        const faqSidebar = document.getElementById('faqSidebar');
        const faqOverlay = document.getElementById('faqSidebarOverlay');

        if (faqToggleBtn) {
            faqToggleBtn.addEventListener('click', () => {
                this.showFAQSidebar();
            });
        }

        if (faqCloseBtn) {
            faqCloseBtn.addEventListener('click', () => {
                this.hideFAQSidebar();
            });
        }

        if (faqOverlay) {
            faqOverlay.addEventListener('click', () => {
                this.hideFAQSidebar();
            });
        }

        // モバイル対応：タッチイベント
        if ('ontouchstart' in window) {
            this.setupTouchHandlers();
        }

        // モバイル対応：キーボード表示時の調整
        this.setupKeyboardHandlers();

        // モバイル対応：スクロール最適化
        this.setupScrollOptimization();

        // FAQアイテムのモバイルタップ処理
        this.setupFAQMobileHandlers();
    }

    showFAQSidebar() {
        const faqSidebar = document.getElementById('faqSidebar');
        const faqOverlay = document.getElementById('faqSidebarOverlay');
        
        if (faqSidebar && faqOverlay) {
            faqSidebar.classList.add('show');
            faqOverlay.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    hideFAQSidebar() {
        const faqSidebar = document.getElementById('faqSidebar');
        const faqOverlay = document.getElementById('faqSidebarOverlay');
        
        if (faqSidebar && faqOverlay) {
            faqSidebar.classList.remove('show');
            faqOverlay.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    setupTouchHandlers() {
        // タッチスクロールの最適化
        if (this.chatMessages) {
            this.chatMessages.style.webkitOverflowScrolling = 'touch';
        }

        // タップハイライトの無効化
        document.addEventListener('touchstart', function() {}, {passive: true});
    }

    setupKeyboardHandlers() {
        // iOS Safari キーボード表示時の処理
        if (navigator.userAgent.match(/iPhone|iPad|iPod/i)) {
            const viewport = document.querySelector('meta[name=viewport]');
            const originalContent = viewport.content;

            this.messageInput.addEventListener('focus', () => {
                viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                
                // キーボード表示でビューポートが変わった時の調整
                setTimeout(() => {
                    if (this.chatMessages) {
                        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                    }
                }, 300);
            });

            this.messageInput.addEventListener('blur', () => {
                viewport.content = originalContent;
            });
        }

        // Android Chrome キーボード表示時の処理
        let initialViewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
        
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', () => {
                const currentHeight = window.visualViewport.height;
                const heightDifference = initialViewportHeight - currentHeight;
                
                if (heightDifference > 150) { // キーボード表示と判定
                    document.body.style.paddingBottom = heightDifference + 'px';
                } else {
                    document.body.style.paddingBottom = '';
                }
            });
        }
    }

    setupScrollOptimization() {
        if (this.chatMessages) {
            let isScrolling = false;
            
            this.chatMessages.addEventListener('scroll', () => {
                if (!isScrolling) {
                    // スクロール中はレンダリングを最適化
                    this.chatMessages.style.pointerEvents = 'none';
                    
                    clearTimeout(this.scrollTimeout);
                    this.scrollTimeout = setTimeout(() => {
                        this.chatMessages.style.pointerEvents = '';
                        isScrolling = false;
                    }, 150);
                    
                    isScrolling = true;
                }
            }, {passive: true});

            // スクロール位置を記憶
            this.chatMessages.addEventListener('scroll', () => {
                this.lastScrollPosition = this.chatMessages.scrollTop;
            }, {passive: true});
        }
    }

    setupFAQMobileHandlers() {
        this.faqItems.forEach(item => {
            // モバイルでのタップ処理を最適化
            item.addEventListener('touchstart', () => {
                item.style.backgroundColor = '#f0f0f0';
            }, {passive: true});

            item.addEventListener('touchend', () => {
                setTimeout(() => {
                    item.style.backgroundColor = '';
                }, 150);
            }, {passive: true});

            // FAQ選択時にモバイルではサイドバーを閉じる
            item.addEventListener('dblclick', () => {
                if (window.innerWidth <= 768) {
                    setTimeout(() => {
                        this.hideFAQSidebar();
                    }, 500); // FAQ内容が表示されてから閉じる
                }
            });
        });
    }

    // モバイル対応：メッセージ送信の最適化
    sendMessage() {
        // キーボードを隠す（モバイル）
        if (window.innerWidth <= 768 && this.messageInput) {
            this.messageInput.blur();
        }

        // 既存の送信処理を呼び出し
        // この部分は既存のsendMessageメソッドの処理と統合する必要があります
        // 元のsendMessageメソッドをここに移動または参照
    }

    // モバイル対応：スクロール位置復元
    scrollToBottom() {
        if (this.chatMessages) {
            // スムーズスクロール（モバイル対応）
            if (window.innerWidth <= 768) {
                this.chatMessages.scrollTo({
                    top: this.chatMessages.scrollHeight,
                    behavior: 'smooth'
                });
            } else {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }
        }
    }

    // モバイル対応：通知表示の調整
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // モバイルでは画面上部に表示
        if (window.innerWidth <= 768) {
            notification.style.position = 'fixed';
            notification.style.top = '10px';
            notification.style.left = '10px';
            notification.style.right = '10px';
            notification.style.zIndex = '1100';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// DOMが読み込まれたらアプリを初期化
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});