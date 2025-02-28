import magic
import streamlit as st
import logging
from cv_parser import GenericCVParser
from database import CVDocument, Session, engine
from ocr_processor import extract_text_from_file
import os
import base64
from streamlit.components.v1 import html
import pandas as pd

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
    if not query:
        return ""
    selected_cv_id = st.session_state.get('selected_cv_id', None)

    if st.button("New Search", key="new_search"):
        if 'selected_cv_id' in st.session_state:
            del st.session_state['selected_cv_id']
        selected_cv_id = None
    
    session = Session()
    try:
        if selected_cv_id:
            cv = session.query(CVDocument).filter(CVDocument.id == selected_cv_id).first()
            if not cv:
                st.error(f"Selected CV with ID {selected_cv_id} not found.")
                if 'selected_cv_id' in st.session_state:
                    del st.session_state['selected_cv_id']
                return "Error: Selected CV not found"
            
            st.subheader(f"Detailed view of: {cv.filename}")
            cv_organizer_and_viewer(cv)

            query_lower = query.lower()
            if "skill" in query_lower:
                st.write("### Skills")
                if cv.skills:
                    st.json(cv.skills)
                else:
                    st.write("No skills information available.")
            elif "education" in query_lower:
                st.write("### Education")
                if cv.education:
                    st.json(cv.education)
                else:
                    st.write("No education information available.")
            elif "experience" in query_lower or "work" in query_lower:
                st.write("### Work Experience")
                if cv.work_experience:
                    st.json(cv.work_experience)
                else:
                    st.write("No work experience information available.")
            elif "personal" in query_lower or "contact" in query_lower:
                st.write("### Personal Information")
                if cv.personal_info:
                    st.json(cv.personal_info)
                else:
                    st.write("No personal information available.")
            elif "project" in query_lower:
                st.write("### Projects")
                if cv.projects:
                    st.json(cv.projects)
                else:
                    st.write("No project information available.")
            elif "certification" in query_lower or "certificate" in query_lower:
                st.write("### Certifications")
                if cv.certifications:
                    st.json(cv.certifications)
                else:
                    st.write("No certification information available.")
            else:
                st.write("### CV Summary")
                for section, title in [
                    ('personal_info', 'Personal Information'),
                    ('education', 'Education'),
                    ('work_experience', 'Work Experience'),
                    ('skills', 'Skills'),
                    ('projects', 'Projects'),
                    ('certifications', 'Certifications')
                ]:
                    data = getattr(cv, section)
                    if data:
                        with st.expander(title):
                            st.json(data)
            
            return f"Showing details for CV: {cv.filename}"
        
        results = []
        query_lower = query.lower()
        
        search_column = None
        if "skill" in query_lower:
            search_column = "skills"
        elif "education" in query_lower:
            search_column = "education"
        elif "experience" in query_lower or "work" in query_lower:
            search_column = "work_experience"
        elif "personal" in query_lower or "contact" in query_lower:
            search_column = "personal_info"
        elif "project" in query_lower:
            search_column = "projects"
        elif "certification" in query_lower or "certificate" in query_lower:
            search_column = "certifications"
            
        cvs = session.query(CVDocument).all()
        for cv in cvs:
            if search_column:
                column_data = getattr(cv, search_column)
                if column_data:
                    json_str = str(column_data).lower()
                    search_terms = [term for term in query_lower.split() if term != search_column.lower() 
                                    and term not in ["skill", "skills", "education", "experience", 
                                                    "work", "personal", "contact", "project", "projects", 
                                                    "certification", "certifications"]]
                    search_term = " ".join(search_terms)
                    if search_term and search_term in json_str:
                        results.append(cv)
            else:
                if query_lower in cv.raw_text.lower():
                    results.append(cv)
        
        if not results:
            return "No matching CVs found."  
        response = f"Found {len(results)} matching CVs:\n\n"
        for cv in results:
            col1, col2 = st.columns([5, 1])
            with col1:
                cv_organizer_and_viewer(cv)
            with col2:
                if st.button("Select", key=f"select_{cv.id}"):
                    st.session_state['selected_cv_id'] = cv.id
                    st.experimental_rerun()
        
        return response
    except Exception as e:
        logger.error(f"Error in chat_interface: {str(e)}", exc_info=True)
        return f"Error processing query: {str(e)}"
    finally:
        session.close()

def main():
    st.set_page_config(page_title="CV Analysis System", layout="wide")
    st.title("CV Analysis System")
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    if 'selected_cv_id' not in st.session_state:
        st.session_state['selected_cv_id'] = None
    page = st.sidebar.radio(
        "Navigation", ["Upload CVs", "Search CVs", "Database Stats"]
    )
    if page == "Upload CVs":
        st.header("Upload CV/s")
        uploaded_files = st.file_uploader(
            "Upload CV/s (PDF/DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key=f"uploaded_files_{st.session_state.uploader_key}",
        )
        if uploaded_files:
            if st.button("Process Files"):
                with st.spinner("Processing files..."):
                    process_uploaded_files(uploaded_files)
                # force pseudo reset since streamlit cannot do it direct
                st.session_state.uploader_key += 1

    elif page == "Search CVs":
        st.header("CV Search Interface")
        st.info("""
        ### How to Use the Advanced CV Search
        
        **Step 1: Search for CVs**
        - Type a search term in the box below (e.g., "Python skills", "MBA education")
        - The system will search relevant sections of all CVs
        
        **Step 2: Explore Results**
        - Review the matching CV documents
        - Click the "Select" button next to any CV to explore it in more detail
        
        **Step 3: Dig Deeper**
        - Once you've selected a CV, you can ask specific questions about it
        - Try queries like "show skills", "education details", or "work experience"
        
        **Step 4: Start Over**
        - Click "New Search" anytime to search across all CVs again

        """)
        
        if st.session_state.get('selected_cv_id'):
            session = Session()
            cv = session.query(CVDocument).filter(CVDocument.id == st.session_state['selected_cv_id']).first()
            session.close()
            if cv:
                st.success(f"🔍 Currently exploring: **{cv.filename}**")
        
        user_query = st.text_input(
            "Enter your search query:",
            placeholder="e.g., 'Python skills', 'education at MIT', 'project experience'",
            help="Include keywords like 'skills', 'education', or 'experience' to search in specific sections"
        )
        
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
                    
                st.subheader("Skills Distribution")
                all_skills = {}
                for cv in cvs:
                    if cv.skills:
                        try:
                            cv_skills = cv.skills if isinstance(cv.skills, list) else cv.skills.get('skills', [])
                            for skill in cv_skills:
                                if isinstance(skill, str):
                                    all_skills[skill] = all_skills.get(skill, 0) + 1
                        except:
                            pass
                
                if all_skills:
                    skills_sorted = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)
                    skills_df = pd.DataFrame(skills_sorted, columns=["Skill", "Count"])
                    st.bar_chart(skills_df.set_index("Skill"))
                else:
                    st.write("No skills data available for analysis.")
        finally:
            session.close()


if __name__ == "__main__":
    CVDocument.metadata.create_all(engine)
    main()