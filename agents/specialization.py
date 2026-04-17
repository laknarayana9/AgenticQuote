"""
Agent Specialization Module
Enables agents to specialize by risk type for improved decision-making.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RiskType(Enum):
    """Risk types for agent specialization."""
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    WIND = "wind"
    EARTHQUAKE = "earthquake"
    CONSTRUCTION = "construction"
    CLAIMS = "claims"
    OCCUPANCY = "occupancy"
    GENERAL = "general"


class AgentSpecialization:
    """
    Agent specialization by risk type.
    
    Routes cases to specialized agents based on dominant risk factors.
    """
    
    def __init__(self):
        """Initialize agent specialization system."""
        self.enabled = os.getenv("AGENT_SPECIALIZATION_ENABLED", "false").lower() == "true"
        
        # Specialized agent registry
        self.specialized_agents = {
            risk_type: [] for risk_type in RiskType
        }
        
        # Risk type detection thresholds
        self.thresholds = {
            RiskType.WILDFIRE: 0.6,
            RiskType.FLOOD: 0.6,
            RiskType.WIND: 0.6,
            RiskType.EARTHQUAKE: 0.6,
            RiskType.CONSTRUCTION: 1940,  # Year built threshold
            RiskType.CLAIMS: 2,  # Loss count threshold
            RiskType.OCCUPANCY: None  # Special handling
        }
        
        logger.info(f"Agent specialization initialized (enabled={self.enabled})")
    
    def register_specialized_agent(
        self,
        agent_id: str,
        risk_type: RiskType,
        agent_instance: Any
    ):
        """
        Register a specialized agent for a risk type.
        
        Args:
            agent_id: Unique agent identifier
            risk_type: Risk type specialization
            agent_instance: Agent instance
        """
        self.specialized_agents[risk_type].append({
            "agent_id": agent_id,
            "instance": agent_instance
        })
        logger.info(f"Registered specialized agent {agent_id} for {risk_type.value}")
    
    def detect_dominant_risk(self, case_data: Dict[str, Any]) -> RiskType:
        """
        Detect the dominant risk type for a case.
        
        Args:
            case_data: Case data
            
        Returns:
            Dominant risk type
        """
        hazard_profile = case_data.get("hazard_profile", {})
        property_profile = case_data.get("property_profile", {})
        claims_history = case_data.get("claims_history", {})
        
        # Extract risk scores
        wildfire_score = hazard_profile.get("wildfire_risk_score", 0)
        flood_score = hazard_profile.get("flood_risk_score", 0)
        wind_score = hazard_profile.get("wind_risk_score", 0)
        earthquake_score = hazard_profile.get("earthquake_risk_score", 0)
        
        # Extract property features
        year_built = property_profile.get("year_built", 2026)
        occupancy = property_profile.get("occupancy", "owner_occupied_primary")
        
        # Extract claims features
        loss_count = claims_history.get("loss_count_5yr", 0)
        
        # Determine dominant risk
        risks = []
        
        if wildfire_score >= self.thresholds[RiskType.WILDFIRE]:
            risks.append((RiskType.WILDFIRE, wildfire_score))
        
        if flood_score >= self.thresholds[RiskType.FLOOD]:
            risks.append((RiskType.FLOOD, flood_score))
        
        if wind_score >= self.thresholds[RiskType.WIND]:
            risks.append((RiskType.WIND, wind_score))
        
        if earthquake_score >= self.thresholds[RiskType.EARTHQUAKE]:
            risks.append((RiskType.EARTHQUAKE, earthquake_score))
        
        if year_built < self.thresholds[RiskType.CONSTRUCTION]:
            risks.append((RiskType.CONSTRUCTION, 1.0 - (year_built / 2026)))
        
        if loss_count >= self.thresholds[RiskType.CLAIMS]:
            risks.append((RiskType.CLAIMS, min(loss_count / 5, 1.0)))
        
        if occupancy in ["tenant_occupied", "vacant"]:
            risks.append((RiskType.OCCUPANCY, 0.8))
        
        if risks:
            # Return the highest-scoring risk
            risks.sort(key=lambda x: x[1], reverse=True)
            return risks[0][0]
        
        return RiskType.GENERAL
    
    def route_to_specialist(
        self,
        case_data: Dict[str, Any],
        general_agent: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Route a case to a specialized agent based on dominant risk.
        
        Args:
            case_data: Case data
            general_agent: Fallback general agent
            
        Returns:
            Routing result with selected agent
        """
        if not self.enabled:
            return {
                "specialization_enabled": False,
                "selected_agent": general_agent,
                "risk_type": RiskType.GENERAL,
                "reason": "Specialization disabled"
            }
        
        dominant_risk = self.detect_dominant_risk(case_data)
        
        # Get specialized agents for this risk type
        specialists = self.specialized_agents[dominant_risk]
        
        if specialists:
            # Select the best specialist (could be based on performance)
            selected = specialists[0]  # Simple: select first
            return {
                "specialization_enabled": True,
                "selected_agent": selected["instance"],
                "selected_agent_id": selected["agent_id"],
                "risk_type": dominant_risk.value,
                "reason": f"Specialized agent selected for {dominant_risk.value} risk"
            }
        
        # Fallback to general agent if no specialist available
        return {
            "specialization_enabled": True,
            "selected_agent": general_agent,
            "risk_type": dominant_risk.value,
            "reason": f"No specialist for {dominant_risk.value}, using general agent"
        }
    
    def get_specialization_stats(self) -> Dict[str, Any]:
        """
        Get specialization statistics.
        
        Returns:
            Dictionary with specialization statistics
        """
        return {
            "enabled": self.enabled,
            "specialized_agents": {
                risk_type.value: len(agents)
                for risk_type, agents in self.specialized_agents.items()
            },
            "thresholds": {
                risk_type.value: threshold
                for risk_type, threshold in self.thresholds.items()
            }
        }


# Global agent specialization instance
_global_specialization: Optional[AgentSpecialization] = None


def get_agent_specialization() -> AgentSpecialization:
    """
    Get global agent specialization instance (singleton pattern).
    
    Returns:
        AgentSpecialization instance
    """
    global _global_specialization
    if _global_specialization is None:
        _global_specialization = AgentSpecialization()
    return _global_specialization
