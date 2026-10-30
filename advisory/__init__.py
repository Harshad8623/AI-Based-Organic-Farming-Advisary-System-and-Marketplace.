"""Local, explainable farm decision support based on recorded field conditions."""

from .engine import AdvisoryInputError, analyze_context, localize_priority

__all__ = ['AdvisoryInputError', 'analyze_context', 'localize_priority']
