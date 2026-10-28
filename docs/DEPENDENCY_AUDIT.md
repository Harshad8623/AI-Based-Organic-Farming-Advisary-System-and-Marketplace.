# Dependency audit

Audit date: 28 October 2026. Scope: the project's Python dependencies and the resolved development environment, using the [PyPI JSON API](https://docs.pypi.org/api/json/) `vulnerabilities` records for each exact version. PyPI publishes [OSV](https://osv.dev/) advisory identifiers and fixed versions. This report records the selected remediation versions; installation, tests and browser checks are validated separately. An empty advisory list means no currently recorded advisory in this source, not proof that a package has no defects.

## Changes selected

| Package | Previous pin | Selected pin | Evidence and affected behavior |
| --- | --- | --- | --- |
| Flask | 3.0.0 | 3.1.3 | [CVE-2026-27205 / GHSA-68rp-wp8r-4726](https://osv.dev/vulnerability/GHSA-68rp-wp8r-4726): some session access missed `Vary: Cookie`, affecting caches. |
| Werkzeug | 3.0.1 | 3.1.9 | [CVE-2024-49767](https://osv.dev/vulnerability/GHSA-q34m-jh98-gwm2): multipart parser resource exhaustion. Later safe-path fixes include [GHSA-g6x2-hccm-hh4m](https://osv.dev/vulnerability/GHSA-g6x2-hccm-hh4m); those Windows-specific paths do not apply to this Linux instance. |
| Pillow | 10.2.0 | 13.0.0 | Image parser fixes include [CVE-2024-28219](https://osv.dev/vulnerability/GHSA-44wm-f244-xhp3), and [GHSA-5xm2-6676-qcp9](https://osv.dev/vulnerability/GHSA-5xm2-6676-qcp9) (APNG canvas allocation). Later decoder/encoder fixes require 13.0.0. Upload validation remains necessary. |
| requests | 2.31.0 | 2.33.0 | [.netrc credential leak CVE-2024-47081](https://osv.dev/vulnerability/GHSA-9hjg-9r4m-mvj7); [CVE-2026-25645](https://osv.dev/vulnerability/GHSA-gc5v-m9x4-r6x2) affects direct use of `extract_zipped_paths`, which this app does not call. |
| gunicorn | 21.2.0 | 23.0.0 | Request-smuggling fixes: [CVE-2024-1135](https://osv.dev/vulnerability/GHSA-w3h3-4rj7-4ph4), [CVE-2024-6827](https://osv.dev/vulnerability/GHSA-hc5x-x2vx-497g). |
| scikit-learn | 1.4.0 | 1.5.0 | [CVE-2024-5206](https://osv.dev/vulnerability/GHSA-jw8x-6495-233v): sensitive-token retention in `TfidfVectorizer`; this project's Random Forest does not use that vectorizer. |
| python-dotenv | 1.0.0 | 1.2.2 | [CVE-2026-28684](https://osv.dev/vulnerability/GHSA-mf9w-mj56-hr94): symlink rewriting via `set_key` / `unset_key`. The app reads configuration with `load_dotenv` and does not call the vulnerable write functions. |
| razorpay | 1.4.2 | 2.0.1 | Compatibility update removes the requirement for a runtime `pkg_resources` import on modern Python. Verified in an isolated environment with setuptools absent: SDK import, client construction, version lookup, `order.create`, `payment.fetch`, and signature-verification APIs. Payment behavior is covered separately by application tests; no live payment was made. |

The exact selected versions above returned no non-withdrawn PyPI advisory records during this audit. Sources can be reproduced using, for example, `https://pypi.org/pypi/Flask/3.1.3/json` and the same package/version pattern.

## Runtime compatibility

- Pillow 13.0.0 requires Python 3.11 or later. The selected environment uses Python 3.12.14; Python 3.10 is no longer the supported deployment pin.
- Keep NumPy on the 1.x ABI for ONNX Runtime 1.17.1; `numpy==1.26.3` satisfies this. A NumPy 2 upgrade requires a separately verified ONNX Runtime upgrade.
- scikit-learn 1.5.0 supports NumPy 1.26.3 and the resolved SciPy version. The crop model is rebuilt deterministically in memory, so there is no old pickle artifact to load across the version change.
- Database drivers and existing table schemas do not need a migration for these dependency updates. New application tables are handled separately by the application's initialization.
- Razorpay 2.0.1 retains the SDK methods used by checkout. Mocked payment validation does not establish real merchant credentials, capture settings, refund automation or gateway availability.

## Resolved runtime inventory

The following retained and selected direct/transitive versions returned no non-withdrawn PyPI advisory records. In particular, ONNX Runtime, NumPy, pandas, Plotly and psycopg2-binary were checked explicitly rather than inferred from their age.

| Package | Audited version |
| --- | --- |
| blinker | 1.9.0 |
| certifi | 2026.10.23 |
| charset-normalizer | 3.5.2 |
| click | 8.5.0 |
| cloudpickle | 3.1.2 |
| coloredlogs | 15.0.1 |
| Flask | 3.1.3 |
| Flask-Login | 0.6.3 |
| Flask-SQLAlchemy | 3.1.1 |
| flatbuffers | 25.12.19 |
| gunicorn | 23.0.0 |
| humanfriendly | 10.0 |
| idna | 3.20 |
| itsdangerous | 2.2.0 |
| Jinja2 | 3.1.6 |
| joblib | 1.6.0 |
| MarkupSafe | 3.0.4 |
| mpmath | 1.3.0 |
| numpy | 1.26.3 |
| onnxruntime | 1.17.1 |
| packaging | 26.3 |
| pandas | 2.2.0 |
| pillow | 13.0.0 |
| plotly | 5.18.0 |
| protobuf | 7.36.2 |
| psycopg2-binary | 2.9.9 |
| python-dateutil | 3.0.0 |
| python-dotenv | 1.2.2 |
| pytz | 2026.5 |
| razorpay | 2.0.1 |
| requests | 2.33.0 |
| scikit-learn | 1.5.0 |
| scipy | 1.16.3 |
| six | 1.17.0 |
| SQLAlchemy | 2.1.6 |
| sympy | 1.14.0 |
| tenacity | 9.2.1 |
| threadpoolctl | 3.7.0 |
| typing_extensions | 4.16.0 |
| tzdata | 2026.5 |
| urllib3 | 2.8.0 |
| Werkzeug | 3.1.9 |

## Development and installation tools

| Tool | Finding | Selected action |
| --- | --- | --- |
| pytest 8.3.5 | [CVE-2025-71176](https://osv.dev/vulnerability/GHSA-6w46-j5rx-g56g): predictable temporary test directories on UNIX. This is test-runner behavior, not a production Flask route. | Use pytest 9.0.3 (Python >=3.10); no recorded advisory at that version. |
| pip 25.0.1 | Installer-only wheel/archive path handling advisories, including [CVE-2026-13346](https://osv.dev/vulnerability/GHSA-qwm4-qh6w-59xr). Older tar fallback issues are also mitigated by Python 3.12's extraction filters. | Use pip 26.2.1 before refreshing dependencies; no recorded advisory at that version. |
| setuptools 80.9.0 | [CVE-2026-59890](https://osv.dev/vulnerability/GHSA-h35f-9h28-mq5c) concerns source-distribution exclusions on Unicode-normalizing filesystems; [GHSA-xmj3-9gf7-h52w](https://osv.dev/vulnerability/GHSA-xmj3-9gf7-h52w) concerns legacy wheel installation on Windows. Neither is an application request handler. | Remove the explicit runtime requirement after upgrading Razorpay. Existing environments should remove the unused package, or use >=84.1.0 if distribution build tooling is needed. |

The resolved `iniconfig==2.3.1` and `pluggy==1.7.0` test dependencies also returned no recorded advisories. This audit does not cover the host OS/browser, provider services, or uninstalled optional model-training dependencies. Recheck advisories when refreshing dependency versions.
