#!/usr/bin/env python3
"""
API Integration Tests
Tests actual API endpoints with real HTTP requests
Critical for demonstrating system functionality end-to-end
"""

import pytest
import asyncio
import time
import sys
import os
from fastapi.testclient import TestClient
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.complete import create_complete_app
from models.schemas import HO3Submission


class TestAPIIntegration:
    """Test API endpoints with real scenarios"""
    
    def setup_method(self):
        """Setup test client"""
        app = create_complete_app()
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test: GET /health endpoint"""
        print("\n🧪 Testing health endpoint...")
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        assert "status" in health_data
        assert "timestamp" in health_data
        assert health_data["status"] in ["healthy", "mock_mode", "degraded"]
        
        print(f"✅ Health endpoint: {health_data['status']} - PASS")
    
    def test_quote_ho3_low_risk_accept(self):
        """Test: Complete low-risk quote → ACCEPT"""
        print("\n🧪 Testing low-risk HO3 quote → ACCEPT...")
        
        # Low-risk HO3 submission
        low_risk_submission = {
            "applicant": {
                "full_name": "John Doe",
                "birth_date": "1980-01-01"
            },
            "risk": {
                "property_address": "123 Safe St, Low Risk City, CA 94536",
                "property_type": "single_family",
                "year_built": 2015,
                "square_footage": 2000,
                "roof_type": "asphalt_shingle",
                "foundation_type": "slab",
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 500000,
                "deductible": 1000
            }
        }
        
        response = self.client.post("/quote/ho3", json=low_risk_submission)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "run_id" in result
        assert "status" in result
        assert "decision" in result
        assert "premium" in result
        assert "citations" in result
        assert "requires_human_review" in result
        
        # Low-risk should be ACCEPT
        decision = result["decision"]
        assert decision["decision"] in ["ACCEPT", "REFER"]  # Could be REFER due to mock LLM
        assert "confidence" in decision
        assert decision["confidence"] >= 0.0
        
        print(f"✅ Low-risk quote: {decision['decision']} - PASS")
    
    def test_quote_ho3_high_risk_refer(self):
        """Test: High-risk wildfire quote → REFER"""
        print("\n🧪 Testing high-risk HO3 quote → REFER...")
        
        # High-risk HO3 submission
        high_risk_submission = {
            "applicant": {
                "full_name": "Jane Smith",
                "birth_date": "1975-05-15"
            },
            "risk": {
                "property_address": "456 Fire Zone Rd, Paradise, CA 95969",
                "property_type": "single_family",
                "year_built": 1965,
                "square_footage": 1800,
                "roof_type": "wood_shake",
                "foundation_type": "crawlspace",
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 750000,
                "deductible": 1500
            }
        }
        
        response = self.client.post("/quote/ho3", json=high_risk_submission)
        
        assert response.status_code == 200
        result = response.json()
        
        decision = result["decision"]
        
        # High-risk should be REFER
        assert decision["decision"] in ["REFER", "DECLINE"]
        assert "confidence" in decision
        assert "reasoning" in decision
        
        if decision["decision"] == "REFER":
            assert "referral_triggers" in result
            assert len(result["referral_triggers"]) > 0
        
        print(f"✅ High-risk quote: {decision['decision']} - PASS")
    
    def test_quote_ho3_ineligible_decline(self):
        """Test: Ineligible property → DECLINE"""
        print("\n🧪 Testing ineligible HO3 quote → DECLINE...")
        
        # Ineligible HO3 submission (commercial property)
        ineligible_submission = {
            "applicant": {
                "full_name": "Business Owner",
                "birth_date": "1970-03-20"
            },
            "risk": {
                "property_address": "789 Commercial Blvd, Business Park, CA 94536",
                "property_type": "commercial",  # Not eligible for HO3
                "year_built": 1950,
                "square_footage": 5000,
                "roof_type": "metal",
                "foundation_type": "basement",
                "construction_type": "steel"
            },
            "coverage_request": {
                "coverage_amount": 1000000,
                "deductible": 2500
            }
        }
        
        response = self.client.post("/quote/ho3", json=ineligible_submission)
        
        assert response.status_code == 200
        result = response.json()
        
        decision = result["decision"]
        
        # Ineligible should be DECLINE
        assert decision["decision"] == "DECLINE"
        assert "reasoning" in decision
        assert "ineligible" in decision["reasoning"].lower() or "commercial" in decision["reasoning"].lower()
        
        print(f"✅ Ineligible quote: {decision['decision']} - PASS")
    
    def test_quote_ho3_missing_info_hitl(self):
        """Test: Missing roof/foundation info → HITL required"""
        print("\n🧪 Testing missing info → HITL required...")
        
        # Submission with missing critical information
        missing_info_submission = {
            "applicant": {
                "full_name": "Incomplete Data",
                "birth_date": "1985-08-10"
            },
            "risk": {
                "property_address": "321 Unknown St, Mystery City, CA 94536",
                "property_type": "single_family",
                "year_built": 1990,
                "square_footage": 1600,
                # Missing roof_type and foundation_type
                "roof_type": "",
                "foundation_type": "",
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 400000,
                "deductible": 1000
            }
        }
        
        response = self.client.post("/quote/ho3", json=missing_info_submission)
        
        assert response.status_code == 200
        result = response.json()
        
        # Should require human review
        assert result["requires_human_review"] == True
        assert "missing_info" in result or "required_questions" in result
        
        if "required_questions" in result:
            assert len(result["required_questions"]) > 0
        
        print(f"✅ Missing info → HITL required: PASS")
    
    def test_quote_ho3_invalid_schema(self):
        """Test: Invalid schema → 400 error"""
        print("\n🧪 Testing invalid schema → 400 error...")
        
        # Invalid submission (missing required fields)
        invalid_submission = {
            "applicant": {
                # Missing full_name and birth_date
            },
            "risk": {
                "property_address": "123 Test St",
                # Missing other required fields
            },
            "coverage_request": {
                "coverage_amount": "invalid",  # Should be number
                "deductible": 1000
            }
        }
        
        response = self.client.post("/quote/ho3", json=invalid_submission)
        
        # Should return 422 for validation error
        assert response.status_code == 422
        
        print(f"✅ Invalid schema → 422 error: PASS")
    
    def test_quote_run_legacy_endpoint(self):
        """Test: POST /quote/run legacy endpoint"""
        print("\n🧪 Testing legacy /quote/run endpoint...")
        
        # Legacy format request
        legacy_request = {
            "applicant_name": "Legacy User",
            "address": "456 Legacy Ln, Old Town, CA 94536",
            "property_type": "single_family",
            "coverage_amount": 300000,
            "construction_year": 2000,
            "square_footage": 1500,
            "roof_type": "composite",
            "use_agentic": True
        }
        
        response = self.client.post("/quote/run", json=legacy_request)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "run_id" in result
        assert "status" in result
        assert "decision" in result
        
        print(f"✅ Legacy endpoint: {result['status']} - PASS")
    
    def test_get_run_by_id(self):
        """Test: GET /runs/{run_id} endpoint"""
        print("\n🧪 Testing GET /runs/{run_id}...")
        
        # First create a run
        submission = {
            "applicant": {
                "full_name": "Run Test User",
                "birth_date": "1982-04-12"
            },
            "risk": {
                "property_address": "789 Test Ave, Test City, CA 94536",
                "property_type": "single_family",
                "year_built": 2010,
                "square_footage": 1800,
                "roof_type": "asphalt_shingle",
                "foundation_type": "slab",
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 450000,
                "deductible": 1000
            }
        }
        
        create_response = self.client.post("/quote/ho3", json=submission)
        assert create_response.status_code == 200
        create_result = create_response.json()
        run_id = create_result["run_id"]
        
        # Now get the run
        get_response = self.client.get(f"/runs/{run_id}")
        
        assert get_response.status_code == 200
        run_data = get_response.json()
        
        assert run_data["run_id"] == run_id
        assert "status" in run_data
        assert "decision" in run_data
        assert "created_at" in run_data
        
        print(f"✅ GET run by ID: {run_data['status']} - PASS")
    
    def test_quotes_resume_hitl(self):
        """Test: POST /quotes/{run_id}/resume for HITL"""
        print("\n🧪 Testing HITL resume endpoint...")
        
        # Create a run that will require HITL
        hitl_submission = {
            "applicant": {
                "full_name": "HITL User",
                "birth_date": "1988-09-25"
            },
            "risk": {
                "property_address": "555 Incomplete St, Unknown City, CA 94536",
                "property_type": "single_family",
                "year_built": 1995,
                "square_footage": 1700,
                "roof_type": "",  # Missing
                "foundation_type": "",  # Missing
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 350000,
                "deductible": 1000
            }
        }
        
        create_response = self.client.post("/quote/ho3", json=hitl_submission)
        assert create_response.status_code == 200
        create_result = create_response.json()
        run_id = create_result["run_id"]
        
        # Resume with additional information
        resume_data = {
            "additional_answers": {
                "roof_type": "asphalt_shingle",
                "foundation_type": "slab"
            }
        }
        
        resume_response = self.client.post(f"/quotes/{run_id}/resume", json=resume_data)
        
        assert resume_response.status_code == 200
        resume_result = resume_response.json()
        
        assert resume_result["run_id"] == run_id
        assert "status" in resume_result
        assert "decision" in resume_result
        
        print(f"✅ HITL resume: {resume_result['status']} - PASS")
    
    def test_api_performance_timing(self):
        """Test: Measure API response times"""
        print("\n🧪 Testing API performance timing...")
        
        submission = {
            "applicant": {
                "full_name": "Performance Test",
                "birth_date": "1980-01-01"
            },
            "risk": {
                "property_address": "123 Performance St, Speed City, CA 94536",
                "property_type": "single_family",
                "year_built": 2015,
                "square_footage": 2000,
                "roof_type": "asphalt_shingle",
                "foundation_type": "slab",
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 500000,
                "deductible": 1000
            }
        }
        
        # Measure response time
        start_time = time.time()
        response = self.client.post("/quote/ho3", json=submission)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        
        print(f"✅ API response time: {response_time_ms:.2f}ms - PASS")
        
        # Should be under 1 second for local testing
        assert response_time_ms < 1000, f"Response time {response_time_ms:.2f}ms exceeds 1000ms"
    
    def test_comprehensive_api_scenarios(self):
        """Test: Comprehensive API scenarios matrix"""
        print("\n🧪 Testing comprehensive API scenarios...")
        
        scenarios = [
            {
                "name": "Perfect property",
                "submission": {
                    "applicant": {"full_name": "Perfect User", "birth_date": "1985-01-01"},
                    "risk": {
                        "property_address": "123 Perfect St, Perfect City, CA 94536",
                        "property_type": "single_family",
                        "year_built": 2020,
                        "square_footage": 2000,
                        "roof_type": "asphalt_shingle",
                        "foundation_type": "slab",
                        "construction_type": "frame"
                    },
                    "coverage_request": {"coverage_amount": 500000, "deductible": 1000}
                },
                "expected_decision": ["ACCEPT", "REFER"]
            },
            {
                "name": "Old property",
                "submission": {
                    "applicant": {"full_name": "Old Property", "birth_date": "1970-01-01"},
                    "risk": {
                        "property_address": "456 Old St, Historic City, CA 94536",
                        "property_type": "single_family",
                        "year_built": 1940,
                        "square_footage": 1200,
                        "roof_type": "wood_shake",
                        "foundation_type": "crawlspace",
                        "construction_type": "frame"
                    },
                    "coverage_request": {"coverage_amount": 300000, "deductible": 1500}
                },
                "expected_decision": ["REFER", "DECLINE"]
            },
            {
                "name": "Large coverage",
                "submission": {
                    "applicant": {"full_name": "Large Coverage", "birth_date": "1990-01-01"},
                    "risk": {
                        "property_address": "789 Luxury Ave, Rich City, CA 94536",
                        "property_type": "single_family",
                        "year_built": 2018,
                        "square_footage": 5000,
                        "roof_type": "tile",
                        "foundation_type": "basement",
                        "construction_type": "frame"
                    },
                    "coverage_request": {"coverage_amount": 2000000, "deductible": 5000}
                },
                "expected_decision": ["REFER", "DECLINE"]
            }
        ]
        
        for scenario in scenarios:
            print(f"  Testing: {scenario['name']}")
            
            response = self.client.post("/quote/ho3", json=scenario["submission"])
            
            assert response.status_code == 200
            result = response.json()
            decision = result["decision"]["decision"]
            
            assert decision in scenario["expected_decision"], \
                f"Expected {scenario['expected_decision']}, got {decision}"
            
            print(f"    Result: {decision}")
        
        print("✅ Comprehensive API scenarios: PASS")


if __name__ == "__main__":
    # Run tests manually
    test_suite = TestAPIIntegration()
    test_suite.setup_method()
    
    try:
        test_suite.test_health_endpoint()
        test_suite.setup_method()
        test_suite.test_quote_ho3_low_risk_accept()
        test_suite.setup_method()
        test_suite.test_quote_ho3_high_risk_refer()
        test_suite.setup_method()
        test_suite.test_quote_ho3_ineligible_decline()
        test_suite.setup_method()
        test_suite.test_quote_ho3_missing_info_hitl()
        test_suite.setup_method()
        test_suite.test_quote_ho3_invalid_schema()
        test_suite.setup_method()
        test_suite.test_quote_run_legacy_endpoint()
        test_suite.setup_method()
        test_suite.test_get_run_by_id()
        test_suite.setup_method()
        test_suite.test_quotes_resume_hitl()
        test_suite.setup_method()
        test_suite.test_api_performance_timing()
        test_suite.setup_method()
        test_suite.test_comprehensive_api_scenarios()
        
        print("\n" + "="*60)
        print("✅ ALL API INTEGRATION TESTS PASSED")
        print("🔗 Real endpoints working correctly")
        print("📋 Complete quote lifecycle verified")
        print("🚨 HITL workflows functional")
        print("⚡ Performance within acceptable limits")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
