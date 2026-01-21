"""
Seed management utilities.

Provides functions for deterministic seed derivation and RNG management.
"""

import random
from typing import Any, Tuple


def derive_seed(parent_seed: int, *identifiers: Any) -> int:
    """
    Derive a child seed from parent seed and identifiers.
    
    This ensures deterministic but unique seeds for sub-generators.
    
    Args:
        parent_seed: Parent generator's seed
        *identifiers: One or more identifiers (e.g., floor_idx, wall_idx)
        
    Returns:
        Derived seed (positive integer)
        
    Example:
        >>> parent_seed = 12345
        >>> floor_0_seed = derive_seed(parent_seed, "floor", 0)
        >>> floor_1_seed = derive_seed(parent_seed, "floor", 1)
        >>> wall_3_seed = derive_seed(floor_0_seed, "wall", 3)
    """
    combined = (parent_seed, *identifiers)
    return abs(hash(combined)) % (2**31)


def create_rng(seed: int) -> random.Random:
    """
    Create a random number generator with given seed.
    
    Args:
        seed: Seed value
        
    Returns:
        Random number generator instance
    """
    rng = random.Random()
    rng.seed(seed)
    return rng


def split_seed(seed: int, count: int) -> Tuple[int, ...]:
    """
    Split a seed into multiple derived seeds.
    
    Useful when generating multiple elements at once.
    
    Args:
        seed: Parent seed
        count: Number of derived seeds to generate
        
    Returns:
        Tuple of derived seeds
        
    Example:
        >>> seed = 12345
        >>> s1, s2, s3 = split_seed(seed, 3)
    """
    return tuple(derive_seed(seed, i) for i in range(count))
