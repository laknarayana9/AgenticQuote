"""
Real-Time Monitoring and Observability System
Implements comprehensive monitoring for production AI systems:

- Real-time performance metrics
- Anomaly detection and alerting
- System health monitoring
- Resource utilization tracking
- Error tracking and analysis
- Performance optimization insights
- Dashboard-ready metrics
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import statistics
import threading
import time
from collections import deque, defaultdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"           # Cumulative count
    GAUGE = "gauge"              # Current value
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Rate per time unit


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""


@dataclass
class Alert:
    """System alert"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    request_rate: float
    error_rate: float
    response_time_p95: float
    throughput: float


class MetricsCollector(ABC):
    """Abstract base class for metrics collectors"""
    
    @abstractmethod
    def collect_metrics(self) -> List[MetricPoint]:
        """Collect metrics"""
        pass


class ReActMetricsCollector(MetricsCollector):
    """Collector for ReAct reasoning metrics"""
    
    def __init__(self, react_engine):
        self.react_engine = react_engine
        
    def collect_metrics(self) -> List[MetricPoint]:
        """Collect ReAct-specific metrics"""
        
        metrics = []
        
        # Global metrics
        global_metrics = self.react_engine.global_performance_metrics
        
        metrics.append(MetricPoint(
            name="react_total_sessions",
            value=global_metrics["total_reasoning_sessions"],
            metric_type=MetricType.COUNTER,
            labels={"component": "react_engine"}
        ))
        
        metrics.append(MetricPoint(
            name="react_average_confidence",
            value=global_metrics["average_confidence"],
            metric_type=MetricType.GAUGE,
            labels={"component": "react_engine"}
        ))
        
        metrics.append(MetricPoint(
            name="react_success_rate",
            value=global_metrics["success_rate"],
            metric_type=MetricType.GAUGE,
            labels={"component": "react_engine"}
        ))
        
        return metrics


class AgentMetricsCollector(MetricsCollector):
    """Collector for hierarchical agent metrics"""
    
    def __init__(self, agent_system):
        self.agent_system = agent_system
        
    def collect_metrics(self) -> List[MetricPoint]:
        """Collect agent-specific metrics"""
        
        metrics = []
        
        # Get system performance
        system_performance = self.agent_system.get_system_performance()
        
        # System-level metrics
        system_metrics = system_performance["system_metrics"]
        
        metrics.append(MetricPoint(
            name="agent_total_agents",
            value=system_metrics["total_agents"],
            metric_type=MetricType.GAUGE,
            labels={"component": "agent_system"}
        ))
        
        metrics.append(MetricPoint(
            name="agent_success_rate",
            value=system_metrics["success_rate"],
            metric_type=MetricType.GAUGE,
            labels={"component": "agent_system"}
        ))
        
        metrics.append(MetricPoint(
            name="agent_conflicts_resolved",
            value=system_metrics["conflicts_resolved"],
            metric_type=MetricType.COUNTER,
            labels={"component": "agent_system"}
        ))
        
        # Individual agent metrics
        agent_performance = system_performance["agent_performance"]
        for agent_id, perf in agent_performance.items():
            labels = {"component": "agent", "agent_id": agent_id, "role": perf["role"]}
            
            metrics.append(MetricPoint(
                name="agent_tasks_completed",
                value=perf["tasks_completed"],
                metric_type=MetricType.COUNTER,
                labels=labels
            ))
            
            metrics.append(MetricPoint(
                name="agent_average_confidence",
                value=perf["average_confidence"],
                metric_type=MetricType.GAUGE,
                labels=labels
            ))
        
        return metrics


