import unittest
import os
import tempfile
import shutil
import sqlite3
from unittest.mock import patch, MagicMock
import json

from database import Base, CVDocument, Session, engine
from cv_parser import GenericCVParser
from ocr_processor import extract_text_from_file
from app import process_uploaded_files, chat_interface

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_upload_dir = os.path.join(self.test_dir, "uploads")
        os.makedirs(self.test_upload_dir, exist_ok=True)
        
        self.test_db_path = os.path.join(self.test_dir, "test_cv_database.db")
        self.test_engine = engine
        
        Base.metadata.create_all(self.test_engine)
        
        self.sample_cv_text = """
        JOHN DOE
        john.doe@example.com | +1 (555) 123-4567 | linkedin.com/in/johndoe | github.com/johndoe
        New York, NY

        EDUCATION
        Master of Science in Computer Science
        Stanford University | 2018 - 2020

        EXPERIENCE
        Senior Software Engineer
        Google | Jan 2021 - Present
        • Developed scalable web applications using React, Python, and AWS
        
        SKILLS
        Programming: Python, JavaScript, SQL, Java
        """
        
        self.sample_pdf_path = os.path.join(self.test_upload_dir, "sample_cv.pdf")
        with open(self.sample_pdf_path, "w") as f:
            f.write(self.sample_cv_text)
        
        self.original_upload_dir = os.environ.get("UPLOAD_DIR")
        os.environ["UPLOAD_DIR"] = self.test_upload_dir
        
    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass
        
        if self.original_upload_dir:
            os.environ["UPLOAD_DIR"] = self.original_upload_dir
        else:
            os.environ.pop("UPLOAD_DIR", None)
    
    @patch("app.extract_text_from_file")
    @patch("app.magic.from_buffer")
    @patch("streamlit.success")
    @patch("streamlit.error")
    def test_end_to_end_cv_processing(self, mock_error, mock_success, mock_from_buffer, mock_extract_text):
        """Test the complete flow of uploading, processing, and querying a CV"""

        mock_file = MagicMock()
        mock_file.name = "sample_cv.pdf"
        with open(self.sample_pdf_path, "rb") as f:
            file_content = f.read()
        mock_file.getvalue.return_value = file_content
        
        mock_from_buffer.return_value = "application/pdf"
        mock_extract_text.return_value = self.sample_cv_text
        
        process_uploaded_files([mock_file])
        
        mock_success.assert_called()
        mock_error.assert_not_called()
        
        session = Session()
        try:
            cv_doc = session.query(CVDocument).filter_by(filename="sample_cv.pdf").first()
            self.assertIsNotNone(cv_doc)
            self.assertEqual(cv_doc.raw_text, self.sample_cv_text)
            
            self.assertIsNotNone(cv_doc.personal_info)
            self.assertIn("email", cv_doc.personal_info)
            self.assertEqual(cv_doc.personal_info["email"], "john.doe@example.com")
            
            with patch("app.cv_organizer_and_viewer") as mock_organizer:
                result = chat_interface("Python")
                self.assertIn("Found", result)
                mock_organizer.assert_called()
                
                mock_organizer.reset_mock()
                result = chat_interface("Ruby")
                self.assertEqual(result, "No matching CVs found.")
                mock_organizer.assert_not_called()
                
        finally:
            session.close()
    
    def test_parser_integration(self):
        """Test that the parser correctly integrates with the database schema"""
        parser = GenericCVParser()
        parsed_data = parser.parse(self.sample_cv_text)
        
        expected_keys = ["personal_info", "education", "work_experience", 
                        "skills", "projects", "certifications"]
        for key in expected_keys:
            self.assertIn(key, parsed_data)
        
        session = Session()
        try:
            if "raw_text" in parsed_data:
                del parsed_data["raw_text"]
                
            cv_doc = CVDocument(filename="parser_test.pdf", raw_text=self.sample_cv_text, **parsed_data)
            session.add(cv_doc)
            session.commit()
            
            db_cv = session.query(CVDocument).filter_by(filename="parser_test.pdf").first()
            self.assertIsNotNone(db_cv)
            
            self.assertEqual(db_cv.personal_info["email"], "john.doe@example.com")
            if db_cv.skills:
                self.assertIsInstance(db_cv.skills, list)
                
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()