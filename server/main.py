"""wolfgang_rush — Indian High Court Drafting MCPB.

Local-execution MCPB Desktop Extension for any High Court of India. Exposes
the six-agent HC drafting pipeline, thirteen case-type drafting templates,
and twenty-eight bench exemplars (covering all 25 Indian High Courts plus
multi-bench HCs) as MCP tools that Claude can orchestrate from a Claude
Desktop chat.

Privacy posture: zero data collection. All processing happens on the user's
machine. The publisher (wolfgang_rush) never receives any user data.

License: MIT
Source: https://github.com/Wolfgangrush/indian-hc-drafting-mcpb
Privacy policy: https://wolfgangrush.github.io/privacy/
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

DEFAULT_DRAFTS_ROOT = Path.home() / "Downloads" / "Wolfgang-Rush-Drafts"
ALLOWED_ARTIFACT_NAMES = {
    "case-facts.md",
    "format-shell.md",
    "draft-v1.md",
    "draft-v1.docx",
    "verification-report.md",
    "draft-v2.md",
    "draft-v2.docx",
    "opposing-notes.md",
    "final-draft.md",
}

mcp = FastMCP("wolfgang-indian-hc-drafting")

BUNDLE_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = BUNDLE_ROOT / "skills"
AGENTS_DIR = BUNDLE_ROOT / "agents"
BENCH_CONFIG_DIR = BUNDLE_ROOT / "bench-config" / "exemplars"

CASE_TYPES: list[str] = [
    "civil-wp",
    "criminal-wp",
    "pil",
    "first-appeal",
    "second-appeal",
    "criminal-appeal",
    "criminal-revision",
    "application-482",
    "bail",
    "anticipatory-bail",
    "contempt-petition",
    "mact",
    "mat",
]

CASE_TYPE_DESCRIPTIONS: dict[str, str] = {
    "civil-wp": "Civil Writ Petition under Articles 226 / 227 of the Constitution",
    "criminal-wp": "Criminal Writ Petition under Articles 226 / 227 of the Constitution",
    "pil": "Public Interest Litigation under Article 226 of the Constitution",
    "first-appeal": "First Appeal from a District Court decree under CPC Section 96",
    "second-appeal": "Second Appeal under CPC Section 100 (substantial question of law)",
    "criminal-appeal": "Criminal Appeal under BNSS Section 415(2) / Section 374(2) CrPC",
    "criminal-revision": "Criminal Revision under BNSS Section 442 / Sections 397 + 401 CrPC",
    "application-482": "Application under Section 482 CrPC / Section 528 BNSS (inherent jurisdiction — typically FIR / proceedings quashing)",
    "bail": "Regular bail under BNSS Section 483 / Section 439 CrPC",
    "anticipatory-bail": "Anticipatory bail under BNSS Section 482 / Section 438 CrPC",
    "contempt-petition": "Contempt Petition under the Contempt of Courts Act 1971",
    "mact": "Motor Accident Claims Tribunal appeal under Section 173 MV Act 1988",
    "mat": "Matrimonial Appeal under the Hindu Marriage Act / Special Marriage Act / Indian Divorce Act",
}

AGENT_NAMES: list[str] = [
    "reader",
    "format",
    "drafter",
    "verifier",
    "refiner",
    "overseer",
]


def _list_benches_internal() -> list[str]:
    """Derive available benches from bench-config/exemplars/ folder."""
    if not BENCH_CONFIG_DIR.exists():
        return []
    return sorted(
        p.stem
        for p in BENCH_CONFIG_DIR.iterdir()
        if p.is_file() and p.suffix == ".md"
    )


ACRONYM_TO_CASE_TYPE: dict[str, str] = {
    "APL": "application-482",
    "ABA": "anticipatory-bail",
    "BA": "bail",
    "WP": "civil-wp",
    "CrWP": "criminal-wp",
    "PIL": "pil",
    "CrA": "criminal-appeal",
    "CrR": "criminal-revision",
    "FA": "first-appeal",
    "SA": "second-appeal",
    "CP": "contempt-petition",
    "CONTEMPT": "contempt-petition",
    "MACT": "mact",
    "MAT": "mat",
}


@mcp.tool(annotations=ToolAnnotations(title="List Available Case Types", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def list_case_types() -> dict:
    """List all High Court case types this connector can draft.

    Returns a dict with the list of case types, a short description of each,
    AND an acronym disambiguation map (Indian advocacy acronyms → case_type).

    CRITICAL: the user's acronym IS the source of truth for case_type
    classification. APL ≠ ABA. Do not infer case_type from FIR content.
    """
    return {
        "case_types": CASE_TYPES,
        "descriptions": CASE_TYPE_DESCRIPTIONS,
        "acronym_to_case_type": ACRONYM_TO_CASE_TYPE,
        "disambiguation_note": (
            "Indian advocacy acronyms are NOT phonetic. If the user typed "
            "APL, case_type is 'application-482' (Section 482 CrPC quashing). "
            "If the user typed ABA, case_type is 'anticipatory-bail'. "
            "APL ≠ ABA. Use the acronym_to_case_type map above as the lookup. "
            "Do not infer case_type from FIR content."
        ),
        "note": "Call get_case_type_format(case_type) for the full drafting skill. Use list_benches() + get_bench_config(bench) to retrieve the bench-specific Registry conventions.",
    }


@mcp.tool(annotations=ToolAnnotations(title="Get Case Type Drafting Format", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def get_case_type_format(case_type: str) -> str:
    """Get the drafting format for a High Court case type.

    Returns the full SKILL.md content for the case type, including statutory
    anchors (Article 226 / 227 of the Constitution, CPC Sections 96 / 100,
    BNSS / CrPC parallels, Contempt of Courts Act 1971, MV Act 1988), format
    placeholders, and the drafting checklist. Also appends format-from-user.md
    if present.

    Args:
        case_type: One of civil-wp, criminal-wp, pil, first-appeal, second-appeal,
                   criminal-appeal, criminal-revision, application-482, bail,
                   anticipatory-bail, contempt-petition, mact, mat.
    """
    if case_type not in CASE_TYPES:
        return (
            f"Error: unknown case_type '{case_type}'. "
            f"Available: {', '.join(CASE_TYPES)}. "
            "Call list_case_types() for descriptions."
        )

    skill_dir = SKILLS_DIR / f"{case_type}-draft"
    skill_md = skill_dir / "SKILL.md"
    format_from_user = skill_dir / "format-from-user.md"

    if not skill_md.exists():
        return f"Error: skill file not found for case_type '{case_type}'."

    parts = ["# Case-type skill: " + case_type, "", skill_md.read_text(encoding="utf-8")]
    if format_from_user.exists():
        parts.extend(
            [
                "",
                "---",
                "",
                "# Format expected from user (case-type checklist)",
                "",
                format_from_user.read_text(encoding="utf-8"),
            ]
        )
    return "\n".join(parts)


FULL_ORCHESTRATION_SCRIPT = """# wolfgang_rush — INDIAN HIGH COURT DRAFTING · FULL ORCHESTRATION SCRIPT

