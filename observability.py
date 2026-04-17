"""
Observability Configuration - OpenTelemetry & Phoenix/Arize

This module sets up distributed tracing and metrics collection for the
Agentic HO3 Underwriting Studio using OpenTelemetry and Phoenix.

Key capabilities:
- Distributed tracing for workflow execution
- Agent-level tracing for decision-making
- Tool call instrumentation
- Metrics collection (latency, decision outcomes, retrieval hit rates)
- Phoenix/Arize integration for trace visualization
"""

import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from phoenix.otel import register
import logging

logger = logging.getLogger(__name__)


class ObservabilityConfig:
    """
    Central configuration for OpenTelemetry and Phoenix/Arize integration.
    """
    
    def __init__(
        self,
        service_name: str = "agentic-underwriting",
        service_version: str = "1.0.0",
        environment: str = "development",
        phoenix_endpoint: Optional[str] = None,
        otlp_endpoint: Optional[str] = None
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.phoenix_endpoint = phoenix_endpoint or os.getenv(
            "PHOENIX_ENDPOINT", 
            "http://localhost:6006"
        )
        self.otlp_endpoint = otlp_endpoint or os.getenv(
            "OTLP_ENDPOINT",
            "http://localhost:4317"  # Phoenix OTLP collector typically on 4317
        )
        # Phoenix collector endpoint (different from UI endpoint)
        # Phoenix accepts traces via gRPC at 4317
        self.phoenix_collector_endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "localhost:4317"
        )
        
        self._tracer = None
        self._meter = None
        self._initialized = False
    
    def initialize(self):
        """
        Initialize OpenTelemetry tracing and metrics.
        """
        if self._initialized:
            logger.warning("Observability already initialized")
            return
        
        try:
            # Create resource with service metadata
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                "service.version": self.service_version,
                "deployment.environment": self.environment,
            })
            
            # Set up tracer provider with Phoenix exporter
            tracer_provider = TracerProvider(resource=resource)
            
            # Export traces to Phoenix's OTLP collector
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.phoenix_collector_endpoint,
                insecure=True
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Set global tracer provider
            trace.set_tracer_provider(tracer_provider)
            self._tracer = trace.get_tracer(__name__)
            
            logger.info(f"Tracing initialized, exporting to {self.phoenix_collector_endpoint}")
            
            # Set up metrics
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=self.phoenix_collector_endpoint,
                    insecure=True
                ),
                export_interval_millis=60000
            )
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(meter_provider)
            self._meter = metrics.get_meter(__name__)
            
            self._initialized = True
            logger.info("Observability initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize observability: {e}", exc_info=True)
            # Don't fail the application if observability setup fails
            self._tracer = trace.get_tracer(__name__)
            self._meter = metrics.get_meter(__name__)
    
    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application for automatic tracing.
        """
        if not self._initialized:
            self.initialize()
        
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)
    
    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine for database query tracing.
        """
        if not self._initialized:
            self.initialize()
        
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}", exc_info=True)
    
    def get_tracer(self, name: str = None) -> trace.Tracer:
        """
        Get a tracer for creating spans.
        """
        if not self._initialized:
            self.initialize()
        return trace.get_tracer(name or __name__)
    
    def get_meter(self, name: str = None) -> metrics.Meter:
        """
        Get a meter for creating metrics.
        """
        if not self._initialized:
            self.initialize()
        return metrics.get_meter(name or __name__)
    
    def record_metric(self, name: str, value: float, attributes: dict = None):
        """
        Record a metric value.
        """
        if not self._initialized:
            self.initialize()
        
        try:
            meter = self.get_meter()
            counter = meter.create_counter(
                name,
                description=f"Metric: {name}"
            )
            counter.add(value, attributes or {})
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")


# Global observability instance
observability = ObservabilityConfig()


def get_tracer(name: str = None) -> trace.Tracer:
    """
    Convenience function to get a tracer.
    """
    return observability.get_tracer(name)


def get_meter(name: str = None) -> metrics.Meter:
    """
    Convenience function to get a meter.
    """
    return observability.get_meter(name)


def record_workflow_latency(workflow_name: str, duration_ms: float, status: str):
    """
    Record workflow execution latency.
    """
    observability.record_metric(
        "workflow.latency",
        duration_ms,
        {
            "workflow.name": workflow_name,
            "workflow.status": status,
            "service.name": observability.service_name
        }
    )


def record_agent_decision(agent_name: str, decision: str, confidence: float):
    """
    Record agent decision.
    """
    observability.record_metric(
        "agent.decision",
        1,
        {
            "agent.name": agent_name,
            "decision": decision,
            "confidence": str(confidence),
            "service.name": observability.service_name
        }
    )


def record_tool_call(tool_name: str, success: bool, duration_ms: float):
    """
    Record tool call execution.
    """
    observability.record_metric(
        "tool.call",
        1,
        {
            "tool.name": tool_name,
            "success": str(success),
            "duration_ms": str(duration_ms),
            "service.name": observability.service_name
        }
    )


def record_retrieval_hit(query: str, hit_count: int, latency_ms: float):
    """
    Record retrieval operation.
    """
    observability.record_metric(
        "retrieval.hit",
        hit_count,
        {
            "query_length": str(len(query)),
            "latency_ms": str(latency_ms),
            "service.name": observability.service_name
        }
    )
