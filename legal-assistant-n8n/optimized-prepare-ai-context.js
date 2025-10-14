// OPTIMIZED RAG PROMPT - Fixes duplicate summaries and integrates vector data
// Based on RAG best practices from Prompt Engineering Guide

// Enhanced RAG context preparation with proper prompt engineering
const items = [];

const normalizedMessage = $('Normalize Message').item.json;
const conversationMemory = $('Get Conversation Memory').all();
const vectorSearchResults = $('Vector Search HTTP Request').all();
const legalDocuments = $('Get Legal Documents').all();
const findlawResults = $('Search FindLaw Database').all();
const cornellResults = $('Search Cornell Law').all();
const scholarResults = $('Search Google Scholar Legal').all();
const justiaResults = $('Search Justia Legal Database').all();

// Build conversation history
let conversationHistory = '';
if (conversationMemory.length > 0 && conversationMemory[0].json.conversation_history) {
  conversationHistory = conversationMemory[0].json.conversation_history;
}

// Build PRIORITIZED context - Vector search first (most relevant)
let relevantContext = '';
let sourcesFound = [];

// 1. PRIORITY: Vector search results (PDF documents) - Most relevant to query
if (vectorSearchResults.length > 0 && vectorSearchResults[0].json) {
  const vectorData = vectorSearchResults[0].json;
  
  // Handle different response formats from Supabase function
  let vectorDocs = [];
  if (Array.isArray(vectorData)) {
    vectorDocs = vectorData;
  } else if (vectorData.data && Array.isArray(vectorData.data)) {
    vectorDocs = vectorData.data;
  }
  
  if (vectorDocs.length > 0) {
    relevantContext += 'MOST RELEVANT LEGAL DOCUMENTS:\\n';
    vectorDocs.slice(0, 5).forEach((doc, index) => {
      if (doc.content || doc.text || doc.document || doc.chunk_text) {
        const text = doc.content || doc.text || doc.document || doc.chunk_text;
        const similarity = doc.similarity ? ` (${(doc.similarity * 100).toFixed(1)}% relevance)` : '';
        relevantContext += `[${index + 1}] ${text.substring(0, 800)}${similarity}\\n\\n`;
        sourcesFound.push(`Vector Document ${index + 1}`);
      }
    });
  }
}

// 2. Additional legal database documents (limit to avoid noise)
if (legalDocuments.length > 0) {
  relevantContext += '\\nSUPPORTING LEGAL REFERENCES:\\n';
  legalDocuments.slice(0, 2).forEach((doc, index) => {
    if (doc.json.content || doc.json.text) {
      const text = doc.json.content || doc.json.text;
      relevantContext += `[REF${index + 1}] ${doc.json.title || 'Legal Reference'}: ${text.substring(0, 400)}\\n\\n`;
      sourcesFound.push(`Legal DB ${index + 1}`);
    }
  });
}

// Create RAG-optimized prompt following best practices
const aiPrompt = `You are analyzing a specific legal scenario. Use the provided legal documents to give a comprehensive, single response that directly addresses the user's question.

LEGAL QUESTION:
${normalizedMessage.messageText}

RETRIEVED LEGAL SOURCES:
${relevantContext}

INSTRUCTIONS:
- Write ONE comprehensive analysis that incorporates information from the retrieved sources
- Quote specific statutes, cases, or regulations from the sources when applicable  
- If the retrieved sources don't contain relevant information, clearly state this
- Focus on practical legal implications for this specific scenario
- Provide concrete next steps or recommendations where appropriate
- Do NOT create separate summary sections - integrate everything into a cohesive response

Sources available: ${sourcesFound.join(', ')}

Provide your analysis in a clear, structured format that flows naturally and incorporates the retrieved legal information.`;

items.push({
  json: {
    aiPrompt: aiPrompt,
    userMessage: normalizedMessage.messageText,
    userId: normalizedMessage.userId,
    chatId: normalizedMessage.chatId,
    conversationHistory: conversationHistory,
    timestamp: normalizedMessage.timestamp,
    sourcesUsed: sourcesFound,
    retrievedSources: {
      vectorDocuments: vectorSearchResults.length || 0,
      legalDocuments: legalDocuments.length || 0,
      findlawResults: findlawResults.length || 0,
      cornellResults: cornellResults.length || 0,
      scholarResults: scholarResults.length || 0,
      justiaResults: justiaResults.length || 0
    }
  }
});

return items;