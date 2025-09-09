/**
 * 認証関連JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // パスワード表示切り替え機能
    window.togglePassword = function(inputId = 'password') {
        const passwordInput = document.getElementById(inputId);
        const toggleButton = passwordInput.parentNode.querySelector('.password-toggle');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleButton.textContent = '🙈';
            toggleButton.title = 'パスワードを非表示';
        } else {
            passwordInput.type = 'password';
            toggleButton.textContent = '👁️';
            toggleButton.title = 'パスワードを表示';
        }
    };
    
    // フォームバリデーション
    const authForm = document.querySelector('.auth-form');
    if (authForm) {
        authForm.addEventListener('submit', function(e) {
            const submitButton = authForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // ローディング状態
            submitButton.innerHTML = '<span class="button-icon">⏳</span>処理中...';
            submitButton.disabled = true;
            
            // フォームバリデーション
            const userIdInput = document.getElementById('user_id');
            const passwordInput = document.getElementById('password');
            
            if (userIdInput && !userIdInput.value.trim()) {
                e.preventDefault();
                showError('ユーザーIDを入力してください');
                resetSubmitButton(submitButton, originalText);
                return;
            }
            
            if (passwordInput && !passwordInput.value) {
                e.preventDefault();
                showError('パスワードを入力してください');
                resetSubmitButton(submitButton, originalText);
                return;
            }
            
            // パスワード変更時の追加バリデーション
            const newPasswordInput = document.getElementById('new_password');
            const confirmPasswordInput = document.getElementById('confirm_password');
            
            if (newPasswordInput && confirmPasswordInput) {
                if (newPasswordInput.value !== confirmPasswordInput.value) {
                    e.preventDefault();
                    showError('新しいパスワードが一致しません');
                    resetSubmitButton(submitButton, originalText);
                    return;
                }
                
                if (newPasswordInput.value.length < 6) {
                    e.preventDefault();
                    showError('パスワードは6文字以上で入力してください');
                    resetSubmitButton(submitButton, originalText);
                    return;
                }
            }
            
            // 3秒後にタイムアウト処理（ネットワークエラー対策）
            setTimeout(() => {
                if (submitButton.disabled) {
                    resetSubmitButton(submitButton, originalText);
                    showError('処理に時間がかかっています。再度お試しください。');
                }
            }, 10000);
        });
    }
    
    // Enter キーでフォーム送信
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && authForm) {
            const activeElement = document.activeElement;
            if (activeElement && activeElement.tagName === 'INPUT') {
                authForm.requestSubmit();
            }
        }
    });
    
    // 自動フォーカス
    const firstInput = authForm?.querySelector('input[type="text"], input[type="password"]');
    if (firstInput) {
        firstInput.focus();
    }
    
    // セッション有効性チェック（ログイン後のページ用）
    if (window.location.pathname !== '/auth/login') {
        checkSessionValidity();
    }
    
    // フラッシュメッセージの自動非表示
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        if (message.classList.contains('flash-success')) {
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            }, 3000);
        }
    });
});

function resetSubmitButton(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

function showError(message) {
    // 既存のエラーメッセージを削除
    const existingErrors = document.querySelectorAll('.flash-error.temp-error');
    existingErrors.forEach(error => error.remove());
    
    // 新しいエラーメッセージを作成
    const errorDiv = document.createElement('div');
    errorDiv.className = 'flash-message flash-error temp-error';
    errorDiv.textContent = message;
    
    // フォームの前に挿入
    const authForm = document.querySelector('.auth-form');
    if (authForm) {
        authForm.parentNode.insertBefore(errorDiv, authForm);
        
        // エラーメッセージを5秒後に自動削除
        setTimeout(() => {
            errorDiv.style.opacity = '0';
            setTimeout(() => errorDiv.remove(), 300);
        }, 5000);
    }
}

function checkSessionValidity() {
    // セッション有効性を定期的にチェック
    setInterval(async () => {
        try {
            const response = await fetch('/auth/check-session');
            const result = await response.json();
            
            if (!result.valid) {
                // セッション無効の場合はログイン画面にリダイレクト
                showError('セッションが無効になりました。再度ログインしてください。');
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 2000);
            }
        } catch (error) {
            console.warn('セッションチェックでエラーが発生しました:', error);
        }
    }, 300000); // 5分ごとにチェック
}

// パスワード強度チェック（パスワード変更時）
function checkPasswordStrength(password) {
    let strength = 0;
    let feedback = [];
    
    if (password.length >= 8) {
        strength += 1;
    } else {
        feedback.push('8文字以上');
    }
    
    if (/[A-Z]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('大文字を含む');
    }
    
    if (/[a-z]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('小文字を含む');
    }
    
    if (/[0-9]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('数字を含む');
    }
    
    if (/[^A-Za-z0-9]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('記号を含む');
    }
    
    return {
        strength: strength,
        feedback: feedback,
        level: strength < 2 ? 'weak' : strength < 4 ? 'medium' : 'strong'
    };
}

// パスワード変更画面での強度表示
document.addEventListener('DOMContentLoaded', function() {
    const newPasswordInput = document.getElementById('new_password');
    if (newPasswordInput) {
        // パスワード強度インジケーターを作成
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength';
        strengthIndicator.innerHTML = `
            <div class="strength-bar">
                <div class="strength-fill"></div>
            </div>
            <div class="strength-text"></div>
        `;
        
        newPasswordInput.parentNode.appendChild(strengthIndicator);
        
        newPasswordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            const fill = strengthIndicator.querySelector('.strength-fill');
            const text = strengthIndicator.querySelector('.strength-text');
            
            // 強度バーの更新
            fill.style.width = (strength.strength * 20) + '%';
            fill.className = `strength-fill ${strength.level}`;
            
            // フィードバックテキストの更新
            if (password.length === 0) {
                text.textContent = '';
            } else if (strength.level === 'weak') {
                text.textContent = '弱い: ' + strength.feedback.join(', ');
                text.className = 'strength-text weak';
            } else if (strength.level === 'medium') {
                text.textContent = '普通: より安全にするには ' + strength.feedback.join(', ');
                text.className = 'strength-text medium';
            } else {
                text.textContent = '強い: 安全なパスワードです';
                text.className = 'strength-text strong';
            }
        });
    }
});

// アクセシビリティ向上
document.addEventListener('keydown', function(e) {
    // Escapeキーでモーダルを閉じる（将来の拡張用）
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.active');
        modals.forEach(modal => modal.classList.remove('active'));
    }
    
    // Tab キーでのフォーカス管理
    if (e.key === 'Tab') {
        const focusableElements = document.querySelectorAll(
            'input, button, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
        }
    }
});