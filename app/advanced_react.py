"""
Advanced ReAct Engine with Dynamic Tool Selection
Implements sophisticated reasoning with self-reflection and adaptive planning

This is the core agentic system that demonstrates:
- Dynamic tool selection based on reasoning
- Self-reflection and meta-cognitive capabilities  
- Adaptive planning and replanning
- Multi-modal reasoning integration
- Explainable AI with reasoning chains
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ReActStepType(Enum):
    """Types of ReAct reasoning steps"""
    THOUGHT = "thought"
    ACTION = "action" 
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    REPLAN = "replan"


class ToolCategory(Enum):
    """Categories of tools for dynamic selection"""
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    RETRIEVAL = "retrieval"
    ASSESSMENT = "assessment"
    VERIFICATION = "verification"
    PLANNING = "planning"
    MONITORING = "monitoring"


class ConfidenceLevel(Enum):
    """Confidence levels for decision making"""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class ReasoningContext:
    """Context for reasoning decisions"""
    current_goal: str
    evidence_quality: float
    tool_performance_history: Dict[str, float]
    domain_constraints: Dict[str, Any]
    previous_outcomes: List[Dict[str, Any]]
    iteration_context: int


@dataclass
class ReActThought:
    """Enhanced reasoning step with self-reflection"""
    step_id: str
    step_type: ReActStepType
    content: str
    confidence: float
    reasoning_type: str  # 'deductive', 'inductive', 'abductive', 'analogical'
    tool_selected: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    observation_result: Optional[Dict[str, Any]] = None
    reflection_score: Optional[float] = None
    reflection_reasoning: Optional[str] = None
    next_step_reasoning: Optional[str] = None
    evidence_cited: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with full reasoning chain"""
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "reasoning_type": self.reasoning_type,
            "tool_selected": self.tool_selected,
            "tool_input": self.tool_input,
            "observation_result": self.observation_result,
            "reflection_score": self.reflection_score,
            "reflection_reasoning": self.reflection_reasoning,
            "next_step_reasoning": self.next_step_reasoning,
            "evidence_cited": self.evidence_cited,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass 
class AdvancedReActState:
    """Enhanced state with meta-cognitive tracking"""
    original_query: str
    current_goal: str
    context: Dict[str, Any]
    thoughts: List[ReActThought] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    evidence_collected: List[Dict[str, Any]] = field(default_factory=list)
    current_decision: Optional[str] = None
    confidence_score: float = 0.0
    iteration_count: int = 0
    max_iterations: int = 15
    completed: bool = False
    completion_reason: Optional[str] = None
    
    # Meta-cognitive tracking
    self_reflection_history: List[Dict[str, Any]] = field(default_factory=list)
    strategy_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    learning_insights: List[str] = field(default_factory=list)


class ToolSelector(ABC):
    """Abstract base class for tool selection strategies"""
    
    @abstractmethod
    def select_tool(
        self, 
        context: ReasoningContext, 
        available_tools: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, Any], float]:
        """Select best tool for current context"""
        pass


