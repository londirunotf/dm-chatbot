class AdminApp {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.setupCSRF();
    }

    initializeElements() {
        // FAQ管理要素
        this.addFaqBtn = document.getElementById('addFaqBtn');
        this.faqModal = document.getElementById('faqModal');
        this.modalClose = document.querySelector('.modal-close');
        this.faqForm = document.getElementById('faqForm');
        this.cancelBtn = document.getElementById('cancelBtn');
        
        // フォーム要素
        this.faqId = document.getElementById('faqId');
        this.modalTitle = document.getElementById('modalTitle');
        this.faqTitle = document.getElementById('faqTitle');
        this.faqCategory = document.getElementById('faqCategory');
        this.faqQuestion = document.getElementById('faqQuestion');
        this.faqAnswer = document.getElementById('faqAnswer');
        this.faqKeywords = document.getElementById('faqKeywords');
        this.faqActive = document.getElementById('faqActive');

        // テーブル要素
        this.editBtns = document.querySelectorAll('.edit-btn');
        this.toggleBtns = document.querySelectorAll('.toggle-btn');
        this.deleteBtns = document.querySelectorAll('.delete-btn');
    }

    setupCSRF() {
        this.csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    }

    attachEventListeners() {
        // FAQ追加ボタン
        this.addFaqBtn?.addEventListener('click', () => this.openAddModal());

        // モーダル制御
        this.modalClose?.addEventListener('click', () => this.closeModal());
        this.cancelBtn?.addEventListener('click', () => this.closeModal());
        this.faqModal?.addEventListener('click', (e) => {
            if (e.target === this.faqModal) this.closeModal();
        });

        // フォーム送信
        this.faqForm?.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // テーブル操作ボタン
        this.editBtns.forEach(btn => {
            btn.addEventListener('click', () => this.editFaq(btn.dataset.faqId));
        });

        this.toggleBtns.forEach(btn => {
            btn.addEventListener('click', () => this.toggleFaq(btn.dataset.faqId, btn.dataset.active === 'true'));
        });

        this.deleteBtns.forEach(btn => {
            btn.addEventListener('click', () => this.deleteFaq(btn.dataset.faqId));
        });

        // アクセシビリティ: Escapeキーでモーダルを閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.faqModal?.style.display === 'block') {
                this.closeModal();
            }
        });
    }

    openAddModal() {
        this.modalTitle.textContent = 'FAQ追加';
        this.resetForm();
        this.faqModal.style.display = 'block';
        this.faqTitle.focus();
    }

    editFaq(faqId) {
        const faq = window.faqData?.find(f => f.id == faqId);
        if (!faq) return;

        this.modalTitle.textContent = 'FAQ編集';
        this.faqId.value = faq.id;
        this.faqTitle.value = faq.title || '';
        this.faqCategory.value = faq.category || '';
        this.faqQuestion.value = faq.question || '';
        this.faqAnswer.value = faq.answer || '';
        this.faqKeywords.value = faq.keywords || '';
        this.faqActive.checked = faq.is_active;

        this.faqModal.style.display = 'block';
        this.faqTitle.focus();
    }

    closeModal() {
        this.faqModal.style.display = 'none';
        this.resetForm();
    }

    resetForm() {
        this.faqForm.reset();
        this.faqId.value = '';
        this.faqActive.checked = true;
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.faqForm);
        const data = Object.fromEntries(formData.entries());
        data.is_active = this.faqActive.checked;

        const isEdit = !!this.faqId.value;
        const url = isEdit ? `/admin/faq/${this.faqId.value}/edit` : '/admin/faq/add';
        const method = 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('FAQが正常に保存されました', 'success');
                this.closeModal();
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showMessage(result.error || 'エラーが発生しました', 'error');
            }
        } catch (error) {
            console.error('保存エラー:', error);
            this.showMessage('通信エラーが発生しました', 'error');
        }
    }

    async toggleFaq(faqId, currentActive) {
        if (!confirm(`このFAQを${currentActive ? '非アクティブ' : 'アクティブ'}にしますか？`)) {
            return;
        }

        try {
            const response = await fetch(`/admin/faq/${faqId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('FAQ状態が更新されました', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showMessage(result.error || 'エラーが発生しました', 'error');
            }
        } catch (error) {
            console.error('状態更新エラー:', error);
            this.showMessage('通信エラーが発生しました', 'error');
        }
    }

    async deleteFaq(faqId) {
        if (!confirm('このFAQを削除しますか？この操作は取り消せません。')) {
            return;
        }

        try {
            const response = await fetch(`/admin/faq/${faqId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('FAQが削除されました', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showMessage(result.error || 'エラーが発生しました', 'error');
            }
        } catch (error) {
            console.error('削除エラー:', error);
            this.showMessage('通信エラーが発生しました', 'error');
        }
    }

    showMessage(message, type) {
        // 既存のメッセージを削除
        const existingMessages = document.querySelectorAll('.temp-flash-message');
        existingMessages.forEach(msg => msg.remove());

        // 新しいメッセージを作成
        const messageDiv = document.createElement('div');
        messageDiv.className = `flash-message flash-${type} temp-flash-message`;
        messageDiv.textContent = message;

        // メッセージを挿入
        const adminMain = document.querySelector('.admin-main');
        adminMain.insertBefore(messageDiv, adminMain.firstChild);

        // 5秒後に自動削除
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

// DOMが読み込まれたらアプリを初期化
document.addEventListener('DOMContentLoaded', () => {
    new AdminApp();
});