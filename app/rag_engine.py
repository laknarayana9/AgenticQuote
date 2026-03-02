"""
RAG Engine for Evidence-First Underwriting Copilot

Implements document ingestion, intelligent chunking, and evidence retrieval
with proper citation tracking and confidence scoring.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import chromadb
from chromadb.config import Settings
import numpy as np

# Try to import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers not available, using mock embeddings")

from models.schemas import RetrievalChunk


@dataclass
class DocumentMetadata:
    """Metadata for ingested documents"""
    doc_id: str
    title: str
    carrier: str
    product: str
    state: str
    effective_date: str
    version: str
    file_path: str
    total_chunks: int = 0


class RAGEngine:
    """
    Evidence-First RAG Engine for Underwriting
    
    Features:
    - Header-based intelligent chunking
    - Semantic search with embeddings
    - Evidence quality verification
    - Citation tracking with offsets
    """
    
    def __init__(self, chroma_path: str = "./storage/chroma_db", data_dir: str = "app/externaldata/docs"):
        self.chroma_path = chroma_path
        self.data_dir = Path(data_dir)
        self.documents: Dict[str, DocumentMetadata] = {}
        self.chunks: List[RetrievalChunk] = []
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Try to get existing collection, or create new one
        try:
            self.collection = self.client.get_collection(name="underwriting_guidelines")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name="underwriting_guidelines"
            )
        
        # Initialize embeddings
        if EMBEDDINGS_AVAILABLE:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        else:
            self.embedding_model = None
            self.embedding_dim = 384  # Mock dimension
            
        # Chunking parameters
        self.chunk_size_tokens = 600  # Target tokens per chunk
        self.chunk_overlap = 100      # Character overlap
        self.min_chunk_size = 100     # Minimum characters
        
    def ingest_documents(self, force_reingest: bool = False) -> Dict[str, Any]:
        """
        Ingest all markdown documents with intelligent chunking
        
        Args:
            force_reingest: Whether to reprocess all documents
            
        Returns:
            Summary of ingestion results
        """
        print("📚 Starting document ingestion...")
        
        # Clear existing data if forced
        if force_reingest:
            print("🗑️ Clearing existing data...")
            try:
                # Get all existing IDs and delete them
                existing = self.collection.get()
                if existing['ids']:
                    self.collection.delete(ids=existing['ids'])
                self.chunks.clear()
                self.documents.clear()
            except Exception as e:
                print(f"Warning: Could not clear existing data: {e}")
                # Continue with ingestion
        
        # Process all markdown files
        md_files = list(self.data_dir.glob("*.md"))
        print(f"📄 Found {len(md_files)} markdown files")
        
        total_chunks = 0
        
        for file_path in md_files:
            try:
                chunks = self._process_document(file_path)
                if chunks:
                    self.chunks.extend(chunks)
                    total_chunks += len(chunks)
                    print(f"✅ {file_path.name}: {len(chunks)} chunks")
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
        
        # Store in ChromaDB
        if self.chunks:
            self._store_chunks()
        
        summary = {
            "documents_processed": len(self.documents),
            "total_chunks": total_chunks,
            "chunks_per_doc": {doc_id: info.total_chunks for doc_id, info in self.documents.items()},
            "embedding_model": "all-MiniLM-L6-v2" if EMBEDDINGS_AVAILABLE else "mock",
            "ingestion_timestamp": datetime.now().isoformat()
        }
        
        print(f"🎉 Ingestion complete: {summary}")
        return summary
    
    def _process_document(self, file_path: Path) -> List[RetrievalChunk]:
        """
        Process a single document with intelligent chunking
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            List of chunks with metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata from header
        metadata = self._extract_metadata(content, file_path)
        self.documents[metadata.doc_id] = metadata
        
        # Remove header lines for chunking
        content_body = self._remove_header(content)
        
        # Intelligent chunking based on headers
        chunks = self._chunk_by_headers(content_body, metadata)
        
        return chunks
    
    def _extract_metadata(self, content: str, file_path: Path) -> DocumentMetadata:
        """Extract document metadata from markdown header"""
        lines = content.split('\n')
        metadata = {}
        
        # Extract key-value pairs from header
        for line in lines[:20]:  # Check first 20 lines
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                metadata[key.strip().lower()] = value.strip()
        
        # Create document ID
        doc_id = file_path.stem
        
        return DocumentMetadata(
            doc_id=doc_id,
            title=lines[0].replace('#', '').strip() if lines else doc_id,
            carrier=metadata.get('carrier', 'DemoCarrier'),
            product=metadata.get('product', 'HO3/HO5'),
            state=metadata.get('state', 'CA'),
            effective_date=metadata.get('effective date', '2026-01-01'),
            version=metadata.get('version', 'v0.1'),
            file_path=str(file_path)
        )
    
    def _remove_header(self, content: str) -> str:
        """Remove metadata header from content"""
        lines = content.split('\n')
        content_start = 0
        
        for i, line in enumerate(lines):
            # Find first actual content (header or section)
            if line.startswith('#') or line.startswith('##'):
                content_start = i
                break
        
        return '\n'.join(lines[content_start:])
    
    def _chunk_by_headers(self, content: str, metadata: DocumentMetadata) -> List[RetrievalChunk]:
        """
        Intelligent chunking based on markdown headers
        
        Strategy:
        1. Split by ## (major sections)
        2. Further split by ### (subsections)  
        3. Split large subsections by paragraphs
        4. Maintain context with overlap
        """
        chunks = []
        
        # Split by major sections (##)
        major_sections = re.split(r'\n(?=## )', content)
        
        chunk_id = 0
        for section in major_sections:
            if not section.strip():
                continue
                
            # Extract section title
            section_lines = section.split('\n')
            section_title = section_lines[0].replace('##', '').strip() if section_lines else "Unknown"
            
            # Split by subsections (###)
            subsections = re.split(r'\n(?=### )', section)
            
            for subsection in subsections:
                if not subsection.strip():
                    continue
                
                # Get subsection title
                sub_lines = subsection.split('\n')
                sub_title = sub_lines[0].replace('###', '').strip() if sub_lines else "Unknown"
                sub_content = '\n'.join(sub_lines[1:])  # Remove title line
                
                # Create chunks based on content length
                sub_chunks = self._create_chunks_from_text(
                    sub_content, 
                    metadata, 
                    section_title, 
                    sub_title,
                    chunk_id
                )
                
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
        
        # Update document chunk count
        metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _create_chunks_from_text(self, text: str, metadata: DocumentMetadata, 
                                section: str, subsection: str, start_chunk_id: int) -> List[RetrievalChunk]:
        """Create chunks from text content with proper sizing"""
        if len(text) <= self.min_chunk_size:
            return []
        
        chunks = []
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        current_start = 0
        
        for i, paragraph in enumerate(paragraphs):
            # Check if adding this paragraph exceeds chunk size
            test_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph
            
            if len(test_chunk) > 800 and current_chunk:  # Start new chunk
                # Create chunk from accumulated content
                chunk = self._create_chunk(
                    current_chunk, metadata, section, subsection, 
                    start_chunk_id + len(chunks), current_start
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                current_chunk = paragraph
                current_start = len('\n\n'.join(paragraphs[:i]))
            else:
                current_chunk = test_chunk
        
        # Add final chunk if content remains
        if current_chunk.strip():
            chunk = self._create_chunk(
                current_chunk, metadata, section, subsection,
                start_chunk_id + len(chunks), current_start
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, text: str, metadata: DocumentMetadata, 
                     section: str, subsection: str, chunk_id: int, 
                     char_start: int) -> RetrievalChunk:
        """Create a RetrievalChunk with full metadata"""
        # Generate unique chunk ID
        unique_id = f"{metadata.doc_id}_{section}_{subsection}_{chunk_id}"
        unique_id = re.sub(r'[^a-zA-Z0-9_]', '_', unique_id).lower()
        
        # Create chunk metadata
        chunk_metadata = {
            "doc_id": metadata.doc_id,
            "doc_title": metadata.title,
            "carrier": metadata.carrier,
            "product": metadata.product,
            "state": metadata.state,
            "effective_date": metadata.effective_date,
            "version": metadata.version,
            "section": section,
            "subsection": subsection,
            "chunk_id": unique_id,
            "char_start": char_start,
            "char_end": char_start + len(text),
            "chunk_type": "guideline",
            "rule_strength": self._extract_rule_strength(text)
        }

        return RetrievalChunk(
            doc_id=metadata.doc_id,
            doc_version=metadata.version,
            section=section,
            chunk_id=unique_id,
            text=text.strip(),
            metadata=chunk_metadata,
            relevance_score=None  # Will be set during retrieval
        )
    
    def _extract_rule_strength(self, text: str) -> str:
        """Extract rule strength from text (MUST/SHALL/SHOULD/MAY)"""
        text_upper = text.upper()
        
        if "MUST" in text_upper:
            return "mandatory"
        elif "SHALL" in text_upper:
            return "required"
        elif "SHOULD" in text_upper:
            return "recommended"
        elif "MAY" in text_upper:
            return "permissive"
        else:
            return "informational"
    
    def _store_chunks(self):
        print(f"📦 Storing {len(self.chunks)} chunks in ChromaDB...")
        
        # Prepare documents and embeddings
        documents = [chunk.text for chunk in self.chunks]
        metadatas = [chunk.metadata for chunk in self.chunks]
        ids = [chunk.chunk_id for chunk in self.chunks]
        
        # Generate embeddings
        if self.embedding_model:
            print("🔢 Generating embeddings...")
            embeddings = self.embedding_model.encode(documents).tolist()
        else:
            # Mock embeddings for testing
            embeddings = [np.random.random(self.embedding_dim).tolist() for _ in documents]
        
        # Store in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        print(f"✅ Successfully stored {len(documents)} chunks")
    
    def retrieve(self, query: str, n_results: int = 5, 
                 filters: Optional[Dict[str, Any]] = None) -> List[RetrievalChunk]:
        """
        Retrieve relevant chunks with semantic search
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Metadata filters (carrier, product, state, etc.)
            
        Returns:
            List of relevant chunks with relevance scores
        """
        try:
            # Generate query embedding
            if self.embedding_model:
                query_embedding = self.embedding_model.encode([query]).tolist()
            else:
                query_embedding = [np.random.random(self.embedding_dim).tolist()]
            
            # Prepare where filter
            where_clause = filters if filters else {}
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to RetrievalChunk objects
            chunks = []
            for i in range(len(results["documents"][0])):
                doc = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                # Convert distance to relevance score (lower distance = higher relevance)
                relevance_score = 1.0 / (1.0 + distance)
                
                chunk = RetrievalChunk(
                    doc_id=metadata["doc_id"],
                    doc_version=metadata["version"],
                    section=metadata["section"],
                    chunk_id=metadata["chunk_id"],
                    text=doc,
                    metadata=metadata,
                    relevance_score=relevance_score
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error retrieving chunks: {e}")
            return []
    
    def get_document_summary(self) -> Dict[str, Any]:
        """Get summary of ingested documents"""
        return {
            doc_id: {
                "title": info.title,
                "carrier": info.carrier,
                "product": info.product,
                "state": info.state,
                "effective_date": info.effective_date,
                "version": info.version,
                "chunk_count": info.total_chunks
            }
            for doc_id, info in self.documents.items()
        }
    
    def verify_evidence(self, chunks: List[RetrievalChunk], query_type: str) -> Dict[str, Any]:
        """
        Verify evidence quality and confidence
        
        Args:
            chunks: Retrieved chunks
            query_type: Type of query (eligibility, referral, endorsement, etc.)
            
        Returns:
            Evidence verification results
        """
        if not chunks:
            return {
                "confidence_score": 0.0,
                "verification_status": "insufficient_evidence",
                "evidence_strength": "none",
                "recommendations": ["No relevant evidence found"]
            }
        
        # Calculate confidence based on relevance scores and rule strength
        relevance_scores = [chunk.relevance_score or 0.0 for chunk in chunks]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        # Check rule strength
        rule_strengths = [chunk.metadata.get("rule_strength", "informational") for chunk in chunks]
        strength_weights = {
            "mandatory": 1.0,
            "required": 0.9,
            "recommended": 0.7,
            "permissive": 0.5,
            "informational": 0.3
        }
        
        strength_scores = [strength_weights.get(strength, 0.3) for strength in rule_strengths]
        avg_strength = sum(strength_scores) / len(strength_scores)
        
        # Overall confidence
        confidence_score = (avg_relevance * 0.6) + (avg_strength * 0.4)
        
        # Determine verification status
        if confidence_score >= 0.8:
            status = "strong_evidence"
        elif confidence_score >= 0.6:
            status = "moderate_evidence"
        elif confidence_score >= 0.4:
            status = "weak_evidence"
        else:
            status = "insufficient_evidence"
        
        # Generate recommendations
        recommendations = []
        if confidence_score < 0.6:
            recommendations.append("Consider query expansion for broader search")
        if avg_strength < 0.7:
            recommendations.append("Look for stronger rule language (MUST/SHALL)")
        if len(chunks) < 3:
            recommendations.append("Retrieve more chunks for comprehensive coverage")
        
        return {
            "confidence_score": confidence_score,
            "verification_status": status,
            "evidence_strength": avg_strength,
            "avg_relevance": avg_relevance,
            "chunk_count": len(chunks),
            "recommendations": recommendations
        }


# Global instance for backward compatibility
_rag_engine_instance = None

def get_rag_engine() -> RAGEngine:
    """Get or create global RAG engine instance"""
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
