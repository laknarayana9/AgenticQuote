"""
Demonstration Scenarios and Performance Metrics
Comprehensive showcase of agentic AI capabilities for job search:

- End-to-end demonstration scenarios
- Performance metrics collection and analysis
- Capability comparison and benchmarking
- Interactive demonstration interface
- Real-time performance visualization
- Success metrics and KPIs
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import statistics
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class DemonstrationType(Enum):
    """Types of demonstration scenarios"""
    BASIC_UNDERWRITING = "basic_underwriting"
    COMPLEX_RISK_ASSESSMENT = "complex_risk_assessment"
    MULTI_MODAL_REASONING = "multi_modal_reasoning"
    ADAPTIVE_LEARNING = "adaptive_learning"
    HIERARCHICAL_AGENT_COORDINATION = "hierarchical_agent_coordination"
    CONFLICT_RESOLUTION = "conflict_resolution"
    REAL_TIME_MONITORING = "real_time_monitoring"


class DifficultyLevel(Enum):
    """Difficulty levels for scenarios"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class DemonstrationScenario:
    """Individual demonstration scenario"""
    scenario_id: str
    name: str
    description: str
    demo_type: DemonstrationType
    difficulty: DifficultyLevel
    estimated_duration: float  # minutes
    input_data: Dict[str, Any]
    expected_capabilities: List[str]
    success_criteria: Dict[str, Any]
    setup_function: Optional[Callable] = None
    cleanup_function: Optional[Callable] = None


@dataclass
class DemonstrationResult:
    """Result of demonstration execution"""
    scenario_id: str
    execution_id: str
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    capabilities_demonstrated: List[str]
    performance_metrics: Dict[str, float]
    detailed_results: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    user_feedback: Optional[Dict[str, Any]] = None


