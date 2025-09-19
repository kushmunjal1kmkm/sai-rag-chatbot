import os
import sys
import re
import hashlib
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from .config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import PyPDF2
    PDF_AVAILABLE = True
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    PDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

if not (PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE or PYMUPDF_AVAILABLE):
    logger.warning("No PDF library found. Install one of: PyPDF2, pdfplumber, or PyMuPDF")
    PDF_AVAILABLE = False

class EnhancedPDFProcessor:
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config()
        self.data_folder = self.config.pdf_data_path
        self.cache_dir = Path(self.config.cache_path) / "pdf_content"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_cache = {}
        
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file to detect changes"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_cache_path(self, pdf_path: str) -> Path:
        filename = Path(pdf_path).stem
        return self.cache_dir / f"{filename}_processed.json"
    
    def _load_cached_content(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        if not self.config.enable_caching:
            return None
            
        cache_path = self._get_cache_path(pdf_path)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            current_hash = self._get_file_hash(pdf_path)
            if cached_data.get('file_hash') == current_hash:
                logger.info(f"Using cached content for: {pdf_path}")
                return cached_data
        except Exception as e:
            logger.warning(f"Failed to load cache for {pdf_path}: {e}")
        
        return None
    
    def _save_to_cache(self, pdf_path: str, processed_data: Dict[str, Any]):
        if not self.config.enable_caching:
            return
            
        cache_path = self._get_cache_path(pdf_path)
        try:
            processed_data['file_hash'] = self._get_file_hash(pdf_path)
            processed_data['processed_at'] = datetime.now().isoformat()
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to cache content for {pdf_path}: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        if pdf_path in self.pdf_cache:
            return self.pdf_cache[pdf_path]
            
        try:
            text_content = ""
            extraction_methods = []
            
            # Method 1: PyMuPDF (most robust)
            if 'PYMUPDF_AVAILABLE' in globals() and PYMUPDF_AVAILABLE:
                extraction_methods.append(self._extract_with_pymupdf)
            
            # Method 2: pdfplumber (good for tables)
            if 'PDFPLUMBER_AVAILABLE' in globals() and PDFPLUMBER_AVAILABLE:
                extraction_methods.append(self._extract_with_pdfplumber)
                
            # Method 3: PyPDF2 (fallback)
            if 'PYPDF2_AVAILABLE' in globals() and PYPDF2_AVAILABLE:
                extraction_methods.append(self._extract_with_pypdf2)
            
            # Try each extraction method
            for method in extraction_methods:
                try:
                    text_content = method(pdf_path)
                    if text_content and len(text_content.strip()) > 50:
                        logger.info(f"Successfully extracted text using {method.__name__}")
                        break
                except Exception as e:
                    logger.warning(f"{method.__name__} failed for {pdf_path}: {e}")
                    continue
            
            # If all methods fail, try OCR as last resort
            if not text_content or len(text_content.strip()) < 50:
                if OCR_AVAILABLE:
                    logger.info(f"Attempting OCR extraction for {pdf_path}")
                    text_content = self._extract_with_ocr(pdf_path)
                else:
                    logger.warning(f"No extraction method worked for {pdf_path}. Consider installing OCR dependencies.")
                    return f"Error: Could not extract text from {pdf_path}"
            
            # Clean and normalize text
            text_content = self._clean_text(text_content)
            
            # Cache the result
            self.pdf_cache[pdf_path] = text_content
            
            logger.info(f"Successfully extracted {len(text_content)} characters from {pdf_path}")
            return text_content
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return f"Error reading PDF: {pdf_path}"
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (fitz)"""
        import fitz
        text_content = ""
        
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Also extract table content
            tables = page.find_tables()
            for table in tables:
                try:
                    table_data = table.extract()
                    for row in table_data:
                        if row:
                            table_text = " | ".join([str(cell) if cell else "" for cell in row])
                            page_text += f"\nTable: {table_text}\n"
                except:
                    pass
            
            if page_text.strip():
                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        doc.close()
        return text_content
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (good for tables)"""
        import pdfplumber
        text_content = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        for row in table:
                            if row:
                                table_text = " | ".join([str(cell) if cell else "" for cell in row])
                                page_text += f"\nTable: {table_text}\n"
                
                if page_text.strip():
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        return text_content
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        import PyPDF2
        text_content = ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        return text_content
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR for scanned PDFs"""
        import fitz
        import pytesseract
        from PIL import Image
        import io
        
        text_content = ""
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(doc.page_count, 5)):  # Limit OCR to first 5 pages
            page = doc[page_num]
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            image = Image.open(io.BytesIO(img_data))
            ocr_text = pytesseract.image_to_string(image, lang='eng')
            
            if ocr_text.strip():
                text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}\n"
        
        doc.close()
        return text_content
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text with enhanced processing"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove page headers/footers patterns
        text = re.sub(r'\n--- Page \d+ ---\n', '\n\n', text)
        text = re.sub(r'\n--- Page \d+ \(OCR\) ---\n', '\n\n', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between joined words
        text = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', text)  # Add space between numbers and letters
        
        # Clean up common OCR artifacts
        text = re.sub(r'[^\w\s\-.,;:()[\]{}\'\"!?@#$%^&*+=<>/\\|`~]', ' ', text)
        
        # Fix broken words (common in PDF extraction)
        text = re.sub(r'(\w+)\s+(\w+)', lambda m: m.group(1) + m.group(2) if len(m.group(2)) == 1 else m.group(0), text)
        
        # Normalize sports-specific terms
        sports_terms = {
            'S A I': 'SAI',
            'T O P S': 'TOPS',
            'N C O E': 'NCOE',
            'K h e l o': 'Khelo',
            'I n d i a': 'India'
        }
        
        for broken_term, correct_term in sports_terms.items():
            text = text.replace(broken_term, correct_term)
        
        # Clean table artifacts
        text = re.sub(r'Table:\s*\|\s*\|\s*\|', '', text)  # Remove empty table rows
        text = re.sub(r'\|\s*\|', '|', text)  # Clean table separators
        
        return text.strip()
    
    def process_all_pdfs(self) -> List[Dict[str, Any]]:
        """Process all PDFs in the data folder and create document objects"""
        documents = []
        
        if not os.path.exists(self.data_folder):
            logger.error(f"Data folder not found: {self.data_folder}")
            return documents
        
        pdf_files = [f for f in os.listdir(self.data_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.data_folder}")
            return documents
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.data_folder, pdf_file)
            
            logger.info(f"Processing: {pdf_file}")
            
            # Extract text content
            text_content = self.extract_text_from_pdf(pdf_path)
            
            if text_content and not text_content.startswith("Error"):
                # Split content into chunks for better processing
                chunks = self._split_into_chunks(text_content, max_chunk_size=2000)
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        doc = {
                            'title': f"{self._get_document_title(pdf_file)} - Part {i+1}",
                            'text': chunk,
                            'source': pdf_file,
                            'category': self._categorize_document(pdf_file),
                            'chunk_id': i,
                            'total_chunks': len(chunks),
                            'file_path': pdf_path
                        }
                        documents.append(doc)
            else:
                logger.warning(f"Failed to extract content from {pdf_file}")
        
        logger.info(f"Successfully processed {len(documents)} document chunks from {len(pdf_files)} PDFs")
        return documents
    
    def _split_into_chunks(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """Split text into manageable chunks while preserving context and semantic meaning"""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        overlap_size = int(max_chunk_size * 0.1)  # 10% overlap for context preservation
        
        # First, try to split by sections (headers, etc.)
        sections = re.split(r'\n(?=[A-Z][A-Z\s]{5,})\n', text)  # Split on likely headers
        
        if len(sections) == 1:
            # No clear sections, split by paragraphs
            sections = text.split('\n\n')
        
        for i, section in enumerate(sections):
            if len(current_chunk) + len(section) <= max_chunk_size:
                current_chunk += section + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If section is too long, split by sentences
                if len(section) > max_chunk_size:
                    sentences = self._split_by_sentences(section, max_chunk_size)
                    for j, sentence_chunk in enumerate(sentences):
                        if j > 0 and chunks:
                            # Add overlap from previous chunk
                            prev_chunk_end = chunks[-1][-overlap_size:]
                            sentence_chunk = prev_chunk_end + " " + sentence_chunk
                        chunks.append(sentence_chunk)
                    current_chunk = ""
                else:
                    # Add overlap from previous chunk if exists
                    if chunks:
                        prev_chunk_end = chunks[-1][-overlap_size:]
                        current_chunk = prev_chunk_end + " " + section + '\n\n'
                    else:
                        current_chunk = section + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Ensure no chunk is too small (merge with previous if possible)
        final_chunks = []
        for chunk in chunks:
            if len(chunk.strip()) < 100 and final_chunks:
                final_chunks[-1] += " " + chunk
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _split_by_sentences(self, text: str, max_chunk_size: int) -> List[str]:
        """Split text by sentences when paragraph splitting isn't enough"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If single sentence is too long, split by words
                if len(sentence) > max_chunk_size:
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) <= max_chunk_size:
                            temp_chunk += word + ' '
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word + ' '
                    current_chunk = temp_chunk
                else:
                    current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_document_title(self, filename: str) -> str:
        """Extract meaningful title from filename"""
        # Remove extension and clean up
        title = os.path.splitext(filename)[0]
        
        # Known document mappings
        title_mappings = {
            '1739970873_SAI Annual Report -2023-2024 Ops.Div. Part-18=-6-24': 'SAI Annual Report 2023-2024',
            'AdminManual': 'SAI Administration Manual',
            'talent-identification-protocols-1622101420': 'SAI Talent Identification Protocols'
        }
        
        return title_mappings.get(title, title.replace('_', ' ').replace('-', ' ').title())
    
    def _categorize_document(self, filename: str) -> str:
        """Categorize document based on filename and content"""
        filename_lower = filename.lower()
        
        if 'annual' in filename_lower and 'report' in filename_lower:
            return 'annual_reports'
        elif 'talent' in filename_lower and 'identification' in filename_lower:
            return 'talent_identification'
        elif 'admin' in filename_lower or 'manual' in filename_lower:
            return 'administration'
        elif 'fitness' in filename_lower:
            return 'fitness_assessment'
        elif 'khelo' in filename_lower:
            return 'khelo_india'
        else:
            return 'general_sports'

