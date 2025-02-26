import unittest
from unittest.mock import patch, MagicMock
import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, CVDocument

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        
        self.sample_data = {
            "filename": "test_cv.pdf",
            "personal_info": {"name": "John Doe", "email": "john@example.com"},
            "education": [{"degree": "BS", "institution": "MIT"}],
            "work_experience": [{"title": "Developer", "company": "Google"}],
            "skills": ["Python", "JavaScript"],
            "projects": [{"title": "Project X", "description": ["A test project"]}],
            "certifications": [{"name": "AWS Cert", "issuer": "Amazon"}],
            "raw_text": "Sample CV text"
        }
        
    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        
    def test_cv_document_creation(self):
        session = self.Session()
        try:
            cv_doc = CVDocument(
                filename=self.sample_data["filename"],
                personal_info=self.sample_data["personal_info"],
                education=self.sample_data["education"],
                work_experience=self.sample_data["work_experience"],
                skills=self.sample_data["skills"],
                projects=self.sample_data["projects"],
                certifications=self.sample_data["certifications"],
                raw_text=self.sample_data["raw_text"]
            )
            
            session.add(cv_doc)
            session.commit()
            
            db_cv = session.query(CVDocument).filter_by(filename="test_cv.pdf").first()
            
            self.assertIsNotNone(db_cv)
            self.assertEqual(db_cv.filename, "test_cv.pdf")
            self.assertEqual(db_cv.personal_info["name"], "John Doe")
            self.assertEqual(db_cv.education[0]["degree"], "BS")
            self.assertIsInstance(db_cv.created_at, datetime.datetime)
            
        finally:
            session.close()
            
    def test_cv_document_update(self):
        session = self.Session()
        try:
            cv_doc = CVDocument(
                filename=self.sample_data["filename"],
                personal_info=self.sample_data["personal_info"],
                education=self.sample_data["education"],
                raw_text=self.sample_data["raw_text"]
            )
            
            session.add(cv_doc)
            session.commit()
            
            db_cv = session.query(CVDocument).filter_by(filename="test_cv.pdf").first()
            db_cv.personal_info = {"name": "Jane Doe", "email": "jane@example.com"}
            old_updated_at = db_cv.updated_at
            
            import time
            time.sleep(0.1)
            
            session.commit()
            
            updated_cv = session.query(CVDocument).filter_by(filename="test_cv.pdf").first()
            
            self.assertEqual(updated_cv.personal_info["name"], "Jane Doe")
            self.assertNotEqual(updated_cv.updated_at, old_updated_at)
            
        finally:
            session.close()
            
    def test_to_dict_method(self):
        cv_doc = CVDocument(
            id=1,
            filename=self.sample_data["filename"],
            personal_info=self.sample_data["personal_info"],
            education=self.sample_data["education"],
            work_experience=self.sample_data["work_experience"],
            skills=self.sample_data["skills"],
            projects=self.sample_data["projects"],
            certifications=self.sample_data["certifications"]
        )
        
        cv_dict = cv_doc.to_dict()
        
        self.assertEqual(cv_dict["id"], 1)
        self.assertEqual(cv_dict["filename"], "test_cv.pdf")
        self.assertEqual(cv_dict["personal_info"]["name"], "John Doe")
        self.assertEqual(cv_dict["education"][0]["degree"], "BS")

if __name__ == '__main__':
    unittest.main()