class DynamicToolSelector(ToolSelector):
    """Dynamic tool selection based on context and performance"""
    
    def __init__(self):
        self.tool_performance = {}
        self.context_patterns = {}
    
    def select_tool(
        self, 
        context: ReasoningContext, 
        available_tools: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, Any], float]:
        """Select tool using multi-factor scoring"""
        
        tool_scores = {}
        
        for tool_name, tool_info in available_tools.items():
            score = self._calculate_tool_score(tool_name, tool_info, context)
            tool_scores[tool_name] = score
        
        if not tool_scores:
            return None, {}, 0.0
        
        # Select best tool
        best_tool = max(tool_scores, key=tool_scores.get)
        confidence = tool_scores[best_tool]
        
        # Prepare tool input
        tool_input = self._prepare_tool_input(best_tool, available_tools[best_tool], context)
        
        return best_tool, tool_input, confidence
    
    def _calculate_tool_score(
        self, 
        tool_name: str, 
        tool_info: Dict[str, Any], 
        context: ReasoningContext
    ) -> float:
        """Calculate tool selection score"""
        
        base_score = 0.5
        
        # Performance history factor
        performance_factor = context.tool_performance_history.get(tool_name, 0.7)
        
        # Context relevance factor
        relevance_factor = self._calculate_context_relevance(tool_info, context)
        
        # Novelty factor (avoid overusing same tools)
        usage_count = sum(1 for tool in context.previous_outcomes if tool.get("tool") == tool_name)
        novelty_factor = max(0.3, 1.0 - (usage_count * 0.1))
        
        # Evidence quality factor
        evidence_factor = min(1.0, context.evidence_quality + 0.2)
        
        # Combine factors
        final_score = base_score * performance_factor * relevance_factor * novelty_factor * evidence_factor
        
        return max(0.1, min(0.95, final_score))
    
    def _calculate_context_relevance(self, tool_info: Dict[str, Any], context: ReasoningContext) -> float:
        """Calculate how relevant tool is to current context"""
        
        tool_category = tool_info.get("category", "")
        current_goal = context.current_goal.lower()
        
        # Category-goal matching
        if "validation" in current_goal and tool_category == "validation":
            return 0.9
        elif "enrich" in current_goal and tool_category == "enrichment":
            return 0.9
        elif "assess" in current_goal and tool_category == "assessment":
            return 0.9
        elif "retrieve" in current_goal and tool_category == "retrieval":
            return 0.9
        elif "verify" in current_goal and tool_category == "verification":
            return 0.9
        
        # Generic relevance
        return 0.6
    
    def _prepare_tool_input(self, tool_name: str, tool_info: Dict[str, Any], context: ReasoningContext) -> Dict[str, Any]:
        """Prepare input for selected tool"""
        
        base_input = {
            "context": context.domain_constraints,
            "evidence": context.previous_outcomes,
            "goal": context.current_goal
        }
        
        # Add tool-specific requirements
        required_fields = tool_info.get("required_fields", [])
        for field in required_fields:
            if field in context.domain_constraints:
                base_input[field] = context.domain_constraints[field]
        
        return base_input


