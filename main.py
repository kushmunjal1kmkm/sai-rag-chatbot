from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
import json
import asyncio

# Load environment variables
load_dotenv("./config/.env")

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['*'])  # Allow all origins for GitHub Pages integration

# Disable Flask auto-reload to prevent venv file watching issues
app.config['DEBUG'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True

rag_system = None

@app.route('/')
def index():
    """API Status and Documentation"""
    return jsonify({
        "name": "SAI Sports Assistant API",
        "version": "1.0.0",
        "description": "AI-powered API for Sports Authority of India information",
        "status": "running",
        "endpoints": {
            "POST /chat": "Send chat messages to the AI assistant",
            "GET /health": "System health check",
            "GET /stats": "System statistics",
            "GET /pipeline/status": "Data pipeline status",
            "POST /pipeline/refresh": "Refresh data pipeline"
        },
        "example_usage": {
            "url": "POST /chat",
            "body": {
                "message": "What is the Sports Authority of India?",
                "conversation_id": "optional_id"
            }
        }
    })

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

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for frontend integration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        print(f"📝 Query: {message}")
        
        # Initialize RAG system if needed
        if rag_system is None:
            initialize_rag()
        
        if rag_system != "fallback":
            try:
                result = rag_system.query(message)
                
                response_data = {
                    'success': True,
                    'message': message,
                    'response': result['answer'],
                    'sources_used': result['num_sources'],
                    'sources': result['sources'],
                    'conversation_id': conversation_id,
                    'system': 'enhanced_rag_pipeline',
                    'model': 'gemini-1.5-flash',
                    'vector_store': 'chromadb'
                }
                
                return jsonify(response_data)
                
            except Exception as e:
                print(f"❌ Enhanced RAG error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'RAG system error',
                    'message': str(e)
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'RAG system not available',
                'message': 'Please check system configuration'
            }), 503
        
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/ask', methods=['POST'])
def ask_question_legacy():
    """Legacy endpoint for backward compatibility"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Redirect to new chat endpoint format
        chat_data = {'message': query}
        return chat()
        
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

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
    print("🚀 Starting SAI Sports Assistant API")
    print("=" * 50)
    print("🔧 Features:")
    print("  • Enhanced RAG system with LangChain")
    print("  • Google Gemini AI integration") 
    print("  • ChromaDB vector storage")
    print("  • CORS enabled for frontend integration")
    print("  • Production-ready API endpoints")
    print()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        print("✅ Gemini API key configured")
    else:
        print("⚠️  Gemini API key not configured - set GEMINI_API_KEY environment variable")
    
    # Get configuration from environment
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Force production mode to prevent file watching issues
    debug_mode = False
    
    print(f"🌐 API Server starting on {host}:{port}")
    print("\n🔗 API Endpoints:")
    print("  GET  / - API documentation and status")
    print("  POST /chat - Main chat endpoint for frontend")
    print("  POST /ask - Legacy endpoint (redirects to /chat)")
    print("  GET  /health - System health check")
    print("  GET  /stats - System statistics")
    print("  GET  /pipeline/status - Pipeline status")
    print("  POST /pipeline/refresh - Refresh data pipeline")
    print()
    print("🔧 Debug mode: DISABLED (prevents file watching issues)")
    print("🌍 CORS: ENABLED for all origins")
    print()
    
    # Run the application
    app.run(
        debug=False,         # Always disable debug in production
        host=host,
        port=port,
        use_reloader=False,  # Disable auto-reloader to prevent venv watching
        threaded=True        # Enable threading for better performance
    )