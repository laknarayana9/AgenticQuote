#!/usr/bin/env python3
"""
Phase 1 RAG Implementation Test

Demonstrates evidence-first underwriting with real chunking,
evidence verification, and decision composition.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag_engine import RAGEngine, get_rag_engine
from app.evidence_verifier import EvidenceVerifier, get_evidence_verifier
from app.decision_composer import DecisionComposer, get_decision_composer
from models.schemas import QuoteSubmission


def test_rag_ingestion():
    """Test document ingestion and chunking"""
    print("🔥 Testing RAG Ingestion")
    print("=" * 50)
    
    # Initialize RAG engine
    rag = get_rag_engine()
    
    # Ingest documents
    summary = rag.ingest_documents(force_reingest=True)
    
    print(f"📊 Ingestion Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Get document details
    doc_summary = rag.get_document_summary()
    print(f"\n📄 Document Details:")
    for doc_id, info in doc_summary.items():
        print(f"  {doc_id}:")
        print(f"    Title: {info['title']}")
        print(f"    Chunks: {info['chunk_count']}")
        print(f"    Carrier: {info['carrier']}")
        print(f"    Product: {info['product']}")
    
    return rag


def test_evidence_retrieval(rag):
    """Test evidence retrieval with different queries"""
    print("\n🔍 Testing Evidence Retrieval")
    print("=" * 50)
    
    test_queries = [
        "roof age requirements",
        "wildfire risk assessment", 
        "flood zone eligibility",
        "endorsement requirements",
        "property eligibility criteria"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        chunks = rag.retrieve(query, n_results=3)
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}:")
            print(f"    Relevance: {chunk.relevance_score:.3f}")
            print(f"    Section: {chunk.section}")
            print(f"    Rule Strength: {chunk.metadata.get('rule_strength', 'unknown')}")
            print(f"    Excerpt: {chunk.text[:100]}...")
    
    return chunks


def test_evidence_verification(chunks):
    """Test evidence quality verification"""
    print("\n✅ Testing Evidence Verification")
    print("=" * 50)
    
    verifier = get_evidence_verifier()
    
    # Test with different query types
    query_types = ["eligibility", "referral", "endorsement", "missing_info"]
    
    for query_type in query_types:
        print(f"\n🔍 Query Type: {query_type}")
        assessment = verifier.verify_evidence(chunks, query_type)
        
        print(f"  Quality: {assessment.quality.value}")
        print(f"  Confidence: {assessment.confidence_score:.3f}")
        print(f"  Rule Strength: {assessment.rule_strength.value}")
        print(f"  Has Thresholds: {assessment.has_thresholds}")
        print(f"  Cross-References: {assessment.cross_reference_count}")
        print(f"  Recommendations: {len(assessment.recommendations)}")
        
        for rec in assessment.recommendations[:2]:  # Show first 2
            print(f"    - {rec}")
    
    return assessment


def test_decision_composition(chunks):
    """Test evidence-based decision composition"""
    print("\n⚖️ Testing Decision Composition")
    print("=" * 50)
    
    composer = get_decision_composer()
    
    # Test with sample submission data
    submission_data = {
        "applicant_name": "Test User",
        "address": "123 Test St, Irvine, CA 92612",
        "property_type": "single_family",
        "coverage_amount": 500000,
        "construction_year": 1985,
        "roof_age": 25  # This should trigger referral
    }
    
    # Test different query types
    query_types = ["eligibility", "referral", "endorsement"]
    
    for query_type in query_types:
        print(f"\n🎯 Query Type: {query_type}")
        
        decision = composer.compose_decision(chunks, query_type, submission_data)
        
        print(f"  Decision: {decision.decision_type.value}")
        print(f"  Confidence: {decision.confidence_score:.3f}")
        print(f"  Primary Reason: {decision.primary_reason}")
        print(f"  Evidence Components: {len(decision.evidence_map)}")
        print(f"  Required Questions: {len(decision.required_questions)}")
        print(f"  Referral Triggers: {len(decision.referral_triggers)}")
        print(f"  Citations: {len(decision.citations)}")
        
        # Show key citations
        if decision.citations:
            print(f"  Key Citations:")
            for citation in decision.citations[:2]:
                print(f"    [{citation['citation_id']}] {citation['doc_title']} - {citation['section']}")
    
    return decision


def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print("\n🔄 Testing End-to-End Workflow")
    print("=" * 50)
    
    # Sample submission
    submission = QuoteSubmission(
        applicant_name="John Doe",
        address="2231 Watermarke Pl, Irvine, CA 92612",
        property_type="single_family",
        coverage_amount=600000,
        construction_year=1979,
        roof_type="tile",  # Use roof_type instead of roof_age
        square_footage=1693
    )
    
    # Initialize components
    rag = get_rag_engine()
    verifier = get_evidence_verifier()
    composer = get_decision_composer()
    
    # Build query from submission
    query_parts = [
        f"property type {submission.property_type}",
        f"coverage amount {submission.coverage_amount}",
        f"construction year {submission.construction_year}",
        f"roof type {submission.roof_type}",
        "eligibility requirements"
    ]
    query = " ".join(query_parts)
    
    print(f"🔍 Query: {query}")
    
    # Retrieve evidence
    chunks = rag.retrieve(query, n_results=5)
    print(f"📊 Retrieved {len(chunks)} chunks")
    
    # Verify evidence
    assessment = verifier.verify_evidence(chunks, "eligibility")
    print(f"✅ Evidence Quality: {assessment.quality.value}")
    print(f"✅ Confidence: {assessment.confidence_score:.3f}")
    
    # Compose decision
    decision = composer.compose_decision(chunks, "eligibility", submission.dict())
    print(f"⚖️ Decision: {decision.decision_type.value}")
    print(f"⚖️ Reason: {decision.primary_reason}")
    
    # Show evidence mapping
    print(f"\n📋 Evidence Mapping:")
    for component, evidence in decision.evidence_map.items():
        print(f"  {component}: {len(evidence.chunk_ids)} chunks, confidence: {evidence.confidence:.3f}")
    
    # Show citations
    print(f"\n📄 Citations:")
    for citation in decision.citations:
        print(f"  [{citation['citation_id']}] {citation['doc_title']} - {citation['section']}")
        print(f"    Rule: {citation['rule_strength']}, Relevance: {citation['relevance_score']:.3f}")
    
    return decision


def main():
    """Main test function"""
    print("🚀 Phase 1 RAG Implementation Test")
    print("=" * 60)
    
    try:
        # Test 1: Document Ingestion
        rag = test_rag_ingestion()
        
        # Test 2: Evidence Retrieval
        chunks = test_evidence_retrieval(rag)
        
        # Test 3: Evidence Verification
        assessment = test_evidence_verification(chunks)
        
        # Test 4: Decision Composition
        decision = test_decision_composition(chunks)
        
        # Test 5: End-to-End Workflow
        final_decision = test_end_to_end_workflow()
        
        print("\n🎉 All Tests Completed Successfully!")
        print("=" * 60)
        
        # Summary
        print(f"📊 Final Results:")
        print(f"  Documents Processed: {len(rag.documents)}")
        print(f"  Total Chunks: {len(rag.chunks)}")
        print(f"  Final Decision: {final_decision.decision_type.value}")
        print(f"  Final Confidence: {final_decision.confidence_score:.3f}")
        print(f"  Evidence Quality: {assessment.quality.value}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
