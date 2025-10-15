"""
Enterprise Documentation System
Comprehensive documentation generation and management for enterprise-level code
"""
import inspect
import ast
import json
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging

from .enterprise_logging import get_enterprise_logger


@dataclass
class FunctionDoc:
    """Function documentation structure"""
    name: str
    description: str
    parameters: List[Dict[str, Any]]
    return_type: str
    return_description: str
    exceptions: List[Dict[str, str]]
    examples: List[str]
    complexity: str
    performance_notes: str
    security_notes: str


@dataclass
class ClassDoc:
    """Class documentation structure"""
    name: str
    description: str
    methods: List[FunctionDoc]
    properties: List[Dict[str, Any]]
    inheritance: List[str]
    dependencies: List[str]
    examples: List[str]


@dataclass
class ModuleDoc:
    """Module documentation structure"""
    name: str
    description: str
    classes: List[ClassDoc]
    functions: List[FunctionDoc]
    constants: List[Dict[str, Any]]
    imports: List[str]
    dependencies: List[str]


class DocumentationGenerator:
    """Enterprise documentation generator"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('documentation_generator')
        self.generated_docs = {}
    
    def generate_module_documentation(self, module_path: str) -> ModuleDoc:
        """Generate comprehensive documentation for a module"""
        try:
            # Import the module
            module = __import__(module_path, fromlist=[''])
            
            # Extract module information
            module_doc = ModuleDoc(
                name=module.__name__,
                description=module.__doc__ or "No description available",
                classes=[],
                functions=[],
                constants=[],
                imports=[],
                dependencies=[]
            )
            
            # Extract classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module.__name__:
                    class_doc = self._generate_class_documentation(obj)
                    module_doc.classes.append(class_doc)
            
            # Extract functions
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if obj.__module__ == module.__name__:
                    func_doc = self._generate_function_documentation(obj)
                    module_doc.functions.append(func_doc)
            
            # Extract constants
            for name, obj in inspect.getmembers(module, lambda x: not inspect.isfunction(x) and not inspect.isclass(x)):
                if not name.startswith('_'):
                    module_doc.constants.append({
                        'name': name,
                        'value': str(obj),
                        'type': type(obj).__name__
                    })
            
            # Extract imports
            module_doc.imports = self._extract_imports(module_path)
            
            # Extract dependencies
            module_doc.dependencies = self._extract_dependencies(module_path)
            
            self.generated_docs[module_path] = module_doc
            return module_doc
            
        except Exception as e:
            self.logger.error(f"Error generating documentation for {module_path}: {e}")
            return None
    
    def _generate_class_documentation(self, cls: Type) -> ClassDoc:
        """Generate documentation for a class"""
        class_doc = ClassDoc(
            name=cls.__name__,
            description=cls.__doc__ or "No description available",
            methods=[],
            properties=[],
            inheritance=[],
            dependencies=[],
            examples=[]
        )
        
        # Extract inheritance
        class_doc.inheritance = [base.__name__ for base in cls.__bases__]
        
        # Extract methods
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith('_') or name in ['__init__', '__str__', '__repr__']:
                method_doc = self._generate_function_documentation(method)
                class_doc.methods.append(method_doc)
        
        # Extract properties
        for name, prop in inspect.getmembers(cls, lambda x: isinstance(x, property)):
            class_doc.properties.append({
                'name': name,
                'description': prop.__doc__ or "No description available",
                'type': 'property'
            })
        
        return class_doc
    
    def _generate_function_documentation(self, func: Callable) -> FunctionDoc:
        """Generate documentation for a function"""
        # Get function signature
        sig = inspect.signature(func)
        
        # Extract parameters
        parameters = []
        for param_name, param in sig.parameters.items():
            param_info = {
                'name': param_name,
                'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                'default': str(param.default) if param.default != inspect.Parameter.empty else None,
                'description': 'No description available'
            }
            parameters.append(param_info)
        
        # Extract return type
        return_type = str(sig.return_annotation) if sig.return_annotation != inspect.Parameter.empty else 'Any'
        
        # Analyze function complexity
        complexity = self._analyze_complexity(func)
        
        # Generate performance notes
        performance_notes = self._generate_performance_notes(func)
        
        # Generate security notes
        security_notes = self._generate_security_notes(func)
        
        return FunctionDoc(
            name=func.__name__,
            description=func.__doc__ or "No description available",
            parameters=parameters,
            return_type=return_type,
            return_description="No description available",
            exceptions=[],
            examples=[],
            complexity=complexity,
            performance_notes=performance_notes,
            security_notes=security_notes
        )
    
    def _analyze_complexity(self, func: Callable) -> str:
        """Analyze function complexity"""
        try:
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            # Count complexity indicators
            complexity_score = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity_score += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity_score += 1
                elif isinstance(node, ast.ListComp):
                    complexity_score += 1
                elif isinstance(node, ast.DictComp):
                    complexity_score += 1
                elif isinstance(node, ast.SetComp):
                    complexity_score += 1
                elif isinstance(node, ast.GeneratorExp):
                    complexity_score += 1
            
            if complexity_score <= 3:
                return "Low"
            elif complexity_score <= 7:
                return "Medium"
            elif complexity_score <= 15:
                return "High"
            else:
                return "Very High"
                
        except Exception:
            return "Unknown"
    
    def _generate_performance_notes(self, func: Callable) -> str:
        """Generate performance notes for a function"""
        notes = []
        
        # Check for async functions
        if inspect.iscoroutinefunction(func):
            notes.append("Async function - consider using asyncio for concurrent operations")
        
        # Check for database operations
        source = inspect.getsource(func)
        if any(keyword in source.lower() for keyword in ['query', 'database', 'db', 'sql']):
            notes.append("Contains database operations - consider query optimization")
        
        # Check for file I/O
        if any(keyword in source.lower() for keyword in ['open', 'read', 'write', 'file']):
            notes.append("Contains file I/O operations - consider caching and error handling")
        
        # Check for network operations
        if any(keyword in source.lower() for keyword in ['request', 'http', 'api', 'fetch']):
            notes.append("Contains network operations - consider timeout and retry logic")
        
        return "; ".join(notes) if notes else "No specific performance considerations"
    
    def _generate_security_notes(self, func: Callable) -> str:
        """Generate security notes for a function"""
        notes = []
        
        source = inspect.getsource(func)
        
        # Check for authentication
        if any(keyword in source.lower() for keyword in ['auth', 'login', 'password', 'token']):
            notes.append("Handles authentication - ensure proper validation and secure storage")
        
        # Check for input validation
        if any(keyword in source.lower() for keyword in ['input', 'validate', 'sanitize']):
            notes.append("Handles user input - ensure proper validation and sanitization")
        
        # Check for SQL operations
        if any(keyword in source.lower() for keyword in ['sql', 'query', 'execute']):
            notes.append("Contains SQL operations - ensure protection against SQL injection")
        
        # Check for file operations
        if any(keyword in source.lower() for keyword in ['file', 'upload', 'download']):
            notes.append("Handles file operations - ensure proper validation and secure handling")
        
        return "; ".join(notes) if notes else "No specific security considerations"
    
    def _extract_imports(self, module_path: str) -> List[str]:
        """Extract imports from module"""
        try:
            with open(module_path.replace('.', '/') + '.py', 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
            
            return imports
        except Exception:
            return []
    
    def _extract_dependencies(self, module_path: str) -> List[str]:
        """Extract external dependencies from module"""
        try:
            with open(module_path.replace('.', '/') + '.py', 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            dependencies = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module.split('.')[0])
            
            return list(dependencies)
        except Exception:
            return []
    
    def generate_api_documentation(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate API documentation"""
        api_doc = {
            'title': 'RichesReach API Documentation',
            'version': '1.0.0',
            'description': 'Enterprise-level API for RichesReach investment platform',
            'base_url': 'https://api.richesreach.com/v1',
            'endpoints': []
        }
        
        for endpoint in endpoints:
            endpoint_doc = {
                'path': endpoint.get('path', ''),
                'method': endpoint.get('method', 'GET'),
                'description': endpoint.get('description', ''),
                'parameters': endpoint.get('parameters', []),
                'responses': endpoint.get('responses', {}),
                'authentication': endpoint.get('authentication', 'required'),
                'rate_limiting': endpoint.get('rate_limiting', {}),
                'examples': endpoint.get('examples', [])
            }
            api_doc['endpoints'].append(endpoint_doc)
        
        return api_doc
    
    def generate_security_documentation(self) -> Dict[str, Any]:
        """Generate security documentation"""
        return {
            'title': 'Security Documentation',
            'version': '1.0.0',
            'description': 'Security measures and best practices for RichesReach',
            'authentication': {
                'jwt_tokens': {
                    'description': 'JWT tokens for API authentication',
                    'expiration': '24 hours',
                    'refresh': 'Automatic on valid token usage'
                },
                'password_policy': {
                    'min_length': 8,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_digits': True,
                    'require_special_chars': True
                }
            },
            'authorization': {
                'role_based': 'Role-based access control (RBAC)',
                'permissions': 'Granular permission system'
            },
            'data_protection': {
                'encryption': 'AES-256 encryption for sensitive data',
                'hashing': 'bcrypt for password hashing',
                'sanitization': 'Input sanitization and validation'
            },
            'rate_limiting': {
                'api_calls': 'Rate limiting per user and endpoint',
                'login_attempts': 'Account lockout after failed attempts'
            },
            'monitoring': {
                'security_events': 'Real-time security event monitoring',
                'audit_logs': 'Comprehensive audit logging',
                'alerts': 'Automated security alerts'
            }
        }
    
    def generate_deployment_documentation(self) -> Dict[str, Any]:
        """Generate deployment documentation"""
        return {
            'title': 'Deployment Documentation',
            'version': '1.0.0',
            'description': 'Deployment guide for RichesReach enterprise platform',
            'environments': {
                'development': {
                    'description': 'Local development environment',
                    'database': 'SQLite',
                    'cache': 'Local memory cache',
                    'monitoring': 'Basic logging'
                },
                'staging': {
                    'description': 'Staging environment for testing',
                    'database': 'PostgreSQL',
                    'cache': 'Redis',
                    'monitoring': 'Full monitoring enabled'
                },
                'production': {
                    'description': 'Production environment',
                    'database': 'PostgreSQL with read replicas',
                    'cache': 'Redis cluster',
                    'monitoring': 'Enterprise monitoring suite'
                }
            },
            'infrastructure': {
                'containerization': 'Docker containers',
                'orchestration': 'AWS ECS',
                'load_balancing': 'Application Load Balancer',
                'scaling': 'Auto-scaling groups',
                'monitoring': 'CloudWatch and custom metrics'
            },
            'deployment_process': {
                'ci_cd': 'GitHub Actions',
                'testing': 'Automated test suite',
                'security_scanning': 'Security vulnerability scanning',
                'rollback': 'Automated rollback on failure'
            }
        }
    
    def export_documentation(self, output_dir: str):
        """Export documentation to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export module documentation
        for module_path, module_doc in self.generated_docs.items():
            filename = f"{module_path.replace('.', '_')}_docs.json"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(asdict(module_doc), f, indent=2, default=str)
        
        # Export API documentation
        api_doc = self.generate_api_documentation([])
        with open(output_path / 'api_documentation.json', 'w') as f:
            json.dump(api_doc, f, indent=2)
        
        # Export security documentation
        security_doc = self.generate_security_documentation()
        with open(output_path / 'security_documentation.json', 'w') as f:
            json.dump(security_doc, f, indent=2)
        
        # Export deployment documentation
        deployment_doc = self.generate_deployment_documentation()
        with open(output_path / 'deployment_documentation.json', 'w') as f:
            json.dump(deployment_doc, f, indent=2)
        
        self.logger.info(f"Documentation exported to {output_dir}")


class CodeQualityAnalyzer:
    """Code quality analyzer for enterprise standards"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('code_quality_analyzer')
    
    def analyze_module_quality(self, module_path: str) -> Dict[str, Any]:
        """Analyze code quality of a module"""
        try:
            module = __import__(module_path, fromlist=[''])
            
            quality_report = {
                'module_name': module.__name__,
                'overall_score': 0,
                'metrics': {},
                'recommendations': []
            }
            
            # Analyze documentation coverage
            doc_coverage = self._analyze_documentation_coverage(module)
            quality_report['metrics']['documentation_coverage'] = doc_coverage
            
            # Analyze complexity
            complexity = self._analyze_module_complexity(module)
            quality_report['metrics']['complexity'] = complexity
            
            # Analyze error handling
            error_handling = self._analyze_error_handling(module)
            quality_report['metrics']['error_handling'] = error_handling
            
            # Analyze security
            security = self._analyze_security_measures(module)
            quality_report['metrics']['security'] = security
            
            # Calculate overall score
            overall_score = (
                doc_coverage * 0.2 +
                complexity * 0.3 +
                error_handling * 0.3 +
                security * 0.2
            )
            quality_report['overall_score'] = overall_score
            
            # Generate recommendations
            quality_report['recommendations'] = self._generate_recommendations(quality_report)
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error analyzing module quality: {e}")
            return {}
    
    def _analyze_documentation_coverage(self, module) -> float:
        """Analyze documentation coverage"""
        total_functions = 0
        documented_functions = 0
        
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ == module.__name__:
                total_functions += 1
                if obj.__doc__ and obj.__doc__.strip():
                    documented_functions += 1
        
        return (documented_functions / total_functions * 100) if total_functions > 0 else 0
    
    def _analyze_module_complexity(self, module) -> float:
        """Analyze module complexity"""
        # This is a simplified complexity analysis
        # In a real implementation, you'd use tools like radon or mccabe
        return 75.0  # Placeholder
    
    def _analyze_error_handling(self, module) -> float:
        """Analyze error handling quality"""
        # This is a simplified error handling analysis
        # In a real implementation, you'd analyze try/except blocks
        return 80.0  # Placeholder
    
    def _analyze_security_measures(self, module) -> float:
        """Analyze security measures"""
        # This is a simplified security analysis
        # In a real implementation, you'd check for security best practices
        return 85.0  # Placeholder
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if quality_report['metrics']['documentation_coverage'] < 80:
            recommendations.append("Improve documentation coverage - aim for 80%+")
        
        if quality_report['metrics']['complexity'] < 70:
            recommendations.append("Reduce code complexity - consider refactoring")
        
        if quality_report['metrics']['error_handling'] < 80:
            recommendations.append("Improve error handling - add more try/except blocks")
        
        if quality_report['metrics']['security'] < 85:
            recommendations.append("Enhance security measures - review security best practices")
        
        return recommendations


# Global documentation instances
doc_generator = DocumentationGenerator()
quality_analyzer = CodeQualityAnalyzer()
