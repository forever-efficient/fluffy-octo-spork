#!/usr/bin/env python3
"""
Simple script to process PDFs from Supabase storage into vector database.
Run this after you manually upload PDFs to Supabase storage.
"""

from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import PyPDF2
from io import BytesIO
from datetime import datetime

# Configuration
SUPABASE_URL = "https://ioncpiocmpusocereeia.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbmNwaW9jbXB1c29jZXJlZWlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDA5Mzc2NiwiZXhwIjoyMDc1NjY5NzY2fQ.eLkYThE01N7JDbNGx1x9B2ja17jNE-dPj7Qxj_NLvtY"
STORAGE_BUCKET = "legal-documents"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def init_supabase():
    """Initialize Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_embeddings():
    """Initialize embedding model - using same model as HuggingFace API"""
    # Note: Using sentence-transformers/all-MiniLM-L6-v2 which produces 384-dim embeddings
    # This matches the BAAI/bge-small-en-v1.5 dimensions used in the n8n workflow
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_pdf_files_from_storage(supabase: Client):
    """Get list of PDF files from Supabase storage"""
    try:
        # First, list all buckets
        print("Debug: Listing all available buckets...")
        buckets = supabase.storage.list_buckets()
        print(f"Debug: Available buckets: {buckets}")
        
        # Now try to access our specific bucket
        response = supabase.storage.from_(STORAGE_BUCKET).list()
        print(f"Debug: Raw response from storage bucket '{STORAGE_BUCKET}': {response}")
        print(f"Debug: Total files found: {len(response) if response else 0}")
        if response:
            for file in response:
                print(f"Debug: File found: {file}")
        pdf_files = [file for file in response if file['name'].lower().endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files in storage")
        return pdf_files
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_pdf(supabase: Client, filename: str):
    """Download PDF from Supabase storage"""
    try:
        response = supabase.storage.from_(STORAGE_BUCKET).download(filename)
        return BytesIO(response)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes"""
    try:
        reader = PyPDF2.PdfReader(pdf_bytes)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def generate_embeddings(model, chunks):
    """Generate embeddings for text chunks - 384 dimensions"""
    embeddings = model.encode(chunks).tolist()
    
    # Verify embeddings are 384 dimensions (should be by default with all-MiniLM-L6-v2)
    for i, embedding in enumerate(embeddings):
        if len(embedding) != 384:
            print(f"Warning: Chunk {i} has {len(embedding)} dimensions, expected 384")
    
    return embeddings

def detect_table_schema(supabase: Client):
    """Detect what columns exist in the table by testing a small insert"""
    print("🔍 Detecting existing table schema...")
    
    test_data_variants = [
        # Variant 1: Most common schema
        {
            "content": "test",
            "embedding": [0.0] * 384,  # 384 dimensions for our model
            "metadata": {"test": True}
        },
        # Variant 2: Alternative column names
        {
            "text": "test", 
            "embedding": [0.0] * 384,
            "metadata": {"test": True}
        },
        # Variant 3: With chunk_text column
        {
            "chunk_text": "test",
            "embedding": [0.0] * 384,
            "metadata": {"test": True}
        }
    ]
    
    for i, test_data in enumerate(test_data_variants):
        try:
            # Try to insert test data
            result = supabase.table("legal_documents_vectors").insert(test_data).execute()
            # If successful, delete the test record and return the schema
            if result.data:
                test_id = result.data[0].get('id')
                if test_id:
                    supabase.table("legal_documents_vectors").delete().eq('id', test_id).execute()
                print(f"✅ Detected schema variant {i+1}: {list(test_data.keys())}")
                return test_data.keys()
        except Exception as e:
            print(f"❌ Schema variant {i+1} failed: {str(e)[:100]}...")
            continue
    
    print("⚠️  Could not detect schema, will try basic fallback")
    return ["content", "embedding"]

