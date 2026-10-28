# Validation of this revision

Validated on 28 October 2026 using Python 3.12.14, SQLite and system Chromium.

- `venv/bin/python -m pytest -q`: **212 passed**. One pandas notice concerns a future optional PyArrow dependency; the installed model trained and predicted successfully.
- `venv/bin/python -m pip check`: passed.
- `python3 scripts/check_ui.py`: passed against a fresh temporary database with CSRF enabled and external APIs disabled.
- Browser widths: 320, 390 and 1440 pixels. Public pages and farmer tools rendered without horizontal overflow; scripts and local assets loaded successfully.
- Browser workflows: registration/login, product listing, tasks, monthly income/expense totals, CSV export, crop demo, safe chat rendering and retry, cash-on-delivery checkout, farmer acceptance/shipping/delivery, buyer rating and remaining stock.
- English/Hindi/Marathi switching and persistence checked. Voice navigation has mocked browser speech-API tests; real microphone recognition depends on browser support and permission.
- Default development database initialized with ten educational guides and zero accounts. Startup does not create demo users.

The suite uses temporary records and mocked provider/payment responses. No live charge was made. Real merchant payment capture/refunds, live weather, Gemini services, PostgreSQL deployment and a trained ONNX artifact remain outside this local validation. The crop explorer is explicitly educational and has no established field accuracy. See [deployment notes](DEPLOYMENT.md) for the corresponding release requirements.

Screenshots from the browser run:

- [Desktop home](screenshots/home-desktop.png)
- [Marathi planner on a phone](screenshots/planner-mobile-marathi.png)