**YOU MUST execute every step below in order. DO NOT skip steps. DO NOT write
standalone python-docx, JavaScript, or shell scripts to generate output —
invoke the tools listed at each step.**

## STEP 0 PRE-CHECK — CASE-TYPE DISAMBIGUATION (CRITICAL — DO NOT GUESS)

Indian advocacy uses acronyms that are NOT phonetic and NOT inferrable from
the FIR or input content. Read this table BEFORE picking case_type. The user's
ACRONYM is the source of truth — DO NOT re-classify based on what the FIR
"looks like" they need.

| Acronym | Full name | case_type value |
|---------|-----------|-----------------|
| **APL** | Application under Section 482 CrPC / Section 528 BNSS (inherent jurisdiction — FIR / proceedings QUASHING) | `application-482` |
| **ABA** | Anticipatory Bail Application (Section 482 BNSS / Section 438 CrPC) | `anticipatory-bail` |
| **BA** | Regular Bail Application (Section 483 BNSS / Section 439 CrPC) | `bail` |
| **WP** | Civil Writ Petition under Articles 226 / 227 | `civil-wp` |
| **CrWP** | Criminal Writ Petition under Articles 226 / 227 | `criminal-wp` |
| **PIL** | Public Interest Litigation | `pil` |
| **CrA** | Criminal Appeal (BNSS Section 415(2) / CrPC Section 374(2)) | `criminal-appeal` |
| **CrR** | Criminal Revision (BNSS Section 442 / CrPC Sections 397 + 401) | `criminal-revision` |
| **FA** | First Appeal (CPC Section 96) | `first-appeal` |
| **SA** | Second Appeal (CPC Section 100) | `second-appeal` |
| **CP / CONTEMPT** | Contempt Petition (Contempt of Courts Act 1971) | `contempt-petition` |
| **MACT** | Motor Accident Claims Tribunal appeal (MV Act 1988 Section 173) | `mact` |
| **MAT** | Matrimonial Appeal (Hindu Marriage Act / Special Marriage Act / Indian Divorce Act) | `mat` |

