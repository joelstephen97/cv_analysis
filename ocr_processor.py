import io
import pytesseract
from pdf2image import convert_from_bytes
import magic
import docx
import logging

logger = logging.getLogger(__name__)


def extract_text_from_file(file_bytes, file_type):
    """Extract text from various file formats"""
    try:
        if file_type == "application/pdf":
            return extract_text_from_pdf(file_bytes)
        elif (
            file_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return extract_text_from_docx(file_bytes)
        elif file_type == "text/plain":
            return file_bytes.decode("utf-8")
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}", exc_info=True)
        return None


def extract_text_from_pdf(file_bytes):
    """Extract text from PDF using OCR"""
    images = convert_from_bytes(file_bytes)
    text = ""
    for i, image in enumerate(images):
        page_text = pytesseract.image_to_string(image)
        text += f"\n--- Page {i+1} ---\n{page_text}"
    return text


def extract_text_from_docx(file_bytes):
    """Extract text from DOCX files"""
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])
