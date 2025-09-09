/**
 * User Identification System
 * ユーザー識別システム - 質問者と回答者の特定機能
 */

class UserIdentificationManager {
    constructor() {
        this.currentUser = null;
        this.isIdentified = false;
        this.sessionId = this.getOrCreateSessionId();
        this.initializeElements();
        this.attachEventListeners();
        this.loadSavedUserInfo();
    }

    initializeElements() {
        // ユーザー識別関連のUI要素
        this.userIdentityPanel = document.getElementById('userIdentityPanel');
        this.userNameInput = document.getElementById('userNameInput');
        this.userDepartmentInput = document.getElementById('userDepartmentInput');
        this.identifyButton = document.getElementById('identifyUserBtn');
        this.clearIdentityButton = document.getElementById('clearIdentityBtn');
        this.userDisplayName = document.getElementById('userDisplayName');
        this.userStatus = document.getElementById('userStatus');
        
        // チャット送信フォーム
        this.messageForm = document.getElementById('messageForm');
        
        // 既存のチャット要素
        this.messagesContainer = document.getElementById('messages');
    }

    attachEventListeners() {
        // ユーザー識別ボタン
        if (this.identifyButton) {
            this.identifyButton.addEventListener('click', () => {
                this.identifyUser();
            });
        }

        // 識別情報クリアボタン
        if (this.clearIdentityButton) {
            this.clearIdentityButton.addEventListener('click', () => {
                this.clearUserIdentity();
            });
        }

        // Enterキーでユーザー識別
        if (this.userNameInput) {
            this.userNameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.identifyUser();
                }
            });
        }

        // メッセージ送信時にユーザー情報を付加
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => {
                this.attachUserInfoToMessage(e);
            });
        }

        // ページ読み込み時にユーザー情報を表示
        document.addEventListener('DOMContentLoaded', () => {
            this.updateUserDisplay();
        });
    }

    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatSessionId', sessionId);
        }
        return sessionId;
    }

    loadSavedUserInfo() {
        const savedUserInfo = localStorage.getItem('userIdentity');
        if (savedUserInfo) {
            try {
                this.currentUser = JSON.parse(savedUserInfo);
                this.isIdentified = true;
                this.updateUserDisplay();
                console.log('👤 保存されたユーザー情報を読み込みました:', this.currentUser.display_name);
            } catch (error) {
                console.error('ユーザー情報の読み込みエラー:', error);
                localStorage.removeItem('userIdentity');
            }
        }
    }

    async identifyUser() {
        const name = this.userNameInput?.value.trim();
        const department = this.userDepartmentInput?.value.trim();

        if (!name) {
            this.showNotification('名前を入力してください', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/identify-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    display_name: name,
                    department: department,
                    session_id: this.sessionId
                })
            });

            if (response.ok) {
                const userData = await response.json();
                this.currentUser = userData.user;
                this.isIdentified = true;
                
                // ローカルストレージに保存
                localStorage.setItem('userIdentity', JSON.stringify(this.currentUser));
                
                this.updateUserDisplay();
                this.hideIdentificationPanel();
                this.showNotification(`こんにちは、${this.currentUser.display_name}さん！`, 'success');
                
                console.log('👤 ユーザー識別完了:', this.currentUser);
            } else {
                throw new Error('ユーザー識別に失敗しました');
            }
        } catch (error) {
            console.error('ユーザー識別エラー:', error);
            this.showNotification('ユーザー識別中にエラーが発生しました', 'error');
        }
    }

    clearUserIdentity() {
        this.currentUser = null;
        this.isIdentified = false;
        localStorage.removeItem('userIdentity');
        
        this.updateUserDisplay();
        this.showIdentificationPanel();
        this.showNotification('ユーザー情報をクリアしました', 'info');
        
        console.log('👤 ユーザー識別情報をクリアしました');
    }

    updateUserDisplay() {
        if (this.userDisplayName && this.userStatus) {
            if (this.isIdentified && this.currentUser) {
                this.userDisplayName.textContent = this.currentUser.display_name;
                this.userStatus.textContent = this.currentUser.department 
                    ? `${this.currentUser.department}` 
                    : '登録ユーザー';
                this.userStatus.className = 'user-status identified';
            } else {
                this.userDisplayName.textContent = '匿名ユーザー';
                this.userStatus.textContent = '未識別';
                this.userStatus.className = 'user-status anonymous';
            }
        }

        // 識別パネルの表示制御
        if (this.isIdentified) {
            this.hideIdentificationPanel();
        } else {
            this.showIdentificationPanel();
        }
    }

    showIdentificationPanel() {
        if (this.userIdentityPanel) {
            this.userIdentityPanel.style.display = 'block';
        }
    }

    hideIdentificationPanel() {
        if (this.userIdentityPanel) {
            this.userIdentityPanel.style.display = 'none';
        }
    }

    attachUserInfoToMessage(event) {
        // メッセージ送信時にユーザー情報を付加
        if (this.isIdentified && this.currentUser) {
            const formData = new FormData(event.target);
            formData.append('user_id', this.currentUser.id);
            formData.append('user_display_name', this.currentUser.display_name);
            formData.append('user_department', this.currentUser.department || '');
        }
        formData.append('session_id', this.sessionId);
    }

    getUserInfo() {
        return {
            user: this.currentUser,
            isIdentified: this.isIdentified,
            sessionId: this.sessionId
        };
    }

    // メッセージ表示時にユーザー情報を表示
    addMessageToChat(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageData.message_type}`;
        
        // 送信者情報を表示
        const senderInfo = this.formatSenderInfo(messageData.sender_info);
        const responderInfo = this.formatResponderInfo(messageData.responder_info);
        
        messageElement.innerHTML = `
            <div class="message-header">
                <div class="message-sender">${senderInfo}</div>
                <div class="message-time">${this.formatTime(messageData.timestamp)}</div>
            </div>
            <div class="message-content">${messageData.content}</div>
            ${responderInfo ? `<div class="message-responder">${responderInfo}</div>` : ''}
            ${messageData.file_name ? `<div class="message-attachment">📎 ${messageData.file_name}</div>` : ''}
        `;
        
        if (this.messagesContainer) {
            this.messagesContainer.appendChild(messageElement);
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    formatSenderInfo(senderInfo) {
        if (!senderInfo) return '不明な送信者';
        
        if (senderInfo.display_name) {
            const typeLabel = this.getSenderTypeLabel(senderInfo.sender_type || senderInfo.user_type);
            return `${senderInfo.display_name} (${typeLabel})`;
        }
        
        return '匿名ユーザー';
    }

    formatResponderInfo(responderInfo) {
        if (!responderInfo) return null;
        
        if (responderInfo.name) {
            // 職員回答の場合
            return `回答者: ${responderInfo.name} (${responderInfo.department || '職員'})`;
        } else if (responderInfo.type === 'faq_bot') {
            // FAQ自動回答の場合
            return `自動回答: ${responderInfo.faq_title}`;
        }
        
        return null;
    }

    getSenderTypeLabel(type) {
        const labels = {
            'anonymous': '匿名',
            'registered': '登録済み',
            'staff': '職員',
            'admin': '管理者'
        };
        return labels[type] || '不明';
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString('ja-JP', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    showNotification(message, type = 'info') {
        // 既存の通知システムを利用
        if (window.chatApp && window.chatApp.showNotification) {
            window.chatApp.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    // 管理者向け機能: 職員として識別
    async identifyAsStaff(staffId, staffName, department) {
        try {
            const response = await fetch('/api/identify-staff', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    staff_id: staffId,
                    name: staffName,
                    department: department,
                    session_id: this.sessionId
                })
            });

            if (response.ok) {
                const staffData = await response.json();
                this.currentUser = staffData.user;
                this.isIdentified = true;
                this.currentUser.user_type = 'staff';
                
                localStorage.setItem('userIdentity', JSON.stringify(this.currentUser));
                this.updateUserDisplay();
                this.showNotification(`職員として識別されました: ${staffName}`, 'success');
                
                console.log('👨‍💼 職員識別完了:', staffData);
            } else {
                throw new Error('職員識別に失敗しました');
            }
        } catch (error) {
            console.error('職員識別エラー:', error);
            this.showNotification('職員識別中にエラーが発生しました', 'error');
        }
    }

    // 統計情報取得
    async getUserStats() {
        if (!this.isIdentified || !this.currentUser) return null;
        
        try {
            const response = await fetch(`/api/user-stats/${this.currentUser.id}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('ユーザー統計取得エラー:', error);
        }
        return null;
    }
}

// グローバルに公開
window.UserIdentificationManager = UserIdentificationManager;

// DOMが読み込まれたら初期化
document.addEventListener('DOMContentLoaded', () => {
    window.userIdentification = new UserIdentificationManager();
    console.log('👤 ユーザー識別システムが初期化されました');
});