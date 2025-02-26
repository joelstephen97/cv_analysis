import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import spacy
from dateutil.parser import parse
from spacy.matcher import Matcher, PhraseMatcher

nlp = spacy.load("en_core_web_sm")

class GenericCVParser:
    def __init__(self):
        self.matcher = Matcher(nlp.vocab)
        self.phrase_matcher = PhraseMatcher(nlp.vocab)
        self._add_patterns()
        
    def _add_patterns(self):
        degree_patterns = [
            [{"LOWER": {"IN": ["bsc", "b.eng", "be", "bs"]}}],
            [{"LOWER": {"IN": ["msc", "m.eng", "me", "ms"]}}],
            [{"LOWER": "phd"}, {"LOWER": "in"}, {"POS": "PROPN", "OP": "+"}],
            [{"LOWER": {"IN": ["bachelor", "master", "doctorate"]}}]
        ]
        self.matcher.add("EDUCATION", degree_patterns)

        job_title_patterns = [
            [{"POS": "PROPN"}, {"POS": "PROPN", "OP": "*"}, {"LOWER": "developer"}],
            [{"POS": "PROPN"}, {"POS": "PROPN", "OP": "*"}, {"LOWER": "engineer"}],
            [{"POS": "PROPN"}, {"POS": "PROPN", "OP": "*"}, {"LOWER": "manager"}],
            [{"POS": "PROPN"}, {"POS": "PROPN", "OP": "*"}, {"LOWER": "analyst"}]
        ]
        self.matcher.add("JOB_TITLE", job_title_patterns)

        skills = ["Python", "JavaScript", "SQL", "AWS", "Docker", "React", "Machine Learning"]
        skill_patterns = [nlp.make_doc(text) for text in skills]
        self.phrase_matcher.add("SKILLS", skill_patterns)

    def parse(self, text: str) -> Dict:
        doc = nlp(text)
        sections = self._identify_sections(text)
        
        return {
            "personal_info": self._extract_personal_info(doc),
            "education": self._extract_education(doc, sections.get("education", "")),
            "work_experience": self._extract_experience(doc, sections.get("experience", "")),
            "skills": self._extract_skills(doc, sections.get("skills", "")),
            "projects": self._extract_projects(sections.get("projects", "")),
            "certifications": self._extract_certifications(sections.get("certifications", "")),
        }

    def _identify_sections(self, text: str) -> Dict[str, str]:
        section_keywords = {
            "education": ["education", "academic", "qualifications", "degrees"],
            "experience": ["experience", "employment", "work history", "positions"],
            "skills": ["skills", "competencies", "technical skills"],
            "projects": ["projects", "key projects", "research"],
            "certifications": ["certifications", "licenses", "courses"]
        }
        
        sections = {}
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.strip().lower()
            for section, keywords in section_keywords.items():
                if any(kw in line_lower for kw in keywords) and section not in sections:
                    start = text.find(line)
                    sections[section] = {"start": start, "header": line.strip()}
        
        sorted_sections = sorted(sections.items(), key=lambda x: x[1]["start"])
        final_sections = {}
        
        for i, (section_name, section_data) in enumerate(sorted_sections):
            start = section_data["start"] + len(section_data["header"])
            if i < len(sorted_sections) - 1:
                end = sorted_sections[i+1][1]["start"]
            else:
                end = len(text)
            final_sections[section_name] = text[start:end].strip()
            
        return final_sections

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
        name_match = re.search(r'(\b[A-Z][A-Z]+\b)\s(\b[A-Z][A-Z]+\b)', doc.text)
        info["name"] = f"{name_match.group(1)} {name_match.group(2)}" if name_match else None
        info["linkedin"] = next(iter(re.findall(r'https://(?:www\.)?linkedin\.com/in/[\w-]+/?', doc.text)), None)
        info["github"] = next(iter(re.findall(r'https://(?:www\.)?github\.com/[\w-]+/?', doc.text)), None)
        
        for ent in doc.ents:
            if ent.label_ == "GPE" and not info["location"]:
                info["location"] = ent.text
                
        return info

    def _extract_education(self, doc, section_text: str) -> List[Dict]:
        education = []
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            if nlp.vocab.strings[match_id] == "EDUCATION":
                entry = {"degree": doc[start:end].text}
                
                org = next((ent.text for ent in doc.ents if ent.label_ == "ORG" and ent.start > start), None)
                dates = self._find_dates_near(doc, start, end)
                
                entry.update({
                    "institution": org,
                    "dates": dates,
                    "description": self._extract_context(doc, start, end)
                })
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
                
        parsed_dates = [self._parse_date(d) for d in dates]
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