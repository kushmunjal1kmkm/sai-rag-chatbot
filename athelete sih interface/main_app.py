from flask import Flask, request, jsonify
import os
import sys
from dotenv import load_dotenv
import json
import asyncio

load_dotenv("./config/.env")

sys.path.append(os.path.dirname(__file__))

app = Flask(__name__)

rag_system = None

@app.route('/')
def index():
    """Simple index page with examples"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SAI RAG System - Sports Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .header { background: #1976d2; color: white; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
            .example { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .example a { color: #1976d2; text-decoration: none; }
            .example a:hover { text-decoration: underline; }
            h1, h2 { color: #1976d2; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 SAI Sports Assistant</h1>
            <p>Ask questions about Sports Authority of India, TOPS, training programs, and more!</p>
        </div>
        
        <h2>📋 Example Questions (Click to try):</h2>
        
        <div class="example">
            <strong>About SAI:</strong><br>
            <a href="/ask/What is the Sports Authority of India">What is the Sports Authority of India?</a>
        </div>
        
        <div class="example">
            <strong>Sports Promotion:</strong><br>
            <a href="/ask/what are the 4 levels of sports promotion schemes">What are the 4 levels of sports promotion schemes?</a>
        </div>
        
        <div class="example">
            <strong>TOPS Program:</strong><br>
            <a href="/ask/What is the TOPS scheme">What is the TOPS scheme?</a>
        </div>
        
        <div class="example">
            <strong>Training Centers:</strong><br>
            <a href="/ask/How many SAI training centers are there in India">How many SAI training centers are there in India?</a>
        </div>
        
        <div class="example">
            <strong>Khelo India:</strong><br>
            <a href="/ask/Tell me about Khelo India scheme">Tell me about Khelo India scheme?</a>
        </div>
        
        <div class="example">
            <strong>Facilities:</strong><br>
            <a href="/ask/What facilities does SAI provide to athletes">What facilities does SAI provide to athletes?</a>
        </div>
        
        <h2>💡 How to Use:</h2>
        <p>Simply add your question after <code>/ask/</code> in the URL:</p>
        <p><strong>Format:</strong> <code>http://127.0.0.1:5000/ask/your question here</code></p>
        
        <h2>🔗 API Endpoints:</h2>
        <ul>
            <li><a href="/health">System Health Check</a></li>
            <li><a href="/stats">System Statistics</a></li>
            <li><a href="/pipeline/status">Pipeline Status</a></li>
        </ul>
    </body>
    </html>
    """

