import magic
import streamlit as st
import logging
from cv_parser import GenericCVParser
from database import CVDocument, Session, engine
from ocr_processor import extract_text_from_file
import os
import base64
from streamlit.components.v1 import html

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "cv_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def process_uploaded_files(uploaded_files):
    if not uploaded_files:
        return
    session = Session()
    try:

        parser = GenericCVParser()
        
        for file in uploaded_files:
            file_bytes = file.getvalue()
            original_filename = file.name
            cleaned_filename = os.path.basename(original_filename)
            file_type = magic.from_buffer(file_bytes, mime=True)
            file_path = os.path.join(UPLOAD_DIR, cleaned_filename)
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            logger.info(f"Processing file: {cleaned_filename} ({file_type})")
            text = extract_text_from_file(file_bytes, file_type)
            if not text:
                st.warning(f"Could not extract text from {cleaned_filename}")
                continue
            existing_entry = (
                session.query(CVDocument).filter_by(filename=cleaned_filename).first()
            )
            parsed_data = parser.parse(text)
            if "raw_text" in parsed_data:
                del parsed_data["raw_text"]
            logger.info(f"Parsed data :{parsed_data}")
            if existing_entry:
                for key, value in parsed_data.items():
                    setattr(existing_entry, key, value)
                existing_entry.raw_text = text
                st.info(f"Updated existing entry for {cleaned_filename}")
            else:
                cv_doc = CVDocument(filename=cleaned_filename, raw_text=text, **parsed_data)
                session.add(cv_doc)
                st.success(f"Added new entry for {cleaned_filename}")
        session.commit()
        st.success(f"Successfully processed {len(uploaded_files)} files")
    except Exception as e:
        session.rollback()
        st.error(f"Error processing files: {str(e)}")
        logger.error(f"Error in process_uploaded_files: {str(e)}", exc_info=True)
    finally:
        session.close()

def open_pdf_in_new_tab(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    js = f"""
    <script>
        window.open("data:application/pdf;base64,{base64_pdf}");
    </script>
    """
    html(js, width=0, height=0)


def cv_organizer_and_viewer(cv_entry):
    """Display CV details with preview and download options"""
    if isinstance(cv_entry, dict):
        filename = cv_entry.get("filename")
        cv_id = cv_entry.get("id", "N/A")
    else:
        filename = cv_entry.filename
        cv_id = cv_entry.id
    file_path = os.path.join(UPLOAD_DIR, filename)
    col1, col2, col3 = st.columns([4, 2, 2])
    with col1:
        st.write(f"📄 {filename} (ID: {cv_id})")
    with col2:
        if os.path.exists(file_path):
            if filename.lower().endswith('.pdf'):
                if st.button(f"Preview", key=f"preview_{cv_id}"):
                    open_pdf_in_new_tab(file_path)
            else:
                st.write("Preview not available")
    
    with col3:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    "Download",
                    data=f,
                    file_name=filename,
                    key=f"dl_{cv_id}"
                )
        else:
            st.error("File missing")


def chat_interface(query):
    # It has been implemented for demonstration purposes and is basic and does not include advanced search functionalities like full text natural language
    if not query:
        return ""
    session = Session()
    try:
        results = []
        cvs = session.query(CVDocument).all()
        for cv in cvs:
            if query.lower() in cv.raw_text.lower():
                results.append(cv)
        if not results:
            return "No matching CVs found."
        response = f"Found {len(results)} matching CVs:\n\n"
        for cv in results:
            cv_organizer_and_viewer(cv)
        return response
    except Exception as e:
        logger.error(f"Error in chat_interface: {str(e)}", exc_info=True)
        return f"Error processing query: {str(e)}"
    finally:
        session.close()


def main():
    st.set_page_config(page_title="CV Analysis System", layout="wide")
    st.title("CV Analysis System")
    page = st.sidebar.radio(
        "Navigation", ["Upload CVs", "Search CVs", "Database Stats"]
    )
    if page == "Upload CVs":
        st.header("Upload CV/s")
        uploaded_files = st.file_uploader(
            "Upload CV/s (PDF/DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            if st.button("Process Files"):
                with st.spinner("Processing files..."):
                    process_uploaded_files(uploaded_files)
    elif page == "Search CVs":
        st.header("CV Query Chatbot")
        user_query = st.text_input("Ask about the CV data:")
        if user_query:
            with st.spinner("Searching..."):
                response = chat_interface(user_query)
                st.write(response)
    elif page == "Database Stats":
        st.header("Database Statistics")
        session = Session()
        try:
            cv_count = session.query(CVDocument).count()
            st.metric("Total CVs in Database", cv_count)

            if cv_count > 0:
                st.subheader("CV Documents")
                cvs = session.query(CVDocument).all()
                for cv in cvs:
                    cv_organizer_and_viewer(cv)
        finally:
            session.close()


if __name__ == "__main__":
    CVDocument.metadata.create_all(engine)
    main()