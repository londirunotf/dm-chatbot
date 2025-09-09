from app import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import uuid

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(100), unique=True, nullable=False)  # ユーザー識別子
    display_name = db.Column(db.String(100))  # 表示名（任意）
    user_type = db.Column(db.String(20), default='user')  # 'user', 'staff', 'admin'
    is_anonymous = db.Column(db.Boolean, default=True)  # 匿名ユーザーかどうか
    
    # 認証情報
    user_id = db.Column(db.String(50), unique=True, nullable=True, index=True)  # ログイン用ID
    password_hash = db.Column(db.String(255))  # ハッシュ化パスワード
    is_admin = db.Column(db.Boolean, default=False)  # 管理者フラグ
    
    # セキュリティ
    login_attempts = db.Column(db.Integer, default=0)  # ログイン試行回数
    is_locked = db.Column(db.Boolean, default=False)  # アカウントロック
    last_login = db.Column(db.DateTime)  # 最終ログイン時刻
    
    # 統計情報
    question_count = db.Column(db.Integer, default=0)  # 質問回数
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 追加情報（任意）
    department = db.Column(db.String(100))  # 部署
    notes = db.Column(db.Text)  # 管理者メモ
    
    def __repr__(self):
        return f'<User {self.identifier}: {self.display_name or "匿名"}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'identifier': self.identifier,
            'display_name': self.display_name,
            'user_type': self.user_type,
            'is_anonymous': self.is_anonymous,
            'question_count': self.question_count,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'department': self.department
        }
    
    @staticmethod
    def generate_anonymous_identifier():
        """匿名ユーザー用の識別子を生成"""
        return f"guest_{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def get_or_create_user(identifier=None, display_name=None, user_type='user'):
        """ユーザーを取得または作成"""
        if not identifier:
            identifier = User.generate_anonymous_identifier()
        
        user = User.query.filter_by(identifier=identifier).first()
        if not user:
            user = User(
                identifier=identifier,
                display_name=display_name,
                user_type=user_type,
                is_anonymous=(display_name is None)
            )
            db.session.add(user)
            db.session.commit()
        
        return user
    
    def update_activity(self):
        """最終活動時刻を更新"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def increment_question_count(self):
        """質問回数をインクリメント"""
        self.question_count += 1
        self.update_activity()
    
    def set_password(self, password):
        """パスワードをハッシュ化して設定"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """パスワードを確認"""
        return check_password_hash(self.password_hash, password)
    
    def can_login(self):
        """ログイン可能かチェック"""
        return not self.is_locked and (self.login_attempts or 0) < 5
    
    def save(self):
        """ユーザー情報を保存"""
        db.session.add(self)
        db.session.commit()
    
    @staticmethod
    def create_authenticated_user(user_id, password, display_name, is_admin=False, department=None):
        """認証付きユーザーを作成"""
        user = User(
            identifier=user_id,  # 既存のidentifierとして保存
            user_id=user_id,     # ログイン用ID
            display_name=display_name,
            user_type='staff' if is_admin else 'user',
            is_anonymous=False,
            is_admin=is_admin,
            department=department
        )
        user.set_password(password)
        user.save()
        return user
    
    @staticmethod
    def get_active_users(days=7):
        """指定期間内のアクティブユーザーを取得"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return User.query.filter(User.last_activity >= cutoff_date).all()
    
    @staticmethod
    def get_user_stats():
        """ユーザー統計を取得"""
        total_users = User.query.count()
        staff_users = User.query.filter_by(user_type='staff').count()
        anonymous_users = User.query.filter_by(is_anonymous=True).count()
        authenticated_users = total_users - anonymous_users
        
        # 活動統計
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users_7d = User.query.filter(User.last_activity >= seven_days_ago).count()
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users_30d = User.query.filter(User.last_activity >= thirty_days_ago).count()
        
        return {
            'total_users': total_users,
            'staff_users': staff_users,
            'anonymous_users': anonymous_users,
            'authenticated_users': authenticated_users,
            'registered_users': authenticated_users,  # 後方互換性
            'active_users_7d': active_users_7d,
            'active_users_30d': active_users_30d
        }


