"""
Facade definition for building footprints.

Defines the 2D classification of footprint edges/segments by their exposure:
- FRONT: Main road face
- BACK: Backroad sides
- OCCLUSION: Facing other buildings (occluded from view)

A single footprint edge can be split into multiple segments when it has
different characteristics along its length (e.g. front + occlusion + back
when a smaller building touches a larger one).

Occlusion segments can have an optional height (meters) above which the
segment is treated as BACK (not-front-road-facing) rather than OCCLUSION.
"""

from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .footprint import Point2D


class FacadeSegmentKind(Enum):
    """Type of facade segment along a footprint edge."""

    FRONT = "front"  # Main road face
    BACK = "back"    # Backroad sides
    OCCLUSION = "occlusion"  # Facing other buildings


@dataclass
class FacadeSegment:
    """
    A segment of a footprint edge with a specific facade type.

    Segments are defined parametrically along the parent edge (0..1).
    Multiple segments can share the same edge when the edge has mixed
    exposure (e.g. front + occlusion + back).
    """

    edge_idx: int
    """Index of the footprint edge this segment belongs to."""

    start_param: float
    """Start position along edge (0..1)."""

    end_param: float
    """End position along edge (0..1)."""

    kind: FacadeSegmentKind
    """Type of facade for this segment."""

    occlusion_height: Optional[float] = None
    """
    For OCCLUSION segments only: height in meters above ground up to which
    occlusion applies. Above this height (starting from the full floor after
    that), the segment is treated as BACK (not-front-road-facing).
    None means occlusion for the full building height.
    """

    def length_param(self) -> float:
        """Length of segment as fraction of edge (0..1)."""
        return self.end_param - self.start_param

    def effective_kind_at_height(self, floor_z_base: float, floor_z_top: float) -> FacadeSegmentKind:
        """
        Get the effective facade kind for a floor at the given Z range.

        For OCCLUSION segments with occlusion_height set: if the floor's
        base is at or above occlusion_height, treat as BACK. Otherwise OCCLUSION.

        Args:
            floor_z_base: Z coordinate of floor base (meters)
            floor_z_top: Z coordinate of floor top (meters)

        Returns:
            Effective FacadeSegmentKind for this floor
        """
        if self.kind != FacadeSegmentKind.OCCLUSION or self.occlusion_height is None:
            return self.kind

        # "Starting from the full floor after that" = first floor whose base >= occlusion_height
        if floor_z_base >= self.occlusion_height:
            return FacadeSegmentKind.BACK
        return FacadeSegmentKind.OCCLUSION


@dataclass
class FacadeDefinition:
    """
    Complete 2D facade definition for a footprint.

    Contains a list of segments. Each segment references an edge by index
    and defines a parametric span (start_param, end_param) with a facade kind.
    Segments can overlap or cover edges partially; typically they partition
    the perimeter.
    """

    segments: List[FacadeSegment]
    """All facade segments, ordered by edge_idx then start_param."""

    def get_segments_for_edge(self, edge_idx: int) -> List[FacadeSegment]:
        """Get all segments belonging to a given edge index."""
        return [s for s in self.segments if s.edge_idx == edge_idx]

    def get_segment_at(
        self,
        edge_idx: int,
        param: float,
        floor_z_base: float = 0.0,
        floor_z_top: float = 0.0,
    ) -> Optional[FacadeSegment]:
        """
        Get the segment containing a given parametric position on an edge.

        Optionally returns the segment with effective kind for the given floor
        Z range (for occlusion height logic).

        Args:
            edge_idx: Edge index
            param: Position along edge (0..1)
            floor_z_base: Floor base Z (for occlusion height)
            floor_z_top: Floor top Z (for occlusion height)

        Returns:
            Segment containing param, or None
        """
        for seg in self.get_segments_for_edge(edge_idx):
            if seg.start_param <= param < seg.end_param:
                return seg
        return None

    def get_effective_kind_at(
        self,
        edge_idx: int,
        param: float,
        floor_z_base: float = 0.0,
        floor_z_top: float = 0.0,
    ) -> Optional[FacadeSegmentKind]:
        """
        Get the effective facade kind at a position on an edge for a given floor.

        Returns None if no segment covers that position.
        """
        seg = self.get_segment_at(edge_idx, param, floor_z_base, floor_z_top)
        if seg is None:
            return None
        return seg.effective_kind_at_height(floor_z_base, floor_z_top)


def default_facade_definition(num_edges: int) -> FacadeDefinition:
    """
    Create a default facade definition where all edges are FRONT.

    Useful when no block/parcel context is available (e.g. standalone building).
    """
    segments = [
        FacadeSegment(edge_idx=i, start_param=0.0, end_param=1.0, kind=FacadeSegmentKind.FRONT)
        for i in range(num_edges)
    ]
    return FacadeDefinition(segments=segments)


def build_facade_from_edge_segments(
    num_edges: int,
    edge_segments: List[List[Tuple[FacadeSegmentKind, float, float, Optional[float]]]],
) -> FacadeDefinition:
    """
    Build a FacadeDefinition from per-edge segment specifications.

    Each edge can have multiple segments. Each segment is:
    (kind, start_param, end_param, occlusion_height=None).
    occlusion_height is only used for OCCLUSION kind.

    Example: Edge 0 split into front [0,0.3], occlusion [0.3,0.6] (6m), back [0.6,1]:
        edge_segments = [
            [
                (FacadeSegmentKind.FRONT, 0.0, 0.3, None),
                (FacadeSegmentKind.OCCLUSION, 0.3, 0.6, 6.0),
                (FacadeSegmentKind.BACK, 0.6, 1.0, None),
            ],
            [(FacadeSegmentKind.FRONT, 0.0, 1.0, None)],  # edge 1: all front
        ]
    """
    segments = []
    for edge_idx, segs in enumerate(edge_segments):
        if edge_idx >= num_edges:
            break
        for kind, start, end, occ_h in segs:
            segments.append(
                FacadeSegment(
                    edge_idx=edge_idx,
                    start_param=start,
                    end_param=end,
                    kind=kind,
                    occlusion_height=occ_h if kind == FacadeSegmentKind.OCCLUSION else None,
                )
            )
    return FacadeDefinition(segments=segments)
