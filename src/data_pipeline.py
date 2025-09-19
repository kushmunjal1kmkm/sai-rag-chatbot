import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from .config_manager import ConfigManager
from .pdf_processor import EnhancedPDFProcessor, create_knowledge_base_from_pdfs
from .web_scraper import WebScraper

class DataPipeline:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config()
        self.logger = logging.getLogger(__name__)
        
        self.pdf_processor = EnhancedPDFProcessor(config_manager)
        self.web_scraper = None
        
        self.processed_documents = []
        self.pipeline_stats = {
            'pdf_documents': 0,
            'web_documents': 0,
            'total_documents': 0,
            'processing_time': 0,
            'last_run': None
        }
    
    async def run_full_pipeline(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Run the complete data processing pipeline"""
        start_time = datetime.now()
        self.logger.info("🚀 Starting full data pipeline...")
        
        all_documents = []
        
        # Process PDFs
        if self.config.enable_pdf_processing:
            self.logger.info("📄 Processing PDF documents...")
            pdf_documents = await self._process_pdfs(force_refresh)
            all_documents.extend(pdf_documents)
            self.pipeline_stats['pdf_documents'] = len(pdf_documents)
            self.logger.info(f"✅ Processed {len(pdf_documents)} PDF documents")
        
        # Process web content
        if self.config.enable_web_scraping:
            self.logger.info("🌐 Processing web content...")
            web_documents = await self._process_web_content(force_refresh)
            all_documents.extend(web_documents)
            self.pipeline_stats['web_documents'] = len(web_documents)
            self.logger.info(f"✅ Processed {len(web_documents)} web documents")
        
        # Deduplicate and clean
        all_documents = self._deduplicate_documents(all_documents)
        all_documents = self._clean_and_validate_documents(all_documents)
        
        # Update stats
        self.pipeline_stats['total_documents'] = len(all_documents)
        self.pipeline_stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        self.pipeline_stats['last_run'] = datetime.now().isoformat()
        
        self.processed_documents = all_documents
        
        self.logger.info(f"🎉 Pipeline completed! Total documents: {len(all_documents)}")
        self._log_pipeline_summary()
        
        return all_documents
    
    async def _process_pdfs(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Process PDF documents"""
        try:
            # Use the existing function but wrap it for async compatibility
            pdf_documents = create_knowledge_base_from_pdfs(self.config.pdf_data_path)
            
            # Add pipeline metadata
            for doc in pdf_documents:
                doc['processed_by'] = 'data_pipeline'
                doc['processed_at'] = datetime.now().isoformat()
                doc['data_source'] = 'pdf'
            
            return pdf_documents
            
        except Exception as e:
            self.logger.error(f"Error processing PDFs: {e}")
            return []
    
    async def _process_web_content(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Process web content from URLs"""
        try:
            async with WebScraper(ConfigManager()) as scraper:
                scraped_content = await scraper.scrape_urls_from_file(self.config.url_file_path)
                web_documents = scraper.convert_to_documents(scraped_content)
                
                # Add pipeline metadata
                for doc in web_documents:
                    doc['processed_by'] = 'data_pipeline'
                    doc['processed_at'] = datetime.now().isoformat()
                    doc['data_source'] = 'web'
                
                return web_documents
                
        except Exception as e:
            self.logger.error(f"Error processing web content: {e}")
            return []
    
    def _deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on content similarity"""
        seen_hashes = set()
        unique_documents = []
        
        for doc in documents:
            # Create a simple hash based on content
            content_hash = hash(doc['text'][:500])  # Use first 500 chars for hash
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_documents.append(doc)
            else:
                self.logger.debug(f"Duplicate document skipped: {doc.get('title', 'Unknown')}")
        
        removed_count = len(documents) - len(unique_documents)
        if removed_count > 0:
            self.logger.info(f"🔄 Removed {removed_count} duplicate documents")
        
        return unique_documents
    
    def _clean_and_validate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate document content"""
        valid_documents = []
        
        for doc in documents:
            # Skip documents with insufficient content
            if len(doc['text'].strip()) < 50:
                self.logger.debug(f"Skipping short document: {doc.get('title', 'Unknown')}")
                continue
            
            # Clean text content
            doc['text'] = self._clean_text_content(doc['text'])
            
            # Ensure required fields
            doc.setdefault('title', 'Unknown Document')
            doc.setdefault('source', 'Unknown Source')
            doc.setdefault('category', 'general')
            
            # Add document ID
            doc['document_id'] = self._generate_document_id(doc)
            
            valid_documents.append(doc)
        
        return valid_documents
    
    def _clean_text_content(self, text: str) -> str:
        """Clean and normalize text content"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
        
        # Fix spacing issues
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _generate_document_id(self, doc: Dict[str, Any]) -> str:
        """Generate unique document ID"""
        import hashlib
        
        id_string = f"{doc['title']}_{doc['source']}_{doc.get('chunk_id', 0)}"
        return hashlib.md5(id_string.encode()).hexdigest()[:12]
    
    def _log_pipeline_summary(self):
        """Log summary of pipeline execution"""
        self.logger.info("📊 Pipeline Summary:")
        self.logger.info(f"  PDF Documents: {self.pipeline_stats['pdf_documents']}")
        self.logger.info(f"  Web Documents: {self.pipeline_stats['web_documents']}")
        self.logger.info(f"  Total Documents: {self.pipeline_stats['total_documents']}")
        self.logger.info(f"  Processing Time: {self.pipeline_stats['processing_time']:.2f}s")
        
        # Log category breakdown
        categories = {}
        for doc in self.processed_documents:
            cat = doc.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        self.logger.info("  Document Categories:")
        for category, count in sorted(categories.items()):
            self.logger.info(f"    {category}: {count}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return self.pipeline_stats.copy()
    
    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get documents filtered by category"""
        return [doc for doc in self.processed_documents if doc.get('category') == category]
    
    def get_documents_by_source(self, source_type: str) -> List[Dict[str, Any]]:
        """Get documents filtered by source type (pdf/web)"""
        return [doc for doc in self.processed_documents if doc.get('data_source') == source_type]
    
    async def incremental_update(self) -> List[Dict[str, Any]]:
        """Run incremental update for new/changed content"""
        self.logger.info("🔄 Running incremental update...")
        
        # For now, run full pipeline - can be optimized later
        # to only process changed files
        return await self.run_full_pipeline(force_refresh=False)

class PipelineManager:
    """Manager class for handling multiple pipeline operations"""
    
    def __init__(self, config_path: str = "./config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.pipeline = DataPipeline(self.config_manager)
        self.logger = logging.getLogger(__name__)
    
    async def initialize_pipeline(self) -> bool:
        """Initialize the data pipeline"""
        try:
            # Validate configuration
            errors = self.config_manager.validate_config()
            if errors:
                for error in errors:
                    self.logger.error(f"Configuration error: {error}")
                return False
            
            self.logger.info("✅ Pipeline configuration validated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pipeline: {e}")
            return False
    
    async def run_pipeline(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Run the complete data pipeline"""
        if not await self.initialize_pipeline():
            return []
        
        return await self.pipeline.run_full_pipeline(force_refresh)
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            'config': {
                'pdf_enabled': self.config_manager.get_config().enable_pdf_processing,
                'web_enabled': self.config_manager.get_config().enable_web_scraping,
                'caching_enabled': self.config_manager.get_config().enable_caching
            },
            'stats': self.pipeline.get_pipeline_stats(),
            'document_count': len(self.pipeline.processed_documents)
        }

async def main():
    """Main function to test the pipeline"""
    logging.basicConfig(level=logging.INFO)
    
    manager = PipelineManager()
    
    print("🚀 Testing Data Pipeline...")
    documents = await manager.run_pipeline()
    
    print(f"\n📊 Results:")
    print(f"Total documents: {len(documents)}")
    
    status = manager.get_pipeline_status()
    print(f"Pipeline status: {status}")
    
    if documents:
        print(f"\n📋 Sample document:")
        sample = documents[0]
        print(f"Title: {sample['title']}")
        print(f"Category: {sample['category']}")
        print(f"Source: {sample['source']}")
        print(f"Data source: {sample['data_source']}")
        print(f"Content preview: {sample['text'][:200]}...")

if __name__ == "__main__":
    asyncio.run(main())