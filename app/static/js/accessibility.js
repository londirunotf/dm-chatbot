/**
 * Accessibility features
 * Font size adjustment, High contrast, Keyboard navigation
 */

class AccessibilityManager {
    constructor() {
        this.initFontSizeControls();
        this.initContrastToggle();
        this.initKeyboardNavigation();
        this.loadUserPreferences();
    }

    // フォントサイズ調整機能
    initFontSizeControls() {
        const buttons = document.querySelectorAll('.font-size-btn');
        console.log(`フォントサイズボタンを初期化: ${buttons.length}個見つかりました`);
        
        buttons.forEach((button, index) => {
            console.log(`ボタン${index + 1}: data-size="${button.dataset.size}"`);
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const size = e.target.dataset.size;
                console.log(`🔘 フォントサイズボタンがクリックされました: ${size}`);
                this.setFontSize(size);
                this.savePreference('fontSize', size);
            });
        });
    }

    setFontSize(size) {
        const body = document.body;
        
        console.log(`フォントサイズ変更開始: ${size}`);
        console.log('変更前のクラス:', body.classList.toString());
        
        // 既存のフォントサイズクラスを削除
        body.classList.remove('font-small', 'font-medium', 'font-large', 'font-xlarge');
        
        // 新しいフォントサイズクラスを追加
        body.classList.add(`font-${size}`);
        
        console.log('変更後のクラス:', body.classList.toString());
        
        // アクティブボタンの更新
        document.querySelectorAll('.font-size-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`[data-size="${size}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
            console.log(`ボタン ${size} をアクティブに設定`);
        } else {
            console.error(`ボタン ${size} が見つかりません`);
        }
        
        // 実際のフォントサイズを確認
        const computedStyle = window.getComputedStyle(body);
        console.log('実際のフォントサイズ:', computedStyle.fontSize);
        
        console.log(`✅ フォントサイズを ${size} に変更しました`);
    }

    // ハイコントラスト機能
    initContrastToggle() {
        const contrastBtn = document.getElementById('contrastToggle');
        if (contrastBtn) {
            contrastBtn.addEventListener('click', () => {
                this.toggleHighContrast();
            });
        }
    }

    toggleHighContrast() {
        const body = document.body;
        const contrastBtn = document.getElementById('contrastToggle');
        
        body.classList.toggle('high-contrast');
        
        const isHighContrast = body.classList.contains('high-contrast');
        contrastBtn.classList.toggle('active', isHighContrast);
        contrastBtn.textContent = isHighContrast ? '☀️' : '🌓';
        contrastBtn.title = isHighContrast ? 'ノーマル表示に戻す' : 'ハイコントラスト表示';
        
        this.savePreference('highContrast', isHighContrast);
        console.log(`ハイコントラストモード: ${isHighContrast ? 'ON' : 'OFF'}`);
    }

    // キーボードナビゲーション強化
    initKeyboardNavigation() {
        // FAQアイテムをTabキーで選択可能にする
        const faqItems = document.querySelectorAll('.faq-item');
        faqItems.forEach((item, index) => {
            item.setAttribute('tabindex', '0');
            item.setAttribute('role', 'button');
            item.setAttribute('aria-label', `FAQ: ${item.querySelector('.faq-title')?.textContent}`);
            
            // Enterキーでクリック
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    item.click();
                }
            });
        });

        // チャット入力のキーボードショートカット
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                // Ctrl+Enter で送信
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    const sendButton = document.getElementById('sendButton');
                    if (sendButton) {
                        sendButton.click();
                    }
                }
                // Escキーでクリア
                else if (e.key === 'Escape') {
                    messageInput.value = '';
                    this.updateCharCount();
                }
            });
        }

        // グローバルキーボードショートカット
        document.addEventListener('keydown', (e) => {
            // Alt + 1-4 でフォントサイズ変更
            if (e.altKey && ['1', '2', '3', '4'].includes(e.key)) {
                e.preventDefault();
                const sizes = ['small', 'medium', 'large', 'xlarge'];
                const size = sizes[parseInt(e.key) - 1];
                this.setFontSize(size);
                this.savePreference('fontSize', size);
            }
            // Alt + C でハイコントラスト切り替え
            else if (e.altKey && e.key.toLowerCase() === 'c') {
                e.preventDefault();
                this.toggleHighContrast();
            }
            // Alt + F でFAQ検索にフォーカス
            else if (e.altKey && e.key.toLowerCase() === 'f') {
                e.preventDefault();
                const firstFaqItem = document.querySelector('.faq-item');
                if (firstFaqItem) {
                    firstFaqItem.focus();
                }
            }
            // Alt + M でメッセージ入力にフォーカス
            else if (e.altKey && e.key.toLowerCase() === 'm') {
                e.preventDefault();
                const messageInput = document.getElementById('messageInput');
                if (messageInput) {
                    messageInput.focus();
                }
            }
        });
    }

    // 文字数カウント更新（既存機能との連携）
    updateCharCount() {
        const messageInput = document.getElementById('messageInput');
        const charCount = document.getElementById('charCount');
        if (messageInput && charCount) {
            charCount.textContent = messageInput.value.length;
        }
    }

    // ユーザー設定の保存
    savePreference(key, value) {
        try {
            localStorage.setItem(`accessibility_${key}`, JSON.stringify(value));
        } catch (e) {
            console.warn('設定の保存に失敗しました:', e);
        }
    }

    // ユーザー設定の読み込み
    loadUserPreferences() {
        try {
            // フォントサイズの復元
            const savedFontSize = localStorage.getItem('accessibility_fontSize');
            if (savedFontSize) {
                const fontSize = JSON.parse(savedFontSize);
                console.log('保存されたフォントサイズを復元:', fontSize);
                this.setFontSize(fontSize);
            } else {
                // デフォルト設定を適用
                console.log('デフォルトフォントサイズを設定: medium');
                this.setFontSize('medium');
            }

            // ハイコントラストの復元
            const savedHighContrast = localStorage.getItem('accessibility_highContrast');
            if (savedHighContrast) {
                const isHighContrast = JSON.parse(savedHighContrast);
                console.log('保存されたハイコントラスト設定を復元:', isHighContrast);
                if (isHighContrast) {
                    this.toggleHighContrast();
                }
            }
        } catch (e) {
            console.error('設定の読み込みに失敗しました:', e);
            // デフォルト設定を適用
            this.setFontSize('medium');
        }
        
        // デバッグ: 現在のbodyクラスを確認
        console.log('現在のbodyのクラス:', document.body.classList.toString());
    }
}

