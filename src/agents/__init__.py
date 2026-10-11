"""Multi-agent student support workflow, copilot, and generative features."""
from ssa.agents.workflow import SupportWorkflow
from ssa.agents.copilot import Copilot
from ssa.agents.guardrails import (
    protected_mentions,
    punitive_terms,
    diagnostic_terms,
    outreach_stigma_terms,
    injection_signals,
    sanitize_text,
    ungrounded_numbers,
)
from ssa.agents.genai import (
    rule_parse,
    understand_query,
    synthesize_precedents,
    cohort_briefing,
    outreach_variant,
    note_themes,
)

# Friendly aliases
CopilotAgent = Copilot
parse_search = understand_query
outreach_variants = outreach_variant

__all__ = [
    "SupportWorkflow",
    "Copilot",
    "CopilotAgent",
    "protected_mentions",
    "punitive_terms",
    "diagnostic_terms",
    "outreach_stigma_terms",
    "injection_signals",
    "sanitize_text",
    "ungrounded_numbers",
    "rule_parse",
    "understand_query",
    "parse_search",
    "synthesize_precedents",
    "cohort_briefing",
    "outreach_variant",
    "outreach_variants",
    "note_themes",
]
