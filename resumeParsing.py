import re
from pdfminer.high_level import extract_text

def extract_text_from_pdf() -> str:
    pdf_path = input("Enter path for your resume: ")
    return extract_text(pdf_path)