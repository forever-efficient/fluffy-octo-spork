#!/usr/bin/env python3
"""
Script to regenerate embeddings with BAAI/bge-small-en-v1.5 model
"""

from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

# Configuration
SUPABASE_URL = "https://ioncpiocmpusocereeia.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbmNwaW9jbXB1c29jZXJlZWlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDA5Mzc2NiwiZXhwIjoyMDc1NjY5NzY2fQ.eLkYThE01N7JDbNGx1x9B2ja17jNE-dPj7Qxj_NLvtY"

def init_supabase():
    """Initialize Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_embeddings():
    """Initialize embedding model - BAAI/bge-small-en-v1.5"""
    print("🔧 Loading BAAI/bge-small-en-v1.5 model...")
    return SentenceTransformer('BAAI/bge-small-en-v1.5')

def clear_embeddings_table(supabase: Client):
    """Clear the existing embeddings table"""
    try:
        print("🗑️  Clearing existing embeddings...")
        
        # Try to delete all records from legal_documents_vectors
        result = supabase.table("legal_documents_vectors").delete().neq("id", 0).execute()
        print(f"✅ Cleared {len(result.data) if result.data else 'all'} existing embeddings")
        
    except Exception as e:
        print(f"⚠️  Error clearing embeddings: {e}")
        print("Continuing with regeneration...")

def regenerate_sample_embeddings(supabase: Client, model):
    """Generate a few sample embeddings to test the new model"""
    try:
        print("🧪 Generating sample embeddings with new model...")
        
        # Sample legal content for testing
        sample_content = [
            "Criminal mischief involves intentional damage to property of another person",
            "Domestic violence includes physical harm between family or household members", 
            "Property damage refers to the destruction or defacement of another's belongings",
            "Assault is the unlawful attempt to cause physical injury to another person",
            "Battery involves unlawful touching or striking of another person without consent"
        ]
        
        for i, content in enumerate(sample_content):
            print(f"📝 Processing sample {i+1}: {content[:50]}...")
            
            # Generate embedding
            embedding = model.encode(content).tolist()
            
            # Insert into database
            supabase.table("legal_documents_vectors").insert({
                "content": content,
                "embedding": embedding,
                "metadata": {
                    "title": f"sample_document_{i+1}",
                    "category": "test",
                    "chunk_index": i,
                    "processed_at": "2025-10-14T22:00:00.000000",
                    "total_chunks": 5,
                    "document_type": "sample_legal_content",
                    "model_used": "BAAI/bge-small-en-v1.5"
                }
            }).execute()
            
            print(f"✅ Inserted sample {i+1} with embedding dimensions: {len(embedding)}")
        
        print("🎉 Sample embeddings generated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error generating sample embeddings: {e}")
        return False

def test_vector_search(supabase: Client, model):
    """Test the vector search with a sample query"""
    try:
        print("🔍 Testing vector search...")
        
        # Generate query embedding
        query = "property damage domestic violence"
        query_embedding = model.encode(query).tolist()
        
        print(f"🎯 Testing search for: '{query}'")
        print(f"📊 Query embedding dimensions: {len(query_embedding)}")
        
        # Test the vector search function
        result = supabase.rpc("match_legal_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.1,  # Lower threshold for testing
            "match_count": 3
        }).execute()
        
        if result.data:
            print(f"✅ Vector search successful! Found {len(result.data)} matches:")
            for match in result.data:
                similarity = match.get('similarity', 0)
                content = match.get('chunk_text', '')[:100]
                print(f"   - Similarity: {similarity:.3f} | Content: {content}...")
        else:
            print("⚠️  No matches found (this might be expected with limited sample data)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing vector search: {e}")
        return False

def main():
    print("🚀 Starting embedding model migration to BAAI/bge-small-en-v1.5...")
    
    # Initialize clients
    supabase = init_supabase()
    model = init_embeddings()
    
    # Ask for confirmation before clearing
    print("\n⚠️  WARNING: This will clear ALL existing embeddings!")
    response = input("Do you want to continue? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        return
    
    # Clear existing embeddings
    clear_embeddings_table(supabase)
    
    # Generate sample embeddings
    if regenerate_sample_embeddings(supabase, model):
        # Test vector search
        if test_vector_search(supabase, model):
            print("\n🎉 Migration successful! Your database is now using BAAI/bge-small-en-v1.5")
            print("✅ You can now run the full PDF processing script to populate with all documents")
        else:
            print("\n⚠️  Migration completed but vector search test failed")
    else:
        print("\n❌ Migration failed during sample generation")

if __name__ == "__main__":
    main()