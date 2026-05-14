"""
discord_osint/pipeline/__init__.py
------------------------------------
Public entry point for the investigation pipeline.

Phase 4 additions
-----------------
``run_module_pipeline(mode, config)`` handles the six new investigation
modules (email, domain, phone, image, url, probe).  It constructs the
correct InvestigationContext, dispatches to the appropriate builder,
and runs the pipeline with the same pivot/emit wiring as
run_osint_pipeline().

Both functions share a common ``_common_setup()`` helper so debug mode,
pivot config, and seed queue initialisation are never duplicated.
"""

from __future__ import annotations

import os

from .context import InvestigationContext
from .builder import build_pipeline, build_module_pipeline
from ..utils import CACHE_DIR

# Phase 4 module modes
_MODULE_MODES = frozenset({"email", "domain", "phone", "image", "url", "probe"})


# ---------------------------------------------------------------------------
# Shared setup helper
# ---------------------------------------------------------------------------

def _common_setup(config) -> tuple:
    """
    Activate debug mode, build PivotConfig + SeedQueue.
    Returns (pivot_config, seed_queue, emitter_or_none).
    """
    from .. import utils
    utils.DEBUG_MODE = getattr(config, "DEBUG", False)
    if utils.DEBUG_MODE:
        print("[DEBUG] Debug mode active")

    from .pivot import PivotConfig, SeedQueue
    pivot_config = PivotConfig.from_config(config)
    seed_queue   = SeedQueue()

    # Retrieve Phase 3 emitter if web_app wired one in
    emitter = getattr(config, "_phase3_emit", None)

    return pivot_config, seed_queue, emitter


# ---------------------------------------------------------------------------
# Legacy pipeline entry point (unchanged public API)
# ---------------------------------------------------------------------------

def run_osint_pipeline(config=None) -> None:
    """
    Main entry point for manual / Discord investigations.
    Signature is identical to the original so all existing callers work.
    """
    if config is None:
        from ..config import config as default_config
        config = default_config

    pivot_config, seed_queue, emitter = _common_setup(config)

    mode         = config.MODE
    manual_email = getattr(config, "MANUAL_EMAIL", "").strip() or \
                   os.environ.get("MANUAL_EMAIL", "").strip()

    # ------------------------------------------------------------------ #
    # Resolve mode / username / target_id                                  #
    # ------------------------------------------------------------------ #
    if mode == "discord":
        target_user_id  = config.TARGET_USER_ID
        target_guild_id = config.TARGET_GUILD_ID
        username        = str(target_user_id)
        target_id       = target_user_id

    elif mode == "manual":
        username = (config.MANUAL_USERNAME or "").strip()
        manual_email = getattr(config, "MANUAL_EMAIL", "").strip()
        if not username and not manual_email:
            print("MANUAL_USERNAME is empty and no email supplied. Exiting.")
            return
        # If only email is provided, switch to the email module
        if not username and manual_email:
            print("Only email provided – switching to email module.")
            run_module_pipeline("email", config)
            return
        # Otherwise, proceed with username investigation
        target_id = hash(username) & 0x7FFFFFFF
        target_user_id = None
        target_guild_id = None

    else:
        # Unknown mode – try module runner
        run_module_pipeline(mode, config)
        return

    from .. import utils
    if utils.DEBUG_MODE:
        utils.init_debug_log(target_id)

    # Load cached intel
    from ..core import InvestigationCore
    intel_core = InvestigationCore(target_id)
    if config.ENABLE_CACHING:
        previous = intel_core.load_latest_state()
        if previous:
            print(f"  [✓] Loaded cached intel ({len(previous.get('timeline', []))} events).")
            intel_core.intel = previous
            intel_core.intel.pop("scraped_urls", None)

    # Mark root seeds as processed
    if mode == "discord":
        seed_queue.mark_processed(str(target_user_id))
    if username:
        seed_queue.mark_processed(username)
    if manual_email:
        seed_queue.mark_processed(manual_email)

    if pivot_config.enabled:
        print(
            f"[PIVOT] Enabled – max_depth={pivot_config.max_depth}, "
            f"max_seeds={pivot_config.max_seeds_per_depth}"
        )

    ctx = InvestigationContext(
        config=config,
        mode=mode,
        username=username,
        target_id=target_id,
        target_user_id=target_user_id,
        target_guild_id=target_guild_id,
        manual_email=manual_email,
        extra_targets=list(getattr(config, "EXTRA_TARGETS", []) or []),
        intel_core=intel_core,
        depth=0,
        seed_type="",
        seed_value="",
    )

    # Resolve pivot confirm function
    confirm_fn = getattr(config, "_pivot_confirm_fn", None)

    pipeline = build_pipeline(ctx)
    pipeline.run(
        emit=emitter or (lambda *_: None),
        pivot_config=pivot_config,
        seed_queue=seed_queue,
        pivot_confirm_fn=confirm_fn,
    )

    if pivot_config.enabled:
        pivot_reports = ctx.intel_core.intel.get("pivot_reports", [])
        print(
            f"\n[PIVOT] Complete – {seed_queue.processed_count} seeds processed, "
            f"{len(pivot_reports)} sub-report(s) merged."
        )

    from .stages.reporting_stage import ReportingStage
    ReportingStage().run(ctx, emit=emitter or (lambda *_: None))


