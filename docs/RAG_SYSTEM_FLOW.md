# RAG System Architecture & Flow Documentation

## 🏗️ System Architecture Overview

Your RAG system is a production-ready Sports Authority of India (SAI) knowledge system with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ DATA SOURCES│    │ PROCESSING  │    │   STORAGE   │         │
│  │             │    │   PIPELINE  │    │             │         │
│  │ • PDF Files │───▶│ • PDF Proc. │───▶│ • ChromaDB  │         │
│  │ • Web Pages │    │ • Web Scraper│    │ • Vector DB │         │
│  │ • SAI Docs  │    │ • Text Split│    │ • Cache     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                ▲                │
│                                                │                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    API      │    │    RAG      │    │ EMBEDDINGS  │         │
│  │             │    │   ENGINE    │    │             │         │
│  │ • Flask API │◀───│ • LangChain │◀───│ • HuggingFace│         │
│  │ • Endpoints │    │ • Retrieval │    │ • MiniLM-L6 │         │
│  │ • JSON Resp │    │ • Generation│    │ • Similarity│         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                              ▲                                 │
│                              │                                 │
│                      ┌─────────────┐                          │
│                      │     LLM     │                          │
│                      │             │                          │
│                      │ • Gemini    │                          │
│                      │ • Flash 1.5 │                          │
│                      │ • Google AI │                          │
│                      └─────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Process

### 1. **Data Ingestion Phase**
```
PDF Documents ──┐
                ├──▶ Data Pipeline ──▶ Text Extraction ──▶ Chunking
Web Content  ───┘
```

**Components:**
- **PDF Processor**: Uses PyMuPDF → pdfplumber → PyPDF2 → OCR fallbacks
- **Web Scraper**: Scrapes SAI websites with hyperlink following (3-depth)
- **Content Filter**: Relevance scoring (0-100) for sports-related content

### 2. **Text Processing Phase**
```
Raw Text ──▶ Text Splitter ──▶ Chunks (1000 chars, 200 overlap) ──▶ Metadata Addition
```

**Configuration:**
- Chunk Size: 1000 characters
- Overlap: 200 characters
- Splitter: RecursiveCharacterTextSplitter

### 3. **Embedding Phase**
```
Text Chunks ──▶ HuggingFace Embeddings ──▶ Vector Representations ──▶ ChromaDB
```

**Embedding Model:**
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- Normalization: Enabled
- Device: CPU optimized

### 4. **Storage Phase**
```
Vector Embeddings ──▶ ChromaDB ──▶ Persistent Storage (./vector_store/)
                  └──▶ Cache ──▶ File System (./cache/)
```

### 5. **Query Processing Phase**
```
User Query ──▶ Embedding ──▶ Similarity Search ──▶ Context Retrieval ──▶ LLM Generation
```

**Retrieval:**
- Algorithm: Cosine Similarity
- Top-K: 5 most relevant chunks
- Search Type: Semantic similarity

### 6. **Response Generation Phase**
```
Retrieved Context + User Query ──▶ Gemini 1.5 Flash ──▶ Generated Response ──▶ JSON API
```

## 🔧 Technical Stack

### **Core Technologies**
| Component | Technology | Version/Model |
|-----------|------------|---------------|
| **Framework** | LangChain | Latest |
| **Vector DB** | ChromaDB | Persistent |
| **Embeddings** | HuggingFace | all-MiniLM-L6-v2 |
| **LLM** | Google Gemini | 1.5-flash |
| **API** | Flask | Python |
| **Text Processing** | RecursiveCharacterTextSplitter | LangChain |

### **Data Sources**
- SAI PDF Documents (./data/)
- SAI Websites (urls.txt)
- Press Releases
- Training Materials
- Policy Documents

## 🚀 API Usage Guide

### **Starting the System**

1. **Environment Setup**
```bash
# Set Gemini API Key in .env
GEMINI_API_KEY=your_actual_api_key_here

# Install dependencies
pip install -r requirements.txt
```

2. **Start the API Server**
```bash
python main_app.py
```

Server starts on: `http://127.0.0.1:5000`

### **API Endpoints**

#### 1. **Ask Questions (Main Endpoint)**
```http
POST /ask
Content-Type: application/json

{
    "query": "What are the TOPS training programs offered by SAI?"
}
```

**Response:**
```json
{
    "query": "What are the TOPS training programs offered by SAI?",
    "response": "Based on SAI documents, TOPS (Target Olympic Podium Scheme) offers...",
    "sources_used": 5,
    "sources": [
        {
            "title": "TOPS Guidelines 2024",
            "source": "sai_tops_document.pdf",
            "category": "pdf_content"
        }
    ],
    "system": "enhanced_rag_pipeline",
    "model": "gemini-1.5-flash",
    "vector_store": "chromadb"
}
```

#### 2. **Health Check**
```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "rag_system": "enhanced_pipeline",
    "total_chunks": 1245,
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model": "gemini-1.5-flash",
    "vector_store": "ChromaDB"
}
```

