"""
Chaos Engineering
Simulates failures to test system resilience.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import random

logger = logging.getLogger(__name__)


class ChaosType(Enum):
    """Types of chaos experiments."""
    LATENCY = "latency"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CORRUPTION = "corruption"


class ChaosExperiment:
    """Chaos experiment configuration."""
    
    def __init__(
        self,
        experiment_id: str,
        name: str,
        chaos_type: str,
        target: str,
        probability: float = 0.5,
        duration_seconds: int = 30
    ):
        self.experiment_id = experiment_id
        self.name = name
        self.chaos_type = chaos_type
        self.target = target
        self.probability = probability
        self.duration_seconds = duration_seconds
        self.enabled = False
        self.start_time = None
        self.end_time = None


class ChaosEngine:
    """
    Chaos engineering engine.
    
    Simulates failures to test system resilience.
    """
    
    def __init__(self):
        """Initialize chaos engine."""
        self.enabled = os.getenv("CHAOS_ENGINEERING_ENABLED", "false").lower() == "true"
        
        # Experiments
        self.experiments = {}
        
        # Chaos history
        self.chaos_history = []
        
        logger.info(f"Chaos engine initialized (enabled={self.enabled})")
    
    def create_experiment(
        self,
        name: str,
        chaos_type: str,
        target: str,
        probability: float = 0.5,
        duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Create a chaos experiment.
        
        Args:
            name: Experiment name
            chaos_type: Type of chaos
            target: Target system/component
            probability: Probability of chaos occurring (0-1)
            duration_seconds: Duration of experiment
            
        Returns:
            Experiment creation result
        """
        if not self.enabled:
            return {
                "chaos_engineering_enabled": False,
                "experiment_id": None,
                "reason": "Chaos engineering disabled"
            }
        
        experiment_id = f"chaos_{datetime.now().timestamp()}"
        experiment = ChaosExperiment(
            experiment_id=experiment_id,
            name=name,
            chaos_type=chaos_type,
            target=target,
            probability=probability,
            duration_seconds=duration_seconds
        )
        
        self.experiments[experiment_id] = experiment
        
        return {
            "chaos_engineering_enabled": True,
            "experiment_id": experiment_id,
            "name": name,
            "chaos_type": chaos_type,
            "target": target,
            "status": "created"
        }
    
    def start_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Start a chaos experiment.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment start result
        """
        if not self.enabled:
            return {
                "chaos_engineering_enabled": False,
                "reason": "Chaos engineering disabled"
            }
        
        if experiment_id not in self.experiments:
            return {
                "chaos_engineering_enabled": True,
                "reason": "Experiment not found"
            }
        
        experiment = self.experiments[experiment_id]
        experiment.enabled = True
        experiment.start_time = datetime.now()
        experiment.end_time = datetime.now() + timedelta(seconds=experiment.duration_seconds)
        
        # Record chaos event
        self.chaos_history.append({
            "experiment_id": experiment_id,
            "action": "start",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Started chaos experiment: {experiment_id}")
        
        return {
            "chaos_engineering_enabled": True,
            "experiment_id": experiment_id,
            "status": "running",
            "start_time": experiment.start_time.isoformat(),
            "end_time": experiment.end_time.isoformat()
        }
    
    def stop_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Stop a chaos experiment.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment stop result
        """
        if not self.enabled:
            return {
                "chaos_engineering_enabled": False,
                "reason": "Chaos engineering disabled"
            }
        
        if experiment_id not in self.experiments:
            return {
                "chaos_engineering_enabled": True,
                "reason": "Experiment not found"
            }
        
        experiment = self.experiments[experiment_id]
        experiment.enabled = False
        experiment.end_time = datetime.now()
        
        # Record chaos event
        self.chaos_history.append({
            "experiment_id": experiment_id,
            "action": "stop",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Stopped chaos experiment: {experiment_id}")
        
        return {
            "chaos_engineering_enabled": True,
            "experiment_id": experiment_id,
            "status": "stopped"
        }
    
    def should_inject_chaos(self, target: str) -> Dict[str, Any]:
        """
        Check if chaos should be injected for a target.
        
        Args:
            target: Target system/component
            
        Returns:
            Chaos injection decision
        """
        if not self.enabled:
            return {
                "chaos_engineering_enabled": False,
                "inject_chaos": False
            }
        
        # Find active experiments for target
        active_experiments = [
            exp for exp in self.experiments.values()
            if exp.enabled and exp.target == target
        ]
        
        if not active_experiments:
            return {
                "chaos_engineering_enabled": True,
                "inject_chaos": False,
                "reason": "No active experiments for target"
            }
        
        # Check if experiment is still within duration
        now = datetime.now()
        for exp in active_experiments:
            if exp.end_time and now > exp.end_time:
                exp.enabled = False
                logger.info(f"Experiment {exp.experiment_id} expired")
        
        # Re-check active experiments
        active_experiments = [
            exp for exp in self.experiments.values()
            if exp.enabled and exp.target == target
        ]
        
        if not active_experiments:
            return {
                "chaos_engineering_enabled": True,
                "inject_chaos": False,
                "reason": "All experiments expired"
            }
        
        # Randomly determine if chaos should be injected
        exp = random.choice(active_experiments)
        should_inject = random.random() < exp.probability
        
        if should_inject:
            return {
                "chaos_engineering_enabled": True,
                "inject_chaos": True,
                "chaos_type": exp.chaos_type,
                "experiment_id": exp.experiment_id
            }
        
        return {
            "chaos_engineering_enabled": True,
            "inject_chaos": False,
            "reason": "Probability check failed"
        }
    
    def get_experiment_status(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an experiment.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment status or None if not found
        """
        if not self.enabled:
            return {"enabled": False}
        
        if experiment_id not in self.experiments:
            return None
        
        exp = self.experiments[experiment_id]
        
        return {
            "enabled": True,
            "experiment_id": experiment_id,
            "name": exp.name,
            "chaos_type": exp.chaos_type,
            "target": exp.target,
            "status": "running" if exp.enabled else "stopped",
            "start_time": exp.start_time.isoformat() if exp.start_time else None,
            "end_time": exp.end_time.isoformat() if exp.end_time else None
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get chaos engineering summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        active_count = sum(1 for exp in self.experiments.values() if exp.enabled)
        
        return {
            "enabled": True,
            "total_experiments": len(self.experiments),
            "active_experiments": active_count,
            "chaos_events": len(self.chaos_history)
        }


# Global chaos engine instance
_global_chaos_engine: Optional[ChaosEngine] = None


def get_chaos_engine() -> ChaosEngine:
    """
    Get global chaos engine instance (singleton pattern).
    
    Returns:
        ChaosEngine instance
    """
    global _global_chaos_engine
    if _global_chaos_engine is None:
        _global_chaos_engine = ChaosEngine()
    return _global_chaos_engine
