from app import db
from datetime import datetime

class FAQ(db.Model):
    __tablename__ = 'faq'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text)  # 検索用キーワード（カンマ区切り）
    category = db.Column(db.String(100))  # カテゴリ分類
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)  # 参照回数
    
    def __repr__(self):
        return f'<FAQ {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'question': self.question,
            'answer': self.answer,
            'keywords': self.keywords,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'view_count': self.view_count
        }
    
    @staticmethod
    def search(query):
        """FAQ検索機能 - より柔軟な検索"""
        import re
        
        # 簡単な日本語キーワード抽出
        # 句読点や助詞を区切り文字として使用
        # まず、句読点や記号で分割
        import re
        temp_words = re.split(r'[、。！？\?\!\s　]+', query)
        
        # さらに助詞で分割（簡単なパターンのみ）
        words = []
        for word in temp_words:
            if word:
                # 「の」「を」「に」「は」「が」「で」「と」「から」「まで」で分割
                sub_words = re.split(r'[のをにはがでとからまで]+', word)
                words.extend([w for w in sub_words if w])
        
        # 最低2文字以上の単語のみを使用
        keywords = [word for word in words if len(word) >= 2]
        
        if not keywords:
            # キーワードが見つからない場合は元のクエリで検索
            return FAQ.query.filter(
                db.or_(
                    FAQ.title.contains(query),
                    FAQ.question.contains(query),
                    FAQ.answer.contains(query),
                    FAQ.keywords.contains(query),
                    FAQ.category.contains(query)  # カテゴリ検索を追加
                ),
                FAQ.is_active == True
            ).order_by(FAQ.view_count.desc()).all()
        
        # 各キーワードに対する検索条件を作成
        conditions = []
        for keyword in keywords:
            word_conditions = db.or_(
                FAQ.title.contains(keyword),
                FAQ.question.contains(keyword),
                FAQ.answer.contains(keyword),
                FAQ.keywords.contains(keyword),
                FAQ.category.contains(keyword)  # カテゴリ検索を追加
            )
            conditions.append(word_conditions)
        
        # いずれかのキーワードにマッチするFAQを返す
        return FAQ.query.filter(
            db.or_(*conditions),
            FAQ.is_active == True
        ).order_by(FAQ.view_count.desc()).all()
    
    @staticmethod
    def get_popular_faqs(limit=10):
        """人気FAQ（閲覧数順）を取得"""
        return FAQ.query.filter_by(is_active=True)\
                       .order_by(FAQ.view_count.desc())\
                       .limit(limit).all()
    
    @staticmethod
    def get_faq_stats():
        """FAQ統計を取得"""
        from sqlalchemy import func
        
        total_faqs = FAQ.query.count()
        active_faqs = FAQ.query.filter_by(is_active=True).count()
        total_views = db.session.query(func.sum(FAQ.view_count)).scalar() or 0
        
        # カテゴリ別統計
        category_stats = db.session.query(
            FAQ.category, 
            func.count(FAQ.id).label('count'),
            func.sum(FAQ.view_count).label('views')
        ).filter_by(is_active=True)\
         .group_by(FAQ.category)\
         .all()
        
        # 最も閲覧されたFAQ
        most_viewed = FAQ.query.filter_by(is_active=True)\
                              .order_by(FAQ.view_count.desc())\
                              .first()
        
        return {
            'total_faqs': total_faqs,
            'active_faqs': active_faqs,
            'inactive_faqs': total_faqs - active_faqs,
            'total_views': total_views,
            'avg_views_per_faq': total_views / max(active_faqs, 1),
            'category_stats': [
                {
                    'category': stat[0] or '未分類',
                    'count': stat[1],
                    'views': stat[2] or 0
                }
                for stat in category_stats
            ],
            'most_viewed_faq': {
                'title': most_viewed.title if most_viewed else None,
                'views': most_viewed.view_count if most_viewed else 0
            }
        }
    
    def increment_view_count(self):
        """閲覧数をインクリメント"""
        self.view_count += 1
        db.session.commit()