#### 3. **System Statistics**
```http
GET /stats
```

**Response:**
```json
{
    "total_chunks": 1245,
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model": "gemini-1.5-flash",
    "vector_store": "ChromaDB",
    "persist_directory": "./vector_store",
    "pipeline_stats": {
        "pdf_documents": 450,
        "web_documents": 95,
        "total_documents": 545
    }
}
```

#### 4. **Refresh Data Pipeline**
```http
POST /pipeline/refresh
```

**Response:**
```json
{
    "status": "success",
    "message": "Data pipeline refreshed successfully",
    "stats": { ... }
}
```

#### 5. **Pipeline Status**
```http
GET /pipeline/status
```

**Response:**
```json
{
    "pipeline_active": true,
    "total_documents": 545,
    "vector_store": "ChromaDB",
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model": "gemini-1.5-flash",
    "pipeline_details": {
        "pdf_documents": 450,
        "web_documents": 95,
        "processing_time": 245.67,
        "last_run": "2025-09-19T10:30:00"
    }
}
```

## 💡 Usage Examples

### **Python Client Example**
```python
import requests
import json

# API base URL
API_URL = "http://127.0.0.1:5000"

def ask_question(question):
    response = requests.post(
        f"{API_URL}/ask",
        json={"query": question},
        headers={"Content-Type": "application/json"}
    )
    return response.json()

# Example usage
questions = [
    "What are the SAI training centers in India?",
    "How do I apply for TOPS funding?",
    "What are the fitness standards for athletics?",
    "Tell me about Khelo India scheme"
]

for question in questions:
    result = ask_question(question)
    print(f"Q: {question}")
    print(f"A: {result['response'][:200]}...")
    print(f"Sources: {result['sources_used']}")
    print("-" * 50)
```

### **JavaScript/Node.js Example**
```javascript
const axios = require('axios');

const API_URL = 'http://127.0.0.1:5000';

async function askQuestion(question) {
    try {
        const response = await axios.post(`${API_URL}/ask`, {
            query: question
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        return null;
    }
}

// Example usage
async function main() {
    const questions = [
        "What are the SAI training facilities?",
        "How does the talent identification program work?",
        "What support does SAI provide to athletes?"
    ];

    for (const question of questions) {
        console.log(`Q: ${question}`);
        const result = await askQuestion(question);
        if (result) {
            console.log(`A: ${result.response.substring(0, 200)}...`);
            console.log(`Sources: ${result.sources_used}`);
        }
        console.log('-'.repeat(50));
    }
}

main();
```

### **cURL Examples**
```bash
# Ask a question
curl -X POST http://127.0.0.1:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the TOPS scheme?"}'

# Check system health
curl -X GET http://127.0.0.1:5000/health

# Get system statistics
curl -X GET http://127.0.0.1:5000/stats

# Refresh data pipeline
curl -X POST http://127.0.0.1:5000/pipeline/refresh
```

## 🔍 How RAG Search Works

### **Search Process Detail**
1. **Query Embedding**: User question → all-MiniLM-L6-v2 → 384D vector
2. **Similarity Search**: Query vector vs Document vectors → Cosine similarity
3. **Context Retrieval**: Top 5 most similar document chunks
4. **Prompt Construction**: Context + Question → Structured prompt
5. **LLM Generation**: Gemini 1.5 Flash → Response based on context
6. **Response Assembly**: Answer + Sources + Metadata → JSON response

### **Similarity Scoring**
- **Range**: 0.0 to 1.0 (higher = more similar)
- **Threshold**: Content relevance ≥ 5.0 (sports-related)
- **Ranking**: Highest similarity scores selected first

## 📈 Performance Metrics

### **Current System Stats**
- **Total Documents**: ~545 documents
- **Vector Chunks**: ~1,245 chunks
- **Response Time**: ~2-5 seconds
- **Accuracy**: High (sports domain-specific)
- **Embeddings**: 384 dimensions per chunk
- **Storage**: ChromaDB with persistence

### **Scalability**
- **Horizontal**: Can handle multiple concurrent requests
- **Vertical**: Memory scales with document count
- **Caching**: File-based caching for performance

## 🔧 Configuration

All settings in `config.yaml`:
```yaml
# Core settings
embedding_model: "all-MiniLM-L6-v2"
llm_model: "gemini-1.5-flash"
chunk_size: 1000
chunk_overlap: 200

# Performance
request_delay: 1.0
max_retries: 3
content_relevance_threshold: 5.0

# Features
enable_pdf_processing: true
enable_web_scraping: true
enable_caching: true
enable_content_filtering: true
```

## 🎯 Use Cases

This RAG system is perfect for:
- SAI information queries
- Sports policy questions
- Training program details
- Facility information
- Athlete support schemes
- Sports development programs

The system provides accurate, contextual responses based on official SAI documents and maintains source attribution for transparency.