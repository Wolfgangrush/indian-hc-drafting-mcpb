# Wolfgang Rush — Indian High Court Drafting

**MCPB Desktop Extension** for drafting pleadings before any High Court of India.

Bench-config-aware: 28 bench exemplars covering all 25 Indian High Courts including multi-bench HCs (Bombay Principal Mumbai, Nagpur, Aurangabad, Goa). Designed for Indian advocates using **Claude Desktop App**. Local-execution. Zero data collection.

> *Also available as a Claude Code Plugin (for developers using the Claude Code CLI):*
> *[github.com/Wolfgangrush/indian-hc-drafting-litigation](https://github.com/Wolfgangrush/indian-hc-drafting-litigation)*

---

## What this connector does

Exposes the Wolfgang Rush six-agent HC drafting pipeline as MCP tools that Claude can orchestrate from a Claude Desktop chat. Drafts the following case types:

### Constitutional / Writ-side

| Case type | Statutory anchor |
|---|---|
| Civil Writ Petition | Articles 226 / 227 of the Constitution |
| Criminal Writ Petition | Articles 226 / 227 of the Constitution |
| Public Interest Litigation | Article 226 of the Constitution |

### Appellate-side

| Case type | Statutory anchor |
|---|---|
| First Appeal | CPC Section 96 |
| Second Appeal | CPC Section 100 (substantial question of law) |
| Criminal Appeal | BNSS Section 415(2) / Section 374(2) CrPC |
| Criminal Revision | BNSS Section 442 / Sections 397 + 401 CrPC |
| MACT Appeal | Section 173 MV Act 1988 |
| Matrimonial Appeal | HMA / SMA / Indian Divorce Act |

### Inherent-jurisdiction and miscellaneous

| Case type | Statutory anchor |
|---|---|
| Application under Section 482 CrPC / 528 BNSS | Inherent jurisdiction (quashing FIR / proceedings) |
| Anticipatory Bail | BNSS Section 482 / Section 438 CrPC |
| Regular Bail | BNSS Section 483 / Section 439 CrPC |
| Contempt Petition | Contempt of Courts Act 1971 |

### Bench exemplars (28 covering all 25 Indian HCs)

`allahabad-hc` · `andhra-pradesh-hc` · `bombay-hc-aurangabad` · `bombay-hc-goa` · `bombay-hc-nagpur` · `bombay-hc-principal-mumbai` · `calcutta-hc` · `chhattisgarh-hc` · `delhi-hc` · `gauhati-hc` · `gujarat-hc` · `himachal-pradesh-hc` · `jammu-kashmir-ladakh-hc` · `jharkhand-hc` · `karnataka-hc` · `kerala-hc` · `madhya-pradesh-hc` · `madras-hc` · `manipur-hc` · `meghalaya-hc` · `orissa-hc` · `patna-hc` · `punjab-haryana-hc` · `rajasthan-hc` · `sikkim-hc` · `telangana-hc` · `tripura-hc` · `uttarakhand-hc`

Each exemplar captures bench-specific Registry conventions (Court header, parties separator, section-header style, annexure prefix, counsel block format, paper size, font preference, Appellate-Side vs Original-Side Rules reference).

Most-validated bench at v0.1.0 is **bombay-hc-nagpur**. Other benches are bundled with verified exemplars and welcome community-validation contributions.

---

## Install

1. Open **Claude Desktop App**
2. **Settings → Extensions → Install Extension**
3. Select `wolfgang-indian-hc-drafting.mcpb`
4. Enable the extension
5. Start a new chat

## System requirements

- macOS, Windows, or Linux with Claude Desktop App ≥ 0.10.0
- Python ≥ 3.10 (Claude Desktop App bundles uv runtime automatically)
- **`pandoc`** for `.docx` output (`brew install pandoc` on macOS · `apt-get install pandoc` on Linux · download from pandoc.org on Windows)
- **`pdftotext`** for PDF reading (`brew install poppler` on macOS · `apt-get install poppler-utils` on Linux)

## Usage

In a Claude Desktop chat, describe what you want to draft and specify the bench. Claude will discover and call the connector's tools as needed.

Example prompts:

- *"Draft a civil writ petition under Article 226 before the Bombay HC Nagpur Bench challenging the SDM order dated 2026-03-15, prayer for quashing + interim stay."*
- *"Draft a Section 482 CrPC application before the Delhi HC for quashing FIR No. [FIR-X] under Sections 318 + 316 BNSS on Bhajan Lal categories."*
- *"Draft a contempt petition before the Madras HC for wilful disobedience of the HC order dated [DATE-N] in [WP-N]."*

## Tools

| Tool | Purpose |
|---|---|
| `list_case_types` | Discover the 13 available HC case types |
| `get_case_type_format` | Retrieve the drafting template for a case type |
| `get_agent_instructions` | Retrieve instructions for a stage in the six-agent pipeline |
| `get_pleading_base` | Retrieve the universal HC pleading skeleton |
| `list_benches` | Discover the 28 bench exemplars bundled |
| `get_bench_config` | Retrieve bench-specific Registry conventions |
| `read_case_folder` | Read files in a case folder for fact extraction |
| `save_draft_as_docx` | Render markdown as filing-grade .docx |

## Privacy

This connector collects **zero** user data. All processing happens on the user's machine. The publisher (Wolfgang Rush) never receives any user data.

Three-layer privacy firewall: **L1 substitution** → **L2 LLM-blind** → **L3 re-substitution**.

Canonical privacy policy: **<https://wolfgangrush.github.io/privacy/>**

## Confidentiality and professional privilege

Case-folder contents passed to this connector may include material attracting attorney-client privilege under **Section 132 of the Bharatiya Sakshya Adhiniyam 2023** / **Section 126 of the Indian Evidence Act 1872**. The user remains professionally responsible consistent with Bar Council of India rules and client-engagement terms.



## Architecture · how the six agents work

This connector runs a strict six-agent pipeline locally on your machine:

| Agent | What it does | Output |
|---|---|---|
| **Reader** | Reads every input document. Extracts facts with per-document audit log. **Applies the pseudonymisation firewall** (see below). Halts if a required statute PDF is missing. | `case-facts.md` |
| **Format** | Loads the case-type-specific skill + bench/state/forum-config + pleading base. Maps Reader's facts into the format placeholders. | `format-shell.md` |
| **Drafter** | Writes the first complete draft — Cause Title, Statutory Opening, Synopsis, Statement of Facts, Grounds, Prayer, Verification, Counsel Block, Index, Annexure List. | `draft-v1.md` + `draft-v1.docx` |
| **Verifier** | Anti-hallucination firewall. Compares draft-v1 against case-facts.md fact-by-fact. Flags hallucinated dates, fabricated citations, unsupported assertions, orphan annexure markers, missing factual basis. | `verification-report.md` |
| **Refiner** | Applies every Verifier flag. Polishes language to formal Indian pleading register. Enforces Registry formatting. Strips AI-style markers. | `draft-v2.md` + `draft-v2.docx` |
| **Overseer** | Reads draft-v2 with opposing-counsel lens. Finds weak prayers, contradictory facts, attackable defects, missing limbs of argument. Suggests hardening. | `opposing-notes.md` + `final-draft.docx` |

The pipeline is **forced by the connector itself** — the `get_agent_instructions()` tool is the mandatory first call when you ask for a draft and returns an 11-step orchestration script that names every agent's tool call. The Drafter cannot legitimately produce final output without the Reader having saved `case-facts.md` first. The `save_artifact` tool's allow-list rejects standalone python-docx or JavaScript generator scripts.

→ **Full pipeline architecture: [wolfgangrush.github.io/mcpb/agents/](https://wolfgangrush.github.io/mcpb/agents/)**

## 🔒 Pseudonymisation gateway — what gets substituted

The Reader agent applies a privacy firewall **before any downstream agent sees the facts**. The following are substituted with structural placeholders:

- **Party identifiers** — Petitioner / Respondent / Plaintiff / Defendant / Accused / Complainant / Witness names → `[Petitioner-A]`, `[Respondent-B]`, `[Witness-A]`
- **Addresses** — Full residential / business addresses → `[Address-Placeholder]`
- **Government identifiers** — PAN, Aadhaar, TAN, DIN, GSTIN → `[PAN-Placeholder]`, `[Aadhaar-Placeholder]`, etc.
- **Case numbers** — FIR / CR / Crime / SLP / Diary / CC / SC / RCS / lower-court case numbers → `[Crime-No-Placeholder]`, `[SLP-No-Placeholder]`, `[Lower-Court-Case-No-Placeholder]`
- **Financial figures** — Amounts in dispute, compensation, tax assessed → `[Amount-Placeholder]`
- **Statutory notice references** — Section 106 TPA notice dates, statutory demand-notice dates → `[Notice-Date-Placeholder]`

The Drafter, Verifier, Refiner, and Overseer agents process **placeholders only**. At the final `save_draft_as_docx` step, the placeholders are re-substituted with the real values **on your local machine**. The LLM never sees the re-substituted output.

This is the connector's contribution to your **Section 8(5) DPDP Act 2023** safeguard.

→ **Full pseudonymisation mechanism: [wolfgangrush.github.io/mcpb/agents/#pseudonymisation-gateway-what-gets-substituted](https://wolfgangrush.github.io/mcpb/agents/#pseudonymisation-gateway--what-gets-substituted)**

## ⚖️ DPDP Act 2023 — what this means for you

**Publisher position.** Wolfgang Rush, in its capacity as software publisher, is **neither a Data Fiduciary nor a Data Processor** under the DPDP Act 2023 in respect of this connector. The connector runs entirely on your machine. There is no Wolfgang Rush server, no telemetry, no API endpoint that the publisher controls. Section 2(i) requires "determining purpose and means of processing" — Wolfgang Rush determines neither.

**User position.** You — the advocate using this connector — are the **Data Fiduciary** for your own client's personal data. This was true before installing the connector and remains true after. Your obligations under Sections 4, 5, 6, 8, 9, 11, 13 of the DPDP Act 2023 continue independent of this connector.

**What the connector helps with.** The pseudonymisation gateway is an architectural safeguard within the meaning of Section 8(5) (reasonable security safeguards). Local-only processing supports your minimisation posture (Section 8). The Reader's per-document audit log supports Section 8(8) (data accuracy). The Section 17(2)(a) exemption ("personal data processed for the purposes of any legal proceeding") substantially covers most everyday advocate processing.

**What the connector does not do.** It does not, by itself, satisfy any DPDP notice / consent / grievance-redressal obligation. Those remain yours to operationalise. It does not cover Anthropic's position as the LLM operator — that is governed by Anthropic's own terms.

→ **Full DPDP applicability analysis: [wolfgangrush.github.io/mcpb/dpdp/](https://wolfgangrush.github.io/mcpb/dpdp/)**

## Multilingual install guides

[हिन्दी](https://wolfgangrush.github.io/mcpb/hi/) · [मराठी](https://wolfgangrush.github.io/mcpb/mr/) · [தமிழ்](https://wolfgangrush.github.io/mcpb/ta/) · [తెలుగు](https://wolfgangrush.github.io/mcpb/te/) · [বাংলা](https://wolfgangrush.github.io/mcpb/bn/) · [ગુજરાતી](https://wolfgangrush.github.io/mcpb/gu/) · [ಕನ್ನಡ](https://wolfgangrush.github.io/mcpb/kn/) · [ਪੰਜਾਬੀ](https://wolfgangrush.github.io/mcpb/pa/) · [മലയാളം](https://wolfgangrush.github.io/mcpb/ml/) · [اردو](https://wolfgangrush.github.io/mcpb/ur/)

## ⚠️ AI verification disclaimer · 🔒 Pseudonymisation procedure

> **⚠️ AI can make mistakes — please verify the information before filing.**
> Every draft produced by this connector is a STARTING POINT. The Verifier
> agent runs an anti-hallucination firewall and the Overseer agent runs an
> opposing-counsel review, but neither replaces an advocate's independent
> verification of statutory references, citation accuracy, factual fidelity,
> and Registry-formatting compliance with the user's High Court / forum.
> The advocate filing the pleading remains responsible for the contents.
>
> **🔒 Protected by pseudonymisation procedure.** The Reader agent applies a
> domain-specific privacy firewall as the first step of the pipeline — party
> names, addresses, identifying numbers (FIR / CR / Crime / Suit / Diary /
> SLP / lower-court case numbers), PAN / Aadhaar references, financial
> figures, witness names, and statutory-notice references are substituted
> with structural placeholders BEFORE any downstream agent sees the facts.
> The Drafter, Verifier, Refiner, and Overseer agents process placeholders
> only. Real values are re-substituted at the final docx render step on the
> user's local machine. No real identifying data leaves the case folder.

## License

MIT. See LICENSE.

## Publisher

**Rushikesh R. Mahajan**, Advocate, Bombay High Court (Nagpur Bench), publishing as **Wolfgang Rush**.

Contact: advrushikeshravindramahajan@gmail.com

## Source

<https://github.com/Wolfgangrush/indian-hc-drafting-mcpb>

## Sample cases

See `SAMPLE-CASES/` for three anonymised fact patterns the reviewer can use to invoke the tools.
