"""
API Documentation Generator
Generates Swagger/OpenAPI documentation for the API
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class APIEndpoint:
    """API endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    security: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class APISchema:
    """API schema definition"""
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    description: str = ""


class OpenAPIDocumentation:
    """OpenAPI 3.0 documentation generator"""
    
    def __init__(
        self,
        title: str = "AgenticQuote API",
        version: str = "1.0.0",
        description: str = "API for AgenticQuote underwriting platform"
    ):
        self.title = title
        self.version = version
        self.description = description
        self.endpoints: List[APIEndpoint] = []
        self.schemas: Dict[str, APISchema] = {}
        self.servers: List[Dict[str, str]] = []
        self.tags: List[Dict[str, str]] = []
    
    def add_server(self, url: str, description: str = ""):
        """Add a server to the documentation"""
        self.servers.append({
            "url": url,
            "description": description
        })
    
    def add_tag(self, name: str, description: str = ""):
        """Add a tag to the documentation"""
        self.tags.append({
            "name": name,
            "description": description
        })
    
    def add_endpoint(self, endpoint: APIEndpoint):
        """Add an endpoint to the documentation"""
        self.endpoints.append(endpoint)
    
    def add_schema(self, schema: APISchema):
        """Add a schema definition"""
        self.schemas[schema.name] = schema
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate the complete OpenAPI specification"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "servers": self.servers,
            "tags": self.tags,
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }
        
        # Add endpoints
        for endpoint in self.endpoints:
            path_item = spec["paths"].setdefault(endpoint.path, {})
            
            path_item[endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "parameters": endpoint.parameters,
                "requestBody": endpoint.request_body,
                "responses": endpoint.responses,
                "tags": endpoint.tags,
                "security": endpoint.security
            }
        
        # Add schemas
        for schema_name, schema in self.schemas.items():
            spec["components"]["schemas"][schema_name] = {
                "type": schema.type,
                "properties": schema.properties,
                "required": schema.required,
                "description": schema.description
            }
        
        return spec
    
    def generate_json(self) -> str:
        """Generate OpenAPI specification as JSON"""
        return json.dumps(self.generate_openapi_spec(), indent=2)
    
    def generate_yaml(self) -> str:
        """Generate OpenAPI specification as YAML"""
        import yaml
        return yaml.dump(self.generate_openapi_spec(), default_flow_style=False)


class EndpointBuilder:
    """Builder for creating API endpoint documentation"""
    
    def __init__(self, path: str, method: str):
        self.endpoint = APIEndpoint(
            path=path,
            method=method,
            summary="",
            description=""
        )
    
    def summary(self, summary: str) -> 'EndpointBuilder':
        """Set endpoint summary"""
        self.endpoint.summary = summary
        return self
    
    def description(self, description: str) -> 'EndpointBuilder':
        """Set endpoint description"""
        self.endpoint.description = description
        return self
    
    def add_parameter(
        self,
        name: str,
        param_type: str,
        data_type: str,
        required: bool = False,
        description: str = ""
    ) -> 'EndpointBuilder':
        """Add a parameter to the endpoint"""
        self.endpoint.parameters.append({
            "name": name,
            "in": param_type,
            "schema": {"type": data_type},
            "required": required,
            "description": description
        })
        return self
    
    def set_request_body(
        self,
        content_type: str = "application/json",
        schema_name: Optional[str] = None,
        example: Optional[Dict[str, Any]] = None
    ) -> 'EndpointBuilder':
        """Set the request body"""
        body = {
            "content": {
                content_type: {
                    "schema": {}
                }
            }
        }
        
        if schema_name:
            body["content"][content_type]["schema"] = {"$ref": f"#/components/schemas/{schema_name}"}
        
        if example:
            body["content"][content_type]["example"] = example
        
        self.endpoint.request_body = body
        return self
    
    def add_response(
        self,
        status_code: str,
        description: str,
        schema_name: Optional[str] = None,
        example: Optional[Dict[str, Any]] = None
    ) -> 'EndpointBuilder':
        """Add a response to the endpoint"""
        response = {
            "description": description,
            "content": {
                "application/json": {
                    "schema": {}
                }
            }
        }
        
        if schema_name:
            response["content"]["application/json"]["schema"] = {
                "$ref": f"#/components/schemas/{schema_name}"
            }
        
        if example:
            response["content"]["application/json"]["example"] = example
        
        self.endpoint.responses[status_code] = response
        return self
    
    def add_tag(self, tag: str) -> 'EndpointBuilder':
        """Add a tag to the endpoint"""
        self.endpoint.tags.append(tag)
        return self
    
    def set_security(self, scheme: str = "bearerAuth") -> 'EndpointBuilder':
        """Set security requirement"""
        self.endpoint.security.append({scheme: []})
        return self
    
    def build(self) -> APIEndpoint:
        """Build the endpoint"""
        return self.endpoint


