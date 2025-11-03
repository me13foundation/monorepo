"""
Dependency injection container for the MED13 Resource Library.

Provides centralized dependency resolution and lifecycle management
for domain services, repositories, and infrastructure components.
"""

from .container import DependencyContainer

__all__ = ["DependencyContainer"]
