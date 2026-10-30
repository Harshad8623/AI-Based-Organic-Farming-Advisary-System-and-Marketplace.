# Field-based advisory and personal case learning

The primary workflow is **My farm → record a field check → read explained priorities → save work → record what happened**. Chat and image services are optional supporting tools. The crop model demonstration is kept separate from farm decisions.

## What the intelligence does

The local expert system uses the farmer's recorded crop, actual growth stage, soil, irrigation method, root-zone moisture, standing water, leaf symptoms, checked/affected plant counts and measured rainfall. It produces ordered checks and actions with the specific supporting observations, missing information, a review period and general reference sources. Every saved report includes its input snapshot and rule version. Editing a field does not rewrite old reports.

Examples of decisions that change with context:

- Dry soil prompts a check of roots, available water and local crop guidance. The app does not invent a fixed irrigation dose.
- Wet soil with wilting prompts investigation of roots and drainage, rather than assuming every wilt needs more water.
- Unwanted waterlogging is reviewed urgently; managed paddy conditions are considered separately.
- Affected plants divided by inspected plants is shown as a sample incidence proportion. It is not a disease confidence score or a whole-field estimate.
- Contradictory inputs are identified for another check. An unknown growth stage or unmeasured rainfall stays unknown.

The engine accepts optional fresh, timestamped and attributed current weather. The field form does not automatically fetch weather: measured rainfall comes from the farmer, and unavailable weather is listed as missing. Old or unattributed readings cannot produce weather-specific alerts.

## What the local ML learns

`advisory/learning.py` fits a multilingual character-based TF-IDF vocabulary to the farmer's actual historical notes, combines it with weighted structured field/observation features, and uses cosine nearest-neighbour retrieval. This finds similar earlier checks for the same crop, including notes, previously suggested checks and the farmer's reported outcome.

There is no generated training dataset, cloud language-model requirement or saved executable model artifact. With no sufficiently relevant history, it returns no cases. The route supplies only the signed-in farmer's earlier records, excludes the current check and future checks, and bounds the search. The algorithm also limits its accepted history and feature vocabulary.

An improvement is the farmer's report. It is not proof that a suggested action was performed or caused the improvement. Feedback does not override urgent current checks, and retrieval scores are not displayed as disease probabilities, accuracy or expected yield. Character features support English, Hindi and Marathi notes, but similarity is not agronomic validation.

## Keeping old advice in context

A plan becomes old when its review period passes, relevant field context changes, or a newer check exists for that field. Old reports and outcomes remain readable; old plans cannot create fresh action tasks. Linked tasks retain their source plan, and outdated open advice requires reviewing the current field state. Manual tasks and completed history are preserved.

Form submissions and action-to-task links are repeat-safe. Fields can be archived without deleting their observations. Concurrent edits are version-checked. Draft observations are saved temporarily in the current browser tab, separately for each account and field; only a matching fresh successful submission clears its draft.

## Cost and water decisions

`/farm-decisions` uses explicit farmer inputs rather than invented mandi prices or yield forecasts:

- Farm pickup value = harvested kg × pickup price/kg.
- Market saleable kg = harvested kg × (1 − entered loss percentage/100).
- Market amount left = saleable kg × market price/kg − growing cost − transport − fees.
- Break-even price divides the relevant total costs by saleable quantity.
- Lower-harvest and lower-price scenarios are arithmetic stress tests, not forecasts.
- Water volume uses 1 mm over 1 m² = 1 litre, then the entered application efficiency and pump flow. The app does not decide the irrigation depth.

Costs can explicitly use all the current farmer's expense entries for one selected month. Those records are not automatically specific to a crop or field. Calculations do not silently create ledger income or expenses. Decimal arithmetic, unit conversion, zero and boundary cases are tested.

## Verification and limits

Tests cover decisions changing with observations, conflicts, wet-soil wilting, managed paddy water, missing data, translations, real TF-IDF case ranking, ownership, retries, stale plans, exact costs and unit conversion. Browser checks use actual forms and CSRF protection at narrow phone widths and desktop sizes. The PostgreSQL check creates a temporary real database and exercises the new JSON reports, action links, local case search and financial calculations.

These checks establish software behavior. They do not establish field-trial accuracy, diagnosis, treatment efficacy, crop yields or financial returns. General ICAR/KVK, FAO and IMD references support the principles; the organizations have not certified the app's individual rules.
