# 🚀 RAG System Deployment Guide

## Quick Start (API Usage)

### 1. **Start the RAG System**
```bash
# Navigate to project directory
cd "c:\Users\kushmunjal\Downloads\coding\SIH2k25\athelete sih interface"

# Start the API server
python main_app.py
```

The server will start on `http://127.0.0.1:5000`

### 2. **Test the System**
```bash
# Run the demo script
python api_demo.py
```

### 3. **Basic API Usage**

#### **Ask a Question (Main Endpoint)**
```bash
curl -X POST http://127.0.0.1:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the Sports Authority of India?"}'
```

#### **Check System Health**
```bash
curl -X GET http://127.0.0.1:5000/health
```

#### **Get System Statistics**
```bash
curl -X GET http://127.0.0.1:5000/stats
```

## 📱 Frontend Integration Examples

### **React.js Integration**
```jsx
import React, { useState } from 'react';
import axios from 'axios';

const RAGChatbot = () => {
    const [question, setQuestion] = useState('');
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);

    const askQuestion = async () => {
        if (!question.trim()) return;
        
        setLoading(true);
        try {
            const result = await axios.post('http://127.0.0.1:5000/ask', {
                query: question
            });
            setResponse(result.data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="rag-chatbot">
            <h2>SAI Sports Assistant</h2>
            <div>
                <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask about SAI, TOPS, training programs..."
                    style={{ width: '400px', padding: '10px' }}
                />
                <button onClick={askQuestion} disabled={loading}>
                    {loading ? 'Thinking...' : 'Ask'}
                </button>
            </div>
            
            {response && (
                <div className="response">
                    <h3>Answer:</h3>
                    <p>{response.response}</p>
                    <small>Sources: {response.sources_used} documents</small>
                </div>
            )}
        </div>
    );
};

export default RAGChatbot;
```

### **HTML/JavaScript Integration**
```html
<!DOCTYPE html>
<html>
<head>
    <title>SAI RAG Chatbot</title>
    <style>
        .chatbot { max-width: 800px; margin: 50px auto; padding: 20px; }
        .input-group { margin: 20px 0; }
        .input-group input { width: 70%; padding: 10px; }
        .input-group button { padding: 10px 20px; margin-left: 10px; }
        .response { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="chatbot">
        <h1>🏆 SAI Sports Assistant</h1>
        
        <div class="input-group">
            <input type="text" id="questionInput" placeholder="Ask about SAI programs, training centers, TOPS scheme...">
            <button onclick="askQuestion()">Ask Question</button>
        </div>
        
        <div id="response" class="response" style="display: none;">
            <h3>Answer:</h3>
            <div id="answerText"></div>
            <div id="sourceInfo"></div>
        </div>
    </div>

    <script>
        async function askQuestion() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            
            if (!question) return;
            
            const responseDiv = document.getElementById('response');
            const answerText = document.getElementById('answerText');
            const sourceInfo = document.getElementById('sourceInfo');
            
            // Show loading
            answerText.innerHTML = '🤔 Thinking...';
            responseDiv.style.display = 'block';
            
            try {
                const response = await fetch('http://127.0.0.1:5000/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: question })
                });
                
                const data = await response.json();
                
                if (data.response) {
                    answerText.innerHTML = data.response;
                    sourceInfo.innerHTML = `<small>📚 Based on ${data.sources_used} source documents</small>`;
                } else {
                    answerText.innerHTML = '❌ Error: ' + (data.error || 'Unknown error');
                    sourceInfo.innerHTML = '';
                }
                
            } catch (error) {
                answerText.innerHTML = '❌ Connection error: ' + error.message;
                sourceInfo.innerHTML = '';
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askQuestion();
            }
        });
    </script>
</body>
</html>
```

## 🔧 Production Deployment

### **1. Environment Variables**
Create `.env` file:
```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key

# Optional
FLASK_PORT=5000
DEBUG=False
```

### **2. Docker Deployment**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main_app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  rag-system:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./vector_store:/app/vector_store
      - ./cache:/app/cache
```

### **3. Production Server (Gunicorn)**
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main_app:app
```

### **4. Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🧪 Testing & Monitoring

### **Health Check Endpoint**
Monitor system health:
```bash
# Check if system is responsive
curl -f http://127.0.0.1:5000/health || echo "System down"
```

### **Performance Testing**
```python
import time
import requests
import concurrent.futures

def test_concurrent_requests():
    questions = [
        "What is SAI?",
        "Tell me about TOPS",
        "SAI training centers",
        "Khelo India scheme"
    ]
    
    def ask_question(q):
        start = time.time()
        response = requests.post(
            'http://127.0.0.1:5000/ask',
            json={'query': q}
        )
        end = time.time()
        return {
            'question': q,
            'status': response.status_code,
            'time': end - start
        }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(ask_question, questions))
    
    for result in results:
        print(f"Q: {result['question'][:30]}... | Status: {result['status']} | Time: {result['time']:.2f}s")

test_concurrent_requests()
```

## 📈 Scaling Considerations

### **Horizontal Scaling**
- Use load balancer (Nginx/HAProxy)
- Multiple API instances
- Shared vector store

### **Performance Optimization**
- Redis caching for frequent queries
- Background pipeline updates
- Async processing

### **Monitoring**
- Response time metrics
- Error rate tracking
- Resource usage monitoring
- Query analytics

## 🔒 Security Considerations

### **API Security**
```python
# Add to main_app.py for production
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/ask', methods=['POST'])
@limiter.limit("10 per minute")
def ask_question():
    # existing code
```

### **CORS Configuration**
```python
from flask_cors import CORS

# Allow specific origins
CORS(app, origins=['http://your-frontend-domain.com'])
```

## 📞 API Integration Patterns

### **Webhook Integration**
```python
# Integrate with external systems
@app.route('/webhook/answer', methods=['POST'])
def webhook_handler():
    data = request.json
    question = data.get('question')
    callback_url = data.get('callback_url')
    
    # Process async and send result to callback
    result = rag_system.query(question)
    
    requests.post(callback_url, json=result)
    return {'status': 'processing'}
```

### **Batch Processing**
```python
@app.route('/batch/ask', methods=['POST'])
def batch_questions():
    questions = request.json.get('questions', [])
    results = []
    
    for q in questions:
        result = rag_system.query(q)
        results.append(result)
    
    return {'results': results}
```

This deployment guide provides everything needed to integrate your RAG system into production applications!