@dataclass
class CapabilityMetrics:
    """Metrics for specific capability"""
    capability_name: str
    execution_count: int = 0
    success_count: int = 0
    average_execution_time: float = 0.0
    average_confidence: float = 0.0
    user_satisfaction_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class DemonstrationOrchestrator:
    """Orchestrates demonstration scenarios"""
    
    def __init__(self):
        """Initialize demonstration orchestrator"""
        
        # Import all our systems
        from app.advanced_react import get_advanced_react_engine
        from app.hierarchical_agents import get_hierarchical_agent_system
        from app.adaptive_learning import get_adaptive_learning_system
        from app.multimodal_reasoning import get_multimodal_reasoning_system
        from app.observability import get_observability_system
        from app.testing_framework import get_testing_framework
        
        # Initialize systems
        self.react_engine = get_advanced_react_engine()
        self.agent_system = get_hierarchical_agent_system()
        self.learning_system = get_adaptive_learning_system()
        self.multimodal_system = get_multimodal_reasoning_system()
        self.observability_system = get_observability_system()
        self.testing_framework = get_testing_framework()
        
        # Scenarios
        self.scenarios: Dict[str, DemonstrationScenario] = {}
        self.execution_history: List[DemonstrationResult] = []
        
        # Capability metrics
        self.capability_metrics: Dict[str, CapabilityMetrics] = {}
        
        # Setup default scenarios
        self._setup_default_scenarios()
        
        logger.info("Demonstration orchestrator initialized")
    
    def register_scenario(self, scenario: DemonstrationScenario):
        """Register a demonstration scenario"""
        
        self.scenarios[scenario.scenario_id] = scenario
        logger.info(f"Registered demonstration scenario: {scenario.name}")
    
    def execute_scenario(self, scenario_id: str, user_context: Optional[Dict[str, Any]] = None) -> DemonstrationResult:
        """Execute a demonstration scenario"""
        
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario = self.scenarios[scenario_id]
        execution_id = str(uuid.uuid4())
        
        start_time = datetime.now()
        
        # Setup scenario
        if scenario.setup_function:
            try:
                scenario.setup_function(scenario.input_data)
            except Exception as e:
                logger.error(f"Scenario setup failed: {e}")
                return self._create_error_result(scenario, execution_id, start_time, str(e))
        
        try:
            logger.info(f"Executing demonstration scenario: {scenario.name}")
            
            # Execute based on scenario type
            if scenario.demo_type == DemonstrationType.BASIC_UNDERWRITING:
                detailed_results = self._execute_basic_underwriting(scenario, user_context)
            elif scenario.demo_type == DemonstrationType.COMPLEX_RISK_ASSESSMENT:
                detailed_results = self._execute_complex_risk_assessment(scenario, user_context)
            elif scenario.demo_type == DemonstrationType.MULTI_MODAL_REASONING:
                detailed_results = self._execute_multimodal_reasoning(scenario, user_context)
            elif scenario.demo_type == DemonstrationType.ADAPTIVE_LEARNING:
                detailed_results = self._execute_adaptive_learning(scenario, user_context)
            elif scenario.demo_type == DemonstrationType.HIERARCHICAL_AGENT_COORDINATION:
                detailed_results = self._execute_agent_coordination(scenario, user_context)
            elif scenario.demo_type == DemonstrationType.CONFLICT_RESOLUTION:
                detailed_results = self._execute_conflict_resolution(scenario, user_context)
            elif scenario.demo_type == DemonstrationType.REAL_TIME_MONITORING:
                detailed_results = self._execute_real_time_monitoring(scenario, user_context)
            else:
                raise ValueError(f"Unsupported scenario type: {scenario.demo_type}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Evaluate success
            success, capabilities_demonstrated = self._evaluate_scenario_success(scenario, detailed_results)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(detailed_results, duration)
            
            # Update capability metrics
            self._update_capability_metrics(capabilities_demonstrated, success, duration, detailed_results)
            
            result = DemonstrationResult(
                scenario_id=scenario_id,
                execution_id=execution_id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                capabilities_demonstrated=capabilities_demonstrated,
                performance_metrics=performance_metrics,
                detailed_results=detailed_results
            )
            
            self.execution_history.append(result)
            
            logger.info(f"Demonstration {scenario.name} completed: {'SUCCESS' if success else 'FAILED'}")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Demonstration execution failed: {e}")
            
            result = self._create_error_result(scenario, execution_id, start_time, str(e))
            result.duration = duration
            self.execution_history.append(result)
            
            return result
        
        finally:
            # Cleanup
            if scenario.cleanup_function:
                try:
                    scenario.cleanup_function(scenario.input_data)
                except Exception as e:
                    logger.warning(f"Scenario cleanup failed: {e}")
    
    def _execute_basic_underwriting(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute basic underwriting demonstration"""
        
        input_data = scenario.input_data
        
        # Use ReAct engine for basic underwriting
        react_result = self.react_engine.execute_advanced_react(
            query="Perform underwriting assessment",
            context=input_data,
            max_iterations=5
        )
        
        # Use agent system for comparison
        agent_result = self.agent_system.process_with_hierarchy(input_data)
        
        return {
            "react_result": {
                "decision": react_result.current_decision,
                "confidence": react_result.confidence_score,
                "iterations": react_result.iteration_count,
                "reasoning_summary": self.react_engine.get_comprehensive_summary(react_result)
            },
            "agent_result": {
                "decision": agent_result.get("final_decision"),
                "confidence": agent_result.get("confidence", 0.0),
                "agent_count": len(agent_result.get("agent_contributions", {})),
                "processing_summary": agent_result.get("processing_summary", {})
            },
            "comparison": {
                "decisions_match": react_result.current_decision == agent_result.get("final_decision"),
                "confidence_difference": abs(react_result.confidence_score - agent_result.get("confidence", 0.0))
            }
        }
    
    def _execute_complex_risk_assessment(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute complex risk assessment demonstration"""
        
        input_data = scenario.input_data
        
        # Enhanced ReAct reasoning with more iterations
        react_result = self.react_engine.execute_advanced_react(
            query="Perform comprehensive risk assessment with detailed analysis",
            context=input_data,
            max_iterations=10
        )
        
        # Multi-modal reasoning
        multimodal_result = self.multimodal_system.reason_multi_modal(
            query="Comprehensive risk assessment",
            text_data=input_data.get("text_description"),
            structured_data=input_data,
            rule_set=input_data.get("business_rules", {}),
            strategy=self.multimodal_system.ReasoningStrategy.UNCERTAINTY_AWARE
        )
        
        return {
            "advanced_react": {
                "decision": react_result.current_decision,
                "confidence": react_result.confidence_score,
                "iterations": react_result.iteration_count,
                "self_reflection_insights": len(react_result.learning_insights),
                "strategy_adjustments": len(react_result.strategy_adjustments)
            },
            "multimodal_analysis": {
                "conclusion": multimodal_result["conclusion"],
                "confidence": multimodal_result["confidence"],
                "reasoning_strategy": multimodal_result["strategy_used"],
                "modality_contributions": multimodal_result["modality_contributions"]
            },
            "risk_factors": {
                "identified_risks": self._extract_risk_factors(react_result),
                "risk_score": self._calculate_overall_risk_score(input_data),
                "mitigation_recommendations": self._generate_mitigation_recommendations(react_result)
            }
        }
    
    def _execute_multimodal_reasoning(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multi-modal reasoning demonstration"""
        
        input_data = scenario.input_data
        
        # Test all reasoning strategies
        from app.multimodal_reasoning import ReasoningStrategy
        strategies = [
            ReasoningStrategy.WEIGHTED_FUSION,
            ReasoningStrategy.HIERARCHICAL,
            ReasoningStrategy.CONSENSUS_BASED,
            ReasoningStrategy.UNCERTAINTY_AWARE,
            ReasoningStrategy.ADAPTIVE_SELECTION
        ]
        
        strategy_results = {}
        
        for strategy in strategies:
            result = self.multimodal_system.reason_multi_modal(
                query="Multi-modal underwriting analysis",
                text_data=input_data.get("text_description"),
                structured_data=input_data,
                rule_set=input_data.get("business_rules", {}),
                strategy=strategy
            )
            
            strategy_results[strategy.value] = {
                "conclusion": result["conclusion"],
                "confidence": result["confidence"],
                "evidence_count": len(result.get("evidence", [])),
                "uncertainty_factors": len(result.get("uncertainty_factors", []))
            }
        
        return {
            "strategy_comparison": strategy_results,
            "best_strategy": max(strategy_results, key=lambda k: strategy_results[k]["confidence"]),
            "modality_analysis": {
                "text_reasoning": strategy_results.get("weighted_fusion", {}).get("modality_contributions", {}).get("text", {}),
                "structured_reasoning": strategy_results.get("weighted_fusion", {}).get("modality_contributions", {}).get("structured", {}),
                "rule_reasoning": strategy_results.get("weighted_fusion", {}).get("modality_contributions", {}).get("rules", {})
            },
            "cross_modal_insights": self._analyze_cross_modal_insights(strategy_results)
        }
    
    def _execute_adaptive_learning(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute adaptive learning demonstration"""
        
        input_data = scenario.input_data
        
        # Initial prediction
        initial_prediction = self.learning_system.make_adaptive_prediction(input_data)
        
        # Simulate learning examples
        learning_examples = scenario.input_data.get("learning_examples", [])
        
        for example in learning_examples:
            self.learning_system.add_learning_example(
                input_data=example["input"],
                prediction=example["prediction"],
                actual_outcome=example["actual"],
                feedback=example["feedback"],
                feedback_type=example.get("feedback_type", "implicit")
            )
        
        # Perform learning
        learning_result = self.learning_system.learn_and_adapt()
        
        # Post-learning prediction
        post_learning_prediction = self.learning_system.make_adaptive_prediction(input_data)
        
        return {
            "initial_prediction": {
                "decision": initial_prediction["prediction"],
                "confidence": initial_prediction["confidence"],
                "reasoning": initial_prediction["reasoning"]
            },
            "learning_process": {
                "examples_processed": len(learning_examples),
                "adaptation_result": learning_result,
                "patterns_discovered": len(self.learning_system.pattern_recognition.patterns)
            },
            "improved_prediction": {
                "decision": post_learning_prediction["prediction"],
                "confidence": post_learning_prediction["confidence"],
                "reasoning": post_learning_prediction["reasoning"],
                "improvement": post_learning_prediction["confidence"] - initial_prediction["confidence"]
            },
            "learning_summary": self.learning_system.get_learning_summary()
        }
    
    def _execute_agent_coordination(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute hierarchical agent coordination demonstration"""
        
        input_data = scenario.input_data
        
        # Process with full agent system
        coordination_result = self.agent_system.process_with_hierarchy(input_data)
        
        # Get detailed agent performance
        system_performance = self.agent_system.get_system_performance()
        
        return {
            "coordination_result": {
                "final_decision": coordination_result.get("final_decision"),
                "confidence": coordination_result.get("confidence", 0.0),
                "processing_summary": coordination_result.get("processing_summary", {}),
                "conflict_resolution": coordination_result.get("conflict_resolution", {})
            },
            "agent_performance": {
                "total_agents": system_performance["system_metrics"]["total_agents"],
                "success_rate": system_performance["system_metrics"]["success_rate"],
                "average_confidence": system_performance["system_metrics"]["average_confidence"],
                "conflicts_resolved": system_performance["system_metrics"]["conflicts_resolved"]
            },
            "individual_agents": system_performance["agent_performance"],
            "coordination_insights": self._analyze_coordination_insights(coordination_result, system_performance)
        }
    
    def _execute_conflict_resolution(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute conflict resolution demonstration"""
        
        input_data = scenario.input_data
        
        # Create conflicting scenario
        conflicting_input = input_data.copy()
        conflicting_input["force_conflict"] = True
        
        # Process with conflict detection
        coordination_result = self.agent_system.process_with_hierarchy(conflicting_input)
        
        return {
            "conflict_scenario": {
                "conflict_detected": "conflict_resolution" in coordination_result,
                "conflict_details": coordination_result.get("conflict_resolution", {}),
                "resolution_strategy": coordination_result.get("conflict_resolution", {}).get("resolution_strategy")
            },
            "resolution_process": {
                "conflicting_agents": coordination_result.get("conflict_resolution", {}).get("conflicting_agents", []),
                "resolution_result": coordination_result.get("conflict_resolution", {}).get("resolution_result", {}),
                "resolution_success": coordination_result.get("conflict_resolution", {}).get("status") == "resolved"
            },
            "system_robustness": {
                "final_decision_stable": coordination_result.get("final_decision") is not None,
                "confidence_maintained": coordination_result.get("confidence", 0.0) > 0.3,
                "processing_completed": "processing_summary" in coordination_result
            }
        }
    
    def _execute_real_time_monitoring(self, scenario: DemonstrationScenario, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute real-time monitoring demonstration"""
        
        # Start monitoring
        self.observability_system.start_monitoring()
        
        # Collect metrics during processing
        initial_metrics = self.observability_system.collect_all_metrics()
        
        # Process some test cases
        test_cases = scenario.input_data.get("test_cases", [])
        processing_results = []
        
        for i, test_case in enumerate(test_cases):
            # Simulate processing
            start_time = time.time()
            
            if test_case.get("use_react", False):
                result = self.react_engine.execute_advanced_react(
                    query=f"Monitoring test case {i}",
                    context=test_case,
                    max_iterations=3
                )
            else:
                result = self.agent_system.process_with_hierarchy(test_case)
            
            processing_results.append({
                "case_id": i,
                "processing_time": time.time() - start_time,
                "success": result is not None
            })
            
            # Collect metrics after each case
            current_metrics = self.observability_system.collect_all_metrics()
        
        # Final metrics collection
        final_metrics = self.observability_system.collect_all_metrics()
        
        # Get dashboard data
        dashboard_data = self.observability_system.get_dashboard_data()
        
        # Stop monitoring
        self.observability_system.stop_monitoring()
        
        return {
            "monitoring_summary": {
                "test_cases_processed": len(test_cases),
                "average_processing_time": statistics.mean([r["processing_time"] for r in processing_results]),
                "success_rate": sum(1 for r in processing_results if r["success"]) / len(processing_results)
            },
            "metrics_collected": {
                "initial_metrics_count": len(initial_metrics),
                "final_metrics_count": len(final_metrics),
                "metrics_growth": len(final_metrics) - len(initial_metrics)
            },
            "dashboard_data": dashboard_data,
            "system_health": dashboard_data.get("system_health", {}),
            "active_alerts": dashboard_data.get("active_alerts", []),
            "performance_summary": dashboard_data.get("performance", {})
        }
    
    def _evaluate_scenario_success(self, scenario: DemonstrationScenario, results: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Evaluate if scenario execution was successful"""
        
        success = True
        capabilities_demonstrated = []
        
        # Check expected capabilities
        for capability in scenario.expected_capabilities:
            if capability in results:
                capability_result = results[capability]
                
                # Basic success check
                if isinstance(capability_result, dict):
                    if "decision" in capability_result or "conclusion" in capability_result:
                        capabilities_demonstrated.append(capability)
                    elif "success" in capability_result and capability_result["success"]:
                        capabilities_demonstrated.append(capability)
                elif capability_result is not None:
                    capabilities_demonstrated.append(capability)
            else:
                success = False
        
        # Check success criteria
        success_criteria = scenario.success_criteria
        
        if "min_confidence" in success_criteria:
            # Extract confidence from results
            confidences = []
            for key, value in results.items():
                if isinstance(value, dict) and "confidence" in value:
                    confidences.append(value["confidence"])
            
            if confidences:
                avg_confidence = statistics.mean(confidences)
                if avg_confidence < success_criteria["min_confidence"]:
                    success = False
        
        if "max_execution_time" in success_criteria:
            # Check execution time (would need to be passed in results)
            pass  # Implementation depends on specific scenario
        
        return success, capabilities_demonstrated
    
    def _calculate_performance_metrics(self, results: Dict[str, Any], duration: float) -> Dict[str, float]:
        """Calculate performance metrics for scenario execution"""
        
        metrics = {
            "execution_time": duration,
            "throughput": 1.0 / duration if duration > 0 else 0.0
        }
        
        # Extract confidence metrics
        confidences = []
        for key, value in results.items():
            if isinstance(value, dict):
                if "confidence" in value:
                    confidences.append(value["confidence"])
                elif "react_result" in value and isinstance(value["react_result"], dict):
                    confidences.append(value["react_result"].get("confidence", 0.0))
                elif "agent_result" in value and isinstance(value["agent_result"], dict):
                    confidences.append(value["agent_result"].get("confidence", 0.0))
        
        if confidences:
            metrics["average_confidence"] = statistics.mean(confidences)
            metrics["confidence_variance"] = statistics.variance(confidences) if len(confidences) > 1 else 0.0
        
        # Count capabilities demonstrated
        capabilities_count = sum(1 for key, value in results.items() if value is not None)
        metrics["capabilities_demonstrated"] = capabilities_count
        
        return metrics
    
    def _update_capability_metrics(self, capabilities: List[str], success: bool, duration: float, results: Dict[str, Any]):
        """Update capability performance metrics"""
        
        for capability in capabilities:
            if capability not in self.capability_metrics:
                self.capability_metrics[capability] = CapabilityMetrics(capability_name=capability)
            
            metrics = self.capability_metrics[capability]
            metrics.execution_count += 1
            
            if success:
                metrics.success_count += 1
            
            # Update average execution time
            metrics.average_execution_time = (
                (metrics.average_execution_time * (metrics.execution_count - 1) + duration) / 
                metrics.execution_count
            )
            
            # Update average confidence
            confidences = []
            for key, value in results.items():
                if isinstance(value, dict) and "confidence" in value:
                    confidences.append(value["confidence"])
            
            if confidences:
                avg_confidence = statistics.mean(confidences)
                metrics.average_confidence = (
                    (metrics.average_confidence * (metrics.execution_count - 1) + avg_confidence) / 
                    metrics.execution_count
                )
            
            metrics.last_updated = datetime.now()
    
    def _create_error_result(self, scenario: DemonstrationScenario, execution_id: str, start_time: datetime, error_message: str) -> DemonstrationResult:
        """Create error result for failed scenario"""
        
        return DemonstrationResult(
            scenario_id=scenario.scenario_id,
            execution_id=execution_id,
            start_time=start_time,
            end_time=datetime.now(),
            duration=0.0,
            success=False,
            capabilities_demonstrated=[],
            performance_metrics={},
            detailed_results={},
            errors=[error_message]
        )
    
    def _extract_risk_factors(self, react_result) -> List[str]:
        """Extract risk factors from ReAct result"""
        
        risk_factors = []
        
        # Extract from reasoning chain
        for thought in react_result.thoughts:
            if "risk" in thought.content.lower():
                risk_factors.append(thought.content)
        
        return risk_factors
    
    def _calculate_overall_risk_score(self, input_data: Dict[str, Any]) -> float:
        """Calculate overall risk score"""
        
        risk_score = 0.3  # Base risk
        
        # Property age factor
        if "construction_year" in input_data:
            age = 2024 - input_data["construction_year"]
            risk_score += min(0.4, age / 50)
        
        # Coverage factor
        if "coverage_amount" in input_data:
            coverage = input_data["coverage_amount"]
            risk_score += min(0.3, coverage / 1000000)
        
        # Location factor
        if "state" in input_data and input_data["state"] == "CA":
            risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _generate_mitigation_recommendations(self, react_result) -> List[str]:
        """Generate mitigation recommendations"""
        
        recommendations = []
        
        # Extract from strategy adjustments
        for adjustment in react_result.strategy_adjustments:
            if "recommendation" in adjustment:
                recommendations.append(adjustment["recommendation"])
        
        return recommendations
    
    def _analyze_cross_modal_insights(self, strategy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cross-modal reasoning insights"""
        
        insights = {
            "strategy_consensus": 0.0,
            "confidence_variance": 0.0,
            "best_performing_strategy": None,
            "strategy_diversity": len(strategy_results)
        }
        
        if strategy_results:
            confidences = [result["confidence"] for result in strategy_results.values()]
            
            insights["confidence_variance"] = statistics.variance(confidences) if len(confidences) > 1 else 0.0
            insights["best_performing_strategy"] = max(strategy_results, key=lambda k: strategy_results[k]["confidence"])
            
            # Calculate consensus (how close confidences are)
            if len(confidences) > 1:
                max_conf = max(confidences)
                min_conf = min(confidences)
                consensus = 1.0 - (max_conf - min_conf)
                insights["strategy_consensus"] = consensus
        
        return insights
    
    def _analyze_coordination_insights(self, coordination_result: Dict[str, Any], system_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent coordination insights"""
        
        return {
            "coordination_efficiency": system_performance["system_metrics"]["success_rate"],
            "agent_utilization": len(coordination_result.get("agent_contributions", {})),
            "conflict_resolution_effectiveness": 1.0 if coordination_result.get("conflict_resolution", {}).get("status") == "resolved" else 0.0,
            "decision_quality": coordination_result.get("confidence", 0.0)
        }
    
    def get_demonstration_summary(self) -> Dict[str, Any]:
        """Get comprehensive demonstration summary"""
        
        if not self.execution_history:
            return {"status": "no_executions"}
        
        # Overall statistics
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for result in self.execution_history if result.success)
        success_rate = successful_executions / total_executions
        
        # Performance statistics
        execution_times = [result.duration for result in self.execution_history]
        avg_execution_time = statistics.mean(execution_times)
        
        # Capability statistics
        capability_stats = {}
        for capability, metrics in self.capability_metrics.items():
            capability_stats[capability] = {
                "execution_count": metrics.execution_count,
                "success_rate": metrics.success_count / metrics.execution_count if metrics.execution_count > 0 else 0.0,
                "average_confidence": metrics.average_confidence,
                "average_execution_time": metrics.average_execution_time
            }
        
        # Recent executions
        recent_executions = self.execution_history[-5:]
        
        return {
            "overall_statistics": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "capabilities_demonstrated": len(self.capability_metrics)
            },
            "capability_performance": capability_stats,
            "registered_scenarios": [
                {
                    "scenario_id": scenario_id,
                    "name": scenario.name,
                    "type": scenario.demo_type.value,
                    "difficulty": scenario.difficulty.value
                }
                for scenario_id, scenario in self.scenarios.items()
            ],
            "recent_executions": [
                {
                    "scenario_id": result.scenario_id,
                    "execution_id": result.execution_id,
                    "success": result.success,
                    "duration": result.duration,
                    "capabilities": len(result.capabilities_demonstrated),
                    "timestamp": result.start_time.isoformat()
                }
                for result in recent_executions
            ],
            "performance_trends": self._analyze_performance_trends()
        }
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        
        if len(self.execution_history) < 3:
            return {"status": "insufficient_data"}
        
        # Split history into halves
        mid_point = len(self.execution_history) // 2
        early_executions = self.execution_history[:mid_point]
        recent_executions = self.execution_history[mid_point:]
        
        # Calculate trends
        early_success_rate = sum(1 for r in early_executions if r.success) / len(early_executions)
        recent_success_rate = sum(1 for r in recent_executions if r.success) / len(recent_executions)
        
        early_avg_time = statistics.mean([r.duration for r in early_executions])
        recent_avg_time = statistics.mean([r.duration for r in recent_executions])
        
        return {
            "success_rate_trend": recent_success_rate - early_success_rate,
            "execution_time_trend": recent_avg_time - early_avg_time,
            "improving": recent_success_rate > early_success_rate and recent_avg_time < early_avg_time
        }
    
    def _setup_default_scenarios(self):
        """Setup default demonstration scenarios"""
        
        # Basic underwriting scenario
        basic_scenario = DemonstrationScenario(
            scenario_id="basic_underwriting_001",
            name="Basic HO3 Underwriting",
            description="Demonstrates basic underwriting capabilities using ReAct and agent systems",
            demo_type=DemonstrationType.BASIC_UNDERWRITING,
            difficulty=DifficultyLevel.BASIC,
            estimated_duration=2.0,
            input_data={
                "property": {
                    "address": "123 Main St, San Diego, CA",
                    "state": "CA",
                    "year_built": 1998,
                    "roof_age": 10,
                    "roof_material": "composite",
                    "occupancy": "owner_occupied"
                },
                "applicant": {
                    "prior_claims": 1,
                    "credit_score": 750
                },
                "coverage": {
                    "dwelling_limit": 500000,
                    "deductible": 2500
                }
            },
            expected_capabilities=["react_result", "agent_result", "comparison"],
            success_criteria={
                "min_confidence": 0.6,
                "max_execution_time": 30.0
            }
        )
        
        # Complex risk assessment scenario
        complex_scenario = DemonstrationScenario(
            scenario_id="complex_risk_001",
            name="Complex Risk Assessment",
            description="Demonstrates advanced risk assessment with multi-modal reasoning",
            demo_type=DemonstrationType.COMPLEX_RISK_ASSESSMENT,
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=5.0,
            input_data={
                "property": {
                    "address": "456 Oak Ave, Malibu, CA",
                    "state": "CA",
                    "year_built": 1960,
                    "roof_age": 25,
                    "roof_material": "wood",
                    "occupancy": "owner_occupied"
                },
                "text_description": "Property located in high wildfire risk area with aging wood roof",
                "business_rules": {
                    "wildfire_risk_threshold": 0.7,
                    "roof_age_limit": 20
                }
            },
            expected_capabilities=["advanced_react", "multimodal_analysis", "risk_factors"],
            success_criteria={
                "min_confidence": 0.5,
                "max_execution_time": 60.0
            }
        )
        
        # Multi-modal reasoning scenario
        multimodal_scenario = DemonstrationScenario(
            scenario_id="multimodal_001",
            name="Multi-Modal Reasoning",
            description="Demonstrates reasoning across text, structured data, and rules",
            demo_type=DemonstrationType.MULTI_MODAL_REASONING,
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=3.0,
            input_data={
                "text_description": "Applicant requesting coverage for coastal property with hurricane exposure",
                "structured_data": {
                    "property": {
                        "address": "789 Beach Rd, Miami, FL",
                        "state": "FL",
                        "year_built": 2015,
                        "coverage_amount": 800000
                    }
                },
                "business_rules": {
                    "coastal_requirements": True,
                    "hurricane_zone": True
                }
            },
            expected_capabilities=["strategy_comparison", "modality_analysis", "cross_modal_insights"],
            success_criteria={
                "min_confidence": 0.6,
                "max_execution_time": 45.0
            }
        )
        
        # Adaptive learning scenario
        learning_scenario = DemonstrationScenario(
            scenario_id="adaptive_learning_001",
            name="Adaptive Learning System",
            description="Demonstrates continuous learning and improvement",
            demo_type=DemonstrationType.ADAPTIVE_LEARNING,
            difficulty=DifficultyLevel.EXPERT,
            estimated_duration=4.0,
            input_data={
                "property": {
                    "address": "321 Test St, Austin, TX",
                    "state": "TX",
                    "year_built": 2010,
                    "coverage_amount": 400000
                },
                "learning_examples": [
                    {
                        "input": {"property": {"state": "TX", "coverage_amount": 300000}},
                        "prediction": {"prediction": "ACCEPT", "confidence": 0.7},
                        "actual": {"decision": "ACCEPT"},
                        "feedback": {"score": 0.8}
                    },
                    {
                        "input": {"property": {"state": "FL", "coverage_amount": 800000}},
                        "prediction": {"prediction": "REFER", "confidence": 0.6},
                        "actual": {"decision": "REFER"},
                        "feedback": {"score": 0.9}
                    }
                ]
            },
            expected_capabilities=["initial_prediction", "learning_process", "improved_prediction"],
            success_criteria={
                "min_confidence": 0.5,
                "improvement_threshold": 0.1
            }
        )
        
        # Register all scenarios
        for scenario in [basic_scenario, complex_scenario, multimodal_scenario, learning_scenario]:
            self.register_scenario(scenario)


# Global demonstration orchestrator instance
_global_demonstration_orchestrator: Optional[DemonstrationOrchestrator] = None


def get_demonstration_orchestrator() -> DemonstrationOrchestrator:
    """Get global demonstration orchestrator instance"""
    global _global_demonstration_orchestrator
    if _global_demonstration_orchestrator is None:
        _global_demonstration_orchestrator = DemonstrationOrchestrator()
    return _global_demonstration_orchestrator