// ページ読み込み完了後に初期化
function initializeAccessibility() {
    console.log('🚀 アクセシビリティマネージャーを初期化します...');
    
    // 既に初期化済みかチェック
    if (window.accessibilityManager) {
        console.log('既に初期化済みです');
        return;
    }
    
    try {
        window.accessibilityManager = new AccessibilityManager();
        console.log('✅ アクセシビリティマネージャーの初期化が完了しました');
        
        // ショートカットヘルプをコンソールに表示
        console.log(`
🎯 アクセシビリティ機能ショートカット:
Alt + 1-4: フォントサイズ変更 (小/中/大/特大)
Alt + C: ハイコントラスト切り替え
Alt + F: FAQ一覧にフォーカス
Alt + M: メッセージ入力にフォーカス
Ctrl + Enter: メッセージ送信
Escape: 入力欄クリア
Tab: 要素間の移動
Enter/Space: 選択した要素のアクション
        `);
    } catch (error) {
        console.error('❌ アクセシビリティマネージャーの初期化に失敗しました:', error);
    }
}

// 複数の方法で初期化を試行
document.addEventListener('DOMContentLoaded', initializeAccessibility);

// もしDOMContentLoadedが既に終わっていた場合の対策
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAccessibility);
} else {
    initializeAccessibility();
}

// 手動テスト用のグローバル関数
window.testFontSize = function(size) {
    console.log(`🧪 手動テスト: フォントサイズを ${size} に変更`);
    const body = document.body;
    
    // 既存のクラスを削除
    body.classList.remove('font-small', 'font-medium', 'font-large', 'font-xlarge');
    
    // 新しいクラスを追加
    body.classList.add(`font-${size}`);
    
    console.log('現在のbodyクラス:', body.classList.toString());
    console.log('計算されたフォントサイズ:', window.getComputedStyle(body).fontSize);
    
    return {
        classes: body.classList.toString(),
        fontSize: window.getComputedStyle(body).fontSize
    };
};