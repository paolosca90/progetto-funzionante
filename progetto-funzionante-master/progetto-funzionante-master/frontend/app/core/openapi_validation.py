"""
OpenAPI Validation and Testing System

This module provides comprehensive OpenAPI specification validation, automated testing,
and documentation quality assurance for the AI Cash Revolution Trading API.

Features:
- OpenAPI 3.0 specification validation
- Automated endpoint testing
- Response validation against schemas
- Performance testing
- Security testing
- Documentation quality checks
- Test report generation
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional, Tuple
import json
import asyncio
import aiohttp
import time
import re
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError as JsonSchemaValidationError

# Import existing modules
from app.core.openapi_docs import custom_openapi
from app.core.security_schemes import SECURITY_SCHEMES
from app.core.error_handling import (
    StructuredError, ErrorCategory, ErrorSeverity, ErrorHandler
)

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TestCategory(Enum):
    """Test categories for organization"""
    SCHEMA_VALIDATION = "schema_validation"
    ENDPOINT_FUNCTIONALITY = "endpoint_functionality"
    RESPONSE_VALIDATION = "response_validation"
    SECURITY_TESTING = "security_testing"
    PERFORMANCE_TESTING = "performance_testing"
    DOCUMENTATION_QUALITY = "documentation_quality"

class ValidationResult(BaseModel):
    """Individual validation result"""
    category: TestCategory
    level: ValidationLevel
    test_name: str
    description: str
    details: Optional[Dict[str, Any]] = None
    passed: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TestReport(BaseModel):
    """Comprehensive test report"""
    summary: Dict[str, Any]
    results: List[ValidationResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    warnings: int
    errors: int
    execution_time: float
    openapi_compliance_score: float
    recommendations: List[str]

class OpenAPIValidator:
    """OpenAPI specification validator and tester"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.test_client = TestClient(app)
        self.openapi_schema = None
        self.results = []
        self.start_time = None

    async def run_comprehensive_validation(self) -> TestReport:
        """Run all validation tests and generate comprehensive report"""
        self.start_time = time.time()
        self.results = []

        # Get OpenAPI schema
        self.openapi_schema = custom_openapi(self.app)

        # Run all validation categories
        await self._validate_schema_structure()
        await self._test_endpoint_functionality()
        await self._validate_response_schemas()
        await self._test_security_implementations()
        await self._test_performance()
        await self._validate_documentation_quality()

        # Generate report
        return self._generate_report()

    async def _validate_schema_structure(self):
        """Validate OpenAPI schema structure and compliance"""
        logger.info("Starting OpenAPI schema validation...")

        # Basic structure validation
        required_fields = ['openapi', 'info', 'paths', 'components']
        for field in required_fields:
            if field not in self.openapi_schema:
                self._add_result(
                    category=TestCategory.SCHEMA_VALIDATION,
                    level=ValidationLevel.ERROR,
                    test_name="required_field_missing",
                    description=f"Required OpenAPI field '{field}' is missing",
                    details={"missing_field": field}
                )

        # Validate OpenAPI version
        if 'openapi' in self.openapi_schema:
            version = self.openapi_schema['openapi']
            if not version.startswith('3.'):
                self._add_result(
                    category=TestCategory.SCHEMA_VALIDATION,
                    level=ValidationLevel.WARNING,
                    test_name="openapi_version",
                    description=f"OpenAPI version {version} detected. 3.0.x recommended.",
                    details={"version": version}
                )

        # Validate info section
        if 'info' in self.openapi_schema:
            info = self.openapi_schema['info']
            info_fields = ['title', 'version', 'description']
            for field in info_fields:
                if field not in info or not info[field]:
                    self._add_result(
                        category=TestCategory.SCHEMA_VALIDATION,
                        level=ValidationLevel.WARNING,
                        test_name="info_field_missing",
                        description=f"Info field '{field}' is missing or empty",
                        details={"field": field}
                    )

        # Validate security schemes
        if 'components' in self.openapi_schema and 'securitySchemes' in self.openapi_schema['components']:
            security_schemes = self.openapi_schema['components']['securitySchemes']
            for scheme_name, scheme in security_schemes.items():
                await self._validate_security_scheme(scheme_name, scheme)

        # Validate schemas
        if 'components' in self.openapi_schema and 'schemas' in self.openapi_schema['components']:
            schemas = self.openapi_schema['components']['schemas']
            for schema_name, schema in schemas.items():
                await self._validate_schema_definition(schema_name, schema)

    async def _validate_security_scheme(self, scheme_name: str, scheme: Dict[str, Any]):
        """Validate individual security scheme definition"""
        if 'type' not in scheme:
            self._add_result(
                category=TestCategory.SCHEMA_VALIDATION,
                level=ValidationLevel.ERROR,
                test_name="security_scheme_type_missing",
                description=f"Security scheme '{scheme_name}' missing type",
                details={"scheme": scheme_name}
            )
            return

        scheme_type = scheme['type']
        if scheme_type == 'http':
            if 'scheme' not in scheme:
                self._add_result(
                    category=TestCategory.SCHEMA_VALIDATION,
                    level=ValidationLevel.ERROR,
                    test_name="http_scheme_missing",
                    description=f"HTTP security scheme '{scheme_name}' missing scheme",
                    details={"scheme": scheme_name}
                )
        elif scheme_type == 'apiKey':
            if 'name' not in scheme or 'in' not in scheme:
                self._add_result(
                    category=TestCategory.SCHEMA_VALIDATION,
                    level=ValidationLevel.ERROR,
                    test_name="apikey_details_missing",
                    description=f"API key scheme '{scheme_name}' missing name or location",
                    details={"scheme": scheme_name}
                )

    async def _validate_schema_definition(self, schema_name: str, schema: Dict[str, Any]):
        """Validate individual schema definition"""
        if 'type' not in schema:
            self._add_result(
                category=TestCategory.SCHEMA_VALIDATION,
                level=ValidationLevel.WARNING,
                test_name="schema_type_missing",
                description=f"Schema '{schema_name}' missing type definition",
                details={"schema": schema_name}
            )
            return

        # Check for proper description
        if 'description' not in schema or not schema['description']:
            self._add_result(
                category=TestCategory.SCHEMA_VALIDATION,
                level=ValidationLevel.WARNING,
                test_name="schema_description_missing",
                description=f"Schema '{schema_name}' missing description",
                details={"schema": schema_name}
            )

        # Validate object schemas
        if schema['type'] == 'object':
            if 'properties' not in schema:
                self._add_result(
                    category=TestCategory.SCHEMA_VALIDATION,
                    level=ValidationLevel.WARNING,
                    test_name="object_schema_properties_missing",
                    description=f"Object schema '{schema_name}' missing properties",
                    details={"schema": schema_name}
                )
            else:
                for prop_name, prop_schema in schema['properties'].items():
                    if 'type' not in prop_schema:
                        self._add_result(
                            category=TestCategory.SCHEMA_VALIDATION,
                            level=ValidationLevel.WARNING,
                            test_name="property_type_missing",
                            description=f"Property '{prop_name}' in schema '{schema_name}' missing type",
                            details={"schema": schema_name, "property": prop_name}
                        )

    async def _test_endpoint_functionality(self):
        """Test endpoint functionality and accessibility"""
        logger.info("Testing endpoint functionality...")

        if 'paths' not in self.openapi_schema:
            return

        for path, path_item in self.openapi_schema['paths'].items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    await self._test_endpoint(path, method, operation)

    async def _test_endpoint(self, path: str, method: str, operation: Dict[str, Any]):
        """Test individual endpoint"""
        test_name = f"{method.upper()} {path}"

        try:
            # Skip endpoints that require authentication for basic functionality test
            if self._requires_authentication(operation):
                self._add_result(
                    category=TestCategory.ENDPOINT_FUNCTIONALITY,
                    level=ValidationLevel.INFO,
                    test_name="endpoint_skipped_auth_required",
                    description=f"Endpoint {test_name} requires authentication",
                    details={"path": path, "method": method}
                )
                return

            # Test endpoint response
            response = self.test_client.request(method, path)

            if response.status_code in [200, 201, 202, 204]:
                self._add_result(
                    category=TestCategory.ENDPOINT_FUNCTIONALITY,
                    level=ValidationLevel.INFO,
                    test_name="endpoint_accessible",
                    description=f"Endpoint {test_name} is accessible",
                    details={
                        "path": path,
                        "method": method,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
                )
            else:
                self._add_result(
                    category=TestCategory.ENDPOINT_FUNCTIONALITY,
                    level=ValidationLevel.WARNING,
                    test_name="endpoint_unexpected_response",
                    description=f"Endpoint {test_name} returned unexpected status code",
                    details={
                        "path": path,
                        "method": method,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )

        except Exception as e:
            self._add_result(
                category=TestCategory.ENDPOINT_FUNCTIONALITY,
                level=ValidationLevel.ERROR,
                test_name="endpoint_test_failed",
                description=f"Failed to test endpoint {test_name}: {str(e)}",
                details={"path": path, "method": method, "error": str(e)}
            )

    def _requires_authentication(self, operation: Dict[str, Any]) -> bool:
        """Check if endpoint requires authentication"""
        if 'security' in operation:
            return True
        return False

    async def _validate_response_schemas(self):
        """Validate response schemas match actual responses"""
        logger.info("Validating response schemas...")

        # This would require more complex implementation with actual response validation
        # For now, we'll check if response schemas are defined
        if 'paths' not in self.openapi_schema:
            return

        for path, path_item in self.openapi_schema['paths'].items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    if 'responses' in operation:
                        await self._validate_operation_responses(path, method, operation['responses'])

    async def _validate_operation_responses(self, path: str, method: str, responses: Dict[str, Any]):
        """Validate operation response definitions"""
        for status_code, response in responses.items():
            if 'description' not in response or not response['description']:
                self._add_result(
                    category=TestCategory.RESPONSE_VALIDATION,
                    level=ValidationLevel.WARNING,
                    test_name="response_description_missing",
                    description=f"Response for {method.upper()} {path} status {status_code} missing description",
                    details={"path": path, "method": method, "status_code": status_code}
                )

            # Check for content and schema
            if 'content' in response:
                for content_type, content in response['content'].items():
                    if 'schema' not in content:
                        self._add_result(
                            category=TestCategory.RESPONSE_VALIDATION,
                            level=ValidationLevel.WARNING,
                            test_name="response_schema_missing",
                            description=f"Response for {method.upper()} {path} status {status_code} content type {content_type} missing schema",
                            details={"path": path, "method": method, "status_code": status_code, "content_type": content_type}
                        )

    async def _test_security_implementations(self):
        """Test security implementations"""
        logger.info("Testing security implementations...")

        # Test authentication endpoints
        auth_endpoints = [
            ('POST', '/register'),
            ('POST', '/token'),
            ('POST', '/login'),
        ]

        for method, path in auth_endpoints:
            try:
                response = self.test_client.request(method, path)
                if response.status_code == 404:
                    self._add_result(
                        category=TestCategory.SECURITY_TESTING,
                        level=ValidationLevel.WARNING,
                        test_name="auth_endpoint_missing",
                        description=f"Authentication endpoint {method} {path} not found",
                        details={"method": method, "path": path}
                    )
            except Exception as e:
                self._add_result(
                    category=TestCategory.SECURITY_TESTING,
                    level=ValidationLevel.ERROR,
                    test_name="auth_endpoint_test_failed",
                    description=f"Failed to test auth endpoint {method} {path}: {str(e)}",
                    details={"method": method, "path": path, "error": str(e)}
                )

        # Check for security scheme implementations
        if 'components' in self.openapi_schema and 'securitySchemes' in self.openapi_schema['components']:
            security_schemes = self.openapi_schema['components']['securitySchemes']
            if not security_schemes:
                self._add_result(
                    category=TestCategory.SECURITY_TESTING,
                    level=ValidationLevel.WARNING,
                    test_name="no_security_schemes",
                    description="No security schemes defined in OpenAPI specification"
                )
        else:
            self._add_result(
                category=TestCategory.SECURITY_TESTING,
                level=ValidationLevel.ERROR,
                test_name="security_component_missing",
                description="Security schemes component missing from OpenAPI specification"
            )

    async def _test_performance(self):
        """Test API performance"""
        logger.info("Testing API performance...")

        # Test basic endpoints performance
        test_endpoints = [
            ('GET', '/'),
            ('GET', '/health'),
            ('GET', '/docs'),
        ]

        for method, path in test_endpoints:
            try:
                # Test multiple requests
                response_times = []
                for _ in range(5):
                    start_time = time.time()
                    response = self.test_client.request(method, path)
                    response_times.append(time.time() - start_time)

                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)

                if avg_response_time > 1.0:  # More than 1 second average
                    self._add_result(
                        category=TestCategory.PERFORMANCE_TESTING,
                        level=ValidationLevel.WARNING,
                        test_name="slow_endpoint",
                        description=f"Endpoint {method} {path} has slow average response time",
                        details={
                            "method": method,
                            "path": path,
                            "avg_response_time": avg_response_time,
                            "max_response_time": max_response_time,
                            "requests_tested": len(response_times)
                        }
                    )
                else:
                    self._add_result(
                        category=TestCategory.PERFORMANCE_TESTING,
                        level=ValidationLevel.INFO,
                        test_name="performance_test",
                        description=f"Endpoint {method} {path} performance test completed",
                        details={
                            "method": method,
                            "path": path,
                            "avg_response_time": avg_response_time,
                            "max_response_time": max_response_time,
                            "requests_tested": len(response_times)
                        }
                    )

            except Exception as e:
                self._add_result(
                    category=TestCategory.PERFORMANCE_TESTING,
                    level=ValidationLevel.ERROR,
                    test_name="performance_test_failed",
                    description=f"Failed to test performance for {method} {path}: {str(e)}",
                    details={"method": method, "path": path, "error": str(e)}
                )

    async def _validate_documentation_quality(self):
        """Validate documentation quality and completeness"""
        logger.info("Validating documentation quality...")

        # Check for comprehensive descriptions
        if 'paths' in self.openapi_schema:
            for path, path_item in self.openapi_schema['paths'].items():
                if 'description' not in path_item or not path_item['description']:
                    self._add_result(
                        category=TestCategory.DOCUMENTATION_QUALITY,
                        level=ValidationLevel.WARNING,
                        test_name="path_description_missing",
                        description=f"Path '{path}' missing description",
                        details={"path": path}
                    )

                for method, operation in path_item.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                        await self._validate_operation_documentation(path, method, operation)

        # Check for examples
        if 'components' in self.openapi_schema and 'examples' in self.openapi_schema['components']:
            examples = self.openapi_schema['components']['examples']
            if not examples:
                self._add_result(
                    category=TestCategory.DOCUMENTATION_QUALITY,
                    level=ValidationLevel.WARNING,
                    test_name="no_examples",
                    description="No examples defined in OpenAPI specification"
                )
        else:
            self._add_result(
                category=TestCategory.DOCUMENTATION_QUALITY,
                level=ValidationLevel.INFO,
                test_name="examples_component_missing",
                description="Examples component not found in OpenAPI specification"
            )

    async def _validate_operation_documentation(self, path: str, method: str, operation: Dict[str, Any]):
        """Validate individual operation documentation"""
        operation_id = f"{method.upper()} {path}"

        if 'summary' not in operation or not operation['summary']:
            self._add_result(
                category=TestCategory.DOCUMENTATION_QUALITY,
                level=ValidationLevel.WARNING,
                test_name="operation_summary_missing",
                description=f"Operation {operation_id} missing summary",
                details={"path": path, "method": method}
            )

        if 'description' not in operation or not operation['description']:
            self._add_result(
                category=TestCategory.DOCUMENTATION_QUALITY,
                level=ValidationLevel.WARNING,
                test_name="operation_description_missing",
                description=f"Operation {operation_id} missing description",
                details={"path": path, "method": method}
            )

        # Check for tags
        if 'tags' not in operation or not operation['tags']:
            self._add_result(
                category=TestCategory.DOCUMENTATION_QUALITY,
                level=ValidationLevel.WARNING,
                test_name="operation_tags_missing",
                description=f"Operation {operation_id} missing tags",
                details={"path": path, "method": method}
            )

    def _add_result(self, category: TestCategory, level: ValidationLevel, test_name: str, description: str, details: Optional[Dict[str, Any]] = None):
        """Add validation result"""
        result = ValidationResult(
            category=category,
            level=level,
            test_name=test_name,
            description=description,
            details=details,
            passed=level in [ValidationLevel.INFO]
        )
        self.results.append(result)

    def _generate_report(self) -> TestReport:
        """Generate comprehensive test report"""
        execution_time = time.time() - self.start_time

        # Calculate summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.passed])
        failed_tests = len([r for r in self.results if not r.passed])
        warnings = len([r for r in self.results if r.level == ValidationLevel.WARNING])
        errors = len([r for r in self.results if r.level == ValidationLevel.ERROR])

        # Calculate compliance score
        info_tests = len([r for r in self.results if r.level == ValidationLevel.INFO])
        compliance_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Create summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warnings": warnings,
            "errors": errors,
            "compliance_score": compliance_score,
            "execution_time": execution_time,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "openapi_version": self.openapi_schema.get('openapi', 'Unknown') if self.openapi_schema else 'Unknown',
            "api_version": self.openapi_schema.get('info', {}).get('version', 'Unknown') if self.openapi_schema else 'Unknown'
        }

        return TestReport(
            summary=summary,
            results=self.results,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warnings=warnings,
            errors=errors,
            execution_time=execution_time,
            openapi_compliance_score=compliance_score,
            recommendations=recommendations
        )

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on test results"""
        recommendations = []

        # Analyze results for common issues
        error_results = [r for r in self.results if r.level == ValidationLevel.ERROR]
        warning_results = [r for r in self.results if r.level == ValidationLevel.WARNING]

        if error_results:
            recommendations.append("Address critical errors before deploying to production")

        if warning_results:
            recommendations.append("Review and resolve warning messages to improve API quality")

        # Check for specific patterns
        schema_issues = [r for r in self.results if 'schema' in r.test_name.lower() and r.level == ValidationLevel.WARNING]
        if len(schema_issues) > 3:
            recommendations.append("Improve schema definitions with better descriptions and validation rules")

        documentation_issues = [r for r in self.results if 'documentation' in r.test_name.lower() or 'description' in r.test_name.lower()]
        if len(documentation_issues) > 3:
            recommendations.append("Enhance documentation with comprehensive descriptions and examples")

        if not recommendations:
            recommendations.append("OpenAPI specification meets quality standards")

        return recommendations

# OpenAPI validation endpoint dependencies
async def get_openapi_validator(request: Request) -> OpenAPIValidator:
    """Get OpenAPI validator instance"""
    app = request.app
    return OpenAPIValidator(app)

# Router for validation endpoints
from fastapi import APIRouter, Depends

validation_router = APIRouter(prefix="/validation", tags=["validation"])

@validation_router.get("/openapi/run")
async def run_openapi_validation(
    validator: OpenAPIValidator = Depends(get_openapi_validator)
) -> TestReport:
    """Run comprehensive OpenAPI validation and return test report"""
    try:
        report = await validator.run_comprehensive_validation()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@validation_router.get("/openapi/summary")
async def get_validation_summary(
    validator: OpenAPIValidator = Depends(get_openapi_validator)
) -> Dict[str, Any]:
    """Get quick validation summary"""
    try:
        report = await validator.run_comprehensive_validation()
        return {
            "summary": report.summary,
            "recommendations": report.recommendations,
            "critical_issues": len([r for r in report.results if r.level == ValidationLevel.ERROR]),
            "warnings": report.warnings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation summary failed: {str(e)}")

@validation_router.get("/openapi/export/{format}")
async def export_validation_report(
    format: str,
    validator: OpenAPIValidator = Depends(get_openapi_validator)
) -> Dict[str, Any]:
    """Export validation report in specified format"""
    try:
        report = await validator.run_comprehensive_validation()

        if format.lower() == 'json':
            return report.dict()
        elif format.lower() == 'yaml':
            return {"yaml_report": yaml.dump(report.dict(), default_flow_style=False)}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report export failed: {str(e)}")

@validation_router.get("/openapi/score")
async def get_openapi_compliance_score(
    validator: OpenAPIValidator = Depends(get_openapi_validator)
) -> Dict[str, Any]:
    """Get OpenAPI compliance score and breakdown"""
    try:
        report = await validator.run_comprehensive_validation()

        # Calculate scores by category
        category_scores = {}
        for category in TestCategory:
            category_results = [r for r in report.results if r.category == category]
            if category_results:
                passed = len([r for r in category_results if r.passed])
                category_scores[category.value] = {
                    "score": (passed / len(category_results) * 100),
                    "total": len(category_results),
                    "passed": passed
                }

        return {
            "overall_score": report.openapi_compliance_score,
            "category_breakdown": category_scores,
            "recommendations": report.recommendations,
            "summary": report.summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score calculation failed: {str(e)}")

# Validation middleware for real-time monitoring
class ValidationMiddleware:
    """Middleware for real-time OpenAPI validation monitoring"""

    def __init__(self, app):
        self.app = app
        self.validator = OpenAPIValidator(app)
        self.validation_cache = {}
        self.last_validation = None

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Check if validation needs to be run
            if not self.last_validation or (datetime.utcnow() - self.last_validation).seconds > 3600:
                await self._run_background_validation()

        await self.app(scope, receive, send)

    async def _run_background_validation(self):
        """Run validation in background"""
        try:
            report = await self.validator.run_comprehensive_validation()
            self.validation_cache = {
                "report": report.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.last_validation = datetime.utcnow()

            # Log significant issues
            errors = len([r for r in report.results if r.level == ValidationLevel.ERROR])
            if errors > 0:
                logger.warning(f"OpenAPI validation found {errors} errors")

        except Exception as e:
            logger.error(f"Background validation failed: {str(e)}")

# Export validation utilities
__all__ = [
    "OpenAPIValidator",
    "ValidationResult",
    "TestReport",
    "TestCategory",
    "ValidationLevel",
    "validation_router",
    "ValidationMiddleware"
]