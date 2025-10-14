#!/bin/bash

echo "🔧 PDF Processing Setup for Legal Assistant Bot"
echo "==============================================="

# Install Python dependencies
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

# Make the processing script executable
chmod +x process-pdfs-from-storage-idempotent.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "🏗️  IMPORTANT: Database Schema Setup Required"
echo "=============================================="
echo ""
echo "1. Open your Supabase project dashboard"
echo "2. Go to SQL Editor" 
echo "3. Copy and paste the contents of 'vector-database-schema-standalone.sql'"
echo "4. Click 'RUN' to create the 384-dimensional vector table"
echo ""
echo "📋 Then to process PDFs:"
echo "1. Upload PDFs to Supabase storage bucket 'legal-documents'"
echo "2. Update API keys in process-pdfs-from-storage-idempotent.py if needed"
echo "3. Run: python3 process-pdfs-from-storage-idempotent.py"
echo ""
echo "🎯 This creates embeddings compatible with:"
echo "   - HuggingFace BAAI/bge-small-en-v1.5 (384-dim)"
echo "   - Your n8n Legal Assistant Bot workflow"