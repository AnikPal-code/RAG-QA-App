from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "RAG QA Bot API is running"}

@app.get("/status")
async def get_status():
    return {
        "has_document": False,
        "supported_formats": [".pdf", ".docx", ".txt"]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Test upload endpoint"""
    try:
        print(f"Received file: {file.filename}")
        print(f"Content type: {file.content_type}")
        
        # Read file content
        file_content = await file.read()
        print(f"File size: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # For now, just return success without processing
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully (test mode)",
            "filename": file.filename,
            "text_length": len(file_content)
        }
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question():
    return {
        "answer": {
            "query": "test",
            "result": "This is test mode. Upload functionality is being tested."
        }
    }
