from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


class CVDocument(Base):
    __tablename__ = "cv_documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), unique=True, index=True)
    personal_info = Column(JSON)
    education = Column(JSON)
    work_experience = Column(JSON)
    skills = Column(JSON)
    projects = Column(JSON)
    certifications = Column(JSON)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        return f"<CVDocument(id={self.id}, filename='{self.filename}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "personal_info": self.personal_info,
            "education": self.education,
            "work_experience": self.work_experience,
            "skills": self.skills,
            "projects": self.projects,
            "certifications": self.certifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


engine = create_engine("sqlite:///cv_database.db")
Session = sessionmaker(bind=engine)