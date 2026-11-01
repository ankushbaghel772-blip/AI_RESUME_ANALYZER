"""
Text Extraction Service for AI Resume Analysis.
Supports PDF, DOCX, and TXT files with clean error handling and scanned document detection.
"""

import os
from io import BytesIO

def extract_text_from_pdf(file_obj_or_path):
    """
    Extracts text from a PDF file using pypdf.
    Handles scanned documents by detecting low or zero text yield.
    """
    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_obj_or_path)
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        # Fallback or error capture
        return "", f"Error reading PDF: {str(e)}"
    
    clean_len = len(text.strip())
    if clean_len == 0:
        return "", "Notice: No readable text extracted. This appears to be a scanned or image-based PDF. Scanned documents require an OCR engine (e.g. Tesseract OCR) to extract text."
    
    return text.strip(), None


def extract_text_from_docx(file_obj_or_path):
    """
    Extracts text from a Word DOCX document paragraph by paragraph,
    including table cells.
    """
    text_parts = []
    try:
        from docx import Document
        doc = Document(file_obj_or_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        
        # Also extract table text
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
                    
    except Exception as e:
        return "", f"Error reading DOCX file: {str(e)}"
        
    extracted_text = "\n".join(text_parts).strip()
    if not extracted_text:
        return "", "Notice: DOCX file is empty or contains only non-text media."
        
    return extracted_text, None


def extract_text_from_txt(file_obj_or_path):
    """
    Extracts text from a plain TXT file trying common encodings.
    """
    try:
        if hasattr(file_obj_or_path, 'read'):
            raw_bytes = file_obj_or_path.read()
            if hasattr(file_obj_or_path, 'seek'):
                file_obj_or_path.seek(0)
        else:
            with open(file_obj_or_path, 'rb') as f:
                raw_bytes = f.read()
                
        # Try UTF-8 first, fallback to latin-1
        try:
            return raw_bytes.decode('utf-8').strip(), None
        except UnicodeDecodeError:
            return raw_bytes.decode('latin-1', errors='ignore').strip(), None
            
    except Exception as e:
        return "", f"Error reading TXT file: {str(e)}"


def extract_resume_text(uploaded_file):
    """
    Main extraction dispatcher.
    Accepts an uploaded file object or file path and detects file type by extension.
    Returns: (extracted_text: str, warning_or_error: str or None)
    """
    filename = uploaded_file.name if hasattr(uploaded_file, 'name') else str(uploaded_file)
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(uploaded_file)
    elif ext == '.docx':
        return extract_text_from_docx(uploaded_file)
    elif ext == '.txt':
        return extract_text_from_txt(uploaded_file)
    else:
        return "", f"Unsupported file format '{ext}'. Only PDF (.pdf), Word (.docx), and Plain Text (.txt) files are supported."
