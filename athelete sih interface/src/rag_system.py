import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
import asyncio

load_dotenv("./config/.env")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document

from .config_manager import ConfigManager
from .data_pipeline import PipelineManager

class LangChainRAGSystem:
    
    def __init__(self, config_path="./config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.pipeline_manager = PipelineManager(config_path)
        
        self.persist_directory = self.config.vector_store_path
        self.vectorstore = None
        self.retriever = None
        self.chain = None
        
        self._setup_embeddings()
        self._setup_llm()
        self._setup_text_splitter()
        
    def _setup_embeddings(self):
        print("🔧 Setting up embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ Embeddings ready")
    
    def _setup_llm(self):
        print("🤖 Setting up Gemini LLM...")
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("Please set your GEMINI_API_KEY in the .env file")
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            google_api_key=api_key
        )
        print("✅ Gemini LLM ready")
    
    def _setup_text_splitter(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def load_and_index_documents(self, force_reload=False):
        print("📚 Loading and indexing documents...")
        
        if os.path.exists(self.persist_directory) and not force_reload:
            print("📂 Loading existing vector store...")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            print("🔄 Creating new vector store...")
            
            # Use the new data pipeline to get documents
            documents = await self.pipeline_manager.run_pipeline(force_refresh=force_reload)
            
            if not documents:
                raise ValueError("No documents found to index")
            
            # Convert to LangChain documents
            langchain_docs = []
            for doc in documents:
                langchain_doc = Document(
                    page_content=doc['text'],
                    metadata={
                        'title': doc['title'],
                        'source': doc['source'],
                        'category': doc['category'],
                        'document_id': doc.get('document_id', ''),
                        'data_source': doc.get('data_source', 'unknown'),
                        'chunk_id': doc.get('chunk_id', 0)
                    }
                )
                langchain_docs.append(langchain_doc)
            
            print(f"📄 Processing {len(langchain_docs)} document chunks...")
            
            # Split documents further if needed
            split_docs = self.text_splitter.split_documents(langchain_docs)
            print(f"📑 Created {len(split_docs)} text chunks")
            
            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Persist the vector store
            self.vectorstore.persist()
            print("💾 Vector store saved to disk")
        
        # Setup retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.config.similarity_top_k if hasattr(self.config, 'similarity_top_k') else 5}
        )
        
        print("✅ Document indexing complete")
    
    def setup_rag_chain(self):
        print("⛓️ Setting up RAG chain...")
        
        template = """You are an expert sports assistant with access to official Sports Authority of India (SAI) documents.

Based on the following context from SAI documents, answer the user's question accurately and professionally.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Answer based ONLY on the provided SAI documents
- Be specific and cite relevant information when possible
- If the documents don't contain the exact answer, explain what related information is available
- Keep responses professional and informative
- For sports standards/requirements, provide specific details when available from the documents
- Structure your response clearly with relevant details

ANSWER:"""

        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join([
                f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                f"Title: {doc.metadata.get('title', 'Unknown')}\n"
                f"Content: {doc.page_content}"
                for doc in docs
            ])
        
        self.chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("✅ RAG chain ready")
    
    def query(self, question: str) -> Dict[str, Any]:
        if not self.chain:
            raise ValueError("RAG chain not setup. Call setup_rag_chain() first.")
        
        print(f"🔍 Processing query: {question}")
        
        relevant_docs = self.retriever.invoke(question)
        response = self.chain.invoke(question)
        
        result = {
            'question': question,
            'answer': response,
            'sources': [
                {
                    'title': doc.metadata.get('title', 'Unknown'),
                    'source': doc.metadata.get('source', 'Unknown'),
                    'category': doc.metadata.get('category', 'Unknown')
                }
                for doc in relevant_docs
            ],
            'num_sources': len(relevant_docs)
        }
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.vectorstore:
            return {"error": "Vector store not initialized"}
        
        collection = self.vectorstore._collection
        count = collection.count()
        
        pipeline_stats = self.pipeline_manager.get_pipeline_status()
        
        return {
            'total_chunks': count,
            'embedding_model': self.config.embedding_model,
            'llm_model': self.config.llm_model,
            'vector_store': "ChromaDB",
            'persist_directory': self.persist_directory,
            'pipeline_stats': pipeline_stats
        }

async def initialize_rag_system(config_path="./config.yaml", force_reload=False):
    print("🚀 Initializing LangChain RAG System")
    print("=" * 50)
    
    try:
        rag_system = LangChainRAGSystem(config_path)
        await rag_system.load_and_index_documents(force_reload=force_reload)
        rag_system.setup_rag_chain()
        
        print("🎉 RAG System initialized successfully!")
        return rag_system
        
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        raise

def demo_rag_system():
    async def async_demo():
        try:
            rag = await initialize_rag_system()
            
            stats = rag.get_stats()
            print(f"\n📊 System Stats:")
            for key, value in stats.items():
                if key != 'pipeline_stats':
                    print(f"  {key}: {value}")
            
            demo_questions = [
                "what are the 4 levels of sports promotion schemes?",
                "what is the success of The TOPS sponsored athletes gained relative success at the 2016 Rio Olympics and the 2018 Commonwealth Games",
                "what cources are provided in lncpe trivandrum"
            ]
            
            print(f"\n🧪 Demo Questions:")
            for i, question in enumerate(demo_questions, 1):
                print(f"\n{'='*60}")
                print(f"Question {i}: {question}")
                print('='*60)
                
                result = rag.query(question)
                
                print(f"Answer: {result['answer']}")
                print(f"\nSources used: {result['num_sources']}")
                for j, source in enumerate(result['sources'], 1):
                    print(f"  {j}. {source['title']} (from {source['source']})")
            
            return rag
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            return None
    
    return asyncio.run(async_demo())

if __name__ == "__main__":
    demo_rag_system()