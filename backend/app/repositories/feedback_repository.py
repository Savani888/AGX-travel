from sqlalchemy.orm import Session

from app.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
