# Deployment and release notes

## Required production settings

Use the pinned Python 3.12.14 and requirements. Set `APP_ENV=production` and provide a strong, stable `SECRET_KEY` through environment settings. Keep that key across workers and restarts. HTTPS is required because production cookies are marked secure. Debug mode must remain disabled.

Use a persistent PostgreSQL `DATABASE_URL` or a genuinely persistent SQLite volume for a single-instance deployment. Keep `static/uploads` on persistent storage as well; a persistent database does not preserve files on an ephemeral application filesystem. Back up both data stores before upgrades and test restoration.

Driverless `postgres://` and `postgresql://` connection strings are normalized to `postgresql+psycopg2://`, matching the installed `psycopg2-binary` dependency. This avoids SQLAlchemy 2.1 selecting the uninstalled psycopg 3 driver. Keep your existing Render `DATABASE_URL`; credentials and query options are preserved. Explicit driver URLs are left unchanged and require their corresponding driver to be installed.

Initialize once before launching multiple workers:

```bash
venv/bin/python -c 'from app import create_app; create_app()'
venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 'app:create_app()'
```

Run these from the repository root. Initialization creates missing tables and educational guides, without demo accounts. `create_all` is not a schema migration system: the present changes add separate tables without modifying legacy columns. Any future column migration needs a separately reviewed migration. Production deployments should run behind a maintained HTTPS reverse proxy with request size/time limits and access monitoring. The application does not trust client-supplied forwarded identity headers by default.

The `Procfile` uses the same application factory. Set the hosting platform's port and worker options as needed. For cloud development, one worker is sufficient and avoids the need to coordinate a temporary local development session key.

## Online payments

Cash on delivery works without a merchant account. Online checkout is exposed only when Razorpay credentials are configured. Use test-mode credentials first and verify the merchant account's payment capture configuration. Test keys are labeled in the checkout; live keys can charge real money.

The app verifies the payment signature, captured state, amount, INR currency, buyer and saved checkout snapshot; duplicate confirmations cannot create another order. Stock changes are atomic. New orders retain immutable product receipts.

There is no automatic refund service, webhook reconciliation, seller settlement or operator refund dashboard in this project. A captured payment that reaches confirmation after stock or price changes must be reconciled by the merchant operator. Paid-online orders cannot be rejected through the farmer's normal cancellation control. Before accepting live money, establish and test an operator reconciliation/refund process, and add automated webhooks/refunds if required by the business. Do not describe a test checkout as proof of live settlement.

## Field advisory records

The new field profiles, observation snapshots, reported outcomes and task links use additive tables. Existing database columns remain unchanged. Initialize once before multiple workers and back up before upgrading. Case retrieval uses only a farmer's earlier private records and is bounded; no model download or paid API is required. Its first meaningful case results appear after relevant field history is entered.

These changes do not restore a deleted Render database. The web service still needs an Available PostgreSQL service and its current connection URL in `DATABASE_URL`. If the former database was deleted, restore from backup where available or configure a replacement in the same Render workspace/region; new tables alone cannot recover old records.

## Daily help and credit records

Account-free `/farm-help` needs no provider credentials. Private `credit_accounts` and `credit_payments` are new additive tables initialized with the app. Settlement and mistaken-entry cancellation use guarded database writes; keep the database persistent and backed up. They do not automatically modify the farm diary or send reminders to contacts. Run the real PostgreSQL check before release to verify these financial records on the deployment database engine.

## Agricultural information

The crop explorer uses generated training examples and has no established field accuracy. Keep its educational label. Never replace it with a crop, yield or fertilizer guarantee without validated data, units and agronomic evaluation.

Leaf analysis requires Gemini or a separately trained ONNX model and class mapping under `ml_models`. No trained ONNX artifact is bundled or validated by this change. An AI image suggestion is not a confirmed diagnosis. Organic treatment decisions still require local expert advice, product labels and certification rules. Images submitted for analysis are validated, stripped of metadata, held temporarily and removed after analysis; Gemini, when enabled, receives the submitted image.

Weather is a timestamped current observation, not a forecast or rain probability. Live provider availability and behavior were not verified without credentials. Core UI and farming-assistant topic guidance support English, Hindi and Marathi locally; user-generated and long English guide content may remain in its original language when optional dynamic translation is unavailable. These pages display that limitation.

Tasks provide reminders inside the planner. No SMS, push notification or offline background synchronization is implemented. Income/expense records are manually entered records, not audited accounts or automatic marketplace profit calculations.

Voice navigation is optional. Browser speech services can send audio to their provider; permission and support vary by browser. The normal navigation and forms remain available.

## Release validation

Run the documented pytest suite and browser workflow after a clean installation. Check both roles, the required languages, actual narrow-screen forms, and recovery from unavailable external services. Validate configured live integrations separately before enabling them for users. Recheck dependency advisories periodically; the saved audit describes the versions and evidence on its audit date.
