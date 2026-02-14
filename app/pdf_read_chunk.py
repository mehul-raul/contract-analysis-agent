from langchain_text_splitters import RecursiveCharacterTextSplitter  
from pypdf import PdfReader
from typing import List


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF"""
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract PDF: {str(e)}")
    
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(text)
    return chunks