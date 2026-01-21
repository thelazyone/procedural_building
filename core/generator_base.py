"""
Base class for all generators.

Defines the common interface and patterns for hierarchical generation.
"""

from typing import Any, Dict
from abc import ABC, abstractmethod


class GeneratorBase(ABC):
    """
    Base class for all procedural generators.
    
    All generators follow the pattern:
    - Take parent context + seed + parameters
    - Generate deterministically
    - Return generated structure
    """
    
    @abstractmethod
    def generate(
        self,
        parent_context: Any,
        seed: int,
        **params: Dict[str, Any]
    ) -> Any:
        """
        Generate elements based on parent context and seed.
        
        Args:
            parent_context: Data from parent generator
                          (e.g., polygon for wall gen, wall segment for window gen)
            seed: Integer seed for deterministic randomness
            **params: Style, density, and constraint parameters
            
        Returns:
            Generated structure(s)
        """
        pass
    
    def derive_seed(self, parent_seed: int, identifier: Any) -> int:
        """
        Derive a child seed deterministically from parent seed and identifier.
        
        Args:
            parent_seed: Seed from parent generator
            identifier: Unique identifier for this element (e.g., wall index)
            
        Returns:
            Derived seed for child generator
        """
        # Simple hash-based derivation
        return hash((parent_seed, identifier)) % (2**31)
