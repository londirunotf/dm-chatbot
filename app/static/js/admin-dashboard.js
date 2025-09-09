/**
 * Enhanced Admin Dashboard Functionality
 * Real-time updates, charts, alerts, and reporting
 */

class AdminDashboard {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.setupRealtimeUpdates();
        this.initializeChart();
        this.loadFAQRanking();
        this.updateLastRefreshTime();
        this.checkForAlerts();
    }

    initializeElements() {
        this.refreshButton = document.getElementById('refreshDashboard');
        this.lastUpdated = document.getElementById('lastUpdated');
        this.usageChart = document.getElementById('usageChart');
        this.faqRanking = document.getElementById('faqRanking');
        this.activityList = document.getElementById('activityList');
        this.dashboardAlerts = document.getElementById('dashboardAlerts');
        
        // Report modal elements
        this.reportModal = document.getElementById('reportModal');
        this.generateReportBtn = document.getElementById('generateReportBtn');
        this.reportType = document.getElementById('reportType');
        this.reportPeriod = document.getElementById('reportPeriod');
        this.customDateRange = document.getElementById('customDateRange');
        
        // Quick action buttons
        this.generateReportAction = document.getElementById('generateReport');
        this.systemMaintenanceAction = document.getElementById('systemMaintenance');
        this.filterActivityBtn = document.getElementById('filterActivity');
    }

    attachEventListeners() {
        // Refresh dashboard
        this.refreshButton.addEventListener('click', () => {
            this.refreshDashboard();
        });

        // Report generation
        this.generateReportAction.addEventListener('click', (e) => {
            e.preventDefault();
            this.showReportModal();
        });

        this.generateReportBtn.addEventListener('click', () => {
            this.generateReport();
        });

        // Report period change
        this.reportPeriod.addEventListener('change', (e) => {
            this.toggleCustomDateRange(e.target.value === 'custom');
        });

        // Modal controls
        const modalCloses = this.reportModal.querySelectorAll('.modal-close');
        modalCloses.forEach(close => {
            close.addEventListener('click', () => {
                this.hideReportModal();
            });
        });

        // Click outside modal to close
        this.reportModal.addEventListener('click', (e) => {
            if (e.target === this.reportModal) {
                this.hideReportModal();
            }
        });

        // System maintenance
        this.systemMaintenanceAction.addEventListener('click', (e) => {
            e.preventDefault();
            this.showMaintenanceDialog();
        });

        // Activity filter
        this.filterActivityBtn.addEventListener('click', () => {
            this.toggleActivityFilter();
        });

        // Alert dismiss and action buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('alert-dismiss')) {
                this.dismissAlert(e.target.closest('.alert-item'));
            }
            // 「対応する」ボタンのクリック処理
            if (e.target.textContent === '対応する' && e.target.classList.contains('btn-primary')) {
                this.handleEscalationAction(e);
            }
        });

        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.refreshDashboard();
        }, 5 * 60 * 1000);

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key.toLowerCase() === 'r') {
                e.preventDefault();
                this.refreshDashboard();
            }
            // テスト用ショートカット（Alt + T で警告テスト）
            if (e.altKey && e.key.toLowerCase() === 't') {
                e.preventDefault();
                this.testAlert();
            }
        });
    }

    setupRealtimeUpdates() {
        // Check for new escalations every 30 seconds
        setInterval(() => {
            this.checkForNewEscalations();
        }, 30000);

        // Update activity feed every 2 minutes
        setInterval(() => {
            this.updateActivityFeed();
        }, 2 * 60 * 1000);
    }

    async refreshDashboard() {
        try {
            this.refreshButton.style.transform = 'rotate(360deg)';
            this.refreshButton.disabled = true;

            // Simulate API calls for now
            await Promise.all([
                this.updateStatistics(),
                this.updateChart(),
                this.loadFAQRanking(),
                this.updateActivityFeed(),
                this.checkForAlerts()
            ]);

            this.updateLastRefreshTime();
            this.showNotification('ダッシュボードが更新されました', 'success');

        } catch (error) {
            console.error('Dashboard refresh failed:', error);
            this.showNotification('更新中にエラーが発生しました', 'error');
        } finally {
            this.refreshButton.disabled = false;
            setTimeout(() => {
                this.refreshButton.style.transform = 'rotate(0deg)';
            }, 300);
        }
    }

    async updateStatistics() {
        // Simulate API call to get updated statistics
        // In real implementation, this would fetch from backend
        return new Promise(resolve => {
            setTimeout(() => {
                // Update stat cards with animation
                const statNumbers = document.querySelectorAll('.stat-number');
                statNumbers.forEach(stat => {
                    this.animateNumber(stat);
                });
                resolve();
            }, 500);
        });
    }

    animateNumber(element) {
        const target = parseInt(element.textContent);
        const duration = 1000;
        const step = Math.ceil(target / (duration / 16));
        let current = 0;

        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = current;
        }, 16);
    }

    initializeChart() {
        if (!this.usageChart) return;

        const ctx = this.usageChart.getContext('2d');
        
        // Simple chart implementation (in real app, use Chart.js or similar)
        this.drawSimpleChart(ctx);
    }

    drawSimpleChart(ctx) {
        const width = ctx.canvas.width;
        const height = ctx.canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Sample data
        const data = [12, 18, 8, 15, 25, 22, 30];
        const escalationData = [2, 3, 1, 2, 5, 4, 6];
        const labels = ['月', '火', '水', '木', '金', '土', '日'];
        
        const maxValue = Math.max(...data, ...escalationData) * 1.2;
        const barWidth = width / (data.length * 2 + 1);
        const chartHeight = height - 40;
        
        // Draw bars
        data.forEach((value, index) => {
            const barHeight = (value / maxValue) * chartHeight;
            const x = (index * 2 + 1) * barWidth;
            const y = height - barHeight - 20;
            
            // Conversations bar
            ctx.fillStyle = '#2196F3';
            ctx.fillRect(x, y, barWidth * 0.8, barHeight);
            
            // Escalation bar
            const escHeight = (escalationData[index] / maxValue) * chartHeight;
            const escY = height - escHeight - 20;
            ctx.fillStyle = '#f44336';
            ctx.fillRect(x + barWidth * 0.8 + 2, escY, barWidth * 0.8, escHeight);
            
            // Labels
            ctx.fillStyle = '#666';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(labels[index], x + barWidth, height - 5);
        });
        
        // Add text if no chart library
        ctx.fillStyle = '#999';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('過去7日間の利用状況', width / 2, 20);
    }

    async updateChart() {
        if (!this.usageChart) return;
        
        // Redraw chart with new data
        const ctx = this.usageChart.getContext('2d');
        this.drawSimpleChart(ctx);
    }

    async loadFAQRanking() {
        if (!this.faqRanking) return;

        try {
            // Simulate loading FAQ ranking data
            const mockFAQs = [
                { title: '送信権限の確認方法', views: 245, trend: '+12%' },
                { title: 'DMの宛先追加手順', views: 189, trend: '+8%' },
                { title: 'エラー対処法', views: 156, trend: '-3%' },
                { title: '添付ファイルの制限', views: 134, trend: '+15%' },
                { title: 'システムメンテナンス情報', views: 98, trend: '+5%' }
            ];

            this.faqRanking.innerHTML = mockFAQs.map((faq, index) => `
                <div class="ranking-item">
                    <div class="rank">${index + 1}</div>
                    <div class="faq-info">
                        <div class="faq-title">${faq.title}</div>
                        <div class="faq-stats">${faq.views}回閲覧 • ${faq.trend}</div>
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('Failed to load FAQ ranking:', error);
            this.faqRanking.innerHTML = '<div class="ranking-item">データの読み込みに失敗しました</div>';
        }
    }

    async updateActivityFeed() {
        if (!this.activityList) return;

        try {
            // In real implementation, fetch from API
            const mockActivities = [
                {
                    icon: '💬',
                    title: '新しい質問が投稿されました',
                    meta: `${this.getRandomMinutes()}分前 • ユーザー#${Math.floor(Math.random() * 9999)}`,
                    status: 'pending'
                },
                {
                    icon: '✅',
                    title: 'FAQ「送信権限について」が更新されました',
                    meta: `${this.getRandomHours()}時間前 • 管理者`,
                    status: 'completed'
                },
                {
                    icon: '🔍',
                    title: `FAQ検索「${this.getRandomSearchTerm()}」が実行されました`,
                    meta: `${this.getRandomHours()}時間前 • ユーザー#${Math.floor(Math.random() * 9999)}`,
                    status: 'info'
                }
            ];

            // Add new activities to the top
            const existingItems = Array.from(this.activityList.querySelectorAll('.activity-item'));
            if (existingItems.length > 0) {
                // Keep only recent activities
                while (existingItems.length > 5) {
                    existingItems.pop().remove();
                }
            }

            // Add new activity
            const newActivity = mockActivities[0];
            const activityHTML = `
                <div class="activity-item" style="opacity: 0; transform: translateY(-10px);">
                    <div class="activity-icon">${newActivity.icon}</div>
                    <div class="activity-content">
                        <div class="activity-title">${newActivity.title}</div>
                        <div class="activity-meta">${newActivity.meta}</div>
                    </div>
                    <div class="activity-status ${newActivity.status}">${this.getStatusLabel(newActivity.status)}</div>
                </div>
            `;

            this.activityList.insertAdjacentHTML('afterbegin', activityHTML);
            
            // Animate new item
            const newItem = this.activityList.firstElementChild;
            setTimeout(() => {
                newItem.style.transition = 'all 0.3s ease-out';
                newItem.style.opacity = '1';
                newItem.style.transform = 'translateY(0)';
            }, 100);

        } catch (error) {
            console.error('Failed to update activity feed:', error);
        }
    }

    getRandomMinutes() {
        return Math.floor(Math.random() * 60) + 1;
    }

    getRandomHours() {
        return Math.floor(Math.random() * 24) + 1;
    }

    getRandomSearchTerm() {
        const terms = ['不明な宛先', '送信エラー', 'ファイル添付', '権限設定', 'メンテナンス'];
        return terms[Math.floor(Math.random() * terms.length)];
    }

    getStatusLabel(status) {
        const labels = {
            'pending': '対応待ち',
            'completed': '完了',
            'info': '参考'
        };
        return labels[status] || status;
    }

    async checkForNewEscalations() {
        // Simulate checking for new escalations
        const hasNewEscalations = Math.random() < 0.1; // 10% chance
        
        if (hasNewEscalations) {
            this.showAlert('新しい質問が投稿されました', '緊急対応が必要な質問があります。', 'high');
        }
    }

    async checkForAlerts() {
        // 実際のエスカレーション件数を確認
        try {
            const pendingEscalations = parseInt(document.querySelector('.stat-card.urgent .stat-number').textContent) || 0;
            
            // 10件以上の場合のみ警告表示
            if (pendingEscalations >= 10 && this.dashboardAlerts) {
                // 警告メッセージを更新
                const alertMessage = document.getElementById('alertMessage');
                if (alertMessage) {
                    alertMessage.textContent = `現在${pendingEscalations}件の未解決質問があります。`;
                }
                
                setTimeout(() => {
                    this.dashboardAlerts.style.display = 'flex';
                }, 2000);
            } else {
                // 条件を満たさない場合は警告を非表示
                if (this.dashboardAlerts) {
                    this.dashboardAlerts.style.display = 'none';
                }
            }
        } catch (error) {
            console.log('Alert check error:', error);
        }
    }

    showAlert(title, message, level = 'info') {
        if (!this.dashboardAlerts) return;

        const alertHTML = `
            <div class="alert-item ${level}" style="opacity: 0; transform: translateX(100%);">
                <div class="alert-icon">${this.getAlertIcon(level)}</div>
                <div class="alert-content">
                    <div class="alert-title">${title}</div>
                    <div class="alert-message">${message}</div>
                </div>
                <div class="alert-actions">
                    <button type="button" class="btn btn-small btn-primary">対応する</button>
                    <button type="button" class="btn btn-small btn-link alert-dismiss">閉じる</button>
                </div>
            </div>
        `;

        this.dashboardAlerts.insertAdjacentHTML('beforeend', alertHTML);
        this.dashboardAlerts.style.display = 'flex';

        // Animate in
        const newAlert = this.dashboardAlerts.lastElementChild;
        setTimeout(() => {
            newAlert.style.transition = 'all 0.3s ease-out';
            newAlert.style.opacity = '1';
            newAlert.style.transform = 'translateX(0)';
        }, 100);

        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            this.dismissAlert(newAlert);
        }, 10000);
    }

    getAlertIcon(level) {
        const icons = {
            'high': '🚨',
            'medium': '⚠️',
            'low': 'ℹ️',
            'info': 'ℹ️'
        };
        return icons[level] || 'ℹ️';
    }

    dismissAlert(alertElement) {
        if (!alertElement) return;

        alertElement.style.transition = 'all 0.3s ease-in';
        alertElement.style.opacity = '0';
        alertElement.style.transform = 'translateX(100%)';

        setTimeout(() => {
            alertElement.remove();
            
            // Hide container if no alerts remain
            if (this.dashboardAlerts && this.dashboardAlerts.children.length === 0) {
                this.dashboardAlerts.style.display = 'none';
            }
        }, 300);
    }

    handleEscalationAction(event) {
        event.preventDefault();
        
        // エスカレーション一覧ページに遷移
        window.location.href = '/admin/escalations';
    }

    testAlert() {
        // テスト用：警告を強制表示
        console.log('警告テスト実行');
        if (this.dashboardAlerts) {
            const alertMessage = document.getElementById('alertMessage');
            if (alertMessage) {
                alertMessage.textContent = 'テスト警告: 現在7件の未解決質問があります。（実際は10件以上の場合のみ表示）';
            }
            this.dashboardAlerts.style.display = 'flex';
            this.showNotification('警告テストを実行しました（Alt + T）', 'info');
        }
    }

    showReportModal() {
        if (this.reportModal) {
            this.reportModal.style.display = 'block';
            this.reportType.focus();
        }
    }

    hideReportModal() {
        if (this.reportModal) {
            this.reportModal.style.display = 'none';
        }
    }

    toggleCustomDateRange(show) {
        if (this.customDateRange) {
            this.customDateRange.style.display = show ? 'grid' : 'none';
        }
    }

    async generateReport() {
        const reportType = this.reportType.value;
        const period = this.reportPeriod.value;
        
        try {
            this.generateReportBtn.disabled = true;
            this.generateReportBtn.textContent = '生成中...';

            // Simulate report generation
            await new Promise(resolve => setTimeout(resolve, 2000));

            // In real implementation, this would call the backend API
            const reportData = this.mockReportGeneration(reportType, period);
            
            this.downloadReport(reportData, reportType);
            this.showNotification('レポートが生成されました', 'success');
            this.hideReportModal();

        } catch (error) {
            console.error('Report generation failed:', error);
            this.showNotification('レポート生成中にエラーが発生しました', 'error');
        } finally {
            this.generateReportBtn.disabled = false;
            this.generateReportBtn.textContent = 'レポート生成';
        }
    }

    mockReportGeneration(type, period) {
        const reportTypes = {
            'conversations': '会話レポート',
            'faq_usage': 'FAQ利用状況',
            'escalations': 'エスカレーション分析',
            'user_satisfaction': 'ユーザー満足度'
        };

        const data = {
            title: reportTypes[type] || 'レポート',
            period: period,
            generated: new Date().toISOString(),
            data: `${reportTypes[type]}のサンプルデータ\n期間: ${period}\n生成日時: ${new Date().toLocaleString('ja-JP')}`
        };

        return data;
    }

    downloadReport(reportData, type) {
        const blob = new Blob([reportData.data], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportData.title}_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showMaintenanceDialog() {
        const confirmed = confirm('システムメンテナンスモードに入りますか？\n※ユーザーのアクセスが一時的に制限されます。');
        
        if (confirmed) {
            this.showNotification('メンテナンスモードは未実装です', 'info');
        }
    }

    toggleActivityFilter() {
        const filterOptions = ['すべて', '対応待ち', '完了', '参考'];
        const currentFilter = this.filterActivityBtn.dataset.filter || 'すべて';
        const currentIndex = filterOptions.indexOf(currentFilter);
        const nextFilter = filterOptions[(currentIndex + 1) % filterOptions.length];
        
        this.filterActivityBtn.dataset.filter = nextFilter;
        this.filterActivityBtn.textContent = `フィルター: ${nextFilter}`;
        
        this.applyActivityFilter(nextFilter);
    }

    applyActivityFilter(filter) {
        const activities = this.activityList.querySelectorAll('.activity-item');
        
        activities.forEach(activity => {
            const status = activity.querySelector('.activity-status');
            if (!status) return;
            
            const statusText = status.textContent.trim();
            const shouldShow = filter === 'すべて' || statusText === filter;
            
            activity.style.display = shouldShow ? 'flex' : 'none';
        });
    }

    updateLastRefreshTime() {
        if (this.lastUpdated) {
            const now = new Date();
            this.lastUpdated.textContent = `最終更新: ${now.toLocaleTimeString('ja-JP', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })}`;
        }
    }

    showNotification(message, type = 'info') {
        // Reuse the notification system from the chat app
        if (window.chatApp && window.chatApp.showNotification) {
            window.chatApp.showNotification(message, type);
        } else {
            // Fallback notification
            console.log(`${type.toUpperCase()}: ${message}`);
            
            // Simple toast notification 
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4CAF50' : '#2196F3'};
                color: white;
                border-radius: 4px;
                z-index: 10000;
                font-size: 14px;
                opacity: 0;
                transform: translateY(-20px);
                transition: all 0.3s ease;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // Animate in
            setTimeout(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateY(0)';
            }, 100);
            
            // Remove after 3 seconds
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-20px)';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.dashboard')) {
        window.adminDashboard = new AdminDashboard();
        
        console.log('🎛️ 管理ダッシュボードが初期化されました');
        console.log('利用可能なショートカット:');
        console.log('- Alt + R: ダッシュボード更新');
        console.log('- Alt + T: 警告表示テスト');
    }
});