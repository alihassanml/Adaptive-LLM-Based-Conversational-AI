import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx
import json
import os

# Initialize embedding model (lightweight)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

FAISS_INDEX_PATH = './src/database/faiss_index.bin'
METADATA_PATH = './src/database/metadata.json'

class RAGHandler:
    def __init__(self):
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self.index = None
        self.metadata = []
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        
        self.load_or_create_index()
    
    def load_or_create_index(self):
        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(METADATA_PATH):
                # Load existing index
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                print("✅ Created new FAISS index")
        except Exception as e:
            print(f"⚠️ Error loading FAISS index: {e}")
            # Create fresh index on error
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
    
    def extract_text_from_file(self, file_path: str, file_type: str):
        try:
            if file_type == 'pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ' '.join([page.extract_text() for page in reader.pages])
            elif file_type in ['doc', 'docx']:
                doc = docx.Document(file_path)
                text = ' '.join([para.text for para in doc.paragraphs])
            elif file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError("Unsupported file type")
            return text
        except Exception as e:
            print(f"❌ Error extracting text from {file_path}: {e}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 500):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
        return chunks
    
    def add_document(self, file_path: str, file_type: str, user_id: str = "user123"):
        try:
            text = self.extract_text_from_file(file_path, file_type)
            chunks = self.chunk_text(text)
            
            print(f"📄 Processing {len(chunks)} chunks from {file_path}")
            
            for chunk in chunks:
                embedding = embedder.encode([chunk])[0]
                self.index.add(np.array([embedding], dtype=np.float32))
                self.metadata.append({
                    "text": chunk,
                    "file": file_path,
                    "user_id": user_id
                })
            
            # Save index with error handling
            self._safe_save()
            print(f"✅ Successfully indexed {file_path}")
            
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            raise
    
    def _safe_save(self):
        """Safely save FAISS index and metadata"""
        try:
            # Save to temporary files first
            temp_index_path = FAISS_INDEX_PATH + '.tmp'
            temp_metadata_path = METADATA_PATH + '.tmp'
            
            # Write FAISS index
            faiss.write_index(self.index, temp_index_path)
            
            # Write metadata
            with open(temp_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            # If successful, replace old files
            if os.path.exists(FAISS_INDEX_PATH):
                os.remove(FAISS_INDEX_PATH)
            os.rename(temp_index_path, FAISS_INDEX_PATH)
            
            if os.path.exists(METADATA_PATH):
                os.remove(METADATA_PATH)
            os.rename(temp_metadata_path, METADATA_PATH)
            
            print(f"💾 Saved index with {self.index.ntotal} vectors")
            
        except Exception as e:
            print(f"❌ Error saving index: {e}")
            # Clean up temp files
            if os.path.exists(temp_index_path):
                os.remove(temp_index_path)
            if os.path.exists(temp_metadata_path):
                os.remove(temp_metadata_path)
            raise
    
    def search(self, query: str, top_k: int = 3):
        try:
            if self.index.ntotal == 0:
                return []
            
            query_embedding = embedder.encode([query])[0]
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32), 
                min(top_k, self.index.ntotal)
            )
            
            results = []
            for idx in indices[0]:
                if idx < len(self.metadata) and idx >= 0:
                    results.append(self.metadata[idx]["text"])
            return results
        except Exception as e:
            print(f"❌ Error during search: {e}")
            return []

rag_handler = RAGHandler()