class SchemaBuilder:
    """Builder for creating API schema definitions"""
    
    def __init__(self, name: str, schema_type: str = "object"):
        self.schema = APISchema(
            name=name,
            type=schema_type
        )
    
    def add_property(
        self,
        name: str,
        prop_type: str,
        description: str = "",
        required: bool = False
    ) -> 'SchemaBuilder':
        """Add a property to the schema"""
        self.schema.properties[name] = {
            "type": prop_type,
            "description": description
        }
        
        if required:
            self.schema.required.append(name)
        
        return self
    
    def set_description(self, description: str) -> 'SchemaBuilder':
        """Set schema description"""
        self.schema.description = description
        return self
    
    def build(self) -> APISchema:
        """Build the schema"""
        return self.schema


# Global documentation instance
docs = OpenAPIDocumentation()


def generate_default_docs() -> OpenAPIDocumentation:
    """Generate default API documentation"""
    documentation = OpenAPIDocumentation()
    
    # Add servers
    documentation.add_server("http://localhost:8000", "Local development")
    documentation.add_server("https://api.agenticquote.com", "Production")
    
    # Add tags
    documentation.add_tag("cases", "Case management endpoints")
    documentation.add_tag("agents", "AI agent endpoints")
    documentation.add_tag("webhooks", "Webhook management")
    documentation.add_tag("auth", "Authentication and authorization")
    
    # Add case endpoints
    cases_endpoint = (
        EndpointBuilder("/api/v1/cases", "GET")
        .summary("List all cases")
        .description("Retrieve a paginated list of all cases")
        .add_parameter("page", "query", "integer", False, "Page number")
        .add_parameter("limit", "query", "integer", False, "Items per page")
        .add_parameter("status", "query", "string", False, "Filter by status")
        .add_response("200", "Successful response", "CaseList", {
            "cases": [
                {"id": "1001", "status": "pending", "risk_level": "low"}
            ],
            "total": 100,
            "page": 1,
            "limit": 10
        })
        .add_tag("cases")
        .set_security()
        .build()
    )
    documentation.add_endpoint(cases_endpoint)
    
    # Add case creation endpoint
    create_case_endpoint = (
        EndpointBuilder("/api/v1/cases", "POST")
        .summary("Create a new case")
        .description("Create a new underwriting case")
        .set_request_body(schema_name="CaseCreate", example={
            "property_address": "123 Main St",
            "property_value": 500000,
            "coverage_amount": 400000
        })
        .add_response("201", "Case created successfully", "Case", {
            "id": "1001",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        })
        .add_tag("cases")
        .set_security()
        .build()
    )
    documentation.add_endpoint(create_case_endpoint)
    
    # Add schemas
    case_schema = (
        SchemaBuilder("Case", "object")
        .add_property("id", "string", "Case ID", True)
        .add_property("status", "string", "Case status", True)
        .add_property("risk_level", "string", "Risk assessment", False)
        .add_property("created_at", "string", "Creation timestamp", True)
        .set_description("Underwriting case information")
        .build()
    )
    documentation.add_schema(case_schema)
    
    return documentation
