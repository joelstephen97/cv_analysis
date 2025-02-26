import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import streamlit as st
from app import process_uploaded_files, chat_interface, cv_organizer_and_viewer

class TestApp(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_upload_dir = os.environ.get('UPLOAD_DIR', None)
        os.environ['UPLOAD_DIR'] = self.temp_dir.name
        
    def tearDown(self):
        self.temp_dir.cleanup()
        if self.original_upload_dir:
            os.environ['UPLOAD_DIR'] = self.original_upload_dir
        else:
            os.environ.pop('UPLOAD_DIR', None)
            
    @patch('app.GenericCVParser')
    @patch('app.extract_text_from_file')
    @patch('app.Session')
    @patch('app.magic.from_buffer')
    @patch('streamlit.success')
    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_process_uploaded_files_success(self, mock_warning, mock_error, mock_success, 
    mock_from_buffer, mock_session, mock_extract_text, 
    mock_parser_class):

        mock_file = MagicMock()
        mock_file.name = "test_cv.pdf"
        mock_file.getvalue.return_value = b"file content"

        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = {
            "personal_info": {"name": "John Doe"},
            "raw_text": "Sample CV text"
        }
        
        mock_from_buffer.return_value = "application/pdf"
        
        mock_extract_text.return_value = "Sample CV text"
        
        process_uploaded_files([mock_file])
        
        mock_from_buffer.assert_called_once_with(b"file content", mime=True)
        mock_extract_text.assert_called_once_with(b"file content", "application/pdf")
        mock_parser.parse.assert_called_once_with("Sample CV text")
        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()
        mock_success.assert_called()
        mock_error.assert_not_called()
        
    @patch('app.extract_text_from_file')
    @patch('app.Session')
    @patch('app.magic.from_buffer')
    @patch('streamlit.success')
    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_process_uploaded_files_text_extraction_failure(self, mock_warning, mock_error, 
    mock_success, mock_from_buffer, 
    mock_session, mock_extract_text):
        mock_file = MagicMock()
        mock_file.name = "test_cv.pdf"
        mock_file.getvalue.return_value = b"file content"
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        mock_from_buffer.return_value = "application/pdf"
        
        mock_extract_text.return_value = None
        
        process_uploaded_files([mock_file])
        
        mock_extract_text.assert_called_once_with(b"file content", "application/pdf")
        mock_warning.assert_called_once()
        mock_session_instance.add.assert_not_called()
        
    @patch('app.Session')
    def test_chat_interface(self, mock_session):
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        cv1 = MagicMock()
        cv1.raw_text = "This is a CV with python experience"
        cv1.filename = "cv1.pdf"
        cv1.id = 1
        
        cv2 = MagicMock()
        cv2.raw_text = "This is another CV with java experience"
        cv2.filename = "cv2.pdf"
        cv2.id = 2
        
        mock_session_instance.query.return_value.all.return_value = [cv1, cv2]
        
        with patch('app.cv_organizer_and_viewer') as mock_organizer:
            result = chat_interface("python")
            self.assertIn("Found 1 matching", result)
            mock_organizer.assert_called_once()
            
            mock_organizer.reset_mock()
            
            mock_session_instance.query.return_value.all.return_value = []
            result = chat_interface("ruby")
            self.assertEqual(result, "No matching CVs found.")
            mock_organizer.assert_not_called()
            
    def test_cv_organizer_and_viewer_dict_input(self):
        cv_entry = {
            "filename": "test_cv.pdf",
            "id": 1
        }
        
        test_file_path = os.path.join(self.temp_dir.name, "test_cv.pdf")
        with open(test_file_path, "wb") as f:
            f.write(b"Test PDF content")
        
        with patch('app.st.columns') as mock_columns:
            col1 = MagicMock()
            col2 = MagicMock()
            col3 = MagicMock()
            mock_columns.return_value = [col1, col2, col3]
            
            with patch('app.open_pdf_in_new_tab') as mock_open_pdf:
                with patch('app.st.download_button') as mock_download:
                    cv_organizer_and_viewer(cv_entry)

if __name__ == '__main__':
    unittest.main()