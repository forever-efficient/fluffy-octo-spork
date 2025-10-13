#!/bin/bash

# Test script for PDF processing
# Replace YOUR_N8N_DOMAIN with your actual n8n domain

echo "Testing PDF Processing Workflow..."

# Test with curl
curl -X POST "https://YOUR_N8N_DOMAIN/webhook/process-pdf-fixed" \
  -F "file=@sample-legal-document.pdf" \
  -F "title=Sample Legal Document" \
  -F "document_type=statute" \
  -F "category=criminal_law" \
  -F "jurisdiction=federal" \
  -F "uploaded_by=admin"

echo "PDF processing test completed!"