class SelfReflectionSystem:
    """Self-reflection and meta-cognitive capabilities"""
    
    def __init__(self):
        self.reflection_patterns = {}
        self.learning_history = []
    
    def reflect_on_thought(
        self, 
        thought: ReActThought, 
        context: ReasoningContext,
        previous_thoughts: List[ReActThought]
    ) -> Tuple[float, str]:
        """Perform self-reflection on reasoning step"""
        
        reflection_score = 0.7  # Base score
        reflection_reasoning = []
        
        # Analyze reasoning quality
        reasoning_quality = self._analyze_reasoning_quality(thought, previous_thoughts)
        reflection_score *= reasoning_quality
        reflection_reasoning.append(f"Reasoning quality: {reasoning_quality:.2f}")
        
        # Analyze tool selection appropriateness
        if thought.tool_selected:
            tool_appropriateness = self._analyze_tool_selection(thought, context)
            reflection_score *= tool_appropriateness
            reflection_reasoning.append(f"Tool appropriateness: {tool_appropriateness:.2f}")
        
        # Analyze confidence calibration
        confidence_calibration = self._analyze_confidence_calibration(thought, context)
        reflection_score *= confidence_calibration
        reflection_reasoning.append(f"Confidence calibration: {confidence_calibration:.2f}")
        
        # Analyze evidence usage
        evidence_quality = self._analyze_evidence_usage(thought, context)
        reflection_score *= evidence_quality
        reflection_reasoning.append(f"Evidence quality: {evidence_quality:.2f}")
        
        # Generate insights
        insights = self._generate_insights(thought, reflection_score, context)
        reflection_reasoning.extend(insights)
        
        final_reasoning = "; ".join(reflection_reasoning)
        
        return max(0.1, min(0.95, reflection_score)), final_reasoning
    
    def _analyze_reasoning_quality(self, thought: ReActThought, previous_thoughts: List[ReActThought]) -> float:
        """Analyze quality of reasoning"""
        
        # Check reasoning type appropriateness
        reasoning_type_scores = {
            "deductive": 0.8,
            "inductive": 0.7,
            "abductive": 0.6,
            "analogical": 0.5
        }
        
        base_score = reasoning_type_scores.get(thought.reasoning_type, 0.5)
        
        # Check for logical consistency
        if previous_thoughts:
            consistency = self._check_logical_consistency(thought, previous_thoughts[-1])
            base_score *= consistency
        
        return base_score
    
    def _analyze_tool_selection(self, thought: ReActThought, context: ReasoningContext) -> float:
        """Analyze appropriateness of tool selection"""
        
        if not thought.tool_selected:
            return 0.5
        
        # Check if tool matches goal
        goal_relevance = self._check_goal_tool_match(thought.tool_selected, context.current_goal)
        
        # Check performance history
        performance = context.tool_performance_history.get(thought.tool_selected, 0.7)
        
        return (goal_relevance + performance) / 2
    
    def _analyze_confidence_calibration(self, thought: ReActThought, context: ReasoningContext) -> float:
        """Analyze if confidence is well-calibrated"""
        
        # Base confidence on evidence quality
        expected_confidence = context.evidence_quality
        
        # Calculate calibration error
        calibration_error = abs(thought.confidence - expected_confidence)
        
        # Convert to score (lower error = higher score)
        calibration_score = max(0.3, 1.0 - calibration_error)
        
        return calibration_score
    
    def _analyze_evidence_usage(self, thought: ReActThought, context: ReasoningContext) -> float:
        """Analyze quality of evidence usage"""
        
        if not thought.evidence_cited:
            return 0.4  # No evidence cited
        
        # Check evidence relevance
        relevant_evidence = sum(1 for evidence in thought.evidence_cited if self._is_evidence_relevant(evidence, context.current_goal))
        
        evidence_score = relevant_evidence / len(thought.evidence_cited) if thought.evidence_cited else 0.5
        
        return evidence_score
    
    def _check_logical_consistency(self, current: ReActThought, previous: ReActThought) -> float:
        """Check logical consistency between consecutive thoughts"""
        
        # Simple consistency check - can be enhanced
        if previous.next_step_reasoning and current.content:
            # Check if current thought addresses previous reasoning
            if any(word in current.content.lower() for word in previous.next_step_reasoning.lower().split()):
                return 0.8
        
        return 0.6
    
    def _check_goal_tool_match(self, tool: str, goal: str) -> float:
        """Check if tool matches current goal"""
        
        goal_lower = goal.lower()
        tool_lower = tool.lower()
        
        # Simple keyword matching
        if "validate" in goal_lower and "validate" in tool_lower:
            return 0.9
        elif "enrich" in goal_lower and "enrich" in tool_lower:
            return 0.9
        elif "assess" in goal_lower and "assess" in tool_lower:
            return 0.9
        elif "retrieve" in goal_lower and "retrieve" in tool_lower:
            return 0.9
        
        return 0.5
    
    def _is_evidence_relevant(self, evidence: str, goal: str) -> bool:
        """Check if evidence is relevant to goal"""
        
        # Simple relevance check
        goal_words = set(goal.lower().split())
        evidence_words = set(evidence.lower().split())
        
        # Check for word overlap
        overlap = goal_words.intersection(evidence_words)
        return len(overlap) > 0
    
    def _generate_insights(self, thought: ReActThought, reflection_score: float, context: ReasoningContext) -> List[str]:
        """Generate learning insights from reflection"""
        
        insights = []
        
        if reflection_score < 0.5:
            insights.append("Low reflection score indicates need for strategy adjustment")
        
        if thought.confidence > 0.8 and reflection_score < 0.6:
            insights.append("Overconfidence detected - consider more evidence")
        
        if thought.tool_selected and context.tool_performance_history.get(thought.tool_selected, 0) < 0.5:
            insights.append(f"Tool {thought.tool_selected} has poor performance history")
        
        return insights


