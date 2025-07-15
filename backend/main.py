from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qa_chain import qa_bot, qa_bot_instance
from file_processor import FileProcessor
from fastapi.staticfiles import StaticFiles

app = FastAPI()
file_processor = FileProcessor()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request models
class QuestionRequest(BaseModel):
    question: str

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document (PDF, DOCX, TXT)
    """
    try:
        print(f"Received file: {file.filename}, Content type: {file.content_type}")
        
        # Check file type
        if not file_processor.is_supported_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(file_processor.supported_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        print(f"File size: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Save file temporarily
        temp_file_path = file_processor.save_uploaded_file(file_content, file.filename)
        print(f"Temporary file saved at: {temp_file_path}")
        
        try:
            # Process file and extract text
            extracted_text = file_processor.process_file(temp_file_path, file.filename)
            print(f"Extracted text length: {len(extracted_text)} characters")
            print(f"First 200 characters: {extracted_text[:200]}...")
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValueError(f"Insufficient text extracted from {file.filename}. Only {len(extracted_text)} characters found.")
            
            # Process the text with QA bot
            result = qa_bot_instance.process_document_text(extracted_text, file.filename)
            
            return {
                "success": True,
                "message": result,
                "filename": file.filename,
                "text_length": len(extracted_text)
            }
        
        finally:
            # Clean up temporary file
            file_processor.cleanup_temp_file(temp_file_path)
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded document
    """
    try:
        answer = qa_bot(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """
    Get the current status of the QA bot
    """
    has_document = qa_bot_instance.current_document_text is not None
    return {
        "has_document": has_document,
        "supported_formats": file_processor.supported_types
    }

@app.get("/")
async def root():
    return {"message": "RAG QA Bot API is running"}
