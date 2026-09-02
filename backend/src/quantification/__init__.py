"""
Quantification Package

Provides opportunity scoring, segment slicing, 2x2 priority matrix generation,
executive report synthesis, and pipeline orchestration.
"""

from src.quantification.scorer import (
    OpportunityScorer,
    opportunity_scorer,
    OUTPUT_SCORES_FILE,
)
from src.quantification.segment_slicer import (
    SegmentSlicer,
    segment_slicer,
    OUTPUT_SEGMENTED_FILE,
)
from src.quantification.matrix_generator import (
    MatrixGenerator,
    matrix_generator,
    OUTPUT_MATRIX_FILE,
    OPPORTUNITY_REPORT_FILE,
    SEGMENT_VIEW_FILE,
)
from src.quantification.runner import (
    run_quantification,
)

__all__ = [
    "OpportunityScorer",
    "opportunity_scorer",
    "OUTPUT_SCORES_FILE",
    "SegmentSlicer",
    "segment_slicer",
    "OUTPUT_SEGMENTED_FILE",
    "MatrixGenerator",
    "matrix_generator",
    "OUTPUT_MATRIX_FILE",
    "OPPORTUNITY_REPORT_FILE",
    "SEGMENT_VIEW_FILE",
    "run_quantification",
]
