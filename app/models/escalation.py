from app import db
from datetime import datetime

class Escalation(db.Model):
    __tablename__ = 'escalation'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'answered', 'closed'
    staff_response = db.Column(db.Text)  # 職員からの回答
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)
    staff_name = db.Column(db.String(100))  # 対応した職員名（任意）
    
    # リレーション
    message = db.relationship('Message', backref='escalation')
    
    def __repr__(self):
        return f'<Escalation {self.id}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'status': self.status,
            'staff_response': self.staff_response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None,
            'staff_name': self.staff_name,
            'original_question': self.message.content if self.message else None
        }
    
    @staticmethod
    def get_pending_count():
        """未解決のエスカレーション件数を取得"""
        return Escalation.query.filter_by(status='pending').count()
    
    @staticmethod
    def get_pending_escalations():
        """未解決のエスカレーション一覧を取得"""
        return Escalation.query.filter_by(status='pending').order_by(Escalation.created_at.asc()).all()