def store_in_vector_db(supabase: Client, filename: str, chunks: list, embeddings: list):
    """Store chunks and embeddings in vector database - BATCH OPTIMIZED"""
    success_count = 0
    batch_size = 50  # Process in batches of 50 for better performance
    
    # Detect what columns the table actually has
    schema_columns = detect_table_schema(supabase)
    
    print(f"📝 Using detected columns: {list(schema_columns)}")
    print(f"🚀 Processing {len(chunks)} chunks in batches of {batch_size}...")
    
    # Process chunks in batches
    for batch_start in range(0, len(chunks), batch_size):
        batch_end = min(batch_start + batch_size, len(chunks))
        batch_data = []
        
        # Prepare batch data
        for i in range(batch_start, batch_end):
            chunk = chunks[i]
            embedding = embeddings[i]
            
            # Build data based on detected schema
            data = {}
            
            # Add text content with the right column name
            if "chunk_text" in schema_columns:
                data["chunk_text"] = chunk
            elif "content" in schema_columns:
                data["content"] = chunk
            elif "text" in schema_columns:
                data["text"] = chunk
            
            # Always include embedding - FIXED: Ensure proper vector format for PostgreSQL
            # Convert list to proper PostgreSQL vector format
            if isinstance(embedding, list) and len(embedding) == 384:
                # Format as PostgreSQL vector: [0.1, 0.2, 0.3, ...]
                vector_string = '[' + ','.join([str(float(x)) for x in embedding]) + ']'
                data["embedding"] = vector_string
            else:
                print(f"❌ Warning: Invalid embedding format for chunk {i}: {type(embedding)}, length: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
                continue  # Skip this chunk if embedding is invalid
            
            # Add metadata if supported
            if "metadata" in schema_columns:
                data["metadata"] = {
                    "title": filename,
                    "document_type": "legal_document", 
                    "category": "general",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "processed_at": datetime.now().isoformat()
                }
            
            # Add chunk_index if supported
            if "chunk_index" in schema_columns:
                data["chunk_index"] = i
            
            batch_data.append(data)
        
        # Insert entire batch at once
        try:
            result = supabase.table("legal_documents_vectors").insert(batch_data).execute()
            batch_success = len(result.data) if result.data else len(batch_data)
            success_count += batch_success
            
            print(f"  ✅ Batch {batch_start//batch_size + 1}: Stored {batch_success} chunks ({batch_start + batch_success}/{len(chunks)})")
            
        except Exception as e:
            print(f"❌ Batch insert failed, falling back to individual inserts for batch {batch_start//batch_size + 1}")
            print(f"Error: {str(e)[:100]}...")
            
            # Fallback: Insert individually for this batch
            for i in range(batch_start, batch_end):
                try:
                    individual_data = batch_data[i - batch_start]
                    supabase.table("legal_documents_vectors").insert(individual_data).execute()
                    success_count += 1
                except Exception as e2:
                    print(f"❌ Individual insert failed for chunk {i}: {str(e2)[:50]}...")
    
    return success_count

def log_processing(supabase: Client, filename: str, chunks_created: int):
    """Log processing result"""
    try:
        data = {
            "file_name": filename,
            "title": filename,
            "document_type": "legal_document",
            "category": "general",
            "processing_status": "completed",
            "chunks_created": chunks_created,
            "processed_at": datetime.now().isoformat()
        }
        
        supabase.table("document_processing_logs").insert(data).execute()
        print(f"Logged processing for {filename}")
        
    except Exception as e:
        print(f"Error logging processing for {filename}: {e}")

def process_single_pdf(supabase: Client, model, filename: str):
    """Process a single PDF file"""
    print(f"\nProcessing {filename}...")
    
    # Download PDF
    pdf_bytes = download_pdf(supabase, filename)
    if not pdf_bytes:
        return False
    
    # Extract text
    text = extract_text_from_pdf(pdf_bytes)
    if not text:
        print(f"No text extracted from {filename}")
        return False
    
    print(f"Extracted {len(text)} characters")
    
    # Chunk text
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = generate_embeddings(model, chunks)
    
    # Store in vector database
    print("Storing in vector database...")
    success_count = store_in_vector_db(supabase, filename, chunks, embeddings)
    
    # Log processing
    log_processing(supabase, filename, success_count)
    
    print(f"Successfully processed {success_count}/{len(chunks)} chunks")
    return True

def main():
    """Main processing function"""
    print("Starting PDF processing from Supabase storage...")
    
    # Initialize clients
    supabase = init_supabase()
    model = init_embeddings()
    
    # Get PDF files from storage
    pdf_files = get_pdf_files_from_storage(supabase)
    
    if not pdf_files:
        print("No PDF files found in storage")
        return
    
    # Process each PDF
    processed_count = 0
    for file_info in pdf_files:
        filename = file_info.get('name', 'unknown')
        file_size = file_info.get('size', 'unknown')
        print(f"\nFound PDF: {filename} (size: {file_size})")
        
        if process_single_pdf(supabase, model, filename):
            processed_count += 1
    
    print(f"\n✅ Processing complete! Successfully processed {processed_count}/{len(pdf_files)} files")

if __name__ == "__main__":
    main()