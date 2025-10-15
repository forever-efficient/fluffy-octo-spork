#!/usr/bin/env python3
"""
Idempotent script to process PDFs from Supabase storage into vector database.
Only processes files that haven't been processed before.
"""

from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import PyPDF2
from io import BytesIO
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
STORAGE_BUCKET = os.getenv('STORAGE_BUCKET', 'legal-documents')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables or .env file")

def init_supabase():
    """Initialize Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_embeddings():
    """Initialize embedding model - using same model as HuggingFace API"""
    return SentenceTransformer('BAAI/bge-small-en-v1.5')

def check_if_processed(supabase: Client, filename: str) -> bool:
    """Check if a file has already been processed in legal_documents_vectors table"""
    try:
        print(f"🔍 Checking if {filename} was already processed in legal_documents_vectors...")
        
        # Fixed approach: filter directly by filename in metadata
        result = supabase.table("legal_documents_vectors").select("id").eq("metadata->>title", filename).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            print(f"✅ Found existing chunks for {filename} (skipping)")
            return True
        
        print(f"❌ No existing data found for {filename}, will process")
        return False
        
    except Exception as e:
        print(f"⚠️  Error checking if {filename} was processed: {e}")
        # If we can't check, assume not processed to be safe
        return False

def get_file_hash(file_content: bytes) -> str:
    """Generate a hash of the file content for deduplication"""
    return hashlib.md5(file_content).hexdigest()

def simple_count_check(supabase: Client, filename: str) -> bool:
    """Simple check - count total records and see if it's reasonable for the file"""
    try:
        # Check if we have a reasonable number of records for this file size
        for table_name in ["legal_document_embeddings", "legal_documents_vectors"]:
            try:
                result = supabase.table(table_name).select("id", count="exact").execute()
                total_count = result.count if hasattr(result, 'count') else len(result.data or [])
                
                # If we have a large number of records, likely already processed
                if total_count > 1000:
                    print(f"📊 Found {total_count} total records in {table_name}")
                    print(f"🤔 Large dataset detected - checking if {filename} should be skipped...")
                    
                    # Additional check: try to get a sample and see if it contains our filename
                    sample = supabase.table(table_name).select("metadata").limit(10).execute()
                    if sample.data:
                        for record in sample.data:
                            if record.get('metadata') and isinstance(record['metadata'], dict):
                                if record['metadata'].get('title', '').startswith('crs2025'):
                                    print(f"✅ Found CRS documents already processed, skipping {filename}")
                                    return True
                    break
            except Exception:
                continue
        return False
    except Exception:
        return False

def check_content_hash(supabase: Client, file_hash: str) -> bool:
    """Check if content with this hash already exists"""
    try:
        # Check both table names for compatibility
        for table_name in ["legal_documents_vectors", "legal_document_embeddings"]:
            try:
                result = supabase.table(table_name).select("id").eq("metadata->>file_hash", file_hash).limit(1).execute()
                if result.data and len(result.data) > 0:
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False

