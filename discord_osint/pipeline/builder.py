"""
discord_osint/pipeline/builder.py
-----------------------------------
Pipeline builders for all investigation modes.

Phase 4 additions
-----------------
Six new builder functions for the Phase 4 modules:

  build_email_pipeline(ctx)   → EmailInvestigationStage + Intelligence + Reporting
  build_domain_pipeline(ctx)  → DomainInvestigationStage + Reporting
  build_phone_pipeline(ctx)   → PhoneInvestigationStage + Reporting
  build_image_pipeline(ctx)   → ImageAnalysisStage + Reporting
  build_url_pipeline(ctx)     → URLAnalysisStage + Reporting
  build_probe_pipeline(ctx)   → DataProbeStage + IntelligenceStage + Reporting

Each module pipeline is intentionally minimal: only the stages that
make sense for that data type.  Adding IntelligenceStage to email and
probe pipelines gives them the knowledge-graph narrative; the others
skip it since they produce structured technical data, not social graphs.

Full pipeline stage order (unchanged):
  1. DiscordModeStage
  2. DiscoveryStage
  3. ScrapingStage
  4. MediaStage
  5. AnalysisStage
  6. IntelligenceStage
  7. EmailIntelStage
  8. ReportingStage
"""

from __future__ import annotations

from .base import Pipeline
from .context import InvestigationContext
from .stages import (
    DiscordModeStage,
    DiscoveryStage,
    ScrapingStage,
    MediaStage,
    AnalysisStage,
    IntelligenceStage,
    EmailIntelStage,
    ReportingStage,
)


# ---------------------------------------------------------------------------
# Legacy pipeline builders (unchanged)
# ---------------------------------------------------------------------------

def build_pipeline(ctx: InvestigationContext) -> Pipeline:
    """Full username / Discord pipeline."""
    stages = [
        DiscordModeStage(),
        DiscoveryStage(),
        ScrapingStage(),
        MediaStage(),
        AnalysisStage(),
        IntelligenceStage(),
        EmailIntelStage(),
    ]
    return Pipeline(stages, ctx)


def build_sub_pipeline(ctx: InvestigationContext) -> Pipeline:
    """Lightweight pivot sub-pipeline (no Discord fetch, no report)."""
    stages = [
        DiscoveryStage(),
        ScrapingStage(),
        MediaStage(),
        AnalysisStage(),
        IntelligenceStage(),
        EmailIntelStage(),
    ]
    return Pipeline(stages, ctx)


# ---------------------------------------------------------------------------
# Phase 4 module pipeline builders
# ---------------------------------------------------------------------------

def build_email_pipeline(ctx: InvestigationContext) -> Pipeline:
    """
    Standalone email investigation pipeline.

    Stages:
      EmailInvestigationStage  – all email-intel tools + Blackbird
      ScrapingStage            – enrich any profiles Blackbird found
      IntelligenceStage        – knowledge graph + AI narrative
      ReportingStage           – HTML report
    """
    from .stages.email_investigation import EmailInvestigationStage

    stages = [
        EmailInvestigationStage(),
        ScrapingStage(),
        IntelligenceStage(),
    ]
    return Pipeline(stages, ctx)


def build_domain_pipeline(ctx: InvestigationContext) -> Pipeline:
    """
    Domain investigation pipeline.

    Stages:
      DomainInvestigationStage – WHOIS, DNS, SSL, subdomains, Wayback
      ReportingStage
    """
    from .stages.domain_investigation import DomainInvestigationStage

    stages = [
        DomainInvestigationStage(),
    ]
    return Pipeline(stages, ctx)


def build_phone_pipeline(ctx: InvestigationContext) -> Pipeline:
    """
    Phone number investigation pipeline.

    Stages:
      PhoneInvestigationStage – validation, carrier, PhoneInfoga
      ReportingStage
    """
    from .stages.phone_investigation import PhoneInvestigationStage

    stages = [
        PhoneInvestigationStage(),
    ]
    return Pipeline(stages, ctx)


def build_image_pipeline(ctx: InvestigationContext) -> Pipeline:
    """
    Image analysis pipeline.

    Stages:
      ImageAnalysisStage – EXIF, pHash, reverse search, OCR
      ReportingStage
    """
    from .stages.image_analysis import ImageAnalysisStage

    stages = [
        ImageAnalysisStage(),
    ]
    return Pipeline(stages, ctx)


def build_url_pipeline(ctx: InvestigationContext) -> Pipeline:
    """
    URL analysis pipeline.

    Stages:
      URLAnalysisStage – HTTP meta, redirects, page meta, Safe Browsing, Wayback
      ReportingStage
    """
    from .stages.url_analysis import URLAnalysisStage

    stages = [
        URLAnalysisStage(),
        ScrapingStage(),
    ]
    return Pipeline(stages, ctx)


def build_probe_pipeline(ctx: InvestigationContext) -> Pipeline:
    """
    Data Probe auto-detect pipeline.

    Stages:
      DataProbeStage    – classifies input, calls sub-module stages inline
      IntelligenceStage – knowledge graph over whatever was collected
      ReportingStage
    """
    from .stages.data_probe import DataProbeStage

    stages = [
        DataProbeStage(),
        IntelligenceStage(),
    ]
    return Pipeline(stages, ctx)


# ---------------------------------------------------------------------------
# Dispatch helper (used by pipeline/__init__.py and web_app.py)
# ---------------------------------------------------------------------------

_MODULE_BUILDERS = {
    "email":   build_email_pipeline,
    "domain":  build_domain_pipeline,
    "phone":   build_phone_pipeline,
    "image":   build_image_pipeline,
    "url":     build_url_pipeline,
    "probe":   build_probe_pipeline,
}


def build_module_pipeline(module_mode: str, ctx: InvestigationContext) -> Pipeline:
    """
    Dispatch to the correct builder by module_mode string.

    Parameters
    ----------
    module_mode:
        One of "email" | "domain" | "phone" | "image" | "url" | "probe".
    ctx:
        InvestigationContext with the appropriate field already set.

    Raises
    ------
    ValueError
        When module_mode is unrecognised.
    """
    builder = _MODULE_BUILDERS.get(module_mode)
    if builder is None:
        raise ValueError(
            f"Unknown module_mode {module_mode!r}. "
            f"Valid values: {sorted(_MODULE_BUILDERS)}"
        )
    ctx.module_mode = module_mode
    return builder(ctx)