# ---------------------------------------------------------------------------
# Phase 4 module pipeline entry point
# ---------------------------------------------------------------------------

def run_module_pipeline(mode: str, config=None) -> None:
    """
    Run a Phase 4 investigation module.

    Parameters
    ----------
    mode:
        One of "email" | "domain" | "phone" | "image" | "url" | "probe".
    config:
        Config / ConfigService object.  When None the default config is used.
    """
    if config is None:
        from ..config import config as default_config
        config = default_config

    if mode not in _MODULE_MODES:
        print(f"[pipeline] Unknown module mode {mode!r}. Falling back to manual pipeline.")
        run_osint_pipeline(config)
        return

    pivot_config, seed_queue, emitter = _common_setup(config)

    # ------------------------------------------------------------------ #
    # Build context for the module                                         #
    # ------------------------------------------------------------------ #
    target_value = _resolve_target(mode, config)
    target_id    = hash(target_value) & 0x7FFFFFFF

    from .. import utils
    if utils.DEBUG_MODE:
        utils.init_debug_log(target_id)

    from ..core import InvestigationCore
    intel_core = InvestigationCore(target_id)

    ctx = InvestigationContext(
        config=config,
        mode="manual",         # all module pipelines run in manual mode
        username=target_value, # used for report header fallback
        target_id=target_id,
        intel_core=intel_core,
        module_mode=mode,
        # Populate the relevant field
        manual_email=     (target_value if mode == "email"  else ""),
        manual_domain=    (target_value if mode == "domain" else ""),
        manual_phone=     (target_value if mode == "phone"  else ""),
        manual_image_url= (target_value if mode == "image"  else ""),
        manual_url=       (target_value if mode == "url"    else ""),
        probe_string=     (target_value if mode == "probe"  else ""),
        depth=0,
        seed_type="",
        seed_value="",
    )

    print(f"\n{'=' * 60}")
    print(f"== WhoCord Module: {mode.upper()} → {target_value[:60]}")
    print(f"{'=' * 60}")

    confirm_fn = getattr(config, "_pivot_confirm_fn", None)

    pipeline = build_module_pipeline(mode, ctx)
    pipeline.run(
        emit=emitter or (lambda *_: None),
        pivot_config=pivot_config,
        seed_queue=seed_queue,
        pivot_confirm_fn=confirm_fn,
    )
   
    from .stages.reporting_stage import ReportingStage
    ReportingStage().run(ctx, emit=emitter or (lambda *_: None))


# ---------------------------------------------------------------------------
# Helper: extract the primary target value from config for a given mode
# ---------------------------------------------------------------------------

def _resolve_target(mode: str, config) -> str:
    """
    Return the relevant raw target string from the config object.
    Handles both attribute-style and dict-style access gracefully.
    """
    mapping = {
        "email":  "MANUAL_EMAIL",
        "domain": "MANUAL_DOMAIN",
        "phone":  "MANUAL_PHONE",
        "image":  "MANUAL_IMAGE_URL",
        "url":    "MANUAL_URL",
        "probe":  "PROBE_STRING",
    }
    attr = mapping.get(mode, "")
    if attr:
        val = getattr(config, attr, "") or ""
        if val.strip():
            return val.strip()

    # Fall back to MANUAL_USERNAME or MANUAL_EMAIL for compatibility
    for fallback in ("MANUAL_USERNAME", "MANUAL_EMAIL"):
        val = getattr(config, fallback, "") or ""
        if val.strip():
            return val.strip()

    return "unknown"
