from app import db
from datetime import datetime
import uuid

class Conversation(db.Model):
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # ユーザーID
    user_identifier = db.Column(db.String(100))  # 個人情報ではないユーザー識別子（後方互換）
    user_display_name = db.Column(db.String(100))  # ユーザー表示名
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 会話メタデータ
    user_agent = db.Column(db.String(255))  # ブラウザ情報
    ip_address = db.Column(db.String(45))  # IPアドレス（匿名化済み）
    
    # リレーション
    user = db.relationship('User', backref='conversations')
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.session_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'user_identifier': self.user_identifier,
            'user_display_name': self.user_display_name,
            'user_info': self.user.to_dict() if self.user else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'message_count': len(self.messages),
            'user_agent': self.user_agent,
            'ip_address': self.ip_address
        }
    
    @staticmethod
    def get_user_conversations(user_id, limit=10):
        """指定ユーザーの会話履歴を取得"""
        return Conversation.query.filter_by(user_id=user_id)\
                               .order_by(Conversation.last_activity.desc())\
                               .limit(limit).all()
    
    def get_display_name(self):
        """表示名を取得（ユーザー情報から優先的に取得）"""
        if self.user and self.user.display_name:
            return self.user.display_name
        elif self.user_display_name:
            return self.user_display_name
        elif self.user and self.user.identifier:
            return f"ユーザー#{self.user.identifier[-4:]}"
        elif self.user_identifier:
            return f"ユーザー#{self.user_identifier[-4:]}"
        else:
            return f"匿名ユーザー#{self.id}"

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # 'user', 'bot', 'staff'
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))  # 添付ファイルのパス
    file_name = db.Column(db.String(255))  # 添付ファイルの元の名前
    faq_id = db.Column(db.Integer, db.ForeignKey('faq.id'))  # FAQ回答の場合のFAQ ID
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_escalated = db.Column(db.Boolean, default=False)  # エスカレーションされた質問か
    
    # 送信者情報
    sender_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 送信者のユーザーID
    sender_name = db.Column(db.String(100))  # 送信者名（表示用）
    sender_type = db.Column(db.String(20))  # 'anonymous', 'registered', 'staff'
    
    # 回答者情報（staff回答の場合）
    staff_id = db.Column(db.Integer, db.ForeignKey('staff_member.id'))  # 職員ID
    response_time_minutes = db.Column(db.Float)  # 回答までの時間（分）
    
    # 追加メタデータ
    confidence_score = db.Column(db.Float)  # FAQ回答の信頼度スコア
    feedback_rating = db.Column(db.Integer)  # ユーザーからの評価（1-5）
    feedback_comment = db.Column(db.Text)  # ユーザーからのフィードバック
    
    # リレーション
    faq = db.relationship('FAQ', backref='messages')
    sender_user = db.relationship('User', foreign_keys=[sender_user_id], backref='sent_messages')
    staff_member = db.relationship('StaffMember', backref='responded_messages')
    
    def __repr__(self):
        return f'<Message {self.message_type}: {self.content[:50]}...>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'message_type': self.message_type,
            'content': self.content,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'faq_id': self.faq_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_escalated': self.is_escalated,
            'sender_info': self.get_sender_info(),
            'responder_info': self.get_responder_info(),
            'response_time_minutes': self.response_time_minutes,
            'confidence_score': self.confidence_score,
            'feedback_rating': self.feedback_rating,
            'feedback_comment': self.feedback_comment
        }
    
    def get_sender_info(self):
        """送信者情報を取得"""
        if self.sender_user:
            return {
                'user_id': self.sender_user.id,
                'identifier': self.sender_user.identifier,
                'display_name': self.sender_user.display_name,
                'user_type': self.sender_user.user_type,
                'is_anonymous': self.sender_user.is_anonymous
            }
        elif self.sender_name:
            return {
                'display_name': self.sender_name,
                'sender_type': self.sender_type
            }
        else:
            return {
                'display_name': f"匿名ユーザー#{self.id}",
                'sender_type': 'anonymous'
            }
    
    def get_responder_info(self):
        """回答者情報を取得"""
        if self.message_type == 'staff' and self.staff_member:
            return {
                'staff_id': self.staff_member.staff_id,
                'name': self.staff_member.name,
                'department': self.staff_member.department,
                'role': self.staff_member.role
            }
        elif self.message_type == 'bot' and self.faq:
            return {
                'type': 'faq_bot',
                'faq_title': self.faq.title,
                'faq_category': self.faq.category
            }
        else:
            return None
    
    def set_sender_from_user(self, user):
        """ユーザー情報から送信者情報を設定"""
        self.sender_user_id = user.id
        self.sender_name = user.display_name or user.identifier
        self.sender_type = 'registered' if not user.is_anonymous else 'anonymous'
    
    def set_staff_responder(self, staff_member, response_time_minutes=None):
        """職員回答者情報を設定"""
        self.staff_id = staff_member.id
        self.response_time_minutes = response_time_minutes
        if response_time_minutes:
            staff_member.record_response(response_time_minutes)
    
    @staticmethod
    def get_user_messages(user_id, limit=50):
        """指定ユーザーのメッセージ履歴を取得"""
        return Message.query.filter_by(sender_user_id=user_id)\
                          .order_by(Message.timestamp.desc())\
                          .limit(limit).all()
    
    @staticmethod
    def get_staff_responses(staff_id, limit=50):
        """指定職員の回答履歴を取得"""
        return Message.query.filter_by(staff_id=staff_id)\
                          .filter_by(message_type='staff')\
                          .order_by(Message.timestamp.desc())\
                          .limit(limit).all()