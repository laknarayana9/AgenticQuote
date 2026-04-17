"""
Multi-Agent Collaboration Framework
Enables multiple agents to collaborate on complex underwriting cases.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in multi-agent collaboration."""
    LEAD = "lead"
    SPECIALIST = "specialist"
    REVIEWER = "reviewer"
    ARBITER = "arbiter"


class CollaborationStatus(Enum):
    """Collaboration session statuses."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    CONFLICT_DETECTED = "conflict_detected"
    RESOLVED = "resolved"
    FAILED = "failed"


class AgentMessage:
    """Message between agents in collaboration."""
    
    def __init__(self, sender: str, recipient: str, content: Dict[str, Any], message_type: str):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.message_type = message_type
        self.timestamp = datetime.now()
        self.message_id = str(uuid.uuid4())


class MultiAgentOrchestrator:
    """
    Orchestrates multi-agent collaboration for complex underwriting cases.
    
    Manages agent communication, consensus building, and conflict resolution.
    """
    
    def __init__(self):
        """Initialize multi-agent orchestrator."""
        self.enabled = os.getenv("ENABLE_MULTI_AGENT", "false").lower() == "true"
        self.agents = {}  # Registered agents
        self.collaboration_sessions = {}  # Active collaboration sessions
        self.message_queue = []  # Message queue for agent communication
        
        logger.info(f"Multi-agent orchestrator initialized (enabled={self.enabled})")
    
    def register_agent(self, agent_id: str, agent_instance: Any, role: AgentRole, capabilities: List[str]):
        """
        Register an agent for collaboration.
        
        Args:
            agent_id: Unique agent identifier
            agent_instance: Agent instance
            role: Agent role in collaboration
            capabilities: List of agent capabilities
        """
        self.agents[agent_id] = {
            "instance": agent_instance,
            "role": role,
            "capabilities": capabilities,
            "registered_at": datetime.now()
        }
        logger.info(f"Registered agent {agent_id} with role {role.value}")
    
    def initiate_collaboration(
        self,
        case_id: str,
        case_data: Dict[str, Any],
        participating_agents: List[str],
        lead_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a multi-agent collaboration session.
        
        Args:
            case_id: Unique case identifier
            case_data: Case data to collaborate on
            participating_agents: List of agent IDs to participate
            lead_agent: Optional lead agent (defaults to first in list)
            
        Returns:
            Collaboration session information
        """
        if not self.enabled:
            logger.warning("Multi-agent collaboration disabled, skipping")
            return self._single_agent_fallback(case_data, participating_agents[0] if participating_agents else None)
        
        session_id = str(uuid.uuid4())
        lead_agent = lead_agent or (participating_agents[0] if participating_agents else None)
        
        session = {
            "session_id": session_id,
            "case_id": case_id,
            "status": CollaborationStatus.INITIATED.value,
            "participants": participating_agents,
            "lead_agent": lead_agent,
            "case_data": case_data,
            "messages": [],
            "assessments": {},
            "consensus": None,
            "conflicts": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        self.collaboration_sessions[session_id] = session
        
        logger.info(f"Initiated collaboration session {session_id} for case {case_id}")
        
        # Start collaboration
        return self._run_collaboration(session)
    
    def _run_collaboration(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the collaboration process.
        
        Args:
            session: Collaboration session
            
        Returns:
            Collaboration result
        """
        session["status"] = CollaborationStatus.IN_PROGRESS.value
        session["updated_at"] = datetime.now()
        
        participants = session["participants"]
        case_data = session["case_data"]
        
        # Collect assessments from all participants
        for agent_id in participants:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not registered, skipping")
                continue
            
            try:
                agent = self.agents[agent_id]["instance"]
                assessment = self._get_agent_assessment(agent, case_data)
                session["assessments"][agent_id] = assessment
                
                # Broadcast assessment to other agents
                self._broadcast_assessment(session, agent_id, assessment)
                
            except Exception as e:
                logger.error(f"Error getting assessment from agent {agent_id}: {e}")
        
        # Check for consensus or conflicts
        consensus_result = self._check_consensus(session)
        
        if consensus_result["has_consensus"]:
            session["status"] = CollaborationStatus.CONSENSUS_REACHED.value
            session["consensus"] = consensus_result["consensus_decision"]
        else:
            session["status"] = CollaborationStatus.CONFLICT_DETECTED.value
            session["conflicts"] = consensus_result["conflicts"]
            
            # Attempt conflict resolution
            resolution = self._resolve_conflicts(session)
            if resolution["resolved"]:
                session["status"] = CollaborationStatus.RESOLVED.value
                session["consensus"] = resolution["final_decision"]
            else:
                session["status"] = CollaborationStatus.FAILED.value
        
        session["updated_at"] = datetime.now()
        
        return {
            "session_id": session["session_id"],
            "case_id": session["case_id"],
            "status": session["status"],
            "consensus": session.get("consensus"),
            "assessments": session["assessments"],
            "conflicts": session.get("conflicts", []),
            "lead_agent": session["lead_agent"]
        }
    
    def _get_agent_assessment(self, agent: Any, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get assessment from an agent.
        
        Args:
            agent: Agent instance
            case_data: Case data
            
        Returns:
            Agent assessment
        """
        # Try to call assess method if available
        if hasattr(agent, "assess"):
            return agent.assess(case_data.get("enrichment", {}), case_data.get("evidence_chunks", []))
        elif hasattr(agent, "verify"):
            return agent.verify(case_data.get("assessment", {}), case_data.get("evidence_chunks", []))
        else:
            # Fallback: return generic assessment
            return {
                "decision": "REFER",
                "confidence": 0.5,
                "rationale": "Generic assessment from agent without specific method"
            }
    
    def _broadcast_assessment(self, session: Dict[str, Any], sender: str, assessment: Dict[str, Any]):
        """
        Broadcast assessment to other participating agents.
        
        Args:
            session: Collaboration session
            sender: Sender agent ID
            assessment: Assessment to broadcast
        """
        message = AgentMessage(
            sender=sender,
            recipient="all",
            content={"assessment": assessment},
            message_type="assessment"
        )
        
        session["messages"].append({
            "sender": sender,
            "recipient": "all",
            "message_type": "assessment",
            "content": assessment,
            "timestamp": message.timestamp.isoformat()
        })
    
    def _check_consensus(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if agents have reached consensus.
        
        Args:
            session: Collaboration session
            
        Returns:
            Consensus check result
        """
        assessments = session["assessments"]
        
        if len(assessments) == 0:
            return {"has_consensus": False, "conflicts": ["No assessments available"]}
        
        # Extract decisions
        decisions = []
        for agent_id, assessment in assessments.items():
            decision = assessment.get("preliminary_decision") or assessment.get("decision")
            if decision:
                decisions.append(decision)
        
        # Check if all decisions are the same
        if len(set(decisions)) == 1:
            return {
                "has_consensus": True,
                "consensus_decision": decisions[0],
                "confidence": sum(a.get("confidence", 0.5) for a in assessments.values()) / len(assessments)
            }
        
        # Identify conflicts
        conflicts = []
        for agent_id, assessment in assessments.items():
            decision = assessment.get("preliminary_decision") or assessment.get("decision")
            if decision and decision != decisions[0]:
                conflicts.append(f"Agent {agent_id} disagrees with consensus")
        
        return {
            "has_consensus": False,
            "conflicts": conflicts
        }
    
    def _resolve_conflicts(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts between agents.
        
        Args:
            session: Collaboration session
            
        Returns:
            Resolution result
        """
        # Simple resolution: use lead agent's decision
        lead_agent = session["lead_agent"]
        
        if lead_agent and lead_agent in session["assessments"]:
            lead_assessment = session["assessments"][lead_agent]
            lead_decision = lead_assessment.get("preliminary_decision") or lead_assessment.get("decision")
            
            return {
                "resolved": True,
                "final_decision": lead_decision,
                "resolution_method": "lead_agent_override"
            }
        
        # Fallback: use majority vote
        decisions = []
        for assessment in session["assessments"].values():
            decision = assessment.get("preliminary_decision") or assessment.get("decision")
            if decision:
                decisions.append(decision)
        
        if decisions:
            from collections import Counter
            decision_counts = Counter(decisions)
            majority_decision = decision_counts.most_common(1)[0][0]
            
            return {
                "resolved": True,
                "final_decision": majority_decision,
                "resolution_method": "majority_vote"
            }
        
        return {
            "resolved": False,
            "final_decision": None,
            "resolution_method": "none"
        }
    
    def _single_agent_fallback(self, case_data: Dict[str, Any], agent_id: Optional[str]) -> Dict[str, Any]:
        """
        Fallback to single-agent processing when multi-agent is disabled.
        
        Args:
            case_data: Case data
            agent_id: Agent ID to use
            
        Returns:
            Single-agent result
        """
        if agent_id and agent_id in self.agents:
            try:
                agent = self.agents[agent_id]["instance"]
                assessment = self._get_agent_assessment(agent, case_data)
                
                return {
                    "session_id": str(uuid.uuid4()),
                    "case_id": case_data.get("case_id"),
                    "status": "single_agent_fallback",
                    "consensus": assessment.get("preliminary_decision") or assessment.get("decision"),
                    "assessments": {agent_id: assessment},
                    "conflicts": [],
                    "lead_agent": agent_id
                }
            except Exception as e:
                logger.error(f"Error in single-agent fallback: {e}")
        
        return {
            "session_id": str(uuid.uuid4()),
            "case_id": case_data.get("case_id"),
            "status": "failed",
            "consensus": None,
            "assessments": {},
            "conflicts": ["No agent available"],
            "lead_agent": None
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collaboration session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        return self.collaboration_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active collaboration sessions.
        
        Returns:
            List of active sessions
        """
        return [
            session for session in self.collaboration_sessions.values()
            if session["status"] in [CollaborationStatus.INITIATED.value, CollaborationStatus.IN_PROGRESS.value]
        ]


# Global multi-agent orchestrator instance
_global_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """
    Get global multi-agent orchestrator instance (singleton pattern).
    
    Returns:
        MultiAgentOrchestrator instance
    """
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = MultiAgentOrchestrator()
    return _global_orchestrator
