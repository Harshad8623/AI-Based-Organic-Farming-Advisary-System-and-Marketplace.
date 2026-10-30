# Validation of this revision

Validated on 30 October 2026 using Python 3.12.14, SQLite, temporary PostgreSQL 16 and system Chromium.

- `venv/bin/python -m pytest -q`: **512 passed**. One pandas notice concerns a future optional PyArrow dependency; the installed demonstration model trained and predicted successfully.
- `venv/bin/python -m pip check`: passed.
- `venv/bin/python scripts/check_postgres.py`: passed against an isolated PostgreSQL 16 container. Verified actual application startup, all tables, guide initialization, registration, COD checkout and immutable receipts, delivery/rating, stock updates, exact ledger writes and CSV, field JSON snapshots, observation outcomes, action/task foreign keys, actual local case retrieval and selling calculations. Also verified account-free problem help, exact credit settlements/retries, rejected overpayment, dashboard due balance, buyer denial and mistaken-entry correction. This uses no Render credentials or production database.
- PostgreSQL driver regression: SQLAlchemy 2.1 defaults to psycopg 3 for plain URLs. Render URLs now explicitly select the declared psycopg2 driver; ten regressions cover both URL schemes, driver initialization and preserved connection details.
- `python3 scripts/check_ui.py`: passed against a fresh temporary database with CSRF enabled and external APIs disabled.
- Browser widths: 320, 390 and 1440 pixels. Public pages and farmer tools rendered without horizontal overflow; scripts and local assets loaded successfully.
- Browser workflows: the five daily tasks visible on a phone, account-free water help with and without JavaScript, registration/login, private credit creation with Marathi digits, exact partial payment, statement CSV and actual due balance, simpler field creation, wet-soil/wilting priorities, action tasks, reported outcomes, real previous-case retrieval, temporary draft recovery, superseded-task warnings and their latest-plan links, printable PDF, separate selling/water calculations and work/money views, product listing, monthly diary totals, crop demo, safe chat rendering and retry, cash-on-delivery checkout, farmer acceptance/shipping/delivery, buyer rating and remaining stock.
- Credit regressions make actual concurrent requests: competing payments cannot overdraw; duplicate submissions create one event; the same token across account tabs returns a correctable error; payment and mistaken-entry cancellation cannot both succeed. Ownership, full CSV escaping, date bounds, unknown input and Marathi numerical input are covered.
- Expert-system tests cover contradictory observations, managed paddy water, wet-soil wilting, unknown inputs and fresh attributed weather. Local ML tests use actual TF-IDF/nearest-neighbour ranking, private earlier records and no-match cases. Input/report snapshots, ownership, repeated requests, stale plans, edit conflicts, safe draft clearing, unit conversion and exact monetary calculations are covered.
- All 16 local JavaScript files passed `node --check`. `git diff --check` passed.
- English/Hindi/Marathi switching and persistence checked. Voice navigation has mocked browser speech-API tests; real microphone recognition depends on browser support and permission.
- Default development database initialized with ten educational guides and zero accounts. Startup does not create demo users.

The suite uses temporary records and mocked provider/payment responses. No live charge was made. Real merchant payment capture/refunds, live weather, Gemini services, Render deployment and a trained ONNX artifact remain outside this local validation. A request to the live Render URL was blocked by the environment's network proxy; no live deployment success is claimed. The previously deleted Render database still requires restoration or replacement and a current `DATABASE_URL` unless already fixed in the dashboard.

The crop explorer is explicitly educational. Field advisory and local case matching have no established field-trial accuracy, diagnosis or treatment-efficacy claim. See [advisory design](ADVISORY_DESIGN.md) and [deployment notes](DEPLOYMENT.md) for the corresponding limits and release requirements.

Screenshots from the browser run:

- [Desktop home](screenshots/home-desktop.png)
- [New Marathi phone home](screenshots/home-phone-marathi.png)
- [Today's work on a phone](screenshots/today-phone-marathi.png)
- [Account-free water help](screenshots/quick-help-mobile-marathi.png)
- [Credit book after a partial payment](screenshots/credit-book-mobile-marathi.png)
- [Marathi field plan on a phone](screenshots/field-advice-phone.png)
- [Full Marathi field plan](screenshots/field-advice-mobile-marathi.png)
- [Selling comparison on a phone](screenshots/selling-decision-mobile.png)
- [Marathi money diary on a phone](screenshots/planner-mobile-marathi.png)