def get_pdf_files_from_storage(supabase: Client):
    """Get list of PDF files from Supabase storage"""
    try:
        response = supabase.storage.from_(STORAGE_BUCKET).list()
        pdf_files = [file for file in response if file['name'].lower().endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files in storage")
        return pdf_files
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_pdf(supabase: Client, filename: str):
    """Download PDF from Supabase storage"""
    try:
        file_data = supabase.storage.from_(STORAGE_BUCKET).download(filename)
        return file_data
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end >= len(text):
            break
            
        start = end - overlap
    
    return chunks

def generate_embeddings(model, chunks: list) -> list:
    """Generate embeddings for chunks"""
    embeddings = model.encode(chunks, show_progress_bar=True)
    return embeddings

def detect_table_schema(supabase: Client):
    """Detect what columns exist in the table"""
    print("🔍 Detecting existing table schema...")
    
    test_data_variants = [
        # Variant 1: Most common schema (legal_document_embeddings)
        {
            "content": "test",
            "embedding": [0.0] * 384,
            "metadata": {"test": True}
        },
        # Variant 2: Alternative table name
        {
            "text": "test", 
            "embedding": [0.0] * 384,
            "metadata": {"test": True}
        }
    ]
    
    table_names = ["legal_document_embeddings", "legal_documents_vectors"]
    
    for table_name in table_names:
        for i, test_data in enumerate(test_data_variants):
            try:
                result = supabase.table(table_name).insert(test_data).execute()
                if result.data:
                    test_id = result.data[0].get('id')
                    if test_id:
                        supabase.table(table_name).delete().eq('id', test_id).execute()
                    print(f"✅ Detected schema variant {i+1}: {list(test_data.keys())} in table {table_name}")
                    return test_data.keys(), table_name
            except Exception as e:
                continue
    
    print("✅ Using default schema: ['content', 'embedding', 'metadata']")
    return ["content", "embedding", "metadata"], "legal_document_embeddings"

def store_in_vector_db(supabase: Client, filename: str, chunks: list, embeddings: list, file_hash: str, table_name: str = "legal_document_embeddings"):
    """Store chunks and embeddings in vector database - BATCH OPTIMIZED"""
    success_count = 0
    batch_size = 50
    
    print(f"🚀 Processing {len(chunks)} chunks in batches of {batch_size}...")
    
    for batch_start in range(0, len(chunks), batch_size):
        batch_end = min(batch_start + batch_size, len(chunks))
        batch_data = []
        
        for i in range(batch_start, batch_end):
            chunk = chunks[i]
            embedding = embeddings[i].tolist()
            
            data = {
                "content": chunk,
                "embedding": embedding,
                "metadata": {
                    "title": filename,
                    "category": "general",
                    "chunk_index": i,
                    "processed_at": datetime.now().isoformat(),
                    "total_chunks": len(chunks),
                    "document_type": "legal_document",
                    "file_hash": file_hash
                }
            }
            
            batch_data.append(data)
        
        try:
            result = supabase.table(table_name).insert(batch_data).execute()
            batch_success = len(result.data) if result.data else len(batch_data)
            success_count += batch_success
            
            print(f"  ✅ Batch {batch_start//batch_size + 1}: Stored {batch_success} chunks ({batch_start + batch_success}/{len(chunks)})")
            
        except Exception as e:
            print(f"❌ Batch insert failed: {str(e)[:100]}...")
    
    return success_count

def log_processing(supabase: Client, filename: str, chunks_created: int, file_hash: str):
    """Log processing result"""
    try:
        data = {
            "file_name": filename,
            "title": filename,
            "document_type": "legal_document",
            "category": "general",
            "processing_status": "completed",
            "chunks_created": chunks_created,
            "processed_at": datetime.now().isoformat(),
            "file_hash": file_hash
        }
        
        supabase.table("document_processing_logs").insert(data).execute()
        print(f"✅ Logged processing for {filename}")
        
    except Exception as e:
        print(f"⚠️  Error logging processing for {filename}: {e}")

def process_single_pdf(supabase: Client, model, filename: str, table_name: str):
    """Process a single PDF file with idempotency checks"""
    
    # Check if already processed by filename
    if check_if_processed(supabase, filename):
        return True
    
    print(f"\n🔄 Processing {filename}...")
    
    # Download PDF
    pdf_content = download_pdf(supabase, filename)
    if not pdf_content:
        print(f"❌ Failed to download {filename}")
        return False
    
    # Generate file hash for deduplication
    file_hash = get_file_hash(pdf_content)
    
    # THIRD: Check if content with same hash already exists
    if check_content_hash(supabase, file_hash):
        print(f"📋 Content with same hash already exists for {filename} (skipping)")
        return True
    
    # Extract text
    text = extract_text_from_pdf(pdf_content)
    if not text.strip():
        print(f"❌ No text extracted from {filename}")
        return False
    
    print(f"Extracted {len(text)} characters")
    
    # Create chunks
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = generate_embeddings(model, chunks)
    
    # Store in database
    print("Storing in vector database...")
    success_count = store_in_vector_db(supabase, filename, chunks, embeddings, file_hash, table_name)
    
    # Log processing
    log_processing(supabase, filename, success_count, file_hash)
    
    print(f"✅ Successfully processed {success_count}/{len(chunks)} chunks")
    return True

def main():
    """Main processing function"""
    print("🚀 Starting idempotent PDF processing...")
    
    # Initialize clients
    supabase = init_supabase()
    model = init_embeddings()
    
    # Detect table schema
    schema_columns, table_name = detect_table_schema(supabase)
    print(f"📝 Using table: {table_name} with columns: {list(schema_columns)}")
    
    # Get PDF files
    pdf_files = get_pdf_files_from_storage(supabase)
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    # Process each file
    processed_count = 0
    skipped_count = 0
    
    for file_info in pdf_files:
        filename = file_info['name']
        print(f"\n📄 Found PDF: {filename}")
        
        if process_single_pdf(supabase, model, filename, table_name):
            processed_count += 1
        else:
            skipped_count += 1
    
    print("\n🎉 Processing complete!")
    print(f"✅ Successfully processed: {processed_count} files")
    print(f"⏭️  Skipped (already processed): {skipped_count} files")
    print(f"📊 Total files: {len(pdf_files)}")

if __name__ == "__main__":
    main()