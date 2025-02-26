# Project - Application Tracking System Advanced by Joel Stephen

## Prerequisites
###
1. Docker
2. project code is available in a directory named 'cv-analysis'

## Build Docker Image

###

Using docker so that its consistent across different environments and operating systems. \
```docker build -t cv-analysis .```

## Run Server
###
```docker run -p 8501:8501 cv-analysis``` \
\
**Note** : Server will be available on : \
http://localhost:8501 \
So you can ignore the URL: http://0.0.0.0:8501 message in terminal and proceed

## Run Test Suite

```docker run --rm --entrypoint python cv-analysis test_runner.py```

## TODO:

###
- [x] Accept CV/CVs for upload in .pdf and .docx formats.
- [x] Rough UI made with Streamlit for easier development.
- [x] Basic Query System to locate CV's with specific keywords.
- [x] OCR
- [x] Basic Parsing System
- [x] DOCKERize the application
- [ ] LLM integration
- [ ] Host code on github, so it can be cloned, and docker build image to have project ready to use.
- [ ] Test Suite can be made into github actions running on every push.
- [ ] Natural Language Search can be implemented.

## To Note:

###

1. LLM Integration is not yet implemented due to issues faced with API calls and limited time. The current setup uses a basic parser to extract data from the CV.
2. The application stores uploaded files into cv_uploads
3. Sample files are available in data/sample_cvs folder.