class AdvancedReActEngine:
    """
    Advanced ReAct Engine with Self-Reflection and Dynamic Tool Selection
    
    This engine demonstrates sophisticated agentic capabilities:
    - Dynamic tool selection based on context and performance
    - Self-reflection and meta-cognitive monitoring
    - Adaptive planning and replanning
    - Multi-modal reasoning integration
    - Explainable AI with detailed reasoning chains
    """
    
    def __init__(self, tool_registry: Optional[Dict[str, Any]] = None):
        """Initialize advanced ReAct engine"""
        self.tool_registry = tool_registry or {}
        self.tool_selector = DynamicToolSelector()
        self.reflection_system = SelfReflectionSystem()
        
        # Performance tracking
        self.reasoning_history: List[AdvancedReActState] = []
        self.global_performance_metrics = {
            "total_reasoning_sessions": 0,
            "average_confidence": 0.0,
            "average_iterations": 0.0,
            "success_rate": 0.0
        }
        
        logger.info("Advanced ReAct Engine initialized with self-reflection capabilities")
    
    def execute_advanced_react(
        self, 
        query: str, 
        context: Dict[str, Any],
        max_iterations: Optional[int] = None
    ) -> AdvancedReActState:
        """
        Execute advanced ReAct loop with self-reflection
        
        Args:
            query: Initial query or problem
            context: Domain context and constraints
            max_iterations: Maximum reasoning iterations
            
        Returns:
            Complete reasoning state with full self-reflection
        """
        logger.info(f"Starting advanced ReAct reasoning: {query}")
        
        # Initialize enhanced state
        state = AdvancedReActState(
            original_query=query,
            current_goal=self._extract_initial_goal(query, context),
            context=context,
            max_iterations=max_iterations or 15
        )
        
        # Execute iterative reasoning with self-reflection
        while not state.completed and state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            logger.info(f"Advanced ReAct iteration {state.iteration_count}/{state.max_iterations}")
            
            # Build reasoning context
            reasoning_context = self._build_reasoning_context(state)
            
            # THOUGHT phase with dynamic tool selection
            thought = self._generate_advanced_thought(reasoning_context, state)
            state.thoughts.append(thought)
            
            # REFLECTION phase (self-reflection)
            reflection_score, reflection_reasoning = self.reflection_system.reflect_on_thought(
                thought, reasoning_context, state.thoughts[:-1]
            )
            thought.reflection_score = reflection_score
            thought.reflection_reasoning = reflection_reasoning
            
            # Initialize observation for this iteration
            observation = {"reasoning": "No action executed in this iteration"}
            
            # ACTION phase with dynamic tool execution
            if thought.tool_selected and thought.tool_selected in self.tool_registry:
                action_result = self._execute_dynamic_action(thought, reasoning_context)
                thought.observation_result = action_result
                
                # OBSERVATION phase with enhanced processing
                observation = self._process_advanced_observation(action_result, reasoning_context, state)
                thought.next_step_reasoning = observation["reasoning"]
                
                # Update tool performance
                self._update_tool_performance(thought.tool_selected, action_result, reasoning_context)
            
            # REPLAN phase with adaptive strategy
            should_continue, new_goal, strategy_adjustment = self._adaptive_replanning(
                observation, 
                state, 
                reasoning_context
            )
            
            if strategy_adjustment:
                state.strategy_adjustments.append(strategy_adjustment)
            
            if not should_continue:
                state.completed = True
                state.completion_reason = observation.get("completion_reason", "Replanning indicated completion")
                break
            elif new_goal:
                state.current_goal = new_goal
        
        # Final decision synthesis with meta-cognitive analysis
        if not state.completed:
            state.completed = True
            state.completion_reason = "Maximum iterations reached"
            state.current_decision, state.confidence_score = self._synthesize_meta_cognitive_decision(state)
        
        # Calculate performance metrics
        state.performance_metrics = self._calculate_performance_metrics(state)
        
        # Store in history
        self.reasoning_history.append(state)
        self._update_global_metrics(state)
        
        logger.info(f"Advanced ReAct completed: {state.current_decision} (confidence: {state.confidence_score:.3f})")
        logger.info(f"Self-reflection insights: {len(state.learning_insights)} generated")
        
        return state
    
    def _build_reasoning_context(self, state: AdvancedReActState) -> ReasoningContext:
        """Build comprehensive reasoning context"""
        
        return ReasoningContext(
            current_goal=state.current_goal,
            evidence_quality=self._calculate_evidence_quality(state),
            tool_performance_history=self.tool_selector.tool_performance,
            domain_constraints=state.context,
            previous_outcomes=[thought.observation_result for thought in state.thoughts if thought.observation_result],
            iteration_context=state.iteration_count
        )
    
    def _generate_advanced_thought(self, context: ReasoningContext, state: AdvancedReActState) -> ReActThought:
        """Generate advanced reasoning thought with dynamic tool selection"""
        
        step_id = f"thought_{state.iteration_count}"
        
        # Select tool dynamically
        selected_tool, tool_input, confidence = self.tool_selector.select_tool(
            context, self.tool_registry
        )
        
        # Determine reasoning type
        reasoning_type = self._select_reasoning_type(context, state)
        
        # Generate reasoning content
        thought_content = self._generate_advanced_reasoning_content(
            context, selected_tool, reasoning_type, state
        )
        
        # Gather evidence citations
        evidence_cited = self._gather_evidence_citations(context, state)
        
        thought = ReActThought(
            step_id=step_id,
            step_type=ReActStepType.THOUGHT,
            content=thought_content,
            confidence=confidence,
            reasoning_type=reasoning_type,
            tool_selected=selected_tool,
            tool_input=tool_input,
            evidence_cited=evidence_cited
        )
        
        logger.info(f"Generated advanced thought: {reasoning_type} reasoning, tool: {selected_tool}")
        logger.debug(f"Thought confidence: {confidence:.3f}, evidence cited: {len(evidence_cited)}")
        
        return thought
    
    def _select_reasoning_type(self, context: ReasoningContext, state: AdvancedReActState) -> str:
        """Select appropriate reasoning type based on context"""
        
        iteration = state.iteration_count
        evidence_quality = context.evidence_quality
        
        if iteration == 1:
            return "deductive"  # Start with rule-based reasoning
        elif evidence_quality > 0.7:
            return "inductive"  # Generalize from strong evidence
        elif evidence_quality < 0.4:
            return "abductive"  # Find best explanations
        else:
            return "analogical"  # Use analogical reasoning
    
    def _generate_advanced_reasoning_content(
        self, 
        context: ReasoningContext, 
        tool: Optional[str], 
        reasoning_type: str, 
        state: AdvancedReActState
    ) -> str:
        """Generate sophisticated reasoning content"""
        
        content_parts = []
        
        # Add reasoning type context
        reasoning_explanations = {
            "deductive": "Based on established rules and facts, I conclude that",
            "inductive": "From patterns in the evidence, I infer that",
            "abductive": "The best explanation for the observed facts is",
            "analogical": "Drawing parallels to similar cases, I reason that"
        }
        
        content_parts.append(reasoning_explanations.get(reasoning_type, "I reason that"))
        
        # Add goal-oriented reasoning
        content_parts.append(f"to achieve the goal: {context.current_goal}")
        
        # Add evidence-based reasoning
        if context.evidence_quality > 0.5:
            content_parts.append(f"supported by evidence quality of {context.evidence_quality:.2f}")
        
        # Add tool-specific reasoning
        if tool:
            tool_explanations = {
                "validate_submission": "submission validation is necessary to ensure data completeness",
                "enrich_data": "data enrichment will provide additional context for risk assessment",
                "retrieve_guidelines": "guideline retrieval will supply domain expertise",
                "assess_underwriting": "underwriting assessment will evaluate eligibility",
                "verify_evidence": "evidence verification will ensure decision reliability"
            }
            
            content_parts.append(tool_explanations.get(tool, f"using {tool} will progress the analysis"))
        
        # Add meta-cognitive awareness
        content_parts.append(f"at iteration {state.iteration_count}")
        
        return " ".join(content_parts) + "."
    
    def _gather_evidence_citations(self, context: ReasoningContext, state: AdvancedReActState) -> List[str]:
        """Gather relevant evidence citations"""
        
        citations = []
        
        # Add evidence from previous observations
        for thought in state.thoughts:
            if thought.observation_result and "evidence" in thought.observation_result:
                evidence = thought.observation_result["evidence"]
                if isinstance(evidence, list):
                    citations.extend([str(e) for e in evidence[:3]])  # Limit to 3 per thought
        
        # Add domain constraint evidence
        if "domain_constraints" in context.domain_constraints:
            citations.append("domain_constraints")
        
        return list(set(citations))  # Remove duplicates
    
    def _execute_dynamic_action(self, thought: ReActThought, context: ReasoningContext) -> Dict[str, Any]:
        """Execute action with dynamic tool"""
        
        tool_func = self.tool_registry[thought.tool_selected]
        
        try:
            logger.info(f"Executing dynamic action: {thought.tool_selected}")
            result = tool_func(thought.tool_input or {})
            
            # Add execution metadata
            result["execution_metadata"] = {
                "tool": thought.tool_selected,
                "timestamp": datetime.now().isoformat(),
                "reasoning_type": thought.reasoning_type,
                "confidence": thought.confidence
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Dynamic action failed: {thought.tool_selected} - {str(e)}")
            return {
                "error": str(e),
                "tool": thought.tool_selected,
                "execution_metadata": {
                    "tool": thought.tool_selected,
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed"
                }
            }
    
    def _process_advanced_observation(
        self, 
        action_result: Dict[str, Any], 
        context: ReasoningContext, 
        state: AdvancedReActState
    ) -> Dict[str, Any]:
        """Process observation with advanced analysis"""
        
        observation = {
            "action_success": "error" not in action_result,
            "key_findings": [],
            "reasoning": "",
            "next_steps": [],
            "completion_indicators": [],
            "evidence_quality_impact": 0.0,
            "strategic_insights": []
        }
        
        if "error" in action_result:
            observation["reasoning"] = f"Action failed: {action_result['error']}. Strategy adjustment required."
            observation["strategic_insights"].append("Tool execution failure indicates need for alternative approach")
            return observation
        
        # Analyze results for strategic insights
        tool = action_result.get("execution_metadata", {}).get("tool", "")
        
        # Tool-specific observation processing
        if tool == "validate_submission":
            validation_result = action_result.get("validation_result", {})
            if validation_result.get("missing_info"):
                observation["key_findings"].append(f"Missing information detected: {validation_result['missing_info']}")
                observation["strategic_insights"].append("Data completeness issues require targeted information gathering")
            else:
                observation["key_findings"].append("Submission validation passed")
                observation["strategic_insights"].append("Clean data enables progression to enrichment phase")
        
        elif tool == "enrich_data":
            enrichment_result = action_result.get("enrichment_result", {})
            if enrichment_result.get("hazard_scores"):
                hazards = enrichment_result["hazard_scores"]
                high_risks = [risk for risk, score in hazards.items() if score > 0.7]
                if high_risks:
                    observation["key_findings"].append(f"High-risk factors identified: {high_risks}")
                    observation["strategic_insights"].append("Risk factors require domain-specific guideline review")
            observation["evidence_quality_impact"] = 0.2
        
        elif tool == "retrieve_guidelines":
            guidelines = action_result.get("guidelines", [])
            observation["key_findings"].append(f"Retrieved {len(guidelines)} guideline items")
            if len(guidelines) >= 3:
                observation["completion_indicators"].append("sufficient_guidelines")
                observation["strategic_insights"].append("Adequate domain guidance available for assessment")
            observation["evidence_quality_impact"] = 0.3
        
        # Generate next step reasoning
        observation["reasoning"] = self._generate_observation_reasoning(observation, context, state)
        
        return observation
    
    def _generate_observation_reasoning(
        self, 
        observation: Dict[str, Any], 
        context: ReasoningContext, 
        state: AdvancedReActState
    ) -> str:
        """Generate sophisticated observation reasoning"""
        
        reasoning_parts = []
        
        # Add action outcome assessment
        if observation["action_success"]:
            reasoning_parts.append("Action completed successfully")
        else:
            reasoning_parts.append("Action encountered issues")
        
        # Add strategic insights
        if observation["strategic_insights"]:
            reasoning_parts.append(f"Strategic insight: {observation['strategic_insights'][0]}")
        
        # Add evidence quality impact
        if observation["evidence_quality_impact"] > 0:
            reasoning_parts.append(f"Evidence quality improved by {observation['evidence_quality_impact']:.2f}")
        
        # Add completion assessment
        if observation["completion_indicators"]:
            reasoning_parts.append(f"Progress indicators: {', '.join(observation['completion_indicators'])}")
        
        # Add next step recommendation
        if state.iteration_count < 5:
            reasoning_parts.append("Continuing evidence gathering phase")
        elif state.iteration_count < 10:
            reasoning_parts.append("Transitioning to assessment phase")
        else:
            reasoning_parts.append("Approaching decision synthesis phase")
        
        return ". ".join(reasoning_parts) + "."
    
    def _update_tool_performance(
        self, 
        tool: str, 
        result: Dict[str, Any], 
        context: ReasoningContext
    ):
        """Update tool performance tracking"""
        
        current_performance = self.tool_selector.tool_performance.get(tool, 0.7)
        
        # Calculate success score
        success_score = 1.0 if "error" not in result else 0.3
        
        # Calculate relevance score
        relevance_score = self._calculate_tool_relevance(tool, result, context)
        
        # Update performance with exponential smoothing
        new_performance = (current_performance * 0.7) + (success_score * relevance_score * 0.3)
        
        self.tool_selector.tool_performance[tool] = max(0.1, min(0.95, new_performance))
    
    def _calculate_tool_relevance(
        self, 
        tool: str, 
        result: Dict[str, Any], 
        context: ReasoningContext
    ) -> float:
        """Calculate relevance of tool result to current goal"""
        
        # Simple relevance calculation based on result content
        goal = context.current_goal.lower()
        
        if "validation" in tool and "missing_info" in str(result):
            return 0.9 if "missing" in goal else 0.6
        
        elif "enrich" in tool and "hazard_scores" in str(result):
            return 0.8 if "risk" in goal else 0.5
        
        elif "guideline" in tool and "guidelines" in str(result):
            return 0.9 if "evidence" in goal or "assess" in goal else 0.6
        
        return 0.5
    
    def _adaptive_replanning(
        self, 
        observation: Dict[str, Any], 
        state: AdvancedReActState, 
        context: ReasoningContext
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Adaptive replanning with strategy adjustment"""
        
        should_continue = True
        new_goal = None
        strategy_adjustment = None
        
        # Check completion conditions
        if len(observation.get("completion_indicators", [])) >= 2:
            should_continue = False
            new_goal = "Synthesize final decision"
            strategy_adjustment = {
                "iteration": state.iteration_count,
                "adjustment": "completion_detected",
                "reason": "Multiple completion indicators present",
                "confidence": context.evidence_quality
            }
        
        elif state.iteration_count >= state.max_iterations:
            should_continue = False
            new_goal = "Force decision synthesis"
            strategy_adjustment = {
                "iteration": state.iteration_count,
                "adjustment": "max_iterations_reached",
                "reason": "Maximum iteration limit reached",
                "confidence": context.evidence_quality
            }
        
        # Adaptive goal adjustment
        elif observation.get("evidence_quality_impact", 0) > 0.2:
            if context.evidence_quality > 0.8:
                new_goal = "Proceed to comprehensive assessment"
            elif context.evidence_quality > 0.6:
                new_goal = "Gather targeted evidence for gaps"
            else:
                new_goal = "Enhance evidence quality"
            
            strategy_adjustment = {
                "iteration": state.iteration_count,
                "adjustment": "goal_refinement",
                "new_goal": new_goal,
                "reason": f"Evidence quality at {context.evidence_quality:.2f}",
                "confidence": context.evidence_quality
            }
        
        # Strategic adjustment based on insights
        elif observation.get("strategic_insights"):
            insight = observation["strategic_insights"][0]
            if "alternative approach" in insight.lower():
                new_goal = "Adjust strategy based on feedback"
                strategy_adjustment = {
                    "iteration": state.iteration_count,
                    "adjustment": "strategy_pivot",
                    "reason": "Current approach requires adjustment",
                    "confidence": 0.5
                }
        
        return should_continue, new_goal, strategy_adjustment
    
    def _calculate_evidence_quality(self, state: AdvancedReActState) -> float:
        """Calculate overall evidence quality"""
        
        if not state.evidence_collected:
            return 0.1
        
        # Base quality on evidence count
        count_factor = min(1.0, len(state.evidence_collected) / 5.0)
        
        # Adjust for tool diversity
        tool_diversity = len(set(state.tools_used)) / 6.0  # 6 main tools
        tool_factor = min(1.0, tool_diversity)
        
        # Adjust for reflection scores
        avg_reflection = 0.7
        if state.thoughts:
            reflection_scores = [t.reflection_score for t in state.thoughts if t.reflection_score]
            avg_reflection = sum(reflection_scores) / len(reflection_scores) if reflection_scores else 0.7
        
        return (count_factor + tool_factor + avg_reflection) / 3.0
    
    def _synthesize_meta_cognitive_decision(self, state: AdvancedReActState) -> Tuple[str, float]:
        """Synthesize decision with meta-cognitive analysis"""
        
        # Base decision on evidence and performance
        evidence_quality = self._calculate_evidence_quality(state)
        
        # Decision logic
        if evidence_quality > 0.8:
            decision = "ACCEPT"
            base_confidence = 0.8
        elif evidence_quality > 0.5:
            decision = "REFER"
            base_confidence = 0.6
        else:
            decision = "DECLINE"
            base_confidence = 0.4
        
        # Adjust confidence based on self-reflection insights
        if state.thoughts:
            avg_reflection = sum(t.reflection_score or 0.7 for t in state.thoughts) / len(state.thoughts)
            base_confidence *= avg_reflection
        
        # Adjust confidence based on strategy adjustments
        if state.strategy_adjustments:
            adjustment_factor = len([adj for adj in state.strategy_adjustments if adj.get("confidence", 0) > 0.7]) / len(state.strategy_adjustments)
            base_confidence *= (0.8 + 0.2 * adjustment_factor)
        
        final_confidence = max(0.1, min(0.95, base_confidence))
        
        return decision, final_confidence
    
    def _calculate_performance_metrics(self, state: AdvancedReActState) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        
        return {
            "reasoning_efficiency": min(1.0, 10.0 / state.iteration_count),  # Lower iterations = better
            "evidence_accumulation_rate": len(state.evidence_collected) / state.iteration_count,
            "tool_utilization_diversity": len(set(state.tools_used)) / 6.0,
            "self_reflection_quality": sum(t.reflection_score or 0 for t in state.thoughts) / len(state.thoughts) if state.thoughts else 0.5,
            "strategy_adaptability": len(state.strategy_adjustments) / state.iteration_count,
            "confidence_calibration": abs(state.confidence_score - self._calculate_evidence_quality(state)),
            "overall_effectiveness": (state.confidence_score + self._calculate_evidence_quality(state)) / 2.0
        }
    
    def _update_global_metrics(self, state: AdvancedReActState):
        """Update global performance metrics"""
        
        self.global_performance_metrics["total_reasoning_sessions"] += 1
        
        # Update averages
        total = self.global_performance_metrics["total_reasoning_sessions"]
        
        # Average confidence
        current_avg = self.global_performance_metrics["average_confidence"]
        new_avg = ((current_avg * (total - 1)) + state.confidence_score) / total
        self.global_performance_metrics["average_confidence"] = new_avg
        
        # Average iterations
        current_iter = self.global_performance_metrics["average_iterations"]
        new_iter = ((current_iter * (total - 1)) + state.iteration_count) / total
        self.global_performance_metrics["average_iterations"] = new_iter
        
        # Success rate (completed with reasonable confidence)
        success = 1 if state.completed and state.confidence_score > 0.5 else 0
        current_success = self.global_performance_metrics["success_rate"]
        new_success = ((current_success * (total - 1)) + success) / total
        self.global_performance_metrics["success_rate"] = new_success
    
    def _extract_initial_goal(self, query: str, context: Dict[str, Any]) -> str:
        """Extract initial goal from query and context"""
        
        query_lower = query.lower()
        
        if "underwrite" in query_lower or "assess" in query_lower:
            return "Complete comprehensive underwriting assessment with evidence-based decision"
        elif "validate" in query_lower:
            return "Validate submission completeness and identify missing information"
        elif "enrich" in query_lower:
            return "Enrich submission data with additional context and risk factors"
        else:
            return "Perform systematic analysis with adaptive reasoning"
    
    def get_comprehensive_summary(self, state: AdvancedReActState) -> Dict[str, Any]:
        """Get comprehensive reasoning summary for explainable AI"""
        
        return {
            "query": state.original_query,
            "final_goal": state.current_goal,
            "final_decision": state.current_decision,
            "final_confidence": state.confidence_score,
            "iterations_used": state.iteration_count,
            "completion_reason": state.completion_reason,
            
            # Reasoning analysis
            "reasoning_summary": {
                "total_thoughts": len(state.thoughts),
                "reasoning_types": list(set(t.reasoning_type for t in state.thoughts)),
                "tools_used": state.tools_used,
                "evidence_collected": len(state.evidence_collected),
                "strategy_adjustments": len(state.strategy_adjustments)
            },
            
            # Self-reflection analysis
            "self_reflection_summary": {
                "average_reflection_score": sum(t.reflection_score or 0 for t in state.thoughts) / len(state.thoughts) if state.thoughts else 0,
                "reflection_insights": [t.reflection_reasoning for t in state.thoughts if t.reflection_reasoning],
                "learning_insights": state.learning_insights,
                "meta_cognitive_awareness": len([t for t in state.thoughts if t.reflection_score and t.reflection_score > 0.7])
            },
            
            # Performance metrics
            "performance_metrics": state.performance_metrics,
            
            # Detailed reasoning chain
            "reasoning_chain": [thought.to_dict() for thought in state.thoughts],
            
            # Strategy evolution
            "strategy_evolution": state.strategy_adjustments,
            
            # Evidence analysis
            "evidence_analysis": {
                "total_evidence": len(state.evidence_collected),
                "evidence_quality": self._calculate_evidence_quality(state),
                "evidence_sources": list(set(e.get("source", "unknown") for e in state.evidence_collected))
            }
        }
    
    def register_tool(self, tool_name: str, tool_func: Callable, category: str, required_fields: List[str] = None):
        """Register tool with advanced metadata"""
        self.tool_registry[tool_name] = {
            "function": tool_func,
            "category": category,
            "required_fields": required_fields or [],
            "performance_history": []
        }
        logger.info(f"Registered advanced tool: {tool_name} in category: {category}")


# Global advanced ReAct engine instance
_global_advanced_react_engine: Optional[AdvancedReActEngine] = None


def get_advanced_react_engine() -> AdvancedReActEngine:
    """Get global advanced ReAct engine instance"""
    global _global_advanced_react_engine
    if _global_advanced_react_engine is None:
        _global_advanced_react_engine = AdvancedReActEngine()
    return _global_advanced_react_engine
