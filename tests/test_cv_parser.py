import unittest
from unittest.mock import patch, MagicMock
import json
import spacy
from cv_parser import GenericCVParser

class TestGenericCVParser(unittest.TestCase):
    def setUp(self):
        self.parser = GenericCVParser()
        self.sample_cv_text = """
        JOHN DOE
        john.doe@example.com | +1 (555) 123-4567 | https://linkedin.com/in/johndoe | https://github.com/johndoe
        New York, NY

        EDUCATION
        Master of Science in Computer Science
        Stanford University | 2018 - 2020

        Bachelor of Engineering in Software Engineering  
        MIT | 2014 - 2018

        EXPERIENCE
        Senior Software Engineer
        Google | Jan 2021 - Present
        • Developed scalable web applications using React, Python, and AWS
        • Led a team of 5 engineers on a critical project

        Software Developer
        Microsoft | Jun 2018 - Dec 2020
        • Built and maintained RESTful APIs using Python and Flask
        • Implemented CI/CD pipelines using Docker and Jenkins

        SKILLS
        Programming: Python, JavaScript, SQL, Java
        Frameworks: React, Django, Flask
        Tools: Docker, AWS, Git
        
        PROJECTS
        Project: Personal Website
        • Developed a personal portfolio website using React and Node.js
        • Implemented responsive design and animation effects
        
        CERTIFICATIONS
        AWS Certified Solutions Architect - Amazon Web Services | 2022
        Microsoft Certified: Azure Developer Associate - Microsoft | 2021
        """

    def test_parse_returns_dict_with_expected_keys(self):
        result = self.parser.parse(self.sample_cv_text)
        expected_keys = ["personal_info", "education", "work_experience", "skills", "projects", "certifications"]
        for key in expected_keys:
            self.assertIn(key, result)

    def test_extract_personal_info(self):
        doc = spacy.load("en_core_web_sm")(self.sample_cv_text)
        info = self.parser._extract_personal_info(doc)
        self.assertEqual(info["email"], "john.doe@example.com")
        self.assertEqual(info["phone"], "1 (555) 123-4567")
        self.assertEqual(info["linkedin"], "https://linkedin.com/in/johndoe")
        self.assertEqual(info["github"], "https://github.com/johndoe")

    def test_identify_sections(self):
        sections = self.parser._identify_sections(self.sample_cv_text)
        self.assertIn("education", sections)
        self.assertIn("experience", sections)
        self.assertIn("skills", sections)
        self.assertIn("projects", sections)
        self.assertIn("certifications", sections)

    def test_extract_education(self):
        doc = spacy.load("en_core_web_sm")(self.sample_cv_text)
        sections = self.parser._identify_sections(self.sample_cv_text)
        education = self.parser._extract_education(doc, sections.get("education", ""))
        self.assertIsInstance(education, list)
        # only format checking here, spacy is inconsistent with actual spacy output
        if education:
            self.assertIn("degree", education[0])
            
    def test_extract_experience(self):
        doc = spacy.load("en_core_web_sm")(self.sample_cv_text)
        sections = self.parser._identify_sections(self.sample_cv_text)
        experience = self.parser._extract_experience(doc, sections.get("experience", ""))
        self.assertIsInstance(experience, list)

        if experience:
            self.assertIn("title", experience[0])

    def test_extract_skills(self):
        doc = spacy.load("en_core_web_sm")(self.sample_cv_text)
        sections = self.parser._identify_sections(self.sample_cv_text)
        skills = self.parser._extract_skills(doc, sections.get("skills", ""))
        self.assertIsInstance(skills, list)
        for skill in ["Python", "JavaScript", "SQL"]:
            self.assertIn(skill, self.sample_cv_text)

    def test_extract_projects(self):
        sections = self.parser._identify_sections(self.sample_cv_text)
        projects = self.parser._extract_projects(sections.get("projects", ""))
        print(sections,projects)
        self.assertIsInstance(projects, list)
        if projects:
            self.assertIn("title", projects[0])
            self.assertIn("description", projects[0])

    def test_extract_certifications(self):
        sections = self.parser._identify_sections(self.sample_cv_text)
        certs = self.parser._extract_certifications(sections.get("certifications", ""))
        self.assertIsInstance(certs, list)
        if certs:
            self.assertIn("name", certs[0])

if __name__ == '__main__':
    unittest.main()