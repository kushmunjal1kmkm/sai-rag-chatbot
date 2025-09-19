# SAI RAG Chatbot - Production Ready

Production-ready RAG (Retrieval Augmented Generation) chatbot for Sports Authority of India (SAI) queries. Optimized for cloud deployment with Docker containerization and Render platform support.

## 🏗️ Architecture

### Core Components
- **data_pipeline.py** - Unified data processing pipeline
- **web_scraper.py** - Async web scraper with hyperlink following  
- **pdf_processor.py** - Enhanced PDF processing with caching
- **rag_system.py** - LangChain RAG with ChromaDB vector store
- **main_app.py** - Flask API server with pipeline management
- **config_manager.py** - Configuration management system

### Configuration
- **config.yaml** - Main configuration file
- **.env** - Environment variables (API keys)
- **data/urls.txt** - URL targets for web scraping

## 🚀 Features

### Data Pipeline
- **Multi-source ingestion**: PDF documents + web content
- **Intelligent deduplication**: Content-based duplicate detection
- **Caching system**: File-based caching for performance
- **Incremental updates**: Detect and process only changed content
- **Async processing**: High-performance concurrent operations

### Web Scraping
- **SAI website integration**: Comprehensive SAI content extraction
- **Hyperlink following**: Automatic discovery of linked content
- **Rate limiting**: Respectful scraping with configurable delays
- **Content cleaning**: Intelligent text extraction and normalization
- **Multi-domain support**: Khelo India, Fit India, SAI sites

### Enhanced RAG
- **Advanced retrieval**: Semantic search with ChromaDB
- **Persistent storage**: Vector embeddings saved for reuse
- **Multi-model support**: Configurable embedding models
- **Source attribution**: Detailed source tracking for responses
- **Context preservation**: Maintaining document relationships

## � Quick Start

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export GEMINI_API_KEY="your_gemini_api_key_here"

# 3. Run the application
python main_app.py
```

### Docker Deployment (Render)
```bash
# Build Docker image
docker build -t sai-rag-chatbot .

# Run locally
docker run -p 5000:5000 -e GEMINI_API_KEY="your_key" sai-rag-chatbot

# Deploy to Render - automatic via GitHub integration
```

## � API Endpoints

### Production Endpoints
- `GET /` - Homepage with sample questions
- `GET /ask/<question>` - Direct URL queries (browser-friendly)
- `POST /ask` - JSON API for applications
- `GET /health` - Health check for monitoring
- `GET /stats` - System statistics

### Example Usage

**Browser Access:**
```
https://your-app.onrender.com/ask/What is Sports Authority of India
```

**API Integration:**
```bash
curl -X POST https://your-app.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are TOPS training programs?"}'
```

**JavaScript Integration:**
```javascript
const response = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: 'SAI training centers'})
});
const result = await response.json();
```

## 📊 Performance & Features

### RAG System Features
- **Advanced Retrieval**: Semantic search with 384-dimensional embeddings
- **Smart Chunking**: 1000-character chunks with 200-character overlap
- **Multi-source Data**: PDF documents + SAI website content
- **Response Quality**: Context-aware answers with source attribution
- **Caching**: Intelligent caching for improved response times

### Performance Metrics
- **Response Time**: 2-5 seconds typical
- **Concurrent Users**: Production-ready scaling
- **Document Corpus**: 500+ SAI documents indexed
- **Vector Chunks**: 1000+ semantic pieces
- **Uptime**: Health monitoring with automatic restarts

### Use Cases
Perfect for queries about:
- SAI training programs and facilities
- Sports policies and regulations  
- Equipment and infrastructure details
- Athlete support schemes
- TOPS (Target Olympic Podium Scheme)
- Khelo India initiatives
- Fit India programs

## � Development

### Local Development Setup
```bash
# Clone and setup
git clone <repository>
cd "athelete sih interface"

# Install dependencies
pip install -r requirements.txt

# Set environment
export GEMINI_API_KEY="your_api_key"

# Run development server
python main_app.py
```

### Project Structure
```
├── main_app.py              # Flask API server (entry point)
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── render.yaml             # Render deployment config
├── .dockerignore           # Docker build exclusions
├── README.md               # This file
│
├── src/                    # Core source code
│   ├── __init__.py         # Package initialization  
│   ├── rag_system.py       # RAG implementation with LangChain
│   ├── data_pipeline.py    # Data processing pipeline
│   ├── pdf_processor.py    # PDF document processing
│   ├── web_scraper.py      # Web content extraction
│   └── config_manager.py   # Configuration management
│
├── config/                 # Configuration files
│   ├── .env               # Environment variables (API keys)
│   └── config.yaml        # System configuration
│
├── docs/                   # Documentation
│   ├── RAG_SYSTEM_FLOW.md  # System architecture guide
│   └── DEPLOYMENT_GUIDE.md # Deployment instructions
│
├── data/                   # Source documents
│   └── urls.txt           # Web scraping targets
│
├── cache/                  # Processing cache
│   ├── pdf_content/       # Cached PDF extractions
│   └── web_content/       # Cached web scraping
│
├── vector_store/          # Vector embeddings
└── chroma_db/            # ChromaDB persistence
```

## 🎯 Smart India Hackathon 2025

**Problem Statement**: Sports Domain Information System  
**Solution**: AI-powered RAG chatbot for comprehensive SAI information access

**Key Innovation**:
- Unified access to scattered sports information
- Intelligent question answering with citations
- Production-ready deployment architecture
- Scalable microservices design

Built with ❤️ for SIH 2025 - Transforming sports information accessibility through AI.

## � Docker Deployment

### Docker Configuration

**Dockerfile Features:**
- Python 3.11 slim base image
- Multi-stage optimization
- Health checks included
- Production-ready logging
- Optimized for Render platform

**Build & Deploy:**
```bash
# Local testing
docker build -t sai-rag-chatbot .
docker run -p 5000:5000 -e GEMINI_API_KEY="your_key" sai-rag-chatbot

# Health check
curl http://localhost:5000/health
```

### Render Deployment

**render.yaml** configured for:
- Automatic Docker builds
- Environment variable management
- Health monitoring
- Auto-scaling ready

**Required Environment Variables:**
- `GEMINI_API_KEY` - Your Google Gemini API key

### System Architecture

```
User Request → Load Balancer → Flask API → RAG System
                                     ↓
                              Vector Search (ChromaDB)
                                     ↓
                              Gemini AI Generation
                                     ↓
                              Formatted Response
```

**Technical Stack:**
- **Backend**: Flask (Python 3.11)
- **AI/ML**: LangChain + Google Gemini 1.5 Flash
- **Vector DB**: ChromaDB with HuggingFace embeddings
- **Deployment**: Docker + Render
- **Monitoring**: Built-in health checks

