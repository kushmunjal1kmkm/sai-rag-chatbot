import os
import json
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PipelineConfig:
    pdf_data_path: str = "./data"
    url_file_path: str = "./data/urls.txt"
    vector_store_path: str = "./vector_store"
    cache_path: str = "./cache"
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.3
    
    max_urls_per_domain: int = 100
    request_delay: float = 1.0
    max_retries: int = 3
    max_depth: int = 3
    content_relevance_threshold: float = 5.0
    
    enable_pdf_processing: bool = True
    enable_web_scraping: bool = True
    enable_caching: bool = True
    enable_content_filtering: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'PipelineConfig':
        config_path = Path(config_path)
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls(**data)
    
    def save(self, config_path: str):
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'pdf_data_path': self.pdf_data_path,
            'url_file_path': self.url_file_path,
            'vector_store_path': self.vector_store_path,
            'cache_path': self.cache_path,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'embedding_model': self.embedding_model,
            'llm_model': self.llm_model,
            'llm_temperature': self.llm_temperature,
            'max_urls_per_domain': self.max_urls_per_domain,
            'request_delay': self.request_delay,
            'max_retries': self.max_retries,
            'max_depth': self.max_depth,
            'content_relevance_threshold': self.content_relevance_threshold,
            'enable_pdf_processing': self.enable_pdf_processing,
            'enable_web_scraping': self.enable_web_scraping,
            'enable_caching': self.enable_caching,
            'enable_content_filtering': self.enable_content_filtering
        }
        
        with open(config_path, 'w') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)

class ConfigManager:
    def __init__(self, config_path: str = "./config/config.yaml"):
        self.config_path = config_path
        self.config = PipelineConfig.from_file(config_path)
    
    def get_config(self) -> PipelineConfig:
        return self.config
    
    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
    
    def save_config(self):
        self.config.save(self.config_path)
    
    def validate_config(self) -> List[str]:
        errors = []
        
        if not Path(self.config.pdf_data_path).exists():
            errors.append(f"PDF data path does not exist: {self.config.pdf_data_path}")
        
        if self.config.enable_web_scraping and not Path(self.config.url_file_path).exists():
            errors.append(f"URL file does not exist: {self.config.url_file_path}")
        
        if self.config.chunk_size <= 0:
            errors.append("Chunk size must be positive")
        
        if self.config.chunk_overlap >= self.config.chunk_size:
            errors.append("Chunk overlap must be less than chunk size")
        
        return errors