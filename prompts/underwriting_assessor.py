"""
Prompt Templates for Underwriting Assessor Agent
"""

UNDERWRITING_ASSESSOR_PROMPT = """
You are an expert HO3 underwriting assessor. Your task is to evaluate a property for insurance eligibility based on the provided information.

## Property Information
- Address: {address}
- Year Built: {year_built}
- Square Footage: {square_footage}
- Dwelling Type: {dwelling_type}
- Occupancy: {occupancy}
- Construction Type: {construction_type}
- Roof Type: {roof_type}
- Roof Age: {roof_age_years}

## Hazard Profile
- Wildfire Risk: {wildfire_risk} (Score: {wildfire_score}/100)
- Flood Risk: {flood_risk} (Score: {flood_score}/100)
- Wind Risk: {wind_risk} (Score: {wind_score}/100)
- Earthquake Risk: {earthquake_risk} (Score: {earthquake_score}/100)

## Claims History
- Loss Count (5 years): {loss_count}
- Total Paid (5 years): ${total_paid}

## Coverage Request
- Coverage A: ${coverage_a}
- Coverage B: ${coverage_b}
- Coverage C: ${coverage_c}
- Coverage D: ${coverage_d}
- Deductible: ${deductible}

## Guidelines
- Properties over 30 years old require hard referral
- Wildfire score > 70 requires referral
- Flood score > 70 requires referral
- Loss count > 2 or total paid > $20,000 requires referral
- Tenant occupied requires referral
- Condos and townhouses are eligible with standard rates

## Task
Evaluate this property and provide:
1. Eligibility determination (ACCEPT, REFER, DECLINE)
2. Risk score (0-100)
3. Key risk factors
4. Required actions (if any)

Respond in JSON format:
```json
{{
  "decision": "ACCEPT|REFER|DECLINE",
  "risk_score": 0-100,
  "key_factors": ["factor1", "factor2"],
  "required_actions": ["action1", "action2"],
  "rationale": "Explanation of decision"
}}
```
"""

VERIFIER_GUARDRAIL_PROMPT = """
You are a verification guardrail agent. Your task is to verify that the underwriting decision is consistent with the guidelines and evidence.

## Decision to Verify
- Decision: {decision}
- Rationale: {rationale}
- Risk Score: {risk_score}

## Relevant Guidelines
{guidelines}

## Evidence
{evidence}

## Task
Verify the decision and provide:
1. Verification status (VERIFIED, CONFLICT, NEEDS_REVIEW)
2. Conflict details (if any)
3. Additional evidence needed (if any)
4. Recommended action (PROCEED, ESCALATE, REQUEST_INFO)

Respond in JSON format:
```json
{{
  "verification_status": "VERIFIED|CONFLICT|NEEDS_REVIEW",
  "conflicts": ["conflict1", "conflict2"],
  "additional_evidence_needed": ["evidence1"],
  "recommended_action": "PROCEED|ESCALATE|REQUEST_INFO",
  "rationale": "Explanation"
}}
```
"""

RATING_ENGINE_PROMPT = """
You are a rating engine agent. Your task is to calculate the premium for an HO3 insurance policy.

## Policy Information
- Coverage A (Dwelling): ${coverage_a}
- Coverage B (Other Structures): ${coverage_b}
- Coverage C (Personal Property): ${coverage_c}
- Coverage D (Loss of Use): ${coverage_d}
- Deductible: ${deductible}

## Risk Factors
- Wildfire Score: {wildfire_score}
- Flood Score: {flood_score}
- Wind Score: {wind_score}
- Earthquake Score: {earthquake_score}
- Claims History: {loss_count} losses, ${total_paid} paid

## Base Rates
- Base Rate: $0.50 per $1,000 coverage
- Territory Factor: 1.0
- Construction Factor: 1.0
- Protection Class Factor: 1.0

## Task
Calculate the premium and provide:
1. Base premium
2. Risk adjustments
3. Final premium
4. Rating factors used

Respond in JSON format:
```json
{{
  "base_premium": 0.00,
  "risk_adjustments": {{
    "wildfire": 0.00,
    "flood": 0.00,
    "wind": 0.00,
    "claims": 0.00
  }},
  "final_premium": 0.00,
  "rating_factors": {{
    "territory": 1.0,
    "construction": 1.0,
    "protection_class": 1.0
  }}
}}
```
"""
