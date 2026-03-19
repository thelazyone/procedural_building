"""
Roof geometry utilities.

Computes roof outline with protrusion on front facades only.
Occluded and back edges stay flush with the footprint.
"""

import math
from typing import List, Tuple

from core.footprint import Point2D
from core.facade import FacadeDefinition, FacadeSegmentKind


def compute_roof_vertices(
    footprint_vertices: List[Point2D],
    facade_definition: FacadeDefinition,
    protrusion: float,
) -> List[Point2D]:
    """
    Compute roof polygon vertices with protrusion on front edges only.

    On FRONT edges, the roof extends outward by protrusion.
    On BACK and OCCLUSION edges, the roof stays flush (no protrusion).

    Args:
        footprint_vertices: Original footprint vertices (CCW order)
        facade_definition: Facade segments per edge
        protrusion: Outward offset in meters for front edges

    Returns:
        List of (x, y) vertices for the roof outline (same order as input)
    """
    if protrusion <= 0 or not footprint_vertices:
        return list(footprint_vertices)

    n = len(footprint_vertices)
    result = []

    for i in range(n):
        prev_i = (i - 1) % n
        next_i = (i + 1) % n

        # Edge from prev to current
        p_prev = footprint_vertices[prev_i]
        p_curr = footprint_vertices[i]
        p_next = footprint_vertices[next_i]

        # Edge (prev -> curr): direction and outward normal
        ex_prev = p_curr[0] - p_prev[0]
        ey_prev = p_curr[1] - p_prev[1]
        len_prev = math.sqrt(ex_prev * ex_prev + ey_prev * ey_prev) or 1e-9
        # Outward normal (left of edge for CCW): (-ey, ex) / len
        nx_prev = -ey_prev / len_prev
        ny_prev = ex_prev / len_prev

        # Edge (curr -> next)
        ex_next = p_next[0] - p_curr[0]
        ey_next = p_next[1] - p_curr[1]
        len_next = math.sqrt(ex_next * ex_next + ey_next * ey_next) or 1e-9
        nx_next = -ey_next / len_next
        ny_next = ex_next / len_next

        # Does each edge have any FRONT segment (protrude)?
        def edge_has_protrusion(edge_idx: int) -> bool:
            for seg in facade_definition.get_segments_for_edge(edge_idx):
                if seg.kind == FacadeSegmentKind.FRONT:
                    return True
            return False

        prev_edge_idx = prev_i  # edge from prev_i to i
        next_edge_idx = i      # edge from i to next_i

        protrude_prev = edge_has_protrusion(prev_edge_idx)
        protrude_next = edge_has_protrusion(next_edge_idx)

        if not protrude_prev and not protrude_next:
            result.append(p_curr)
            continue

        # Row building: one front edge → vertices move orthogonally (edge normal).
        # Corner: two front edges → vertices extrude along bisector.
        if protrude_prev and protrude_next:
            # Corner: bisector of the two edge normals
            bx = nx_prev + nx_next
            by = ny_prev + ny_next
            blen = math.sqrt(bx * bx + by * by)
            if blen < 1e-9:
                bx, by = nx_prev, ny_prev
            else:
                bx /= blen
                by /= blen
            offset_x = bx * protrusion
            offset_y = by * protrusion
        else:
            # Single front edge: use that edge's normal (orthogonal extrusion, no widening)
            if protrude_prev:
                offset_x = nx_prev * protrusion
                offset_y = ny_prev * protrusion
            else:
                offset_x = nx_next * protrusion
                offset_y = ny_next * protrusion

        result.append((p_curr[0] + offset_x, p_curr[1] + offset_y))

    return result
