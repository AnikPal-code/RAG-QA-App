from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.schema import Document
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import os
import shutil
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer  
from sklearn.metrics.pairwise import cosine_similarity

class DynamicQABot:
    def __init__(self):
        # Initialize models lazily to speed up startup
        self.embedding_model = None
        self.similarity_model = None
        self.llm = None
        self.models_loaded = False
        
        # Text splitter
        self.text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        # Initialize with default document if exists
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
        self.current_document_text = None
        
        # Load default document if exists
        self._load_default_document()
    
    def _load_models(self):
        """Load AI models on first use"""
        if self.models_loaded:
            return
        
        try:
            print("Loading AI models...")
            # Initialize models
            self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self.similarity_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            
            # Load HuggingFace model for QA
            model_name = "google/flan-t5-small"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=200)
            self.llm = HuggingFacePipeline(pipeline=pipe)
            
            self.models_loaded = True
            print("AI models loaded successfully!")
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            raise
    
    def _load_default_document(self):
        """Load default business_docs.txt if it exists"""
        try:
            if os.path.exists("business_docs.txt"):
                loader = TextLoader("business_docs.txt")
                documents = loader.load()
                self._setup_vectorstore(documents)
                self.current_document_text = documents[0].page_content if documents else None
        except Exception as e:
            print(f"Warning: Could not load default document: {str(e)}")
    
    def _cleanup_vectorstore(self):
        """Safely cleanup existing vector store"""
        try:
            # Close existing vectorstore connection if it exists
            if self.vectorstore is not None:
                # Try to delete the collection first
                try:
                    self.vectorstore.delete_collection()
                except:
                    pass
                self.vectorstore = None
                self.retriever = None
                self.qa_chain = None
            
            # Wait a bit for file handles to be released
            import time
            time.sleep(0.5)
            
            # Try to remove the directory
            if os.path.exists("./chroma_db"):
                try:
                    shutil.rmtree("./chroma_db")
                except PermissionError:
                    # If we can't delete, create a new unique directory name
                    import uuid
                    new_dir = f"./chroma_db_{uuid.uuid4().hex[:8]}"
                    print(f"Could not clean old database, using new directory: {new_dir}")
                    self.db_dir = new_dir
                    return
            
            self.db_dir = "./chroma_db"
        except Exception as e:
            print(f"Warning during vectorstore cleanup: {str(e)}")
            # Create a unique directory name as fallback
            import uuid
            self.db_dir = f"./chroma_db_{uuid.uuid4().hex[:8]}"
    
    def _setup_vectorstore(self, documents: List[Document]):
        """Setup vector store with given documents"""
        self._load_models()  # Load models when first needed
        
        docs = self.text_splitter.split_documents(documents)
        
        # Clean up existing vector store safely
        self._cleanup_vectorstore()
        
        # Create new vector store
        if not hasattr(self, 'db_dir'):
            self.db_dir = "./chroma_db"
        self.vectorstore = Chroma.from_documents(docs, self.embedding_model, persist_directory=self.db_dir)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        self.qa_chain = RetrievalQA.from_chain_type(llm=self.llm, retriever=self.retriever)
    
    def process_document_text(self, text: str, filename: str = "uploaded_document"):
        """Process document text and create vector store"""
        if not text.strip():
            raise ValueError("Document text is empty")
        
        # Create document object
        doc = Document(page_content=text, metadata={"source": filename})
        self._setup_vectorstore([doc])
        self.current_document_text = text
        
        return f"Document '{filename}' processed successfully. You can now ask questions about it."
    
    def _check_relevance(self, question: str, threshold: float = 0.3) -> bool:
        """Check if question is relevant to the document content"""
        if not self.current_document_text:
            return False
        
        try:
            self._load_models()  # Load models when first needed
            # Get embeddings for question and document
            question_embedding = self.similarity_model.encode([question])
            
            # Get a sample of document text (first 1000 characters)
            doc_sample = self.current_document_text[:1000]
            doc_embedding = self.similarity_model.encode([doc_sample])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(question_embedding, doc_embedding)[0][0]
            
            return similarity > threshold
        except Exception as e:
            print(f"Error checking relevance: {str(e)}")
            return True  # If error, assume relevant to avoid blocking
    
    def ask_question(self, question: str) -> dict:
        """Ask a question about the document"""
        if not self.qa_chain:
            return {
                "query": question,
                "result": "No document has been uploaded yet. Please upload a document first."
            }
        
        # Check if question is relevant
        if not self._check_relevance(question):
            return {
                "query": question,
                "result": "I'm sorry, but your question doesn't appear to be relevant to the uploaded document. Please ask questions related to the document content."
            }
        
        try:
            # Get answer from QA chain
            result = self.qa_chain.invoke({"query": question})
            
            # Format response
            if isinstance(result, dict):
                return {
                    "query": question,
                    "result": result.get("result", "No answer found.")
                }
            else:
                return {
                    "query": question,
                    "result": str(result)
                }
        except Exception as e:
            return {
                "query": question,
                "result": f"Error processing question: {str(e)}"
            }

# Create global instance
qa_bot_instance = DynamicQABot()

# Maintain backward compatibility
def qa_bot(question):
    result = qa_bot_instance.ask_question(question)
    return result
