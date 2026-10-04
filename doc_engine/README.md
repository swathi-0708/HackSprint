# doc_engine (P1)

PDF -> SHA256 id -> cache -> Sarvam Digitise + Extract -> `AgreementFacts` (see brief for the contract).

## Setup
    pip install -r doc_engine/requirements.txt
    cp .env.example .env      # put SARVAM_API_KEY in .env (never commit)

## Use
    python -m doc_engine.run data/agreements/rental1.pdf      # ~1 Digitise + 1 Extract job, then cached
    python eval/doc/evaluate.py                               # scores cache vs data/labels/<agreement_id>.json
    pytest doc_engine                                         # no network

From code (P3):  `from doc_engine import build_agreement_facts; facts = build_agreement_facts(path)`
Returns a plain dict. Second call on the same file = zero API calls (`data/cache/<id>/facts.json`).

## Labelling
Run the CLI once to get the `agreement_id`, copy `data/labels/_TEMPLATE.json` to `data/labels/<agreement_id>.json`,
fill by hand from the PDF. Deposit "2 months" -> value 2, unit `months_of_rent`.
