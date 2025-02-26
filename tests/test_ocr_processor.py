import unittest
from unittest.mock import patch, MagicMock
import io
from ocr_processor import extract_text_from_file, extract_text_from_pdf, extract_text_from_docx

class TestOCRProcessor(unittest.TestCase):
    
    @patch('ocr_processor.extract_text_from_pdf')
    def test_extract_text_from_pdf_file(self, mock_extract_pdf):
        mock_extract_pdf.return_value = "Sample PDF text"
        file_bytes = b"PDF bytes"
        file_type = "application/pdf"
        
        result = extract_text_from_file(file_bytes, file_type)
        
        mock_extract_pdf.assert_called_once_with(file_bytes)
        self.assertEqual(result, "Sample PDF text")
        
    @patch('ocr_processor.extract_text_from_docx')
    def test_extract_text_from_docx_file(self, mock_extract_docx):
        mock_extract_docx.return_value = "Sample DOCX text"
        file_bytes = b"DOCX bytes"
        file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        result = extract_text_from_file(file_bytes, file_type)
        
        mock_extract_docx.assert_called_once_with(file_bytes)
        self.assertEqual(result, "Sample DOCX text")
        
    def test_extract_text_from_txt_file(self):
        file_bytes = b"Sample text file content"
        file_type = "text/plain"
        
        result = extract_text_from_file(file_bytes, file_type)
        
        self.assertEqual(result, "Sample text file content")
        
    def test_extract_text_unsupported_file_type(self):
        file_bytes = b"Some bytes"
        file_type = "application/unsupported"
        
        result = extract_text_from_file(file_bytes, file_type)
        
        self.assertIsNone(result)
        
    @patch('ocr_processor.convert_from_bytes')
    @patch('ocr_processor.pytesseract.image_to_string')
    def test_extract_text_from_pdf(self, mock_image_to_string, mock_convert_from_bytes):
        mock_image1 = MagicMock()
        mock_image2 = MagicMock()
        mock_convert_from_bytes.return_value = [mock_image1, mock_image2]
        
        mock_image_to_string.side_effect = ["Page 1 content", "Page 2 content"]
        
        file_bytes = b"PDF bytes"
        result = extract_text_from_pdf(file_bytes)
        
        mock_convert_from_bytes.assert_called_once_with(file_bytes)
        self.assertEqual(mock_image_to_string.call_count, 2)
        self.assertIn("Page 1 content", result)
        self.assertIn("Page 2 content", result)
        
    @patch('ocr_processor.docx.Document')
    def test_extract_text_from_docx(self, mock_document):
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        para1 = MagicMock()
        para1.text = "Paragraph 1"
        para2 = MagicMock()
        para2.text = "Paragraph 2"
        mock_doc.paragraphs = [para1, para2]
        
        file_bytes = b"DOCX bytes"
        result = extract_text_from_docx(file_bytes)
        
        mock_document.assert_called_once()
        self.assertEqual(result, "Paragraph 1\nParagraph 2")

if __name__ == '__main__':
    unittest.main()