class LearningMetricsCollector(MetricsCollector):
    """Collector for adaptive learning metrics"""
    
    def __init__(self, learning_system):
        self.learning_system = learning_system
        
    def collect_metrics(self) -> List[MetricPoint]:
        """Collect learning-specific metrics"""
        
        metrics = []
        
        # Get learning summary
        learning_summary = self.learning_system.get_learning_summary()
        
        # Learning statistics
        learning_stats = learning_summary["learning_statistics"]
        
        metrics.append(MetricPoint(
            name="learning_total_examples",
            value=learning_stats["total_examples"],
            metric_type=MetricType.COUNTER,
            labels={"component": "learning_system"}
        ))
        
        metrics.append(MetricPoint(
            name="learning_adaptations_performed",
            value=learning_stats["adaptations_performed"],
            metric_type=MetricType.COUNTER,
            labels={"component": "learning_system"}
        ))
        
        metrics.append(MetricPoint(
            name="learning_patterns_discovered",
            value=learning_stats["patterns_discovered"],
            metric_type=MetricType.GAUGE,
            labels={"component": "learning_system"}
        ))
        
        # Performance metrics
        current_performance = learning_summary["current_performance"]
        
        metrics.append(MetricPoint(
            name="learning_accuracy",
            value=current_performance["accuracy"],
            metric_type=MetricType.GAUGE,
            labels={"component": "learning_system"}
        ))
        
        # Learning effectiveness
        effectiveness = learning_summary["learning_effectiveness"]
        
        metrics.append(MetricPoint(
            name="learning_adaptation_success_rate",
            value=effectiveness["adaptation_success_rate"],
            metric_type=MetricType.GAUGE,
            labels={"component": "learning_system"}
        ))
        
        return metrics


class AnomalyDetector:
    """Detects anomalies in metrics data"""
    
    def __init__(self):
        self.metric_history = defaultdict(lambda: deque(maxlen=100))  # Keep last 100 points
        self.thresholds = {
            "default_std_dev": 2.0,      # Standard deviations for anomaly
            "min_samples": 10,            # Minimum samples for detection
            "rate_change_threshold": 0.5  # 50% change rate threshold
        }
        
    def add_metric_point(self, metric: MetricPoint):
        """Add metric point to history"""
        self.metric_history[metric.name].append(metric)
    
    def detect_anomalies(self, metric: MetricPoint) -> List[str]:
        """Detect anomalies for a metric point"""
        
        anomalies = []
        history = self.metric_history[metric.name]
        
        if len(history) < self.thresholds["min_samples"]:
            return anomalies  # Not enough data
        
        # Statistical anomaly detection
        values = [m.value for m in history]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0.0
        
        if std_val > 0:
            z_score = abs(metric.value - mean_val) / std_val
            if z_score > self.thresholds["default_std_dev"]:
                anomalies.append(f"Statistical anomaly: {metric.name} = {metric.value:.3f} (z-score: {z_score:.2f})")
        
        # Rate of change anomaly
        if len(history) >= 2:
            prev_value = history[-2].value
            if prev_value != 0:
                rate_change = abs(metric.value - prev_value) / abs(prev_value)
                if rate_change > self.thresholds["rate_change_threshold"]:
                    anomalies.append(f"Rate anomaly: {metric.name} changed by {rate_change:.2%}")
        
        return anomalies
    
    def get_metric_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        
        history = self.metric_history[metric_name]
        if not history:
            return {}
        
        values = [m.value for m in history]
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "latest": values[-1],
            "trend": self._calculate_trend(values)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear regression for trend
        n = len(values)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"


class AlertManager:
    """Manages system alerts"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
    def add_alert_rule(self, name: str, condition: Callable[[MetricPoint], bool], severity: AlertSeverity, message_template: str):
        """Add alert rule"""
        
        rule = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "message_template": message_template
        }
        self.alert_rules.append(rule)
    
    def check_metric_alerts(self, metric: MetricPoint):
        """Check metric against alert rules"""
        
        for rule in self.alert_rules:
            try:
                if rule["condition"](metric):
                    alert_id = f"{rule['name']}_{metric.name}"
                    
                    # Create or update alert
                    if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                        alert = Alert(
                            alert_id=alert_id,
                            name=rule["name"],
                            severity=rule["severity"],
                            message=rule["message_template"].format(metric=metric),
                            source=f"metric:{metric.name}",
                            metadata={"metric_value": metric.value, "labels": metric.labels}
                        )
                        
                        self.alerts[alert_id] = alert
                        self._trigger_alert(alert)
                        
            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {e}")
    
    def check_system_health_alerts(self, health_checks: List[HealthCheck]):
        """Check health checks for alerts"""
        
        for health_check in health_checks:
            if health_check.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                severity = AlertSeverity.CRITICAL if health_check.status == HealthStatus.UNHEALTHY else AlertSeverity.WARNING
                
                alert_id = f"health_{health_check.component}"
                
                if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                    alert = Alert(
                        alert_id=alert_id,
                        name=f"Health Check: {health_check.component}",
                        severity=severity,
                        message=f"Component {health_check.component} is {health_check.status.value}: {health_check.message}",
                        source=f"health_check:{health_check.component}",
                        metadata={
                            "response_time": health_check.response_time,
                            "status": health_check.status.value
                        }
                    )
                    
                    self.alerts[alert_id] = alert
                    self._trigger_alert(alert)
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for alert notifications"""
        
        self.alert_callbacks.append(callback)
    
    def _trigger_alert(self, alert: Alert):
        """Trigger alert notifications"""
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")