def create_knowledge_base_from_pdfs(data_folder="data") -> List[Dict[str, Any]]:
    """Main function to create knowledge base from PDF files"""
    
    if not PDF_AVAILABLE:
        logger.error("PDF processing libraries not available. Please install: pip install PyPDF2 pdfplumber")
        return []
    
    from .config_manager import ConfigManager
    config_manager = ConfigManager()
    processor = EnhancedPDFProcessor(config_manager)
    documents = processor.process_all_pdfs()
    
    if documents:
        logger.info(f"✅ Successfully created knowledge base with {len(documents)} document chunks")
        
        # Print summary
        categories = {}
        for doc in documents:
            cat = doc['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("📊 Document categories:")
        for category, count in categories.items():
            logger.info(f"  {category}: {count} chunks")
    
    return documents

# Test function
def test_pdf_processing():
    """Test the PDF processing functionality"""
    print("🧪 Testing PDF Processing...")
    
    documents = create_knowledge_base_from_pdfs()
    
    if documents:
        print(f"\n✅ Success! Processed {len(documents)} document chunks")
        print("\n📋 Sample document:")
        sample_doc = documents[0]
        print(f"Title: {sample_doc['title']}")
        print(f"Category: {sample_doc['category']}")
        print(f"Source: {sample_doc['source']}")
        print(f"Text preview: {sample_doc['text'][:200]}...")
    else:
        print("❌ No documents processed. Check your PDF files and dependencies.")

if __name__ == "__main__":
    test_pdf_processing()