class StaffMember(db.Model):
    __tablename__ = 'staff_member'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)  # 職員ID
    name = db.Column(db.String(100), nullable=False)  # 職員名
    department = db.Column(db.String(100))  # 所属部署
    role = db.Column(db.String(50), default='staff')  # 'staff', 'supervisor', 'admin'
    
    # 対応統計
    responses_count = db.Column(db.Integer, default=0)  # 回答数
    average_response_time = db.Column(db.Float)  # 平均回答時間（分）
    
    # アクティブ状況
    is_active = db.Column(db.Boolean, default=True)
    last_response_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーション
    user = db.relationship('User', backref='staff_profile')
    
    def __repr__(self):
        return f'<StaffMember {self.staff_id}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'staff_id': self.staff_id,
            'name': self.name,
            'department': self.department,
            'role': self.role,
            'responses_count': self.responses_count,
            'average_response_time': self.average_response_time,
            'is_active': self.is_active,
            'last_response_at': self.last_response_at.isoformat() if self.last_response_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def record_response(self, response_time_minutes=None):
        """回答記録を更新"""
        self.responses_count += 1
        self.last_response_at = datetime.utcnow()
        
        if response_time_minutes:
            if self.average_response_time:
                # 移動平均を計算
                self.average_response_time = (
                    (self.average_response_time * (self.responses_count - 1) + response_time_minutes) 
                    / self.responses_count
                )
            else:
                self.average_response_time = response_time_minutes
        
        db.session.commit()
    
    @staticmethod
    def get_active_staff():
        """アクティブな職員一覧を取得"""
        return StaffMember.query.filter_by(is_active=True).all()
    
    @staticmethod
    def get_staff_stats():
        """職員統計を取得"""
        total_staff = StaffMember.query.count()
        active_staff = StaffMember.query.filter_by(is_active=True).count()
        
        # 平均応答時間計算
        staff_with_response_time = StaffMember.query.filter(
            StaffMember.average_response_time.isnot(None)
        ).all()
        
        if staff_with_response_time:
            avg_response_time = sum(s.average_response_time for s in staff_with_response_time) / len(staff_with_response_time)
        else:
            avg_response_time = 0
        
        # 職員の回答数統計
        total_responses = sum(s.responses_count for s in StaffMember.query.all())
        
        # 最近活動した職員数（過去7日）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_active_staff = StaffMember.query.filter(
            StaffMember.last_response_at >= seven_days_ago
        ).count()
        
        return {
            'total_staff': total_staff,
            'active_staff': active_staff,
            'inactive_staff': total_staff - active_staff,
            'avg_response_time': round(avg_response_time, 1),
            'total_responses': total_responses,
            'recent_active_staff': recent_active_staff,
            'resolution_rate': 95.0,  # デフォルト値
            'utilization_rate': 75.0  # デフォルト値
        }


class LoginSession(db.Model):
    """ログインセッション"""
    __tablename__ = 'login_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45))  # IPv6対応
    user_agent = db.Column(db.Text)
    last_activity = db.Column(db.DateTime)
    
    # リレーション
    user = db.relationship('User', backref=db.backref('login_sessions', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.session_id = self.generate_session_id()
        self.expires_at = datetime.utcnow() + timedelta(hours=8)  # 8時間で期限切れ
        self.last_activity = datetime.utcnow()
    
    @staticmethod
    def generate_session_id():
        """セッションIDを生成"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @classmethod
    def create_session(cls, user_id, ip_address=None, user_agent=None):
        """新しいセッションを作成"""
        # 既存のアクティブセッションを無効化
        cls.query.filter_by(user_id=user_id, is_active=True).update({'is_active': False})
        
        # 新しいセッション作成
        session = cls(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(session)
        db.session.commit()
        
        return session
    
    def is_expired(self):
        """セッションが期限切れかチェック"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours=8):
        """セッションを延長"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """セッションを無効化"""
        self.is_active = False
        db.session.commit()
    
    def update_activity(self):
        """最終活動時刻を更新"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """期限切れセッションを削除"""
        expired_sessions = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired_sessions)
    
    @classmethod
    def get_active_sessions_count(cls):
        """アクティブセッション数を取得"""
        return cls.query.filter_by(is_active=True).filter(
            cls.expires_at > datetime.utcnow()
        ).count()
    
    def to_dict(self):
        """辞書形式で返す"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_expired': self.is_expired()
        }