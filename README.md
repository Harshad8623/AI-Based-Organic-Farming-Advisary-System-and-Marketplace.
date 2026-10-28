# Dharti Rakshak — Organic Farming & Local Marketplace

A Flask application for farmers and buyers, with simple English, Hindi and Marathi controls. The project was previously called KrishiAI.

**Made by Harshad Madhav Dhuppe · PRN 23025331844046 · CSMSS Chh. Shahu College of Engineering Sambhajinagar · Electronics and Computer Engineering.**

## Features

- Farmer and buyer accounts with hashed passwords, role checks, CSRF protection, and secure production cookie settings.
- Marketplace listings with verified image uploads, explicit stock units, search, filters, sorting and farmer profiles.
- Cart and cash-on-delivery orders with stock checks, repeat-submission protection, controlled order transitions, delivery tracking and buyer ratings.
- Immutable receipts for new orders preserve the purchased product name, unit and price when listings change or are deleted.
- Private farm planner: crop/field tasks, due dates, overdue reminders, completion and history pagination.
- Private income and expense diary: exact INR totals by month, categories, notes and spreadsheet-safe CSV export. Entries are manual; marketplace orders are separate.
- Responsive phone/desktop pages, keyboard navigation, readable controls, local Bootstrap assets and persistent language selection. Core controls and farm records do not need an AI API for translation.
- Optional voice navigation in English, Hindi and Marathi. It starts only after a tap and depends on browser support and microphone permission.
- Ten educational crop guides; actual marketplace counts and private order activity, without simulated analytics.
- A three-language farming assistant with curated topic guidance when Gemini is unavailable.
- Current weather observations when OpenWeather is configured; clear unavailable states otherwise.
- Optional leaf-image analysis through Gemini or a separately trained ONNX model. Without an analysis engine, the app reports unavailable rather than inventing a diagnosis.
- An explicitly labeled **synthetic-data crop explorer** for learning. It is not a validated planting recommendation or fertilizer calculator.

## Local setup

Use **Python 3.12.14**, the version in `.python-version`. No Node build, Redis, GPU or external database is required for the standard local workflow.

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install pip==26.2.1
python -m pip install -r requirements-dev.txt
python app.py
```

On Windows, activate with `venv\Scripts\activate` instead. For a runtime-only installation, use `requirements.txt` instead of `requirements-dev.txt`.

The app listens on port 5000. SQLite tables and the ten crop guides are created automatically. Register a farmer or buyer account in the application; startup does **not** create test accounts. The default local session key is temporary, so a process restart can require logging in again. Debug mode is off unless explicitly enabled with `FLASK_DEBUG=1`.

`.env.example` lists supported settings. Copy it to the ignored `.env` file if needed, and enter credentials securely. Never commit a populated `.env` or API keys. Core accounts, marketplace/COD, planner, diary, guides and offline topic assistance work without API credentials.

## Validation

```bash
venv/bin/python -m pytest -q
venv/bin/python -m pip check
```

Tests use isolated temporary databases and cover account/role access, CSRF, finite input validation, stock/payment replay protection, order receipts and transitions, ledger arithmetic, ownership, CSV safety, translation failures, malformed provider responses and real demonstration-model training. Gateway responses are mocked; tests do not move money.

The browser check creates its own temporary database and accounts, with real CSRF enabled. It checks 320/390/1440-pixel pages, language persistence, task/diary/CSV actions, safe chat and failed-message recovery, and an order from checkout through delivery and rating.

```bash
venv/bin/python -m pip install -r requirements-browser.txt
venv/bin/python scripts/check_ui.py --browser-executable /usr/bin/chromium
```

Use the path to your installed Chromium. If no system browser is available, install the Playwright browser with `venv/bin/python -m playwright install chromium` and omit `--browser-executable`. This optional download requires network access to Playwright's browser distribution hosts. Screenshots are written under `/tmp/organic-farming-ui` by default; use `--artifacts` to change that location.

## Optional integrations

| Setting | Purpose | Behavior when absent |
| --- | --- | --- |
| `GEMINI_API_KEY` | AI conversation, image analysis, optional translation of dynamic English content | Curated multilingual topic guidance; dynamic content stays in its original language; no invented diagnosis |
| `OPENWEATHER_API_KEY` | Current weather from OpenWeather | Weather unavailable message; no random readings |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Merchant online checkout | Cash on delivery remains available |
| `DATABASE_URL` | PostgreSQL connection; `postgres://` is normalized | Local SQLite database |
| `SECRET_KEY` | Stable session signing across restarts/workers | Temporary development key; required in production |

Required HTTPS destinations for enabled integrations are `generativelanguage.googleapis.com`, `api.openweathermap.org`, `api.razorpay.com` and the browser payment SDK at `checkout.razorpay.com`. Configure these in the hosting environment's network settings when enabling the corresponding service. Core styles, scripts, icons and artwork are served locally.

## Deployment and data

Read [deployment and release notes](docs/DEPLOYMENT.md) before enabling live users or payments. Set `APP_ENV=production`, supply a strong stable `SECRET_KEY`, terminate HTTPS correctly and use persistent database/upload storage. Production mode uses secure cookies and refuses to start without an environment-provided session key.

Existing table columns are preserved. Planner, checkout-attempt and order-receipt tables are additive and created during initialization. Back up the database and uploads before upgrading any deployment. Legacy orders cannot recover a historical name/unit that was never recorded; their fallback remains explicit.

[Dependency audit](docs/DEPENDENCY_AUDIT.md) documents the pinned security updates and their sources. Live weather, AI, trained image-model accuracy and merchant payment behavior require separate validation with configured services. No software test suite establishes an absolute “zero bugs” guarantee.
