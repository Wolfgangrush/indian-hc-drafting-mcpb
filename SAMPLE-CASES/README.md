# Sample Cases — Reviewer Examples

Three anonymised High Court fact patterns the Anthropic reviewer can use to invoke the connector's tools and exercise the drafting pipeline.

All party names are placeholders. No real client data appears here.

---

## Example 1 — Civil Writ Petition under Article 226 (Bombay HC (your bench))

**Prompt to use in Claude Desktop chat:**

> *"Draft a civil writ petition under Article 226 of the Constitution before the Bombay High Court (the bench you specify). Petitioner is [PETITIONER], challenging the order dated 2026-03-15 of the Sub-Divisional Magistrate at [LOCATION-X] cancelling petitioner's caste-validity certificate. Grounds: violation of principles of natural justice (no opportunity of hearing), arbitrary exercise of power (Article 14), and ultra vires the Maharashtra Scheduled Castes etc. (Regulation of Issuance and Verification of) Caste Certificate Act 2000. Prayer: quashing of impugned order + interim stay during pendency."*

**Expected tool sequence:**
1. `list_case_types()` → confirms civil-wp available
2. `get_case_type_format("civil-wp")` → retrieves the Article 226 civil writ drafting template
3. `list_benches()` → confirms bombay-hc available
4. `get_bench_config("bombay-hc")` → retrieves Bombay HC Appellate-Side Rules + Court header + annexure prefix conventions
5. `get_pleading_base()` → retrieves the universal HC pleading skeleton
6. Drafts the writ using Article 226 + natural justice + ultra vires framework
7. `save_draft_as_docx(markdown, "/path/draft-civil-wp.docx")` → renders filing-grade .docx

---

## Example 2 — Application under Section 482 CrPC / 528 BNSS (Delhi HC)

**Prompt to use in Claude Desktop chat:**

> *"Draft an application under Section 482 CrPC / Section 528 BNSS before the Delhi High Court for quashing FIR No. [FIR-X] dated 2025-11-10 registered at [PS-LOCATION] PS under Sections 318 + 316 BNSS. Petitioner-accused is [PETITIONER]. Grounds based on Bhajan Lal categories — allegations even if taken at face value do not constitute the offence + dispute is essentially civil dressed up as criminal + abuse of process. Documentary evidence shows complainant has parallel civil suit pending on same facts."*

**Expected tool sequence:**
1. `list_case_types()` → confirms application-482 available
2. `get_case_type_format("application-482")` → retrieves the Section 482 / 528 BNSS quashing template with Bhajan Lal categories encoded
3. `list_benches()` → confirms delhi-hc available
4. `get_bench_config("delhi-hc")` → retrieves Delhi HC Original-Side Rules + Court header + counsel block conventions
5. `get_pleading_base()` → retrieves the universal HC pleading skeleton
6. Drafts the quashing application within Bhajan Lal framework
7. `save_draft_as_docx(markdown, "/path/draft-482.docx")` → renders filing-grade .docx

---

## Example 3 — Contempt Petition (Madras HC)

**Prompt to use in Claude Desktop chat:**

> *"Draft a contempt petition under the Contempt of Courts Act 1971 before the Madras High Court. Petitioner is [DECREE-HOLDER], respondent-contemnor is [JUDGEMENT-DEBTOR]. Underlying order: Madras HC judgment dated 2025-08-20 in WP No. [WP-N]/2024 directing respondent to remove unauthorised construction within 30 days. Compliance window expired 2025-09-19. Respondent has not removed the construction despite three reminder communications dated 2025-10-15, 2025-11-30, 2026-01-10. Wilful disobedience pleaded. Prayer: punishment under Section 12 of the Contempt of Courts Act 1971 + direction for compliance + costs."*

**Expected tool sequence:**
1. `list_case_types()` → confirms contempt-petition available
2. `get_case_type_format("contempt-petition")` → retrieves the contempt petition template
3. `list_benches()` → confirms madras-hc available
4. `get_bench_config("madras-hc")` → retrieves Madras HC conventions (bilingual Tamil/English filing requirement, Appellate-Side Rules reference)
5. `get_pleading_base()` → retrieves the universal HC pleading skeleton
6. Drafts the contempt petition with wilful-disobedience plea + Section 12 framework
7. `save_draft_as_docx(markdown, "/path/draft-contempt.docx")` → renders filing-grade .docx

---

## Notes for the reviewer

- These examples use placeholder party names (`[PETITIONER]`, `[DECREE-HOLDER]`, `[JUDGEMENT-DEBTOR]`, `[FIR-X]`, `[LOCATION-X]`, `[PS-LOCATION]`, `[WP-N]`, etc.) — no real client data.
- The connector does not require any external API keys or accounts.
- The `read_case_folder(path)` tool is optional and only used when the user has prepared a case-files folder on their machine.
- The `save_draft_as_docx` tool requires `pandoc` to be installed on the user's machine.
- The connector applies a three-layer privacy firewall throughout.
- The 28 bench exemplars cover all 25 Indian High Courts; calling `list_benches()` returns the available identifiers.

---

## Synthetic case folder for Anthropic reviewer

A fully-fictional, AAAK-pseudonymised case folder is bundled at:

`SAMPLE-CASES/synthetic-caste-cert-quashing-civil-wp/`

It contains 2 source documents (.docx) plus a `case-facts-background.md` narrative.

**To exercise the pipeline end-to-end**, point `read_case_folder(path)` at this folder and follow the orchestration script returned by `get_agent_instructions()`. The Reader stage will extract facts, the Format stage will load the case-type SKILL.md template, and the remaining four agents (Drafter → Verifier → Refiner → Overseer) will produce `final-draft.docx`.

All identifiers in the bundled documents are structural placeholders (`[Petitioner-A]`, `[Premises-Address-Placeholder]`, `[Monthly-Rent-Placeholder]`, `[PAN-PLACEHOLDER-10-CHAR]`, `[DIN-PLACEHOLDER-19-DIGIT]`, `[Total-Arrears-Placeholder]`, etc.). The Pseudonymisation Gateway is therefore exercising against pre-pseudonymised content; reviewers seeking to test re-substitution may replace placeholders with their own fictional values before invoking the pipeline.

