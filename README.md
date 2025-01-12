# CAI-Media-Analysis
This project assists in media analysis for the lecture "Communicating AI" at Johannes Kepler University.
It uses OLLAMA local LLMs to analyze PDF files and assist in research.

# Author
Mathias Schneider, 12.01.2025

# Topics covered
- Reading PDF or DOCX files and extracting the text in a readable format (works best with DOCX)
- LLM based creation of:
    - Summary
    - Short Summary
    - Answering dynamic questions
    - Extracting sentiment (-5, +5)
    - Entity extraction
    - Topic extractions
    - Topic clustering
- LDA analysis for topic identification, including LDA topic summarization
- TF-IDF analysis for all documents to identify their uniqueness
- LLM based answering of research question
- Export in DOCX or Markdown


# Installation of OLLAMA
1) Download ollama from https://ollama.com
2) Install the models. Not everything is needed, I suggest granite3.1-moe:3b-instruct-q8_0 (from IBM)
Run in terminal:
ollama run granite3.1-moe:3b-instruct-q8_0
#ollama run llama3.1
#ollama run mistral
#ollama run qwen:14b
#ollama run phi4

# Environment
To create the environment, run the following commands in your terminal:

conda create -n nlp
conda activate nlp
conda install -c conda-forge pypdf ollama spacy numpy pandas ipykernel jupyter dill ollama-python pip matplotlib wordcloud python-docx scikit-learn
pip install pymupdf
