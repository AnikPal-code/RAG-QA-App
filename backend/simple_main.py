from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os
from typing import Optional
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering
import torch

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class SimpleQABot:
    def __init__(self):
        self.document_text = None
        self.filename = None
        self.qa_pipeline = None
        
    def load_qa_model(self):
        """Load QA model on first use"""
        if self.qa_pipeline is None:
            print("Loading QA model...")
            model_name = "distilbert-base-cased-distilled-squad"
            self.qa_pipeline = pipeline("question-answering", 
                                      model=model_name, 
                                      tokenizer=model_name)
            print("QA model loaded successfully!")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error processing DOCX: {str(e)}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            raise ValueError(f"Error processing TXT: {str(e)}")
    
    def process_file(self, file_path: str, filename: str) -> str:
        """Process uploaded file and extract text"""
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        if not text or len(text.strip()) < 10:
            raise ValueError(f"No meaningful text extracted from {filename}")
        
        self.document_text = text
        self.filename = filename
        return text
    
    def answer_question(self, question: str) -> dict:
        """Answer question using the uploaded document"""
        if not self.document_text:
            return {
                "query": question,
                "result": "No document has been uploaded yet. Please upload a document first."
            }
        
        self.load_qa_model()
        
        try:
            # Split document into smaller chunks if it's too long
            max_length = 512
            text = self.document_text
            
            if len(text) > max_length:
                # Take first part of document for simplicity
                text = text[:max_length]
            
            # Get answer from the model
            result = self.qa_pipeline(question=question, context=text)
            
            return {
                "query": question,
                "result": result['answer'],
                "confidence": result['score']
            }
        except Exception as e:
            return {
                "query": question,
                "result": f"Error processing question: {str(e)}"
            }

# Global bot instance
qa_bot = SimpleQABot()

@app.get("/")
async def root():
    return {"message": "Simple RAG QA Bot API is running"}

@app.get("/status")
async def get_status():
    return {
        "has_document": qa_bot.document_text is not None,
        "supported_formats": [".pdf", ".docx", ".txt"],
        "filename": qa_bot.filename
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        print(f"Received file: {file.filename}")
        
        # Check file type
        supported_types = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(supported_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        print(f"File size: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Process file and extract text
            extracted_text = qa_bot.process_file(temp_file_path, file.filename)
            print(f"Extracted text length: {len(extracted_text)} characters")
            
            return {
                "success": True,
                "message": f"Document '{file.filename}' processed successfully. You can now ask questions about it.",
                "filename": file.filename,
                "text_length": len(extracted_text)
            }
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded document"""
    try:
        answer = qa_bot.answer_question(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
