#!/usr/bin/env python3
"""
Minimal HITL demo server without any complex imports
"""

import json
import uuid
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class HITLHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/quote/run':
            self.handle_quote_run()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_GET(self):
        if self.path == '/health':
            self.handle_health()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def handle_quote_run(self):
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON
            try:
                request = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid JSON')
                return
            
            # Extract request parameters
            submission = request.get('submission', {})
            use_agentic = request.get('use_agentic', False)
            additional_answers = request.get('additional_answers', {})
            
            if use_agentic:
                # Check for missing required fields
                required_fields = ['roof_age_years', 'construction_type', 'occupancy_type']
                missing_fields = []
                for field in required_fields:
                    if field not in submission or not submission.get(field):
                        missing_fields.append(field)
                
                # Determine status based on missing info
                if missing_fields and not additional_answers:
                    status = 'waiting_for_info'
                    message = 'Additional information required - please answer the following questions'
                    required_questions = [
                        {
                            'question_id': f'missing_{field}',
                            'question_text': f'Please provide {field.replace("_", " ")}',
                            'question_type': 'text',
                            'required': True
                        }
                        for field in missing_fields
                    ]
                    
                    # Return waiting state
                    response = {
                        'run_id': str(uuid.uuid4()),
                        'status': status,
                        'message': message,
                        'required_questions': required_questions,
                        'missing_info': missing_fields,
                        'requires_human_review': True,
                        'current_node': 'handle_missing_info'
                    }
                else:
                    # If we have answers or no missing info, continue processing
                    status = 'completed'
                    message = 'Quote processing completed'
                    
                    # Use real underwriting content for demo
                    rag_evidence = [
                        {
                            'chunk_id': 'uw_guidelines_2_1',
                            'doc_title': 'Homeowners Underwriting Guidelines',
                            'section': '2. Construction & Maintenance Standards',
                            'text': 'If roof age is > 20 years, the risk SHALL BE REFERRED. Roof condition must be documented with recent photos or inspection report.',
                            'relevance_score': 0.92,
                            'rule_strength': 'mandatory'
                        },
                        {
                            'chunk_id': 'uw_guidelines_1_1',
                            'doc_title': 'Homeowners Underwriting Guidelines', 
                            'section': '1. Eligibility Overview',
                            'text': 'Properties used for short-term rental SHALL BE REFERRED. Home office businesses require HOB-02 endorsement.',
                            'relevance_score': 0.87,
                            'rule_strength': 'required'
                        }
                    ]
                    
                    # Generate decision based on missing info and evidence
                    if missing_fields:
                        decision = 'REFER'
                        confidence = 0.65
                    else:
                        decision = 'ACCEPT'
                        confidence = 0.82
                    
                    # Build final response
                    response = {
                        'run_id': str(uuid.uuid4()),
                        'status': status,
                        'decision': {
                            'decision': decision,
                            'confidence': confidence,
                            'reason': f'Agentic {decision.lower()} decision based on evidence review'
                        },
                        'premium': {
                            'annual_premium': round(random.uniform(500, 2000), 2),
                            'monthly_premium': round(random.uniform(40, 170), 2),
                            'coverage_amount': submission.get('coverage_amount', 500000)
                        },
                        'citations': rag_evidence,
                        'required_questions': [
                            {
                                'question': 'Please provide additional documentation',
                                'description': 'Required for underwriting review'
                            }
                        ] if decision == 'REFER' else [],
                        'referral_triggers': [f'Real RAG trigger for {decision}'],
                        'conditions': [f'Real RAG condition for {decision}'],
                        'rag_evidence': rag_evidence,
                        'requires_human_review': decision in ['REFER', 'DECLINE'],
                        'human_review_details': {
                            'review_type': 'agentic_review',
                            'assigned_reviewer': 'underwriting_team',
                            'review_priority': 'high' if decision in ['REFER', 'DECLINE'] else 'low',
                            'estimated_review_time': '24-48 hours' if decision in ['REFER', 'DECLINE'] else 'N/A'
                        },
                        'message': f'Agentic quote processing completed - {decision}',
                        'processing_time_ms': random.randint(100, 300)
                    }
            else:
                # Mock logic fallback (when not using agentic)
                decisions = ['ACCEPT', 'REFER', 'DECLINE']
                decision = random.choice(decisions)
                confidence = random.uniform(0.6, 0.95)
                
                response = {
                    'run_id': str(uuid.uuid4()),
                    'status': 'completed',
                    'decision': {
                        'decision': decision,
                        'confidence': confidence,
                        'reason': f'Mock {decision.lower()} decision based on evidence review'
                    },
                    'premium': {
                        'annual_premium': round(random.uniform(500, 2000), 2),
                        'monthly_premium': round(random.uniform(40, 170), 2),
                        'coverage_amount': submission.get('coverage_amount', 500000)
                    },
                    'citations': [
                        {
                            'doc_title': 'Underwriting Guidelines',
                            'text': f'Mock citation for {decision} decision',
                            'relevance_score': random.uniform(0.8, 0.95)
                        }
                    ],
                    'message': f'Mock quote processing completed - {decision}',
                    'processing_time_ms': random.randint(100, 300)
                }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'detail': f'Processing failed: {str(e)}'}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_health(self):
        response = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server():
    server = HTTPServer(('0.0.0.0', 8000), HITLHandler)
    print("Starting HITL Demo Server")
    print("Server will be available at: http://localhost:8000")
    print("HITL functionality:")
    print("- POST /quote/run with use_agentic=true to trigger missing info flow")
    print("- Add additional_answers to complete the workflow")
    print("- GET /health for health check")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