**Critical disambiguation: APL ≠ ABA.** APL is the QUASHING application (challenge
the FIR / proceedings on Bhajan Lal grounds — typically when accused contends
the FIR is malicious, time-barred, makes out no offence, etc.). ABA is the
ANTICIPATORY BAIL application (accused apprehends arrest, seeks pre-arrest bail).
A FIR naming an unknown accused does NOT auto-map to anticipatory-bail — that
inference WOULD SKIP the user's stated intent. If the user typed APL, use
`application-482`. If unclear, ASK before calling create_case_folder.

If the acronym is not in the table above, ask the user to spell it out.

## STEP 0 — CREATE THE CASE FOLDER

Call `create_case_folder(case_type, bench)` where:
- `case_type` is one of the 13 values resolved via the STEP 0 PRE-CHECK table
- `bench` is the lowercase hyphenated bench identifier — **REQUIRED**. The
  plugin is BENCH-NEUTRAL and does NOT assume any particular High Court.

**If the user has not named their High Court / bench, ASK THEM before calling
this tool.** Examples: `delhi-hc`, `madras-hc`, `bombay-hc-principal-mumbai`,
`calcutta-hc`, `allahabad-hc`, `karnataka-hc`, `bombay-hc`,
`gauhati-hc`, `kerala-hc`, `punjab-haryana-hc`, etc. Call `list_benches()`
first to enumerate all 28 bundled exemplars.

A Delhi advocate filing in Delhi HC must get `bench="delhi-hc"`. A Madras
advocate filing in Madras HC must get `bench="madras-hc"`. The connector does
NOT default to any single High Court.

The tool returns `case_folder` — an absolute path. **Use this path in every
subsequent save_artifact and save_draft_as_docx call.**

## STEP 1 — MATERIALIZE THE USER'S INPUT DOCUMENTS

Every source document the user attached to this conversation (FIR, judgment,
order, contract, lower-court record, etc.) must be saved to disk before the
Reader can run. For each attachment in the chat:

Call `save_artifact(case_folder, "inputs/<original-filename>", <extracted-text>)`

If the source is a PDF and you have its raw text from the chat, save the text
as `inputs/<original-filename>.txt`. The Reader will pick up the inputs/ folder.

## STEP 2 — LOAD THE CASE-TYPE SKILL

Call `get_case_type_format(case_type)`. Read the returned SKILL.md carefully.
This is the format the Drafter will produce.

## STEP 3 — LOAD THE BENCH CONFIG

Call `get_bench_config(bench)`. Read the returned bench-specific Registry
conventions (Court header, parties separator, annexure prefix, paper size,
font preference, Appellate-Side / Original-Side Rules reference).

## STEP 4 — LOAD THE PLEADING BASE

