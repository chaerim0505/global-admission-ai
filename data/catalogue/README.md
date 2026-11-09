# Expanded searchable catalogue

Handover update (2026-11-09): partial, source-reviewed 2027 requirements are now
linked separately in `data/admissions/2027/requirements.json`. Ajou undergraduate
Software's catalogue label was corrected to the guide's AI Computer Engineering
admission unit, retaining its stable ID. Programme existence and confirmed 2027
admission coverage remain different; see `coverage.json` and `START_HERE.md`.

25 universities in KR, US, GB, NL and IE; 93 entries across undergraduate,
master and PhD levels. Each university has computing-related entries at all
three levels. Electrical/electronic coverage exists in each country but does
not cover all universities. Other field options are not promises of coverage.

`programs.json` follows the existing backend Program schema. The original six
Ajou records are preserved exactly. The backend team can pass this file to
`admission.program_repository.load_programs`; backend default data and AI
recommendations have not been changed or connected by this expansion.

`evidence.json` links new records to official sources reviewed for programme
existence on 2026-11-08. Some sources are departmental curricula, research
directories or vacancy pages rather than international admissions guides.
All new entries remain `needs_check`: GPA, language requirements, documents,
fees, scholarships, application dates and intake availability are not inferred.
PhD listings describe research routes, not guaranteed open vacancies.
Netherlands doctoral applications commonly depend on specific research positions.
Trinity's undergraduate award is not represented as a BSc. Birmingham's MSc
is a conversion route; York and Galway include research master's routes.

Rebuild and verify from the repository root:

    python data/scripts/import_catalogue.py
    python data/scripts/check_catalogue.py
    python data/scripts/check_database.py

The expanded database is `database/admission_catalogue.sqlite`; the original
`admission_sample.sqlite`, original programme fixtures, Ajou detail package
and backend golden cases remain independent. `search_cases.json` contains
catalogue search expectations only, not eligibility or backend AI evaluation.

UI regression checks: python data/scripts/check_catalogue_ui.py
Verified 45 catalogue searches in each of English and Korean (90 total),
matching detail-panel counts, guest form submission and preserved input/results
after switching from English to Korean. This is not backend AI evaluation.
