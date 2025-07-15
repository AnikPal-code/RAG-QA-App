import os
import tempfile
from typing import List, Dict, Any
from docx import Document
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


class FileProcessor:
    """Handles processing of uploaded files (PDF, DOCX, TXT)"""

    def __init__(self):
        self.supported_types = ['.pdf', '.docx', '.txt']

    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        return any(filename.lower().endswith(ext) for ext in self.supported_types)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using pdfplumber and Tesseract OCR fallback"""
        print(f"DEBUG: Processing PDF file: {file_path}")
        
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                print(f"DEBUG: PDF has {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract regular text
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        print(f"DEBUG: Page {page_num + 1} extracted {len(page_text)} characters")
                    else:
                        print(f"DEBUG: Page {page_num + 1} - No text extracted")
                    
                    # Also try to extract tables if regular text is minimal
                    if not page_text or len(page_text.strip()) < 20:
                        tables = page.extract_tables()
                        if tables:
                            print(f"DEBUG: Found {len(tables)} tables on page {page_num + 1}")
                            for table in tables:
                                for row in table:
                                    if row:
                                        text += " | ".join([cell or "" for cell in row]) + "\n"
            
            print(f"DEBUG: pdfplumber extracted {len(text.strip())} characters total")
            
            # If no text extracted, try OCR
            if not text.strip():
                print("DEBUG: No text found with pdfplumber, trying OCR...")
                try:
                    # Convert PDF to images
                    images = convert_from_path(file_path)
                    ocr_text = ""
                    
                    for i, image in enumerate(images):
                        print(f"DEBUG: Processing page {i+1} with OCR...")
                        # Extract text using Tesseract OCR
                        page_text = pytesseract.image_to_string(image)
                        if page_text.strip():
                            ocr_text += page_text + "\n"
                            print(f"DEBUG: OCR extracted {len(page_text)} characters from page {i+1}")
                    
                    if ocr_text.strip():
                        text = ocr_text.strip()
                        print(f"DEBUG: OCR extracted {len(text)} characters total")
                    
                except Exception as ocr_error:
                    print(f"DEBUG: OCR failed: {str(ocr_error)}")
                    raise ValueError(f"Error processing PDF with OCR: {str(ocr_error)}")
            
            # Final check
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF. The PDF might be image-based, corrupted, or password-protected.")
            
            print(f"DEBUG: Final text length: {len(text.strip())} characters")
            return text.strip()
            
        except Exception as e:
            print(f"DEBUG: Error in extract_text_from_pdf: {str(e)}")
            raise ValueError(f"Error processing PDF: {str(e)}")

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        print(f"DEBUG: Processing DOCX file: {file_path}")
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            print(f"DEBUG: DOCX extracted {len(text.strip())} characters")
            return text.strip()
        except Exception as e:
            print(f"DEBUG: Error in extract_text_from_docx: {str(e)}")
            raise ValueError(f"Error processing DOCX: {str(e)}")

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        print(f"DEBUG: Processing TXT file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read().strip()
            print(f"DEBUG: TXT extracted {len(text)} characters")
            return text
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read().strip()
                print(f"DEBUG: TXT extracted {len(text)} characters (latin-1 encoding)")
                return text
            except Exception as e:
                print(f"DEBUG: Error in extract_text_from_txt: {str(e)}")
                raise ValueError(f"Error processing TXT: {str(e)}")
        except Exception as e:
            print(f"DEBUG: Error in extract_text_from_txt: {str(e)}")
            raise ValueError(f"Error processing TXT: {str(e)}")

    def process_file(self, file_path: str, filename: str) -> str:
        """Process uploaded file and extract text"""
        print(f"DEBUG: Processing file: {filename}")
        print(f"DEBUG: File path: {file_path}")
        print(f"DEBUG: File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"DEBUG: File size: {file_size} bytes")
        
        if not self.is_supported_file(filename):
            raise ValueError(f"Unsupported file type. Supported types: {', '.join(self.supported_types)}")

        file_extension = os.path.splitext(filename)[1].lower()
        print(f"DEBUG: File extension: {file_extension}")

        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file temporarily and return path"""
        print(f"DEBUG: Saving uploaded file: {filename}")
        print(f"DEBUG: File content size: {len(file_content)} bytes")
        
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, filename)
        print(f"DEBUG: Temp file path: {temp_file_path}")

        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(file_content)
        
        print(f"DEBUG: File saved successfully")
        return temp_file_path

    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"DEBUG: Cleaned up temp file: {file_path}")
        except Exception as e:
            print(f"WARNING: Could not delete temp file {file_path}: {str(e)}")