Call `get_pleading_base()`. Read the universal HC pleading skeleton (Cause
Title → Synopsis → Statement of Facts → Grounds → Prayer → Annexures) and
the common drafting discipline (citation rules, AI-fabricated-citation risk
per HC cautions).

## STEP 5 — RUN THE READER AGENT

Call `get_agent_instructions("reader")` to load the Reader persona. Then,
acting as the Reader, process every file in `<case_folder>/inputs/` and
produce `case-facts.md` according to the Reader specification.

Save the output via `save_artifact(case_folder, "case-facts.md", <content>)`.

## STEP 6 — RUN THE FORMAT AGENT

Call `get_agent_instructions("format")` to load the Format persona. Acting
as Format, map the Reader's case-facts.md into the case-type SKILL.md
placeholders, with bench-config substitution applied.

Save the output via `save_artifact(case_folder, "format-shell.md", <content>)`.

## STEP 7 — RUN THE DRAFTER AGENT

Call `get_agent_instructions("drafter")` to load the Drafter persona. Acting
as Drafter, write the first complete draft in markdown, using format-shell.md
as scaffold and case-facts.md as ground-truth.

Save the markdown via `save_artifact(case_folder, "draft-v1.md", <content>)`.

Then call `save_draft_as_docx(<markdown>, f"{case_folder}/draft-v1.docx")` to
produce the .docx.

## STEP 8 — RUN THE VERIFIER AGENT (ANTI-HALLUCINATION FIREWALL — DO NOT SKIP)

Call `get_agent_instructions("verifier")` to load the Verifier persona.
Acting as Verifier, compare draft-v1.md against case-facts.md fact-by-fact.
Flag every hallucinated date, fabricated citation, unsupported assertion,
orphan annexure marker, and missing factual basis.

Save the report via `save_artifact(case_folder, "verification-report.md", <content>)`.

## STEP 9 — RUN THE REFINER AGENT

Call `get_agent_instructions("refiner")` to load the Refiner persona. Acting
as Refiner, apply every Verifier flag, polish language, enforce HC Registry
formatting, remove AI-style markers.

Save markdown via `save_artifact(case_folder, "draft-v2.md", <content>)`.
Then call `save_draft_as_docx(<markdown>, f"{case_folder}/draft-v2.docx")`.

## STEP 10 — RUN THE OVERSEER AGENT (OPPOSING-COUNSEL LENS — DO NOT SKIP)

Call `get_agent_instructions("overseer")` to load the Overseer persona.
Acting as Overseer, read draft-v2.md with opposing-counsel lens. Find weak
prayers, contradictory facts, attackable defects, missing limbs of argument.

Save the notes via `save_artifact(case_folder, "opposing-notes.md", <content>)`.

Then apply the Overseer's hardening recommendations to produce the final
draft. Save markdown via `save_artifact(case_folder, "final-draft.md", <content>)`
and call `save_draft_as_docx(<markdown>, f"{case_folder}/final-draft.docx")`.

## STEP 11 — REPORT TO THE USER

Return the absolute path to `final-draft.docx` and a one-paragraph summary
of (a) the case-type drafted, (b) the bench targeted, (c) any Verifier flags
the Refiner addressed, (d) the Overseer's top three hardening observations.

---

**FALSIFICATION CHECK before STEP 11:** the case folder must contain at
minimum these six artifacts. If any are missing, return to the matching
STEP and produce it. Do not present a partial pipeline as complete.

1. case-facts.md
2. format-shell.md
3. draft-v1.docx (or draft-v1.md)
4. verification-report.md
5. draft-v2.docx (or draft-v2.md)
6. final-draft.docx

