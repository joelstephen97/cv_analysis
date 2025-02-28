import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import spacy
from dateutil.parser import parse
from spacy.matcher import Matcher, PhraseMatcher

nlp = spacy.load("en_core_web_sm")

def clean_text(text: str) -> str:
    text = re.sub(r'^--- Page \d+ ---$', '', text, flags=re.MULTILINE)

    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.isupper() and stripped_line.endswith(':'):
            line = line.replace(":", "")
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

# NOTE : The parser is still not accurate, in certain cases with differing formatting,
# it may fail to correctly identify and extract information.
# I am trying to improve it by adding more patterns and improving the accuracy of the spacy model.
class GenericCVParser:
    def __init__(self):
        self.matcher = Matcher(nlp.vocab)
        self.phrase_matcher = PhraseMatcher(nlp.vocab)
        self._add_patterns()

    def _add_patterns(self):
        degree_patterns = [
            [{"LOWER": {"IN": ["bsc", "b.eng", "be", "bs", "b.s.", "b.eng."]}}],
            [{"LOWER": {"IN": ["msc", "m.eng", "me", "ms", "m.s.", "m.eng."]}}],
            [{"LOWER": {"IN": ["phd", "ph.d.", "doctorate"]}}],
            [{"LOWER": {"IN": ["bachelor", "bachelors", "bachelor's"]}}],
            [{"LOWER": {"IN": ["master", "masters", "master's"]}}],
            [{"LOWER": {"IN": ["bachelor", "bachelors", "bachelor's"]}}, {"LOWER": "of"}, {"OP": "+"}],
            [{"LOWER": {"IN": ["master", "masters", "master's"]}}, {"LOWER": "of"}, {"OP": "+"}]
        ]
        self.matcher.add("EDUCATION", degree_patterns)

        job_title_patterns = [
            [{"LOWER": {"IN": ["software", "senior", "junior", "lead", "full", "stack", "devops", "qa", "security", "cloud"]}},
            {"LOWER": {"IN": ["engineer", "architect", "specialist"]}}],

            [{"LOWER": {"IN": ["software", "web", "mobile", "frontend", "backend", "full-stack", "game", "app", "blockchain"]}},
            {"LOWER": {"IN": ["developer", "programmer", "coder"]}}],

            [{"LOWER": {"IN": ["data", "business", "financial", "systems", "risk", "marketing", "security"]}},
            {"LOWER": "analyst"}],

            [{"LOWER": {"IN": ["project", "product", "technical", "program", "engineering",
                                "operations", "sales", "marketing", "hr", "finance", "it", "support"]}},
            {"LOWER": "manager"}],

            [{"LOWER": {"IN": ["business", "it", "technology", "marketing", "strategy", "management"]}},
            {"LOWER": "consultant"}],

            [{"LOWER": {"IN": ["ux", "ui", "graphic", "visual", "product", "web", "motion"]}},
            {"LOWER": "designer"}],

            [{"LOWER": {"IN": ["administrative", "office", "business"]}},
            {"LOWER": "administrator"}],

            [{"LOWER": {"IN": ["director", "head", "chief", "vp", "vice"]}}],

            [{"TEXT": {"REGEX": "(?i)(software|senior|junior|lead|full|stack|data|systems|devops|qa|cloud)\\s+(engineer|developer|analyst|architect|scientist)"}}]
        ]
        self.matcher.add("JOB_TITLE", job_title_patterns)

        skills = [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "Swift", "Kotlin", "Rust", "Scala", "Perl", "R", "Matlab",
            "HTML", "CSS", "React", "Angular", "Vue", "Svelte", "Bootstrap", "Tailwind", "jQuery",
            "Node.js", "Express", "Django", "Flask", "Spring", "Laravel", "Ruby on Rails", "ASP.NET", ".NET Core", "FastAPI", "NestJS",
            "MongoDB", "MySQL", "PostgreSQL", "Oracle", "SQL Server", "SQLite", "Redis", "Cassandra", "DynamoDB", "MariaDB", "Elasticsearch",
            "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Netlify", "Vercel", "Docker", "Kubernetes", "Jenkins", "CI/CD", "Terraform", "Ansible", "Git", "GitHub", "GitLab", "CircleCI", "Travis CI",
            "Machine Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Data Analysis", "Deep Learning", "Keras", "NLTK", "spaCy",
            "iOS", "Android", "Flutter", "Xamarin", "React Native", "SwiftUI", "Jetpack Compose",
            "Selenium", "Jest", "Mocha", "Chai", "Cypress", "Postman", "SoapUI",
            "RESTful API", "GraphQL", "WebSockets", "Microservices", "Agile", "Scrum", "Kanban", "Jira", "UI/UX", "TDD", "Design Patterns",
            "Project Management", "Business Strategy", "Client Relationship Management", "Data-Driven Decision Making", "Financial Analysis", "Market Research", "Change Management",
            "Adobe Photoshop", "Adobe Illustrator", "Adobe InDesign", "Sketch", "Figma", "UX Research", "Wireframing", "Prototyping", "Animation", "Motion Graphics", "Creative Direction",
            "Microsoft Office", "Google Workspace", "Scheduling", "Time Management", "CRM Systems", "Bookkeeping", "Data Entry", "Report Generation", "Customer Service",
            "Leadership", "Strategic Planning", "Budget Management", "Team Management", "Negotiation", "Decision Making", "Risk Management", "Public Speaking", "Stakeholder Management",
            "Digital Marketing", "SEO", "Content Strategy", "Social Media Management", "Salesforce", "Lead Generation", "Brand Management", "Customer Engagement",
            "Contract Negotiation", "Regulatory Compliance", "Risk Assessment", "Legal Research", "Policy Analysis"
        ]
        skill_patterns = [nlp.make_doc(text) for text in skills]
        self.phrase_matcher.add("SKILLS", skill_patterns)

    def parse(self, text: str, use_layout_analysis: bool = True) -> Dict:
        text = clean_text(text)
        doc = nlp(text)
        sections = self._identify_sections(text, use_layout_analysis=use_layout_analysis)

        return {
            "personal_info": self._extract_personal_info(doc),
            "education": self._extract_education(sections.get("education", "")),
            "work_experience": self._extract_experience(doc, sections.get("experience", "")),
            "skills": self._extract_skills(doc, sections.get("skills", "")),
            "projects": self._extract_projects(sections.get("projects", "")),
            "certifications": self._extract_certifications(sections.get("certifications", "")),
        }

    def _identify_sections(self, text: str, use_layout_analysis: bool = True) -> Dict[str, str]:
        if use_layout_analysis:
            layout_sections = self._analyze_text_layout(text)
            sections_text_based = {}
            lines = text.split('\n')
            section_name_mapping = {
                "education": "education",
                "experience": "work_experience",
                "skills": "skills",
                "projects": "projects",
                "certifications": "certifications",
                "academic qualifications" : "education",
                "professional experience" : "work_experience",
                "technical skills" : "skills",
                "qualifications" : "education",
                "degrees" : "education",
                "employment" : "work_experience",
                "licenses" : "certifications",
                "courses" : "certifications"
            }

            for section_heading, (start_index, end_index) in layout_sections.items():
                section_name = section_heading.lower()
                mapped_section_name = section_name_mapping.get(section_name, section_name)
                section_content = "\n".join(lines[start_index:end_index]).strip()
                sections_text_based[mapped_section_name] = section_content

            return sections_text_based
        else:
            section_patterns = {
                "education": r'(?:EDUCATION|Education|ACADEMIC|Academic|QUALIFICATIONS|Qualifications|DEGREES|Degrees)(?:\s*\n+)',
                "experience": r'(?:WORK\s*EXPERIENCE|Work\s*Experience|EMPLOYMENT|Employment|PROFESSIONAL\s*EXPERIENCE|Professional\s*Experience)(?:\s*\n+)',
                "skills": r'(?:SKILLS|Skills|COMPETENCIES|Competencies|TECHNICAL\s*SKILLS|Technical\s*Skills)(?:\s*\n+)',
                "projects": r'(?:PROJECTS|Projects|KEY\s*PROJECTS|Key\s*Projects|RESEARCH|Research)(?:\s*\n+)',
                "certifications": r'(?:CERTIFICATIONS|Certifications|LICENSES|Licenses|COURSES|Courses)(?:\s*\n+)'
            }

            sections = {}
            for section, pattern in section_patterns.items():
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                if matches:
                    start = matches[0].end()

                    end = len(text)
                    for other_pattern in section_patterns.values():
                        other_matches = list(re.finditer(other_pattern, text[start:], re.IGNORECASE))
                        if other_matches:
                            potential_end = start + other_matches[0].start()
                            if potential_end < end:
                                end = potential_end

                    sections[section] = text[start:end].strip()

            return sections
    def _extract_personal_info(self, doc) -> Dict:
        info = {
            "name": None,
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "location": None
        }

        info["email"] = next(iter(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', doc.text)), None)
        info["phone"] = next(iter(re.findall(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', doc.text)), None)

        first_lines = doc.text.split('\n')[:5]
        for line in first_lines:
            line = line.strip()
            if line and all(c.isupper() or c.isspace() for c in line):
                info["name"] = line
                break

        if not info["name"]:
            name_match = re.search(r'(\b[A-Z][a-zA-Z]+\b)\s+(\b[A-Z][a-zA-Z]+\b)', doc.text[:200])
            info["name"] = f"{name_match.group(1)} {name_match.group(2)}" if name_match else None

        info["linkedin"] = next(iter(re.findall(r'(?:linkedin\.com/in/[\w-]+|[Ll]inkedin)', doc.text)), None)
        info["github"] = next(iter(re.findall(r'(?:github\.com/[\w-]+|[Gg]ithub)', doc.text)), None)

        for ent in doc.ents:
            if ent.label_ == "GPE" and not info["location"]:
                info["location"] = ent.text

        if not info["location"]:
            location_match = re.search(r'([A-Z][a-zA-Z]+),\s*([A-Z]{2})', doc.text)
            if location_match:
                info["location"] = f"{location_match.group(1)}, {location_match.group(2)}"

        return info

    def _extract_education(self,section_text: str) -> List[Dict]:
        education = []

        if not section_text:
            return education

        edu_blocks = re.split(r'\n\n+', section_text)

        for block in edu_blocks:
            if not block.strip():
                continue

            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if not lines:
                continue

            entry = {"degree": None, "institution": None, "dates": {"start_date": None, "end_date": None}}

            if lines:
                entry["degree"] = lines[0]

            institution_line = None
            for i, line in enumerate(lines[1:], 1):
                if "University" in line or "College" in line or "Institute" in line or "School" in line:
                    institution_line = i
                    entry["institution"] = line
                    break

            for line in lines:
                date_match = re.search(r'(\d{4})-(\d{4})', line)
                if date_match:
                    entry["dates"]["start_date"] = date_match.group(1)
                    entry["dates"]["end_date"] = date_match.group(2)
                    break

            education.append(entry)

        return education

    def _extract_experience(self, doc, section_text: str) -> List[Dict]:
        experience = []
        matches = self.matcher(doc)

        for match_id, start, end in matches:
            if nlp.vocab.strings[match_id] == "JOB_TITLE":
                entry = {"title": doc[start:end].text}

                org = next((ent.text for ent in doc.ents if ent.label_ == "ORG" and ent.start > start), None)
                dates = self._find_dates_near(doc, start, end)

                entry.update({
                    "company": org,
                    "dates": dates,
                    "description": self._extract_context(doc, start, end),
                    "technologies": self._find_technologies(doc, start, end)
                })
                experience.append(entry)

        return experience

    def _find_dates_near(self, doc, start: int, end: int) -> Dict:
        dates = []
        for ent in doc.ents:
            if ent.label_ == "DATE" and start - 5 < ent.start < end + 5:
                dates.append(ent.text)

        date_ranges = re.findall(r'(\d{4})-(\d{4})', doc.text[max(0, start-30):min(len(doc.text), end+30)])
        for start_year, end_year in date_ranges:
            dates.append(f"{start_year}")
            dates.append(f"{end_year}")

        parsed_dates = [self._parse_date(d) for d in dates]
        parsed_dates = [d for d in parsed_dates if d]

        return {
            "start_date": parsed_dates[0] if parsed_dates else None,
            "end_date": parsed_dates[1] if len(parsed_dates) > 1 else None
        }

    def _extract_context(self, doc, start: int, end: int) -> str:
        context_start = max(0, start - 3)
        context_end = min(len(doc), end + 5)
        return doc[context_start:context_end].text

    def _find_technologies(self, doc, start: int, end: int) -> List[str]:
        matches = self.phrase_matcher(doc[start:end])
        return [doc[start + s:start + e].text for _, s, e in matches]

    def _extract_skills(self, doc, section_text: str) -> List[str]:
        skills = set()

        if section_text:
            for line in section_text.split('\n'):
                if any(c.isalnum() for c in line):
                    skills.update(re.split(r',|\||•|\t|:', line))

        matches = self.phrase_matcher(doc)
        for _, start, end in matches:
            skills.add(doc[start:end].text)

        return [s.strip() for s in skills if s.strip()]

    def _extract_projects(self, section_text: str) -> List[Dict]:
        projects = []
        current_project = {}

        for line in section_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            if re.match(r'^(Project:|•\s*\w+|\d+\.\s*\w+)', line):
                if current_project:
                    projects.append(current_project)
                    current_project = {}
                title = re.sub(r'^(Project:|•\s*|\d+\.\s*)', '', line)
                current_project["title"] = title
            elif current_project:
                if "description" not in current_project:
                    current_project["description"] = []
                current_project["description"].append(line)

        if current_project:
            projects.append(current_project)

        return projects

    def _extract_certifications(self, section_text: str) -> List[Dict]:
        certs = []
        for line in section_text.split('\n'):
            line = line.strip()
            if not line or len(line) < 4:
                continue

            parts = re.split(r' - | – |: ', line)
            cert = {"name": parts[0].strip()}

            if len(parts) > 1:
                details = parts[1].split('|')
                cert["issuer"] = details[0].strip()
                if len(details) > 1:
                    cert["date"] = self._parse_date(details[1].strip())
            certs.append(cert)

        return certs

    def _parse_date(self, date_str: str) -> Optional[str]:
        try:
            dt = parse(date_str, fuzzy=True)
            return dt.isoformat()
        except:
            return None
        
    def _analyze_text_layout(self, text: str) -> Dict[str, List[Tuple[int, int]]]:
        """Analyze text layout to identify section boundaries based on spacing and formatting"""
        lines = text.split('\n')
        line_info = []

        for i, line in enumerate(lines):
            if not line.strip():
                line_info.append({"index": i, "type": "blank"})
                continue
                
            indent = len(line) - len(line.lstrip())
            is_all_caps = line.strip().isupper()
            is_title_case = line.strip().istitle()
            
            line_type = "content"
            if is_all_caps and len(line.strip()) < 30:
                line_type = "heading"
            elif is_title_case and indent < 4:
                line_type = "subheading"
                
            line_info.append({
                "index": i,
                "text": line.strip(),
                "indent": indent,
                "type": line_type
            })
        
        sections = {}
        current_section = None
        section_start = 0
        
        for i, info in enumerate(line_info):
            if info["type"] == "heading":
                if current_section:
                    sections[current_section] = (section_start, info["index"])
                
                current_section = info["text"].lower()
                section_start = info["index"] + 1
        
        if current_section:
            sections[current_section] = (section_start, len(lines))
            
        return sections