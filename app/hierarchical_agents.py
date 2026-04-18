"""
Hierarchical Agent Delegation System with Conflict Resolution
Implements sophisticated multi-agent orchestration demonstrating:

- Role-based agent hierarchy
- Dynamic task delegation
- Advanced conflict resolution strategies
- Consensus building mechanisms
- Performance monitoring and adaptation
- Cross-agent communication protocols
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Hierarchical agent roles with clear responsibilities"""
    COORDINATOR = "coordinator"          # Orchestrates overall process
    SPECIALIST_LEAD = "specialist_lead"  # Leads domain specialists
    VALIDATION_SPECIALIST = "validation_specialist"
    ENRICHMENT_SPECIALIST = "enrichment_specialist"
    ASSESSMENT_SPECIALIST = "assessment_specialist"
    RISK_SPECIALIST = "risk_specialist"
    COMPLIANCE_SPECIALIST = "compliance_specialist"
    REVIEWER = "reviewer"                # Quality control
    ARBITER = "arbiter"                  # Conflict resolution
    SYNTHESIZER = "synthesizer"          # Final decision synthesis


class AgentCapability(Enum):
    """Specific agent capabilities"""
    DATA_VALIDATION = "data_validation"
    DATA_ENRICHMENT = "data_enrichment"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_CHECKING = "compliance_checking"
    EVIDENCE_RETRIEVAL = "evidence_retrieval"
    DECISION_SYNTHESIS = "decision_synthesis"
    CONFLICT_RESOLUTION = "conflict_resolution"
    QUALITY_REVIEW = "quality_review"
    PERFORMANCE_MONITORING = "performance_monitoring"


class ConflictType(Enum):
    """Types of conflicts between agents"""
    DECISION_DISAGREEMENT = "decision_disagreement"
    EVIDENCE_CONFLICT = "evidence_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    METHODOLOGY_CONFLICT = "methodology_conflict"
    RESOURCE_CONFLICT = "resource_conflict"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    HIERARCHICAL_OVERRIDE = "hierarchical_override"
    CONSENSUS_BUILDING = "consensus_building"
    WEIGHTED_VOTING = "weighted_voting"
    EVIDENCE_BASED = "evidence_based"
    PERFORMANCE_BASED = "performance_based"
    ESCALATION = "escalation"


class TaskPriority(Enum):
    """Task priority levels for delegation"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AgentTask:
    """Task assigned to an agent"""
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    required_capabilities: List[AgentCapability]
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class AgentMessage:
    """Communication message between agents"""
    message_id: str
    sender: str
    recipient: str
    message_type: str  # task_assignment, result_share, conflict_notification, consensus_request
    content: Dict[str, Any]
    priority: TaskPriority
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentConflict:
    """Conflict between agents"""
    conflict_id: str
    conflict_type: ConflictType
    conflicting_agents: List[str]
    conflict_details: Dict[str, Any]
    severity: float  # 0.0 to 1.0
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolution_result: Optional[Dict[str, Any]] = None
    status: str = "detected"  # detected, resolving, resolved, escalated


@dataclass
class AgentPerformance:
    """Performance metrics for an agent"""
    agent_id: str
    role: AgentRole
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_confidence: float = 0.0
    average_processing_time: float = 0.0
    conflict_participation: int = 0
    consensus_contributions: int = 0
    quality_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class Agent(ABC):
    """Abstract base class for hierarchical agents"""
    
    def __init__(self, agent_id: str, role: AgentRole, capabilities: List[AgentCapability]):
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities
        self.performance = AgentPerformance(agent_id=agent_id, role=role)
        self.message_queue: List[AgentMessage] = []
        self.current_tasks: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []
        
    @abstractmethod
    def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process assigned task and return result"""
        pass
    
    @abstractmethod
    def assess_conflict(self, conflict: AgentConflict) -> Dict[str, Any]:
        """Assess conflict and provide resolution input"""
        pass
    
    def receive_message(self, message: AgentMessage):
        """Receive message from another agent"""
        self.message_queue.append(message)
        
    def send_message(self, recipient: str, message_type: str, content: Dict[str, Any], priority: TaskPriority):
        """Send message to another agent"""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content,
            priority=priority
        )
        return message
    
    def update_performance(self, task_completed: bool, processing_time: float, confidence: float):
        """Update performance metrics"""
        if task_completed:
            self.performance.tasks_completed += 1
        else:
            self.performance.tasks_failed += 1
        
        # Update averages
        total_tasks = self.performance.tasks_completed + self.performance.tasks_failed
        self.performance.average_confidence = (
            (self.performance.average_confidence * (total_tasks - 1) + confidence) / total_tasks
        )
        self.performance.average_processing_time = (
            (self.performance.average_processing_time * (total_tasks - 1) + processing_time) / total_tasks
        )
        self.performance.last_updated = datetime.now()


