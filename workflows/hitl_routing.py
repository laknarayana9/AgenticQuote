"""
Smart HITL Task Routing
Routes HITL tasks to reviewers based on expertise, workload, and availability.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExpertiseArea(Enum):
    """Reviewer expertise areas."""
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    WIND = "wind"
    EARTHQUAKE = "earthquake"
    CONSTRUCTION = "construction"
    CLAIMS = "claims"
    OCCUPANCY = "occupancy"
    GENERAL = "general"


class ReviewerStatus(Enum):
    """Reviewer availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    ON_LEAVE = "on_leave"


class Reviewer:
    """Reviewer profile with expertise and availability."""
    
    def __init__(
        self,
        reviewer_id: str,
        name: str,
        expertise: List[str],
        max_concurrent_tasks: int = 5
    ):
        self.reviewer_id = reviewer_id
        self.name = name
        self.expertise = expertise
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks = 0
        self.status = ReviewerStatus.AVAILABLE
        self.last_assigned = None
        self.performance_score = 0.5  # 0-1 scale
        self.task_history = []


class SmartHITLRouter:
    """
    Smart HITL task router based on expertise, workload, and availability.
    
    Routes tasks to the most appropriate reviewer using multiple factors.
    """
    
    def __init__(self):
        """Initialize smart HITL router."""
        self.enabled = os.getenv("HITL_SMART_ROUTING", "false").lower() == "true"
        
        # Reviewer registry
        self.reviewers = {}
        
        # Routing configuration
        self.routing_weights = {
            "expertise_match": 0.4,
            "workload": 0.3,
            "performance": 0.2,
            "availability": 0.1
        }
        
        logger.info(f"Smart HITL router initialized (enabled={self.enabled})")
    
    def register_reviewer(
        self,
        reviewer_id: str,
        name: str,
        expertise: List[str],
        max_concurrent_tasks: int = 5
    ):
        """
        Register a reviewer for task routing.
        
        Args:
            reviewer_id: Unique reviewer identifier
            name: Reviewer name
            expertise: List of expertise areas
            max_concurrent_tasks: Maximum concurrent tasks
        """
        self.reviewers[reviewer_id] = Reviewer(
            reviewer_id=reviewer_id,
            name=name,
            expertise=expertise,
            max_concurrent_tasks=max_concurrent_tasks
        )
        logger.info(f"Registered reviewer {reviewer_id} with expertise: {expertise}")
    
    def route_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Route a HITL task to the most appropriate reviewer.
        
        Args:
            task_type: Type of task (review, verification, approval)
            task_data: Task data including risk factors
            priority: Task priority (low, medium, high, urgent)
            
        Returns:
            Routing result with selected reviewer
        """
        if not self.enabled:
            return {
                "smart_routing_enabled": False,
                "selected_reviewer": None,
                "reason": "Smart routing disabled"
            }
        
        # Identify required expertise
        required_expertise = self._identify_required_expertise(task_data)
        
        # Score reviewers
        scored_reviewers = []
        for reviewer_id, reviewer in self.reviewers.items():
            if reviewer.status != ReviewerStatus.AVAILABLE:
                continue
            
            score = self._score_reviewer(
                reviewer,
                required_expertise,
                task_type,
                priority
            )
            
            if score > 0:
                scored_reviewers.append({
                    "reviewer_id": reviewer_id,
                    "score": score,
                    "reviewer": reviewer
                })
        
        # Select best reviewer
        if scored_reviewers:
            scored_reviewers.sort(key=lambda x: x["score"], reverse=True)
            selected = scored_reviewers[0]
            
            # Update reviewer
            selected["reviewer"].current_tasks += 1
            selected["reviewer"].last_assigned = datetime.now()
            
            return {
                "smart_routing_enabled": True,
                "selected_reviewer": selected["reviewer_id"],
                "score": selected["score"],
                "required_expertise": required_expertise,
                "reason": f"Best match based on expertise, workload, and performance"
            }
        
        # No available reviewers
        return {
            "smart_routing_enabled": True,
            "selected_reviewer": None,
            "reason": "No available reviewers with required expertise"
        }
    
    def _identify_required_expertise(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Identify required expertise based on task data.
        
        Args:
            task_data: Task data including risk factors
            
        Returns:
            List of required expertise areas
        """
        required = []
        
        # Check hazard risks
        hazard_profile = task_data.get("hazard_profile", {})
        if hazard_profile.get("wildfire_risk_score", 0) > 0.6:
            required.append(ExpertiseArea.WILDFIRE.value)
        if hazard_profile.get("flood_risk_score", 0) > 0.6:
            required.append(ExpertiseArea.FLOOD.value)
        if hazard_profile.get("wind_risk_score", 0) > 0.6:
            required.append(ExpertiseArea.WIND.value)
        if hazard_profile.get("earthquake_risk_score", 0) > 0.6:
            required.append(ExpertiseArea.EARTHQUAKE.value)
        
        # Check property features
        property_profile = task_data.get("property_profile", {})
        if property_profile.get("year_built", 2026) < 1940:
            required.append(ExpertiseArea.CONSTRUCTION.value)
        
        # Check claims
        claims_history = task_data.get("claims_history", {})
        if claims_history.get("loss_count_5yr", 0) > 2:
            required.append(ExpertiseArea.CLAIMS.value)
        
        # Check occupancy
        occupancy = property_profile.get("occupancy", "")
        if occupancy in ["tenant_occupied", "vacant"]:
            required.append(ExpertiseArea.OCCUPANCY.value)
        
        # Default to general if no specific expertise required
        if not required:
            required.append(ExpertiseArea.GENERAL.value)
        
        return required
    
    def _score_reviewer(
        self,
        reviewer: Reviewer,
        required_expertise: List[str],
        task_type: str,
        priority: str
    ) -> float:
        """
        Score a reviewer for a task.
        
        Args:
            reviewer: Reviewer to score
            required_expertise: Required expertise areas
            task_type: Type of task
            priority: Task priority
            
        Returns:
            Score (0-1)
        """
        score = 0.0
        
        # Expertise match score
        expertise_match = self._calculate_expertise_match(reviewer.expertise, required_expertise)
        score += expertise_match * self.routing_weights["expertise_match"]
        
        # Workload score (prefer reviewers with lower current workload)
        workload_score = 1.0 - (reviewer.current_tasks / reviewer.max_concurrent_tasks)
        score += workload_score * self.routing_weights["workload"]
        
        # Performance score (prefer higher performing reviewers)
        score += reviewer.performance_score * self.routing_weights["performance"]
        
        # Availability score (prefer recently available)
        if reviewer.last_assigned:
            time_since_last = (datetime.now() - reviewer.last_assigned).total_seconds() / 3600
            availability_score = min(time_since_last / 24, 1.0)  # Normalize to 0-1 over 24 hours
            score += availability_score * self.routing_weights["availability"]
        
        return score
    
    def _calculate_expertise_match(
        self,
        reviewer_expertise: List[str],
        required_expertise: List[str]
    ) -> float:
        """
        Calculate expertise match score.
        
        Args:
            reviewer_expertise: Reviewer's expertise areas
            required_expertise: Required expertise areas
            
        Returns:
            Match score (0-1)
        """
        if not required_expertise:
            return 1.0
        
        # Count matching expertise
        matches = sum(1 for exp in required_expertise if exp in reviewer_expertise)
        
        # Calculate score
        return matches / len(required_expertise)
    
    def complete_task(self, reviewer_id: str):
        """
        Mark a task as completed for a reviewer.
        
        Args:
            reviewer_id: Reviewer ID
        """
        if reviewer_id in self.reviewers:
            self.reviewers[reviewer_id].current_tasks = max(0, self.reviewers[reviewer_id].current_tasks - 1)
            logger.debug(f"Task completed for reviewer {reviewer_id}")
    
    def update_reviewer_performance(self, reviewer_id: str, score: float):
        """
        Update reviewer performance score.
        
        Args:
            reviewer_id: Reviewer ID
            score: Performance score (0-1)
        """
        if reviewer_id in self.reviewers:
            # Exponential moving average for performance score
            current_score = self.reviewers[reviewer_id].performance_score
            alpha = 0.1  # Smoothing factor
            self.reviewers[reviewer_id].performance_score = alpha * score + (1 - alpha) * current_score
    
    def get_reviewer_stats(self) -> Dict[str, Any]:
        """
        Get reviewer statistics.
        
        Returns:
            Dictionary with reviewer statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        stats = {
            "enabled": True,
            "total_reviewers": len(self.reviewers),
            "available_reviewers": sum(1 for r in self.reviewers.values() if r.status == ReviewerStatus.AVAILABLE),
            "busy_reviewers": sum(1 for r in self.reviewers.values() if r.status == ReviewerStatus.BUSY),
            "reviewers": {}
        }
        
        for reviewer_id, reviewer in self.reviewers.items():
            stats["reviewers"][review_id] = {
                "name": reviewer.name,
                "expertise": reviewer.expertise,
                "current_tasks": reviewer.current_tasks,
                "max_concurrent_tasks": reviewer.max_concurrent_tasks,
                "status": reviewer.status.value,
                "performance_score": reviewer.performance_score
            }
        
        return stats


# Global smart HITL router instance
_global_router: Optional[SmartHITLRouter] = None


def get_smart_hitl_router() -> SmartHITLRouter:
    """
    Get global smart HITL router instance (singleton pattern).
    
    Returns:
        SmartHITLRouter instance
    """
    global _global_router
    if _global_router is None:
        _global_router = SmartHITLRouter()
    return _global_router
