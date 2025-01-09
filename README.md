# CAI-Media-Analysis
This project assists in media analysis for the lecture "Communicating AI" at Johannes Kepler University. It uses OLLAMA local LLMs to analyze PDF files and assist in research.

# Author
Mathias Schneider, 09.01.2025

# Installation of OLLAMA
1) Download ollama from https://ollama.com
2) Install the models. Not everything is needed, I suggest llama3.1
Run in terminal:
ollama run llama3.1
#ollama run mistral
#ollama run qwen:14b
#ollama run phi4

# Environment
To create the environment, run the following commands in your terminal:

conda create -n nlp
conda activate nlp
conda install -c conda-forge pypdf ollama spacy numpy pandas ipykernel jupyter dill ollama-python pip matplotlib wordcloud python-docx
pip install pymupdf