class SpecialistAgent(Agent):
    """Domain specialist agent with specific expertise"""
    
    def __init__(self, agent_id: str, role: AgentRole, specialty: str):
        super().__init__(agent_id, role, self._get_role_capabilities(role))
        self.specialty = specialty
        self.domain_knowledge = {}
        self.processing_history = []
        
    def _get_role_capabilities(self, role: AgentRole) -> List[AgentCapability]:
        """Get capabilities based on role"""
        role_capabilities = {
            AgentRole.VALIDATION_SPECIALIST: [AgentCapability.DATA_VALIDATION],
            AgentRole.ENRICHMENT_SPECIALIST: [AgentCapability.DATA_ENRICHMENT],
            AgentRole.ASSESSMENT_SPECIALIST: [AgentCapability.RISK_ASSESSMENT],
            AgentRole.RISK_SPECIALIST: [AgentCapability.RISK_ASSESSMENT],
            AgentRole.COMPLIANCE_SPECIALIST: [AgentCapability.COMPLIANCE_CHECKING],
        }
        return role_capabilities.get(role, [])
    
    def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process task with domain-specific expertise"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Specialist {self.agent_id} processing task: {task.task_type}")
            
            # Domain-specific processing
            result = self._domain_specific_processing(task)
            
            # Add specialist metadata
            result["specialist_metadata"] = {
                "agent_id": self.agent_id,
                "specialty": self.specialty,
                "confidence": self._calculate_confidence(task, result),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "domain_rules_applied": self._get_applied_rules(task)
            }
            
            # Update performance
            processing_time = (datetime.now() - start_time).total_seconds()
            confidence = result["specialist_metadata"]["confidence"]
            self.update_performance(True, processing_time, confidence)
            
            # Store in history
            self.processing_history.append({
                "task_id": task.task_id,
                "result": result,
                "timestamp": datetime.now()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Specialist {self.agent_id} failed to process task: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_performance(False, processing_time, 0.0)
            
            return {
                "error": str(e),
                "specialist_metadata": {
                    "agent_id": self.agent_id,
                    "specialty": self.specialty,
                    "confidence": 0.0,
                    "processing_time": processing_time
                }
            }
    
    def _domain_specific_processing(self, task: AgentTask) -> Dict[str, Any]:
        """Perform domain-specific processing based on specialty"""
        
        if self.role == AgentRole.VALIDATION_SPECIALIST:
            return self._validate_data(task.input_data)
        elif self.role == AgentRole.ENRICHMENT_SPECIALIST:
            return self._enrich_data(task.input_data)
        elif self.role == AgentRole.ASSESSMENT_SPECIALIST:
            return self._assess_risk(task.input_data)
        elif self.role == AgentRole.RISK_SPECIALIST:
            return self._analyze_risk(task.input_data)
        elif self.role == AgentRole.COMPLIANCE_SPECIALIST:
            return self._check_compliance(task.input_data)
        else:
            return {"result": "Generic processing", "confidence": 0.5}
    
    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate submission data"""
        missing_fields = []
        validation_errors = []
        
        # Check required fields
        required_fields = ["applicant_name", "address", "property_type", "coverage_amount"]
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        # Check data quality
        if data.get("coverage_amount", 0) > 10000000:
            validation_errors.append("Coverage amount exceeds maximum limit")
        
        if data.get("construction_year", 0) > 2024:
            validation_errors.append("Construction year cannot be in the future")
        
        confidence = 0.9 if not missing_fields and not validation_errors else 0.4
        
        return {
            "validation_result": "passed" if not missing_fields and not validation_errors else "failed",
            "missing_fields": missing_fields,
            "validation_errors": validation_errors,
            "confidence": confidence
        }
    
    def _enrich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich data with additional context"""
        # Mock enrichment - in real system would call external services
        enrichment = {
            "normalized_address": {
                "street": data.get("address", "").split(",")[0],
                "city": data.get("address", "").split(",")[1].strip() if "," in data.get("address", "") else "",
                "state": data.get("address", "").split(",")[2].strip() if "," in data.get("address", "") else "",
                "zip_code": "00000"
            },
            "hazard_scores": {
                "wildfire_risk": 0.3,
                "flood_risk": 0.2,
                "earthquake_risk": 0.1,
                "wind_risk": 0.15
            },
            "property_details": {
                "estimated_value": data.get("coverage_amount", 0) * 1.5,
                "construction_type": "standard",
                "quality_grade": "average"
            }
        }
        
        return {
            "enrichment_result": enrichment,
            "confidence": 0.8
        }
    
    def _assess_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess underwriting risk"""
        risk_factors = []
        risk_score = 0.3  # Base risk
        
        # Check property age
        construction_year = data.get("construction_year", 2000)
        if construction_year < 1940:
            risk_factors.append("Old construction")
            risk_score += 0.2
        
        # Check coverage amount
        coverage = data.get("coverage_amount", 0)
        if coverage > 1000000:
            risk_factors.append("High coverage amount")
            risk_score += 0.1
        
        # Check property type
        property_type = data.get("property_type", "")
        if property_type not in ["single_family", "condo", "townhouse"]:
            risk_factors.append("Non-standard property type")
            risk_score += 0.3
        
        confidence = 0.7 if risk_score < 0.6 else 0.5
        
        return {
            "risk_assessment": {
                "risk_score": min(1.0, risk_score),
                "risk_factors": risk_factors,
                "risk_level": "low" if risk_score < 0.3 else "medium" if risk_score < 0.6 else "high"
            },
            "confidence": confidence
        }
    
    def _analyze_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed risk analysis"""
        # More sophisticated risk analysis
        enrichment = data.get("enrichment_result", {})
        hazard_scores = enrichment.get("hazard_scores", {})
        
        high_risks = []
        for hazard, score in hazard_scores.items():
            if score > 0.7:
                high_risks.append(hazard)
        
        overall_risk = max(hazard_scores.values()) if hazard_scores else 0.3
        
        return {
            "risk_analysis": {
                "overall_risk_score": overall_risk,
                "high_risk_factors": high_risks,
                "mitigation_recommendations": self._generate_mitigation_recommendations(high_risks)
            },
            "confidence": 0.8
        }
    
    def _check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check regulatory compliance"""
        compliance_issues = []
        
        # Mock compliance checks
        state = data.get("state", "")
        if state == "CA":
            # California specific compliance
            if not data.get("earthquake_coverage", False):
                compliance_issues.append("Earthquake coverage disclosure required")
        
        if data.get("coverage_amount", 0) > 500000:
            compliance_issues.append("High-value coverage requires additional documentation")
        
        compliance_score = max(0.0, 1.0 - (len(compliance_issues) * 0.2))
        
        return {
            "compliance_result": {
                "compliant": len(compliance_issues) == 0,
                "compliance_issues": compliance_issues,
                "compliance_score": compliance_score
            },
            "confidence": 0.9
        }
    
    def _calculate_confidence(self, task: AgentTask, result: Dict[str, Any]) -> float:
        """Calculate confidence in result"""
        base_confidence = result.get("confidence", 0.5)
        
        # Adjust based on data quality
        input_quality = self._assess_input_quality(task.input_data)
        
        # Adjust based on task complexity
        complexity_factor = 1.0 - (len(task.required_capabilities) * 0.1)
        
        return max(0.1, min(0.95, base_confidence * input_quality * complexity_factor))
    
    def _assess_input_quality(self, input_data: Dict[str, Any]) -> float:
        """Assess quality of input data"""
        if not input_data:
            return 0.1
        
        # Check data completeness
        total_fields = len(input_data)
        non_null_fields = sum(1 for value in input_data.values() if value is not None and value != "")
        
        completeness = non_null_fields / total_fields if total_fields > 0 else 0.0
        
        # Check data consistency
        consistency = 0.8  # Mock consistency check
        
        return (completeness + consistency) / 2.0
    
    def _get_applied_rules(self, task: AgentTask) -> List[str]:
        """Get list of domain rules applied"""
        rules = []
        
        if self.role == AgentRole.VALIDATION_SPECIALIST:
            rules = ["required_fields_check", "data_quality_validation", "business_rules_validation"]
        elif self.role == AgentRole.ENRICHMENT_SPECIALIST:
            rules = ["address_normalization", "hazard_scoring", "property_valuation"]
        elif self.role == AgentRole.ASSESSMENT_SPECIALIST:
            rules = ["risk_factor_analysis", "eligibility_assessment", "threshold_evaluation"]
        elif self.role == AgentRole.RISK_SPECIALIST:
            rules = ["hazard_analysis", "risk_aggregation", "mitigation_planning"]
        elif self.role == AgentRole.COMPLIANCE_SPECIALIST:
            rules = ["regulatory_check", "state_compliance", "policy_validation"]
        
        return rules
    
    def _generate_mitigation_recommendations(self, high_risks: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        for risk in high_risks:
            if "wildfire" in risk:
                recommendations.append("Require defensible space documentation")
            elif "flood" in risk:
                recommendations.append("Request elevation certificate")
            elif "earthquake" in risk:
                recommendations.append("Verify seismic retrofitting")
        
        return recommendations
    
    def assess_conflict(self, conflict: AgentConflict) -> Dict[str, Any]:
        """Assess conflict from specialist perspective"""
        assessment = {
            "agent_id": self.agent_id,
            "specialty": self.specialty,
            "conflict_assessment": {
                "severity": conflict.severity,
                "impact": self._assess_conflict_impact(conflict),
                "recommended_resolution": self._recommend_resolution(conflict),
                "confidence": 0.7
            }
        }
        
        return assessment
    
    def _assess_conflict_impact(self, conflict: AgentConflict) -> str:
        """Assess impact of conflict"""
        if conflict.severity > 0.8:
            return "critical"
        elif conflict.severity > 0.5:
            return "significant"
        else:
            return "minor"
    
    def _recommend_resolution(self, conflict: AgentConflict) -> ResolutionStrategy:
        """Recommend resolution strategy"""
        if conflict.conflict_type == ConflictType.DECISION_DISAGREEMENT:
            return ResolutionStrategy.WEIGHTED_VOTING
        elif conflict.conflict_type == ConflictType.EVIDENCE_CONFLICT:
            return ResolutionStrategy.EVIDENCE_BASED
        else:
            return ResolutionStrategy.CONSENSUS_BUILDING


class CoordinatorAgent(Agent):
    """Coordinator agent that orchestrates the entire process"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.COORDINATOR, [AgentCapability.PERFORMANCE_MONITORING])
        self.active_agents: Dict[str, Agent] = {}
        self.task_queue: List[AgentTask] = []
        self.delegation_history: List[Dict[str, Any]] = []
        self.conflict_history: List[AgentConflict] = []
        
    def register_agent(self, agent: Agent):
        """Register an agent with the coordinator"""
        self.active_agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} with role: {agent.role.value}")
    
    def orchestrate_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate complete multi-agent process"""
        logger.info("Starting coordinated multi-agent process")
        
        # Create initial tasks
        tasks = self._create_initial_tasks(input_data)
        self.task_queue.extend(tasks)
        
        # Process tasks with delegation
        results = {}
        while self.task_queue:
            task = self.task_queue.pop(0)
            result = self._delegate_and_execute_task(task)
            results[task.task_type] = result
            
            # Create follow-up tasks based on results
            follow_up_tasks = self._create_follow_up_tasks(task, result)
            self.task_queue.extend(follow_up_tasks)
        
        # Synthesize final result
        final_result = self._synthesize_results(results)
        
        return final_result
    
    def _create_initial_tasks(self, input_data: Dict[str, Any]) -> List[AgentTask]:
        """Create initial set of tasks"""
        tasks = []
        
        # Validation task
        validation_task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="validation",
            description="Validate submission data completeness and quality",
            priority=TaskPriority.CRITICAL,
            required_capabilities=[AgentCapability.DATA_VALIDATION],
            input_data=input_data
        )
        tasks.append(validation_task)
        
        # Enrichment task (depends on validation)
        enrichment_task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="enrichment",
            description="Enrich data with additional context and risk factors",
            priority=TaskPriority.HIGH,
            required_capabilities=[AgentCapability.DATA_ENRICHMENT],
            input_data=input_data,
            dependencies=[validation_task.task_id]
        )
        tasks.append(enrichment_task)
        
        return tasks
    
    def _delegate_and_execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Delegate task to appropriate agent and execute"""
        # Find best agent for task
        assigned_agent = self._select_agent_for_task(task)
        
        if not assigned_agent:
            logger.error(f"No agent available for task: {task.task_type}")
            return {"error": "No available agent"}
        
        # Assign task
        task.assigned_agent = assigned_agent.agent_id
        task.status = "in_progress"
        
        # Execute task
        result = assigned_agent.process_task(task)
        
        # Update task status
        task.result = result
        task.status = "completed" if "error" not in result else "failed"
        task.completed_at = datetime.now()
        
        # Record delegation
        self.delegation_history.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "assigned_agent": assigned_agent.agent_id,
            "agent_role": assigned_agent.role.value,
            "timestamp": datetime.now(),
            "success": "error" not in result
        })
        
        logger.info(f"Task {task.task_type} delegated to {assigned_agent.agent_id}: {'SUCCESS' if 'error' not in result else 'FAILED'}")
        
        return result
    
    def _select_agent_for_task(self, task: AgentTask) -> Optional[Agent]:
        """Select best agent for task based on capabilities and performance"""
        suitable_agents = []
        
        for agent in self.active_agents.values():
            # Check if agent has required capabilities
            if any(cap in agent.capabilities for cap in task.required_capabilities):
                suitable_agents.append(agent)
        
        if not suitable_agents:
            return None
        
        # Select agent with best performance for this task type
        best_agent = max(suitable_agents, key=lambda a: a.performance.quality_score)
        
        return best_agent
    
    def _create_follow_up_tasks(self, completed_task: AgentTask, result: Dict[str, Any]) -> List[AgentTask]:
        """Create follow-up tasks based on task results"""
        follow_up_tasks = []
        
        if completed_task.task_type == "validation" and result.get("validation_result") == "passed":
            # Create assessment task
            assessment_task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="assessment",
                description="Perform comprehensive risk assessment",
                priority=TaskPriority.HIGH,
                required_capabilities=[AgentCapability.RISK_ASSESSMENT],
                input_data=completed_task.input_data,
                dependencies=[completed_task.task_id]
            )
            follow_up_tasks.append(assessment_task)
        
        elif completed_task.task_type == "enrichment":
            # Create risk analysis task
            risk_task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="risk_analysis",
                description="Analyze specific risk factors",
                priority=TaskPriority.HIGH,
                required_capabilities=[AgentCapability.RISK_ASSESSMENT],
                input_data={**completed_task.input_data, "enrichment_result": result.get("enrichment_result", {})},
                dependencies=[completed_task.task_id]
            )
            follow_up_tasks.append(risk_task)
        
        elif completed_task.task_type == "assessment":
            # Create compliance task
            compliance_task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="compliance",
                description="Check regulatory compliance",
                priority=TaskPriority.MEDIUM,
                required_capabilities=[AgentCapability.COMPLIANCE_CHECKING],
                input_data=completed_task.input_data,
                dependencies=[completed_task.task_id]
            )
            follow_up_tasks.append(compliance_task)
        
        return follow_up_tasks
    
    def _synthesize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final result from all agent results"""
        
        synthesis = {
            "final_decision": "REFER",
            "confidence": 0.5,
            "agent_contributions": {},
            "processing_summary": {
                "total_tasks": len(results),
                "successful_tasks": sum(1 for r in results.values() if "error" not in r),
                "failed_tasks": sum(1 for r in results.values() if "error" in r)
            },
            "recommendations": []
        }
        
        # Collect agent contributions
        for task_type, result in results.items():
            if "specialist_metadata" in result:
                agent_id = result["specialist_metadata"]["agent_id"]
                synthesis["agent_contributions"][agent_id] = {
                    "task_type": task_type,
                    "confidence": result["specialist_metadata"]["confidence"],
                    "processing_time": result["specialist_metadata"]["processing_time"]
                }
        
        # Make final decision based on all results
        validation_result = results.get("validation", {})
        assessment_result = results.get("assessment", {})
        compliance_result = results.get("compliance", {})
        
        # Decision logic
        if validation_result.get("validation_result") == "failed":
            synthesis["final_decision"] = "REFER"
            synthesis["confidence"] = 0.3
            synthesis["recommendations"].append("Request missing information")
        elif compliance_result.get("compliance_result", {}).get("compliant") is False:
            synthesis["final_decision"] = "REFER"
            synthesis["confidence"] = 0.4
            synthesis["recommendations"].append("Address compliance issues")
        elif assessment_result.get("risk_assessment", {}).get("risk_level") == "high":
            synthesis["final_decision"] = "REFER"
            synthesis["confidence"] = 0.6
            synthesis["recommendations"].append("Manual review required for high risk")
        else:
            synthesis["final_decision"] = "ACCEPT"
            synthesis["confidence"] = 0.8
            synthesis["recommendations"].append("Proceed with policy issuance")
        
        # Calculate overall confidence
        confidences = [r.get("specialist_metadata", {}).get("confidence", 0.5) for r in results.values()]
        synthesis["confidence"] = sum(confidences) / len(confidences) if confidences else 0.5
        
        return synthesis
    
    def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process task as coordinator"""
        if task.task_type == "orchestration":
            return self.orchestrate_process(task.input_data)
        else:
            return {"error": f"Coordinator cannot process task type: {task.task_type}"}
    
    def assess_conflict(self, conflict: AgentConflict) -> Dict[str, Any]:
        """Assess conflict from coordinator perspective"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "conflict_assessment": {
                "system_impact": self._assess_system_impact(conflict),
                "recommended_escalation": conflict.severity > 0.8,
                "coordination_strategy": self._recommend_coordination_strategy(conflict),
                "confidence": 0.9
            }
        }
    
    def _assess_system_impact(self, conflict: AgentConflict) -> str:
        """Assess system-wide impact of conflict"""
        if conflict.conflict_type == ConflictType.DECISION_DISAGREEMENT:
            return "decision_blocking"
        elif conflict.conflict_type == ConflictType.RESOURCE_CONFLICT:
            return "performance_degradation"
        else:
            return "quality_risk"
    
    def _recommend_coordination_strategy(self, conflict: AgentConflict) -> str:
        """Recommend coordination strategy"""
        if conflict.severity > 0.8:
            return "immediate_intervention"
        elif conflict.severity > 0.5:
            return "mediated_negotiation"
        else:
            return "autonomous_resolution"


class ConflictResolutionSystem:
    """Advanced conflict resolution system"""
    
    def __init__(self):
        self.resolution_strategies = {
            ResolutionStrategy.HIERARCHICAL_OVERRIDE: self._hierarchical_override,
            ResolutionStrategy.CONSENSUS_BUILDING: self._consensus_building,
            ResolutionStrategy.WEIGHTED_VOTING: self._weighted_voting,
            ResolutionStrategy.EVIDENCE_BASED: self._evidence_based_resolution,
            ResolutionStrategy.PERFORMANCE_BASED: self._performance_based_resolution,
            ResolutionStrategy.ESCALATION: self._escalate_conflict
        }
        
    def resolve_conflict(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Resolve conflict using appropriate strategy"""
        
        # Select resolution strategy
        strategy = self._select_resolution_strategy(conflict)
        conflict.resolution_strategy = strategy
        
        # Apply resolution strategy
        resolution_func = self.resolution_strategies[strategy]
        resolution_result = resolution_func(conflict, agents)
        
        conflict.resolution_result = resolution_result
        conflict.status = "resolved"
        
        logger.info(f"Conflict {conflict.conflict_id} resolved using {strategy.value}")
        
        return resolution_result
    
    def _select_resolution_strategy(self, conflict: AgentConflict) -> ResolutionStrategy:
        """Select best resolution strategy for conflict"""
        
        if conflict.severity > 0.9:
            return ResolutionStrategy.ESCALATION
        elif conflict.conflict_type == ConflictType.DECISION_DISAGREEMENT:
            return ResolutionStrategy.WEIGHTED_VOTING
        elif conflict.conflict_type == ConflictType.EVIDENCE_CONFLICT:
            return ResolutionStrategy.EVIDENCE_BASED
        elif conflict.severity > 0.7:
            return ResolutionStrategy.HIERARCHICAL_OVERRIDE
        else:
            return ResolutionStrategy.CONSENSUS_BUILDING
    
    def _hierarchical_override(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Resolve conflict using hierarchical override"""
        
        # Find highest-ranking agent in conflict
        conflicting_agents = [agents[agent_id] for agent_id in conflict.conflicting_agents if agent_id in agents]
        
        if not conflicting_agents:
            return {"resolution": "failed", "reason": "No conflicting agents found"}
        
        # Sort by role hierarchy
        role_hierarchy = {
            AgentRole.COORDINATOR: 1,
            AgentRole.SPECIALIST_LEAD: 2,
            AgentRole.REVIEWER: 3,
            AgentRole.ARBITER: 4,
            AgentRole.VALIDATION_SPECIALIST: 5,
            AgentRole.ENRICHMENT_SPECIALIST: 6,
            AgentRole.ASSESSMENT_SPECIALIST: 7,
            AgentRole.RISK_SPECIALIST: 8,
            AgentRole.COMPLIANCE_SPECIALIST: 9,
            AgentRole.SYNTHESIZER: 10
        }
        
        highest_ranking_agent = min(conflicting_agents, key=lambda a: role_hierarchy.get(a.role, 99))
        
        return {
            "resolution": "hierarchical_override",
            "overriding_agent": highest_ranking_agent.agent_id,
            "agent_role": highest_ranking_agent.role.value,
            "reasoning": f"Hierarchical override by {highest_ranking_agent.role.value}"
        }
    
    def _consensus_building(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Resolve conflict through consensus building"""
        
        # Gather inputs from all conflicting agents
        agent_inputs = {}
        for agent_id in conflict.conflicting_agents:
            if agent_id in agents:
                agent_inputs[agent_id] = agents[agent_id].assess_conflict(conflict)
        
        # Calculate consensus score
        consensus_score = self._calculate_consensus_score(agent_inputs)
        
        if consensus_score > 0.7:
            return {
                "resolution": "consensus_reached",
                "consensus_score": consensus_score,
                "agent_inputs": agent_inputs,
                "reasoning": "High consensus achieved among conflicting agents"
            }
        else:
            return {
                "resolution": "consensus_failed",
                "consensus_score": consensus_score,
                "agent_inputs": agent_inputs,
                "reasoning": "Insufficient consensus, alternative resolution needed"
            }
    
    def _weighted_voting(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Resolve conflict through weighted voting"""
        
        votes = {}
        weights = {}
        
        for agent_id in conflict.conflicting_agents:
            if agent_id in agents:
                agent = agents[agent_id]
                
                # Get agent's vote (mock implementation)
                vote = self._get_agent_vote(agent, conflict)
                weight = self._calculate_agent_weight(agent)
                
                votes[agent_id] = vote
                weights[agent_id] = weight
        
        # Calculate weighted decision
        weighted_votes = {}
        for agent_id, vote in votes.items():
            weight = weights[agent_id]
            if vote not in weighted_votes:
                weighted_votes[vote] = 0
            weighted_votes[vote] += weight
        
        # Find winning vote
        winning_vote = max(weighted_votes, key=weighted_votes.get)
        
        return {
            "resolution": "weighted_voting",
            "winning_vote": winning_vote,
            "vote_weights": weighted_votes,
            "individual_votes": votes,
            "reasoning": f"Weighted voting result: {winning_vote}"
        }
    
    def _evidence_based_resolution(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Resolve conflict based on evidence strength"""
        
        evidence_scores = {}
        
        for agent_id in conflict.conflicting_agents:
            if agent_id in agents:
                agent = agents[agent_id]
                evidence_score = self._evaluate_agent_evidence(agent, conflict)
                evidence_scores[agent_id] = evidence_score
        
        # Select agent with strongest evidence
        best_agent = max(evidence_scores, key=evidence_scores.get)
        
        return {
            "resolution": "evidence_based",
            "selected_agent": best_agent,
            "evidence_scores": evidence_scores,
            "reasoning": f"Resolution based on evidence strength from {best_agent}"
        }
    
    def _performance_based_resolution(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Resolve conflict based on agent performance"""
        
        performance_scores = {}
        
        for agent_id in conflict.conflicting_agents:
            if agent_id in agents:
                agent = agents[agent_id]
                performance_score = self._calculate_performance_score(agent)
                performance_scores[agent_id] = performance_score
        
        # Select agent with best performance
        best_agent = max(performance_scores, key=performance_scores.get)
        
        return {
            "resolution": "performance_based",
            "selected_agent": best_agent,
            "performance_scores": performance_scores,
            "reasoning": f"Resolution based on performance of {best_agent}"
        }
    
    def _escalate_conflict(self, conflict: AgentConflict, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Escalate conflict to higher authority"""
        
        return {
            "resolution": "escalated",
            "escalation_level": "high",
            "conflict_severity": conflict.severity,
            "reasoning": "Conflict escalated due to high severity",
            "requires_human_intervention": True
        }
    
    def _calculate_consensus_score(self, agent_inputs: Dict[str, Any]) -> float:
        """Calculate consensus score from agent inputs"""
        if not agent_inputs:
            return 0.0
        
        # Mock consensus calculation
        confidences = [inp.get("conflict_assessment", {}).get("confidence", 0.5) for inp in agent_inputs.values()]
        return sum(confidences) / len(confidences)
    
    def _get_agent_vote(self, agent: Agent, conflict: AgentConflict) -> str:
        """Get agent's vote for conflict resolution"""
        # Mock voting - in real system would be based on agent's analysis
        return f"vote_{agent.agent_id}"
    
    def _calculate_agent_weight(self, agent: Agent) -> float:
        """Calculate agent's voting weight based on performance"""
        performance = agent.performance
        return (performance.quality_score + performance.average_confidence) / 2.0
    
    def _evaluate_agent_evidence(self, agent: Agent, conflict: AgentConflict) -> float:
        """Evaluate strength of agent's evidence"""
        # Mock evidence evaluation
        return agent.performance.quality_score
    
    def _calculate_performance_score(self, agent: Agent) -> float:
        """Calculate overall performance score for agent"""
        perf = agent.performance
        
        if perf.tasks_completed + perf.tasks_failed == 0:
            return 0.5
        
        success_rate = perf.tasks_completed / (perf.tasks_completed + perf.tasks_failed)
        
        return (success_rate + perf.average_confidence + perf.quality_score) / 3.0


class HierarchicalAgentSystem:
    """Complete hierarchical agent system with conflict resolution"""
    
    def __init__(self):
        """Initialize hierarchical agent system"""
        self.coordinator = CoordinatorAgent("coordinator_001")
        self.specialists = {}
        self.conflict_resolver = ConflictResolutionSystem()
        self.active_conflicts: List[AgentConflict] = []
        self.processing_history: List[Dict[str, Any]] = []
        
        # Initialize specialists
        self._initialize_specialists()
        
        # Register specialists with coordinator
        for specialist in self.specialists.values():
            self.coordinator.register_agent(specialist)
        
        logger.info("Hierarchical Agent System initialized with conflict resolution")
    
    def _initialize_specialists(self):
        """Initialize specialist agents"""
        
        # Validation specialist
        validation_specialist = SpecialistAgent(
            "validation_001", 
            AgentRole.VALIDATION_SPECIALIST, 
            "data_validation"
        )
        self.specialists[validation_specialist.agent_id] = validation_specialist
        
        # Enrichment specialist
        enrichment_specialist = SpecialistAgent(
            "enrichment_001", 
            AgentRole.ENRICHMENT_SPECIALIST, 
            "data_enrichment"
        )
        self.specialists[enrichment_specialist.agent_id] = enrichment_specialist
        
        # Assessment specialist
        assessment_specialist = SpecialistAgent(
            "assessment_001", 
            AgentRole.ASSESSMENT_SPECIALIST, 
            "risk_assessment"
        )
        self.specialists[assessment_specialist.agent_id] = assessment_specialist
        
        # Risk specialist
        risk_specialist = SpecialistAgent(
            "risk_001", 
            AgentRole.RISK_SPECIALIST, 
            "risk_analysis"
        )
        self.specialists[risk_specialist.agent_id] = risk_specialist
        
        # Compliance specialist
        compliance_specialist = SpecialistAgent(
            "compliance_001", 
            AgentRole.COMPLIANCE_SPECIALIST, 
            "compliance_checking"
        )
        self.specialists[compliance_specialist.agent_id] = compliance_specialist
    
    def process_with_hierarchy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input using hierarchical agent system"""
        
        logger.info("Starting hierarchical agent processing")
        
        # Create orchestration task
        orchestration_task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="orchestration",
            description="Orchestrate multi-agent underwriting process",
            priority=TaskPriority.CRITICAL,
            required_capabilities=[AgentCapability.PERFORMANCE_MONITORING],
            input_data=input_data
        )
        
        # Process through coordinator
        result = self.coordinator.process_task(orchestration_task)
        
        # Check for conflicts and resolve
        conflicts = self._detect_conflicts(result)
        for conflict in conflicts:
            resolution = self.conflict_resolver.resolve_conflict(conflict, self._get_all_agents())
            result["conflict_resolution"] = resolution
        
        # Record processing
        self.processing_history.append({
            "timestamp": datetime.now(),
            "input_data": input_data,
            "result": result,
            "conflicts_resolved": len(conflicts)
        })
        
        logger.info(f"Hierarchical processing completed: {result.get('final_decision', 'UNKNOWN')}")
        
        return result
    
    def _detect_conflicts(self, result: Dict[str, Any]) -> List[AgentConflict]:
        """Detect conflicts in processing results"""
        conflicts = []
        
        # Check for decision conflicts between agents
        agent_contributions = result.get("agent_contributions", {})
        
        if len(agent_contributions) > 1:
            # Check for confidence conflicts
            confidences = [contrib.get("confidence", 0.5) for contrib in agent_contributions.values()]
            max_confidence = max(confidences)
            min_confidence = min(confidences)
            
            if max_confidence - min_confidence > 0.4:
                conflict = AgentConflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.DECISION_DISAGREEMENT,
                    conflicting_agents=list(agent_contributions.keys()),
                    conflict_details={
                        "confidence_range": [min_confidence, max_confidence],
                        "agent_contributions": agent_contributions
                    },
                    severity=(max_confidence - min_confidence)
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _get_all_agents(self) -> Dict[str, Agent]:
        """Get all agents in the system"""
        all_agents = {"coordinator_001": self.coordinator}
        all_agents.update(self.specialists)
        return all_agents
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        
        all_agents = self._get_all_agents()
        
        # Aggregate performance metrics
        total_tasks = sum(agent.performance.tasks_completed + agent.performance.tasks_failed for agent in all_agents.values())
        total_completed = sum(agent.performance.tasks_completed for agent in all_agents.values())
        total_failed = sum(agent.performance.tasks_failed for agent in all_agents.values())
        
        average_confidence = sum(agent.performance.average_confidence for agent in all_agents.values()) / len(all_agents)
        average_processing_time = sum(agent.performance.average_processing_time for agent in all_agents.values()) / len(all_agents)
        
        return {
            "system_metrics": {
                "total_agents": len(all_agents),
                "total_tasks_processed": total_tasks,
                "success_rate": total_completed / total_tasks if total_tasks > 0 else 0.0,
                "average_confidence": average_confidence,
                "average_processing_time": average_processing_time,
                "conflicts_resolved": len(self.active_conflicts),
                "processing_sessions": len(self.processing_history)
            },
            "agent_performance": {
                agent_id: {
                    "role": agent.role.value,
                    "tasks_completed": agent.performance.tasks_completed,
                    "tasks_failed": agent.performance.tasks_failed,
                    "average_confidence": agent.performance.average_confidence,
                    "quality_score": agent.performance.quality_score
                }
                for agent_id, agent in all_agents.items()
            },
            "conflict_resolution_metrics": {
                "total_conflicts": len(self.active_conflicts),
                "resolution_strategies_used": list(set(conflict.resolution_strategy.value for conflict in self.active_conflicts if conflict.resolution_strategy)),
                "average_resolution_time": 0.0  # Mock metric
            }
        }


# Global hierarchical agent system instance
_global_hierarchical_system: Optional[HierarchicalAgentSystem] = None


def get_hierarchical_agent_system() -> HierarchicalAgentSystem:
    """Get global hierarchical agent system instance"""
    global _global_hierarchical_system
    if _global_hierarchical_system is None:
        _global_hierarchical_system = HierarchicalAgentSystem()
    return _global_hierarchical_system