class HealthChecker:
    """Performs system health checks"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable[[], HealthCheck]] = {}
        
    def register_health_check(self, component: str, check_function: Callable[[], HealthCheck]):
        """Register a health check"""
        
        self.health_checks[component] = check_function
    
    def check_all_health(self) -> List[HealthCheck]:
        """Perform all registered health checks"""
        
        results = []
        
        for component, check_function in self.health_checks.items():
            try:
                start_time = time.time()
                health_check = check_function()
                health_check.response_time = time.time() - start_time
                results.append(health_check)
            except Exception as e:
                # Create failed health check
                failed_check = HealthCheck(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    response_time=0.0
                )
                results.append(failed_check)
                logger.error(f"Health check failed for {component}: {e}")
        
        return results
    
    def get_overall_health(self, health_checks: List[HealthCheck]) -> HealthStatus:
        """Get overall system health status"""
        
        if not health_checks:
            return HealthStatus.UNKNOWN
        
        status_counts = {status: 0 for status in HealthStatus}
        
        for check in health_checks:
            status_counts[check.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.HEALTHY] == len(health_checks):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


class PerformanceMonitor:
    """Monitors system performance metrics"""
    
    def __init__(self):
        self.performance_history = deque(maxlen=1000)  # Keep last 1000 snapshots
        self.monitoring_interval = 30  # seconds
        self.monitoring_active = False
        
    def start_monitoring(self):
        """Start performance monitoring"""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    snapshot = self.collect_performance_snapshot()
                    self.performance_history.append(snapshot)
                except Exception as e:
                    logger.error(f"Error collecting performance snapshot: {e}")
                
                time.sleep(self.monitoring_interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    def collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance snapshot"""
        
        # Mock implementation - in real system would use system monitoring libraries
        import psutil
        
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv
        }
        
        # Application metrics (mock)
        active_connections = 50
        request_rate = 10.5  # requests per second
        error_rate = 0.02  # 2%
        response_time_p95 = 0.150  # 150ms
        throughput = 100.0  # operations per second
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            network_io=network_io,
            active_connections=active_connections,
            request_rate=request_rate,
            error_rate=error_rate,
            response_time_p95=response_time_p95,
            throughput=throughput
        )
    
    def get_recent_performance(self, minutes: int = 5) -> List[PerformanceSnapshot]:
        """Get recent performance snapshots"""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            snapshot for snapshot in self.performance_history
            if snapshot.timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get performance summary for recent period"""
        
        recent_snapshots = self.get_recent_performance(minutes)
        
        if not recent_snapshots:
            return {"status": "no_data"}
        
        # Calculate aggregates
        cpu_values = [s.cpu_usage for s in recent_snapshots]
        memory_values = [s.memory_usage for s in recent_snapshots]
        response_times = [s.response_time_p95 for s in recent_snapshots]
        error_rates = [s.error_rate for s in recent_snapshots]
        
        return {
            "period_minutes": minutes,
            "snapshot_count": len(recent_snapshots),
            "cpu": {
                "average": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "average": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "response_time": {
                "average_p95": statistics.mean(response_times),
                "max_p95": max(response_times),
                "min_p95": min(response_times)
            },
            "error_rate": {
                "average": statistics.mean(error_rates),
                "max": max(error_rates),
                "min": min(error_rates)
            },
            "throughput": {
                "average": statistics.mean([s.throughput for s in recent_snapshots]),
                "max": max(s.throughput for s in recent_snapshots),
                "min": min(s.throughput for s in recent_snapshots)
            }
        }


class ObservabilitySystem:
    """Main observability system that coordinates all monitoring components"""
    
    def __init__(self):
        """Initialize observability system"""
        
        # Core components
        self.metrics_collectors: List[MetricsCollector] = []
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.performance_monitor = PerformanceMonitor()
        
        # Metrics storage
        self.metrics_storage: List[MetricPoint] = []
        self.metrics_storage_limit = 10000  # Keep last 10k metrics
        
        # Alert callbacks
        self._setup_default_alert_callbacks()
        
        # Default alert rules
        self._setup_default_alert_rules()
        
        # Default health checks
        self._setup_default_health_checks()
        
        logger.info("Observability system initialized")
    
    def register_metrics_collector(self, collector: MetricsCollector):
        """Register a metrics collector"""
        
        self.metrics_collectors.append(collector)
        logger.info(f"Registered metrics collector: {collector.__class__.__name__}")
    
    def collect_all_metrics(self) -> List[MetricPoint]:
        """Collect metrics from all registered collectors"""
        
        all_metrics = []
        
        for collector in self.metrics_collectors:
            try:
                metrics = collector.collect_metrics()
                all_metrics.extend(metrics)
            except Exception as e:
                logger.error(f"Error collecting metrics from {collector.__class__.__name__}: {e}")
        
        # Store metrics
        self._store_metrics(all_metrics)
        
        # Check for anomalies
        for metric in all_metrics:
            self.anomaly_detector.add_metric_point(metric)
            anomalies = self.anomaly_detector.detect_anomalies(metric)
            
            if anomalies:
                self._create_anomaly_alerts(metric, anomalies)
        
        # Check for metric alerts
        for metric in all_metrics:
            self.alert_manager.check_metric_alerts(metric)
        
        return all_metrics
    
    def _store_metrics(self, metrics: List[MetricPoint]):
        """Store metrics with size limit"""
        
        self.metrics_storage.extend(metrics)
        
        # Enforce storage limit
        if len(self.metrics_storage) > self.metrics_storage_limit:
            excess = len(self.metrics_storage) - self.metrics_storage_limit
            self.metrics_storage = self.metrics_storage[excess:]
    
    def _create_anomaly_alerts(self, metric: MetricPoint, anomalies: List[str]):
        """Create alerts for detected anomalies"""
        
        for anomaly in anomalies:
            alert = Alert(
                alert_id=f"anomaly_{metric.name}_{int(metric.timestamp.timestamp())}",
                name=f"Anomaly Detected: {metric.name}",
                severity=AlertSeverity.WARNING,
                message=f"Anomaly in {metric.name}: {anomaly}",
                source=f"anomaly_detector:{metric.name}",
                metadata={
                    "metric_value": metric.value,
                    "anomaly_description": anomaly,
                    "labels": metric.labels
                }
            )
            
            self.alert_manager.alerts[alert.alert_id] = alert
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Alert):
        """Trigger alert notification"""
        
        # Log alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        logger.log(log_level, f"ALERT: {alert.name} - {alert.message}")
        
        # Call alert callbacks
        for callback in self.alert_manager.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        
        health_checks = self.health_checker.check_all_health()
        overall_health = self.health_checker.get_overall_health(health_checks)
        
        # Check for health alerts
        self.alert_manager.check_system_health_alerts(health_checks)
        
        return {
            "overall_status": overall_health.value,
            "timestamp": datetime.now().isoformat(),
            "component_health": [
                {
                    "component": check.component,
                    "status": check.status.value,
                    "message": check.message,
                    "response_time": check.response_time
                }
                for check in health_checks
            ],
            "active_alerts": len(self.alert_manager.get_active_alerts())
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        
        # Recent metrics
        recent_metrics = self.metrics_storage[-100:]  # Last 100 metrics
        
        # Active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        # System health
        health_status = self.check_system_health()
        
        # Performance summary
        performance_summary = self.performance_monitor.get_performance_summary(5)
        
        # Metric statistics
        metric_names = set(metric.name for metric in recent_metrics)
        metric_stats = {}
        
        for metric_name in metric_names:
            metric_stats[metric_name] = self.anomaly_detector.get_metric_statistics(metric_name)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": health_status,
            "active_alerts": [
                {
                    "id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ],
            "performance": performance_summary,
            "metrics_summary": {
                "total_metrics": len(recent_metrics),
                "metric_types": list(metric_names),
                "metric_statistics": metric_stats
            },
            "collectors_status": [
                {
                    "name": collector.__class__.__name__,
                    "status": "active"
                }
                for collector in self.metrics_collectors
            ]
        }
    
    def get_observability_summary(self) -> Dict[str, Any]:
        """Get comprehensive observability summary"""
        
        return {
            "system_info": {
                "monitoring_active": self.performance_monitor.monitoring_active,
                "metrics_collectors": len(self.metrics_collectors),
                "alert_rules": len(self.alert_manager.alert_rules),
                "health_checks": len(self.health_checker.health_checks),
                "metrics_stored": len(self.metrics_storage)
            },
            "recent_activity": {
                "alerts_triggered": len(self.alert_manager.get_active_alerts()),
                "anomalies_detected": len([
                    alert for alert in self.alert_manager.get_active_alerts()
                    if "anomaly" in alert.alert_id
                ]),
                "health_issues": len([
                    check for check in self.health_checker.check_all_health()
                    if check.status != HealthStatus.HEALTHY
                ])
            },
            "performance_trends": {
                "cpu_trend": self.anomaly_detector.get_metric_statistics("cpu_usage").get("trend", "unknown"),
                "memory_trend": self.anomaly_detector.get_metric_statistics("memory_usage").get("trend", "unknown"),
                "error_rate_trend": self.anomaly_detector.get_metric_statistics("error_rate").get("trend", "unknown")
            }
        }
    
    def _setup_default_alert_callbacks(self):
        """Setup default alert callbacks"""
        
        def log_alert(alert: Alert):
            """Default alert logging callback"""
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.ERROR: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.INFO)
            
            logger.log(log_level, f"ALERT [{alert.severity.value.upper()}]: {alert.message}")
        
        self.alert_manager.add_alert_callback(log_alert)
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        
        # High error rate alert
        self.alert_manager.add_alert_rule(
            name="High Error Rate",
            condition=lambda metric: metric.name == "error_rate" and metric.value > 0.05,
            severity=AlertSeverity.ERROR,
            message_template="High error rate detected: {metric.value:.2%}"
        )
        
        # Low confidence alert
        self.alert_manager.add_alert_rule(
            name="Low Confidence",
            condition=lambda metric: metric.name.endswith("_confidence") and metric.value < 0.3,
            severity=AlertSeverity.WARNING,
            message_template="Low confidence in {metric.name}: {metric.value:.3f}"
        )
        
        # High response time alert
        self.alert_manager.add_alert_rule(
            name="High Response Time",
            condition=lambda metric: metric.name == "response_time_p95" and metric.value > 1.0,
            severity=AlertSeverity.WARNING,
            message_template="High response time: {metric.value:.3f}s"
        )
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        
        def metrics_collector_health() -> HealthCheck:
            """Health check for metrics collectors"""
            
            if not self.metrics_collectors:
                return HealthCheck(
                    component="metrics_collectors",
                    status=HealthStatus.UNHEALTHY,
                    message="No metrics collectors registered",
                    response_time=0.0
                )
            
            # Try to collect metrics
            try:
                start_time = time.time()
                metrics = self.collect_all_metrics()
                response_time = time.time() - start_time
                
                if len(metrics) == 0:
                    return HealthCheck(
                        component="metrics_collectors",
                        status=HealthStatus.DEGRADED,
                        message="No metrics collected",
                        response_time=response_time
                    )
                
                return HealthCheck(
                    component="metrics_collectors",
                    status=HealthStatus.HEALTHY,
                    message=f"Collected {len(metrics)} metrics",
                    response_time=response_time
                )
                
            except Exception as e:
                return HealthCheck(
                    component="metrics_collectors",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error collecting metrics: {str(e)}",
                    response_time=0.0
                )
        
        def storage_health() -> HealthCheck:
            """Health check for metrics storage"""
            
            storage_usage = len(self.metrics_storage) / self.metrics_storage_limit
            
            if storage_usage > 0.9:
                status = HealthStatus.DEGRADED
                message = f"Storage usage high: {storage_usage:.1%}"
            elif storage_usage > 0.95:
                status = HealthStatus.UNHEALTHY
                message = f"Storage usage critical: {storage_usage:.1%}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Storage usage normal: {storage_usage:.1%}"
            
            return HealthCheck(
                component="metrics_storage",
                status=status,
                message=message,
                response_time=0.0
            )
        
        self.health_checker.register_health_check("metrics_collectors", metrics_collector_health)
        self.health_checker.register_health_check("metrics_storage", storage_health)
    
    def start_monitoring(self):
        """Start all monitoring processes"""
        
        self.performance_monitor.start_monitoring()
        logger.info("Observability monitoring started")
    
    def stop_monitoring(self):
        """Stop all monitoring processes"""
        
        self.performance_monitor.stop_monitoring()
        logger.info("Observability monitoring stopped")


# Global observability system instance
_global_observability_system: Optional[ObservabilitySystem] = None


def get_observability_system() -> ObservabilitySystem:
    """Get global observability system instance"""
    global _global_observability_system
    if _global_observability_system is None:
        _global_observability_system = ObservabilitySystem()
    return _global_observability_system