def initialize_rag():
    global rag_system
    
    if rag_system is None:
        try:
            from src.rag_system import initialize_rag_system
            print("🔧 Initializing Enhanced RAG system with data pipeline...")
            
            async def async_init():
                return await initialize_rag_system()
            
            rag_system = asyncio.run(async_init())
            print("✅ Enhanced RAG system ready!")
        except Exception as e:
            print(f"❌ Failed to initialize RAG system: {e}")
            rag_system = "fallback"

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        print(f"📝 Query: {query}")
        
        if rag_system is None:
            initialize_rag()
        
        if rag_system != "fallback":
            try:
                result = rag_system.query(query)
                
                response_data = {
                    'query': query,
                    'response': result['answer'],
                    'sources_used': result['num_sources'],
                    'sources': result['sources'],
                    'system': 'enhanced_rag_pipeline',
                    'model': 'gemini-1.5-flash',
                    'vector_store': 'chromadb'
                }
                
                return jsonify(response_data)
                
            except Exception as e:
                print(f"❌ Enhanced RAG error: {e}")
                return jsonify({
                    'error': 'RAG system error',
                    'message': str(e)
                }), 500
        else:
            return jsonify({
                'error': 'RAG system not available',
                'message': 'Please check system configuration'
            }), 503
        
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/ask/<path:question>', methods=['GET'])
def ask_question_get(question):
    """GET endpoint for browser testing - URL format: /ask/your question here"""
    try:
        query = question.strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        print(f"📝 Query (GET): {query}")
        
        if rag_system is None:
            initialize_rag()
        
        if rag_system != "fallback":
            try:
                result = rag_system.query(query)
                
                # Format for browser display
                response_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>SAI RAG System Response</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        .question {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                        .answer {{ background: #f3e5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                        .sources {{ background: #fff3e0; padding: 15px; border-radius: 5px; }}
                        .metadata {{ color: #666; font-size: 0.9em; margin-top: 15px; }}
                        h1, h2 {{ color: #1976d2; }}
                    </style>
                </head>
                <body>
                    <h1>🏆 SAI Sports Assistant</h1>
                    
                    <div class="question">
                        <h2>❓ Question:</h2>
                        <p><strong>{result['question']}</strong></p>
                    </div>
                    
                    <div class="answer">
                        <h2>💬 Answer:</h2>
                        <p>{result['answer']}</p>
                    </div>
                    
                    <div class="sources">
                        <h2>📚 Sources ({result['num_sources']} documents):</h2>
                        <ul>
                """
                
                for i, source in enumerate(result['sources'], 1):
                    response_html += f"<li><strong>{source['title']}</strong><br><small>From: {source['source']}</small></li>"
                
                response_html += """
                        </ul>
                    </div>
                    
                    <div class="metadata">
                        <p><strong>System:</strong> Enhanced RAG Pipeline | <strong>Model:</strong> Gemini 1.5 Flash | <strong>Vector Store:</strong> ChromaDB</p>
                    </div>
                    
                    <hr>
                    <p><a href="/ask/What is the Sports Authority of India">🔗 Try another question</a></p>
                </body>
                </html>
                """
                
                return response_html
                
            except Exception as e:
                return f"<html><body><h1>❌ Error</h1><p>{str(e)}</p></body></html>", 500
        else:
            return "<html><body><h1>❌ RAG System Not Available</h1><p>Please check system configuration</p></body></html>", 503
        
    except Exception as e:
        print(f"❌ Error processing GET request: {e}")
        return f"<html><body><h1>❌ Error</h1><p>{str(e)}</p></body></html>", 500

@app.route('/health', methods=['GET'])
def health_check():
    if rag_system is None:
        initialize_rag()
    
    system_info = {
        'status': 'healthy' if rag_system != "fallback" else 'degraded',
        'rag_system': 'enhanced_pipeline' if rag_system != "fallback" else 'fallback',
        'gemini_available': True
    }
    
    if rag_system != "fallback":
        try:
            stats = rag_system.get_stats()
            system_info.update(stats)
        except:
            system_info['rag_system'] = 'error'
    
    return jsonify(system_info)

@app.route('/stats', methods=['GET'])
def get_stats():
    if rag_system is None:
        initialize_rag()
    
    if rag_system != "fallback":
        try:
            return jsonify(rag_system.get_stats())
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'system': 'fallback',
        'message': 'Enhanced RAG system not available'
    })

@app.route('/pipeline/refresh', methods=['POST'])
def refresh_pipeline():
    """Refresh the data pipeline with latest content"""
    global rag_system
    
    try:
        print("🔄 Refreshing data pipeline...")
        
        # Reinitialize with force refresh
        async def async_refresh():
            from src.rag_system import initialize_rag_system
            return await initialize_rag_system(force_reload=True)
        
        rag_system = asyncio.run(async_refresh())
        
        return jsonify({
            'status': 'success',
            'message': 'Data pipeline refreshed successfully',
            'stats': rag_system.get_stats()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Pipeline refresh failed: {str(e)}'
        }), 500

@app.route('/pipeline/status', methods=['GET'])
def pipeline_status():
    """Get detailed pipeline status"""
    if rag_system is None:
        initialize_rag()
    
    if rag_system != "fallback":
        try:
            stats = rag_system.get_stats()
            pipeline_stats = stats.get('pipeline_stats', {})
            
            return jsonify({
                'pipeline_active': True,
                'total_documents': stats.get('total_chunks', 0),
                'vector_store': stats.get('vector_store', 'unknown'),
                'embedding_model': stats.get('embedding_model', 'unknown'),
                'llm_model': stats.get('llm_model', 'unknown'),
                'pipeline_details': pipeline_stats
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'pipeline_active': False,
        'message': 'Enhanced pipeline not available'
    })

@app.route('/reload', methods=['POST'])
def reload_system():
    global rag_system
    
    try:
        print("🔄 Reloading RAG system...")
        rag_system = None
        initialize_rag()
        
        return jsonify({
            'status': 'success',
            'message': 'RAG system reloaded',
            'system': 'langchain' if rag_system != "fallback" else 'fallback'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Reload failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Enhanced Sports RAG Chatbot API")
    print("=" * 60)
    print("🔧 Features:")
    print("  • Enhanced data pipeline with PDF + Web scraping")
    print("  • LangChain RAG with advanced retrieval")
    print("  • Google Gemini AI integration") 
    print("  • ChromaDB vector storage with persistence")
    print("  • Intelligent caching and deduplication")
    print("  • Production-ready Docker deployment")
    print()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        print("✅ Gemini API key configured")
    else:
        print("⚠️  Gemini API key not configured - set GEMINI_API_KEY environment variable")
    
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🌐 Server starting on {host}:{port}")
    print("\n🔗 Endpoints:")
    print("  GET  / - Homepage with examples")
    print("  GET  /ask/<question> - Ask questions via URL")
    print("  POST /ask - Ask sports questions with enhanced RAG")
    print("  GET  /health - System health and status")
    print("  GET  /stats - Detailed system statistics")
    print("  POST /pipeline/refresh - Refresh data pipeline")
    print("  GET  /pipeline/status - Pipeline status and metrics")
    
    app.run(debug=debug_mode, host=host, port=port)