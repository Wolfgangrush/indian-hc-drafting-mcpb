# Case Facts Background — Caste-Cert Quashing Civil Writ Petition

All party names, dates beyond the impugned order date, addresses, and case numbers are fictional placeholders.

## Parties

- **Petitioner:** [Petitioner-A], aged 34, agricultural labourer, resident of [Address-Placeholder], Taluka [PLACEHOLDER-TALUKA], District [PLACEHOLDER-DISTRICT-X], Maharashtra. Caste claim: Scheduled Caste under Maharashtra notification.
- **Respondent No. 1:** The State of Maharashtra, through the Sub-Divisional Magistrate, [PLACEHOLDER-DISTRICT-X].
- **Respondent No. 2:** The Caste Scrutiny Committee, [PLACEHOLDER-DIVISION].
- **Respondent No. 3:** [Complainant-B], the private complainant who triggered the administrative action.

## Chronology

- **12 August 2018** — Caste Validity Certificate No. CV-MH-[XXXX]/2018 issued to the petitioner by the Caste Scrutiny Committee, [PLACEHOLDER-DIVISION], after a contested inquiry.
- **20 January 2026** — Private complaint by [Complainant-B] received at the SDM's office alleging false caste claim.
- **(no intermediate notice issued)**
- **15 March 2026** — Impugned order passed by the Sub-Divisional Magistrate cancelling the certificate (see `01-impugned-sdm-order-2026-03-15.docx`).
- **22 March 2026** — Petitioner first learns of cancellation when SDM officer visits residence demanding surrender.
- **10 April 2026** — Petitioner submits written representation (see `02-petitioner-representation-2026-04-10.docx`). No response from SDM office.
- **As on date of approaching this Hon'ble Court** — Petitioner faces immediate consequences in employment (caste-based reservation post) and government scheme benefits.

## Forum and case type

- **Forum:** Bombay High Court (the bench you specify)
- **Case type:** `civil-wp` (Articles 226 / 227 of the Constitution of India)
- **Reliefs sought:** (a) quashing of the SDM's order dated 15 March 2026; (b) interim stay of the cancellation pending final hearing; (c) consequential direction to treat the caste validity certificate as subsisting.

## Grounds (skeleton)

1. **Violation of natural justice** — no notice, no hearing, no opportunity to produce evidence.
2. **Article 14** — arbitrary exercise of statutory power; no recorded reasons.
3. **Ultra vires** — SDM's office lacks original jurisdiction under the Maharashtra Act XXIII of 2001 to cancel a certificate already validated by the Caste Scrutiny Committee.
4. **Subordinate-officer overreach** — the certificate, once validated, is amenable only to a defined review process before the Committee itself, not a unilateral cancellation by the SDM.
5. **Civil-consequences without procedural safeguards** — Maneka Gandhi / Olga Tellis line of cases on Article 21 procedural fairness.

## How to use this fixture

1. Point `read_case_folder(path)` at this directory.
2. The Reader agent will read both `.docx` files plus this `case-facts-background.md` and produce a structured `case-facts.md`.
3. Call `get_case_type_format("civil-wp")` to retrieve the writ-petition skeleton.
4. Call `get_bench_config("bombay-hc")` to retrieve [Your Bench] Registry conventions.
5. The remaining 5 agents (Format → Drafter → Verifier → Refiner → Overseer) run end-to-end to produce `final-draft.docx`.