**REMINDER:** YOU MUST NOT write a standalone python-docx generator script,
a JavaScript script, or any one-shot drafting program. The MCPB exposes
every required tool. Use them.
"""


@mcp.tool(annotations=ToolAnnotations(title="Get Pipeline Agent Instructions", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def get_agent_instructions(agent_name: str = "") -> str:
    """Get the instructions for the HC drafting pipeline.

    Default mode (no agent_name, or agent_name=""): returns the FULL orchestration
    script enumerating every step and tool call from case-folder creation through
    final-draft.docx. THIS IS THE MANDATORY FIRST CALL when the user asks you to
    draft anything.

    Single-agent mode (agent_name ∈ {reader, format, drafter, verifier, refiner,
    overseer}): returns that agent's persona instructions only. Use after the
    orchestration script tells you which agent to invoke at each step.

    Args:
        agent_name: Empty string for the orchestration script (default).
                    Otherwise one of reader, format, drafter, verifier, refiner,
                    overseer for that agent's persona only.
    """
    if not agent_name or agent_name == "full":
        return FULL_ORCHESTRATION_SCRIPT

    if agent_name not in AGENT_NAMES:
        return (
            f"Error: unknown agent_name '{agent_name}'. "
            f"Available: {', '.join(AGENT_NAMES)}. "
            "Call with no arguments to receive the full orchestration script."
        )

    agent_md = AGENTS_DIR / agent_name / f"{agent_name}.md"
    if not agent_md.exists():
        return f"Error: agent file not found for '{agent_name}'."
    return agent_md.read_text(encoding="utf-8")


def _sanitise_path_component(value: str) -> str:
    """Strip path separators and dangerous chars from a single path component."""
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "-", value.strip())
    cleaned = cleaned.strip(".-_") or "untitled"
    return cleaned[:80]


@mcp.tool(annotations=ToolAnnotations(title="Create Case Folder", readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
def create_case_folder(case_type: str, bench: str, base_dir: str = "") -> dict:
    """Create the case folder for a drafting session on the user's machine.

    Creates a timestamped folder under ~/Downloads/Wolfgang-Rush-Drafts/ (or the
    base_dir if supplied) named <case-type>-<bench>-<YYYYMMDD-HHMMSS>/, with an
    inputs/ subfolder (for source documents).

    The `bench` argument is REQUIRED — the plugin is bench-neutral and does NOT
    assume any particular High Court. If the user has not named their bench,
    ASK them before calling this tool. Examples: delhi-hc, madras-hc,
    bombay-hc-principal-mumbai, calcutta-hc, allahabad-hc, karnataka-hc,
    bombay-hc, gauhati-hc. Call list_benches() to discover all 28
    bundled exemplars.

    Args:
        case_type: One of civil-wp, criminal-wp, pil, first-appeal, second-appeal,
                   criminal-appeal, criminal-revision, application-482, bail,
                   anticipatory-bail, contempt-petition, mact, mat.
        bench: Lowercase hyphenated bench identifier. REQUIRED. If user did not
               specify, ask before calling.
        base_dir: Optional override for the parent directory. Defaults to
                  ~/Downloads/Wolfgang-Rush-Drafts/.

    Returns:
        Dict with case_folder (absolute path), inputs_folder, case_type, bench,
        timestamp.
    """
    if case_type not in CASE_TYPES:
        return {
            "error": f"unknown case_type '{case_type}'. Available: {', '.join(CASE_TYPES)}.",
        }

    if not bench:
        return {
            "error": (
                "bench argument is REQUIRED. The plugin is bench-neutral and does "
                "NOT assume any particular High Court. Ask the user which Indian "
                "High Court / bench they are filing in, then call this tool again. "
                "Use list_benches() to enumerate available exemplar identifiers."
            ),
        }

    available_benches = _list_benches_internal()
    if available_benches and bench not in available_benches:
        return {
            "error": f"unknown bench '{bench}'. Available: {', '.join(available_benches[:10])}...",
        }

    parent = Path(base_dir).expanduser().resolve() if base_dir else DEFAULT_DRAFTS_ROOT
    parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_name = f"{_sanitise_path_component(case_type)}-{_sanitise_path_component(bench)}-{timestamp}"
    case_folder = parent / folder_name
    inputs_folder = case_folder / "inputs"
    inputs_folder.mkdir(parents=True, exist_ok=True)

    readme = case_folder / "README.md"
    readme.write_text(
        f"# wolfgang_rush HC Drafting · Case Folder\n\n"
        f"- Case type: {case_type}\n"
        f"- Bench: {bench}\n"
        f"- Created: {datetime.now().isoformat(timespec='seconds')}\n\n"
        f"## Folder layout\n\n"
        f"- `inputs/` — source documents (FIR, judgments, orders, etc.)\n"
        f"- `case-facts.md` — Reader output\n"
        f"- `format-shell.md` — Format output\n"
        f"- `draft-v1.docx` — Drafter output\n"
        f"- `verification-report.md` — Verifier output (anti-hallucination firewall)\n"
        f"- `draft-v2.docx` — Refiner output\n"
        f"- `opposing-notes.md` — Overseer output\n"
        f"- `final-draft.docx` — Final filing-grade output\n",
        encoding="utf-8",
    )

    return {
        "case_folder": str(case_folder),
        "inputs_folder": str(inputs_folder),
        "case_type": case_type,
        "bench": bench,
        "timestamp": timestamp,
        "next_step": (
            "Save every source document the user attached to this conversation "
            f"into '{inputs_folder}' via save_artifact, then proceed to STEP 2 "
            "of the orchestration script (get_case_type_format)."
        ),
    }


@mcp.tool(annotations=ToolAnnotations(title="Save Pipeline Artifact", readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def save_artifact(case_folder: str, relative_path: str, content: str) -> dict:
    """Save a pipeline artifact or input document into the case folder.

    Required at the end of every agent step. Saves the supplied text content
    to <case_folder>/<relative_path>. Rejects path traversal (.. components)
    and absolute relative_paths.

    Args:
        case_folder: Absolute path returned by create_case_folder.
        relative_path: Path relative to case_folder. Pipeline artifact names
                       (case-facts.md, format-shell.md, draft-v1.md,
                       verification-report.md, draft-v2.md, opposing-notes.md,
                       final-draft.md) are accepted at the root.
                       Input documents go under inputs/ (e.g.,
                       'inputs/source-document.txt').
        content: The text content to write.

    Returns:
        Dict with success, path, file_size_bytes.
    """
    case_dir = Path(case_folder).expanduser().resolve()
    if not case_dir.exists() or not case_dir.is_dir():
        return {
            "success": False,
            "error": f"case_folder '{case_folder}' does not exist or is not a directory. Call create_case_folder first.",
        }

    rel = Path(relative_path)
    if rel.is_absolute():
        return {"success": False, "error": "relative_path must not be absolute."}
    if any(part == ".." for part in rel.parts):
        return {"success": False, "error": "relative_path must not contain '..' segments."}

    is_root_artifact = len(rel.parts) == 1
    if is_root_artifact and rel.name not in ALLOWED_ARTIFACT_NAMES:
        return {
            "success": False,
            "error": (
                f"'{rel.name}' is not a recognised root-level artifact. "
                f"Allowed: {', '.join(sorted(ALLOWED_ARTIFACT_NAMES))}. "
                "Input documents must go under inputs/."
            ),
        }

    target = (case_dir / rel).resolve()
    try:
        target.relative_to(case_dir)
    except ValueError:
        return {"success": False, "error": "resolved path escapes the case_folder."}

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "path": str(target),
        "file_size_bytes": target.stat().st_size,
        "relative_path": rel.as_posix(),
    }


@mcp.tool(annotations=ToolAnnotations(title="Get Pleading Base Structure", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def get_pleading_base() -> str:
    """Get the shared HC pleading base structure used by all case-types.

    Returns the universal High Court pleading skeleton (Cause Title to
    Synopsis to Statement of Facts to Grounds to Prayer to Annexures), the
    HC Registry formatting rules, and the cross-cutting drafting discipline
    (citation, AOR / counsel block format, AI-fabricated-citation risk per
    Bombay HC / Madras HC / Delhi HC cautions to advocates).
    """
    base_dir = SKILLS_DIR / "_hc_pleading_base"
    common_md = SKILLS_DIR / "_drafting_common" / "SKILL.md"

    parts: list[str] = []
    if base_dir.exists():
        for md_file in sorted(base_dir.glob("*.md")):
            parts.append(f"# {md_file.stem}")
            parts.append("")
            parts.append(md_file.read_text(encoding="utf-8"))
            parts.append("")
            parts.append("---")
            parts.append("")
    if common_md.exists():
        parts.append("# Common Drafting Discipline")
        parts.append("")
        parts.append(common_md.read_text(encoding="utf-8"))
    return "\n".join(parts)


@mcp.tool(annotations=ToolAnnotations(title="List Available High Court Benches", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def list_benches() -> dict:
    """List the High Court bench exemplars available.

    Returns the list of bench exemplars this connector bundles. Each exemplar
    captures the Court header text, parties separator, section-header style,
    annexure-marker prefix, counsel block format, paper size, font preference,
    and Appellate-Side vs Original-Side Rules reference for that bench.

    Most-validated bench at v0.1.0 is bombay-hc; other benches are
    supported via bundled exemplars and welcome community-validation
    contributions for Registry-acceptance discipline.
    """
    benches = _list_benches_internal()
    return {
        "benches": benches,
        "count": len(benches),
        "note": (
            "Call get_bench_config(bench) for the per-bench Registry conventions. "
            "Bench names use lowercase hyphenated form (e.g., 'bombay-hc', "
            "'delhi-hc', 'madras-hc'). Multi-bench HCs have separate exemplars "
            "for each bench (Bombay HC has multiple benches: principal-mumbai, aurangabad, goa, etc.)."
        ),
    }


@mcp.tool(annotations=ToolAnnotations(title="Get Bench-Specific Registry Conventions", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def get_bench_config(bench: str) -> str:
    """Get the bench-specific configuration for a High Court bench.

    Returns the bench-specific Registry conventions: Court header, parties
    separator, section-header style, annexure prefix, counsel block format,
    paper size, font preference, Appellate-Side / Original-Side Rules
    reference, and any bench-specific procedural specialities.

    Args:
        bench: Lowercase hyphenated bench identifier. Use list_benches() to
               discover available identifiers (e.g., 'bombay-hc',
               'delhi-hc', 'madras-hc', 'calcutta-hc').
    """
    available = _list_benches_internal()
    if bench not in available:
        return (
            f"Error: no exemplar found for bench '{bench}'. "
            f"Available: {', '.join(available)}. "
            "Call list_benches() to discover available identifiers."
        )

    exemplar_path = BENCH_CONFIG_DIR / f"{bench}.md"
    if not exemplar_path.exists():
        return f"Error: exemplar file missing for bench '{bench}'."
    return exemplar_path.read_text(encoding="utf-8")


@mcp.tool(annotations=ToolAnnotations(title="Read Case Folder Files", readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def read_case_folder(path: str) -> dict:
    """Read all files in a case folder on the user's machine.

    Walks the folder recursively, reads .md, .txt, .pdf (via pdftotext), and
    .docx (via pandoc) files, and returns text content as a dict mapping
    relative filename to content. Hidden files are skipped.

    Args:
        path: Absolute or relative path to the case folder on the user's machine.
    """
    folder = Path(path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        return {
            "error": f"Path '{path}' is not a valid directory.",
            "files": {},
            "warnings": [],
            "file_count": 0,
        }

    files: dict[str, str] = {}
    warnings: list[str] = []

    for f in sorted(folder.rglob("*")):
        if not f.is_file():
            continue
        if any(part.startswith(".") for part in f.relative_to(folder).parts):
            continue
        rel = f.relative_to(folder).as_posix()
        ext = f.suffix.lower()

        try:
            if ext in (".md", ".txt"):
                files[rel] = f.read_text(encoding="utf-8", errors="replace")
            elif ext == ".pdf":
                try:
                    result = subprocess.run(
                        ["pdftotext", str(f), "-"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        files[rel] = result.stdout
                    else:
                        warnings.append(f"pdftotext failed on {rel}: {result.stderr.strip()[:200]}")
                        files[rel] = f"[PDF file at {rel} — text not extracted]"
                except FileNotFoundError:
                    warnings.append(
                        "pdftotext not installed. Install via 'brew install poppler' "
                        "(macOS) or 'apt-get install poppler-utils' (Linux)."
                    )
                    files[rel] = f"[PDF file at {rel} — pdftotext not installed]"
                except subprocess.TimeoutExpired:
                    warnings.append(f"pdftotext timed out on {rel}")
                    files[rel] = f"[PDF file at {rel} — extraction timed out]"
            elif ext == ".docx":
                try:
                    result = subprocess.run(
                        ["pandoc", "-f", "docx", "-t", "markdown", str(f)],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        files[rel] = result.stdout
                    else:
                        warnings.append(f"pandoc failed on {rel}: {result.stderr.strip()[:200]}")
                        files[rel] = f"[DOCX file at {rel} — text not extracted]"
                except FileNotFoundError:
                    warnings.append(
                        "pandoc not installed. Install via 'brew install pandoc' (macOS) "
                        "or 'apt-get install pandoc' (Linux)."
                    )
                    files[rel] = f"[DOCX file at {rel} — pandoc not installed]"
                except subprocess.TimeoutExpired:
                    warnings.append(f"pandoc timed out on {rel}")
                    files[rel] = f"[DOCX file at {rel} — extraction timed out]"
            else:
                warnings.append(f"Skipped unsupported file type: {rel}")
        except Exception as exc:
            warnings.append(f"Error reading {rel}: {exc}")

    return {
        "folder": str(folder),
        "files": files,
        "warnings": warnings,
        "file_count": len(files),
    }


@mcp.tool(annotations=ToolAnnotations(title="Save Draft as Filing-Grade DOCX", readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False))
def save_draft_as_docx(markdown_text: str, output_path: str) -> dict:
    """Save a draft pleading as a filing-grade .docx using pandoc.

    Renders the supplied markdown text to a Microsoft Word .docx file using
    pandoc. If the HC pleading base ships a reference.docx, it is applied for
    HC Registry formatting conventions.

    Args:
        markdown_text: The draft pleading content in markdown format.
        output_path: Absolute or relative path on the user's machine where the
                     .docx file should be saved.
    """
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    reference_docx_candidates = [
        SKILLS_DIR / "_hc_pleading_base" / "reference.docx",
        SKILLS_DIR / "_hc_pleading_base" / "REFERENCE.docx",
    ]
    reference_docx = next((p for p in reference_docx_candidates if p.exists()), None)

    temp_md = output.parent / f".{output.stem}.tmp.md"
    temp_md.write_text(markdown_text, encoding="utf-8")

    cmd = ["pandoc", str(temp_md), "-o", str(output)]
    if reference_docx is not None:
        cmd.extend(["--reference-doc", str(reference_docx)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        temp_md.unlink(missing_ok=True)

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip()[:500],
                "output_path": str(output),
            }

        return {
            "success": True,
            "output_path": str(output),
            "file_size_bytes": output.stat().st_size,
            "reference_docx_applied": reference_docx is not None,
        }
    except FileNotFoundError:
        temp_md.unlink(missing_ok=True)
        return {
            "success": False,
            "error": (
                "pandoc not installed. Install via 'brew install pandoc' (macOS), "
                "'apt-get install pandoc' (Linux), or download from pandoc.org (Windows)."
            ),
            "output_path": str(output),
        }
    except subprocess.TimeoutExpired:
        temp_md.unlink(missing_ok=True)
        return {
            "success": False,
            "error": "pandoc conversion timed out after 60 seconds.",
            "output_path": str(output),
        }


if __name__ == "__main__":
    mcp.run()
