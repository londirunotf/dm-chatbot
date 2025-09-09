/**
 * FAQ Search and Filter Functionality
 * Enhanced search with category filtering, highlighting, and sorting
 */

class FAQSearchManager {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.initializeSearch();
        this.originalFAQs = this.getAllFAQItems();
    }

    initializeElements() {
        this.searchInput = document.getElementById('faqSearchInput');
        this.searchClear = document.getElementById('faqSearchClear');
        this.categoryFilter = document.getElementById('faqCategoryFilter');
        this.faqList = document.getElementById('faqList');
        this.searchResults = document.querySelector('.faq-search-results');
        this.searchResultCount = document.getElementById('faqSearchResultCount');
        this.noSearchResults = document.querySelector('.no-search-results');
    }

    attachEventListeners() {
        // 検索入力のイベント
        this.searchInput.addEventListener('input', (e) => {
            this.performSearch(e.target.value);
        });

        // 検索クリアボタン
        this.searchClear.addEventListener('click', () => {
            this.clearSearch();
        });

        // カテゴリフィルター
        this.categoryFilter.addEventListener('change', (e) => {
            this.filterByCategory(e.target.value);
        });

        // キーボードショートカット: Alt + F でFAQ検索にフォーカス
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key.toLowerCase() === 'f') {
                e.preventDefault();
                this.searchInput.focus();
            }
        });

        // Escapeキーで検索クリア
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
            }
        });
    }

    initializeSearch() {
        // 初期状態では検索結果表示を隠す
        this.searchResults.style.display = 'none';
        
        // 検索クリアボタンの表示制御
        this.updateClearButtonVisibility();
    }

    getAllFAQItems() {
        return Array.from(this.faqList.querySelectorAll('.faq-item'));
    }

    performSearch(query) {
        const trimmedQuery = query.trim().toLowerCase();
        const selectedCategory = this.categoryFilter.value;
        
        if (!trimmedQuery && !selectedCategory) {
            this.showAllFAQs();
            return;
        }

        const matchingFAQs = this.originalFAQs.filter(faq => {
            const searchText = faq.dataset.searchText || '';
            const category = faq.dataset.category || '';
            
            const matchesQuery = !trimmedQuery || searchText.includes(trimmedQuery);
            const matchesCategory = !selectedCategory || category === selectedCategory;
            
            return matchesQuery && matchesCategory;
        });

        this.displaySearchResults(matchingFAQs, trimmedQuery);
        this.updateClearButtonVisibility();
    }

    filterByCategory(category) {
        const query = this.searchInput.value.trim().toLowerCase();
        
        if (!category && !query) {
            this.showAllFAQs();
            return;
        }

        const matchingFAQs = this.originalFAQs.filter(faq => {
            const searchText = faq.dataset.searchText || '';
            const faqCategory = faq.dataset.category || '';
            
            const matchesQuery = !query || searchText.includes(query);
            const matchesCategory = !category || faqCategory === category;
            
            return matchesQuery && matchesCategory;
        });

        this.displaySearchResults(matchingFAQs, query);
    }

    displaySearchResults(matchingFAQs, query) {
        // すべてのFAQアイテムを非表示にする
        this.originalFAQs.forEach(faq => {
            faq.style.display = 'none';
            faq.classList.remove('search-highlight');
        });

        // 検索結果を表示
        if (matchingFAQs.length > 0) {
            matchingFAQs.forEach(faq => {
                faq.style.display = 'block';
                if (query) {
                    faq.classList.add('search-highlight');
                    this.highlightSearchTerms(faq, query);
                }
            });
            
            // 関連度でソート（より関連性の高いものを上に）
            this.sortFAQsByRelevance(matchingFAQs, query);
            
            this.noSearchResults.style.display = 'none';
        } else {
            this.noSearchResults.style.display = 'block';
        }

        // 検索結果カウントを更新
        this.updateSearchResultCount(matchingFAQs.length);
        this.searchResults.style.display = 'block';
    }

    highlightSearchTerms(faqElement, query) {
        if (!query) return;

        const title = faqElement.querySelector('.faq-title');
        const preview = faqElement.querySelector('.faq-preview');
        
        if (title) {
            title.innerHTML = this.highlightText(title.textContent, query);
        }
        if (preview) {
            preview.innerHTML = this.highlightText(preview.textContent, query);
        }
    }

    highlightText(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${this.escapeRegExp(query)})`, 'gi');
        return text.replace(regex, '<mark class="search-highlight-text">$1</mark>');
    }

    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    sortFAQsByRelevance(faqs, query) {
        if (!query) return;

        faqs.sort((a, b) => {
            const scoreA = this.calculateRelevanceScore(a, query);
            const scoreB = this.calculateRelevanceScore(b, query);
            return scoreB - scoreA;
        });

        // DOM内での順序を更新
        faqs.forEach((faq, index) => {
            faq.style.order = index;
        });
    }

    calculateRelevanceScore(faq, query) {
        const title = faq.querySelector('.faq-title')?.textContent.toLowerCase() || '';
        const preview = faq.querySelector('.faq-preview')?.textContent.toLowerCase() || '';
        const keywords = faq.dataset.keywords?.toLowerCase() || '';
        
        let score = 0;
        
        // タイトルでの一致は高スコア
        if (title.includes(query)) score += 10;
        
        // キーワードでの一致は中スコア
        if (keywords.includes(query)) score += 5;
        
        // プレビューでの一致は低スコア
        if (preview.includes(query)) score += 2;
        
        // 完全一致はボーナス
        if (title === query || keywords.split(',').some(k => k.trim() === query)) {
            score += 20;
        }
        
        return score;
    }

    showAllFAQs() {
        this.originalFAQs.forEach(faq => {
            faq.style.display = 'block';
            faq.style.order = '';
            faq.classList.remove('search-highlight');
            
            // ハイライトを削除
            const title = faq.querySelector('.faq-title');
            const preview = faq.querySelector('.faq-preview');
            
            if (title && title.innerHTML.includes('<mark')) {
                title.innerHTML = title.textContent;
            }
            if (preview && preview.innerHTML.includes('<mark')) {
                preview.innerHTML = preview.textContent;
            }
        });

        this.noSearchResults.style.display = 'none';
        this.searchResults.style.display = 'none';
    }

    clearSearch() {
        this.searchInput.value = '';
        this.categoryFilter.value = '';
        this.showAllFAQs();
        this.updateClearButtonVisibility();
        this.searchInput.focus();
    }

    updateSearchResultCount(count) {
        this.searchResultCount.textContent = `${count}件の検索結果`;
    }

    updateClearButtonVisibility() {
        const hasContent = this.searchInput.value.trim().length > 0 || this.categoryFilter.value;
        this.searchClear.style.display = hasContent ? 'flex' : 'none';
    }

    // 外部から呼び出し可能な検索メソッド
    searchFAQ(query) {
        this.searchInput.value = query;
        this.performSearch(query);
    }

    // カテゴリ統計取得
    getCategoryStats() {
        const stats = {};
        this.originalFAQs.forEach(faq => {
            const category = faq.dataset.category || '未分類';
            stats[category] = (stats[category] || 0) + 1;
        });
        return stats;
    }

    // 人気FAQ取得（閲覧数ベース）
    getPopularFAQs(limit = 5) {
        return this.originalFAQs
            .map(faq => ({
                element: faq,
                viewCount: parseInt(faq.querySelector('.faq-stats')?.textContent.match(/\d+/)?.[0] || '0')
            }))
            .sort((a, b) => b.viewCount - a.viewCount)
            .slice(0, limit)
            .map(item => item.element);
    }

    // 人気FAQセクションの初期化
    initializePopularFAQs() {
        const popularFAQSection = document.getElementById('popularFaqSection');
        const popularFAQList = document.getElementById('popularFaqList');
        
        if (!popularFAQSection || !popularFAQList) return;

        // 人気FAQを取得（上位5件）
        const popularFAQs = this.getPopularFAQs(5);
        
        if (popularFAQs.length === 0) {
            // 人気FAQがない場合は、最初の5件を表示
            const topFAQs = this.originalFAQs.slice(0, 5);
            this.renderPopularFAQs(topFAQs, popularFAQList);
        } else {
            this.renderPopularFAQs(popularFAQs, popularFAQList);
        }
    }

    // 人気FAQをレンダリング
    renderPopularFAQs(faqs, container) {
        container.innerHTML = '';
        
        faqs.forEach(faq => {
            const faqId = faq.dataset.faqId;
            const title = faq.querySelector('.faq-title')?.textContent || '';
            const viewCount = faq.querySelector('.faq-stats')?.textContent?.match(/\d+/)?.[0] || '0';
            
            const popularItem = document.createElement('div');
            popularItem.className = 'popular-faq-item';
            popularItem.dataset.faqId = faqId;
            popularItem.innerHTML = `
                <div class="popular-faq-item-title">${title}</div>
                <div class="popular-faq-item-stats">閲覧数: ${viewCount}回</div>
            `;
            
            // ダブルクリックイベントを追加
            popularItem.addEventListener('dblclick', () => {
                if (window.chatApp && window.chatApp.showFaqModal) {
                    window.chatApp.showFaqModal(faqId);
                } else if (window.showFaqModal) {
                    window.showFaqModal(faqId);
                }
            });
            
            container.appendChild(popularItem);
        });
    }

    // 検索時に人気FAQセクションの表示制御
    showAllFAQs() {
        super.showAllFAQs();
        // 検索クリア時に人気FAQセクションを表示
        const popularFAQSection = document.getElementById('popularFaqSection');
        if (popularFAQSection) {
            popularFAQSection.style.display = 'block';
        }
    }

    performSearch(query) {
        super.performSearch(query);
        // 検索中は人気FAQセクションを隠す
        const popularFAQSection = document.getElementById('popularFaqSection');
        if (popularFAQSection && query.trim()) {
            popularFAQSection.style.display = 'none';
        } else if (popularFAQSection) {
            popularFAQSection.style.display = 'block';
        }
    }
}

// CSS for search highlights
const searchHighlightStyles = `
<style>
.search-highlight-text {
    background-color: #ffeb3b;
    color: #000;
    padding: 1px 2px;
    border-radius: 2px;
    font-weight: bold;
}

body.high-contrast .search-highlight-text {
    background-color: #fff;
    color: #000;
    border: 1px solid #000;
}

.faq-list {
    display: flex;
    flex-direction: column;
}
</style>
`;

// スタイルを追加
document.head.insertAdjacentHTML('beforeend', searchHighlightStyles);

// DOMが読み込まれたら初期化
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('faqSearchInput')) {
        window.faqSearchManager = new FAQSearchManager();
        
        // 人気FAQセクションを初期化
        window.faqSearchManager.initializePopularFAQs();
        
        // デバッグ用のグローバル関数
        window.searchFAQ = (query) => window.faqSearchManager.searchFAQ(query);
        window.getFAQStats = () => window.faqSearchManager.getCategoryStats();
        
        console.log('🔍 FAQ検索機能が初期化されました');
        console.log('🔥 人気FAQセクションが追加されました');
        console.log('利用可能なショートカット:');
        console.log('- Alt + F: FAQ検索にフォーカス');
        console.log('- Escape: 検索クリア');
    }
});