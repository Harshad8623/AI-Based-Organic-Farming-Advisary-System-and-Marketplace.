"""
database/seed.py
----------------
Seeds the database with:
  1. Test accounts (farmer + buyer)
  2. 10 Organic Crop Roadmaps (Tomato, Potato, Onion, Rice, Wheat, Chilli,
     Brinjal, Garlic, Cauliflower, Spinach)

Run once:  python database/seed.py
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import db, User, FarmerProfile, BuyerProfile, CropRoadmap
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

# App will be created inside __main__ context or passed by caller.

# ---------------------------------------------------------------------------
# Crop Roadmap data
# ---------------------------------------------------------------------------
CROPS = [
    {
        "crop_name":      "Tomato",
        "slug":           "tomato",
        "emoji":          "🍅",
        "description":    "Tomato is one of the most widely grown vegetables in India. With proper organic care, you can get 20–25 tonnes per hectare in 70–80 days.",
        "season":         "Kharif",
        "duration_days":  75,
        "expected_yield": "20–25 tonnes/hectare",
        "soil_type":      "Well-drained loamy soil, pH 6.0–7.0",
        "climate":        "Warm climate, 20–27°C, avoid frost",
        "stages": [
            {
                "stage":   "Land Preparation",
                "days":    "Day 1–7",
                "actions": [
                    "Deep plow the field 2–3 times to 30 cm depth.",
                    "Add 20–25 tonnes/ha of well-rotted FYM (farmyard manure).",
                    "Form raised beds 120 cm wide for good drainage.",
                    "Test soil pH and adjust with lime if below 6.0."
                ],
                "tips": [
                    "Use vermicompost for extra micronutrient boost.",
                    "Avoid waterlogging — raise beds at least 15 cm high.",
                    "Add neem cake (250 kg/ha) to reduce soil-borne pathogens."
                ]
            },
            {
                "stage":   "Seed Sowing / Nursery",
                "days":    "Day 1–25 (nursery)",
                "actions": [
                    "Prepare nursery beds of 1m × 3m size.",
                    "Use certified organic tomato seeds (200–250 g/ha).",
                    "Treat seeds with Trichoderma viride (4 g/kg seed) before sowing.",
                    "Sow seeds 0.5 cm deep in rows 10 cm apart.",
                    "Water gently with a watering can."
                ],
                "tips": [
                    "Cover nursery with agro-shade net (50%) to protect from scorching sun.",
                    "Use coco peat + compost mix (1:1) for nursery trays for better germination.",
                    "Discard weak or pale seedlings — only transplant vigorous ones."
                ]
            },
            {
                "stage":   "Transplanting",
                "days":    "Day 25–30",
                "actions": [
                    "Transplant 25-day-old seedlings when 15–20 cm tall.",
                    "Spacing: 60 cm × 45 cm (row × plant).",
                    "Water immediately after transplanting.",
                    "Apply cow dung slurry near roots to reduce transplant shock."
                ],
                "tips": [
                    "Transplant in the evening to reduce wilting stress.",
                    "Dip roots in Pseudomonas fluorescens solution before planting.",
                    "Shade newly transplanted seedlings for 2–3 days."
                ]
            },
            {
                "stage":   "Vegetative Growth",
                "days":    "Day 30–50",
                "actions": [
                    "Irrigate every 7–10 days (drip irrigation preferred).",
                    "Stake plants with bamboo sticks at 45 cm height.",
                    "Apply liquid bio-fertilizer (fish emulsion or panchagavya) at 20-day intervals.",
                    "Weed manually 2–3 times.",
                    "Pinch lateral shoots to encourage main stem growth."
                ],
                "tips": [
                    "Spray diluted buttermilk (1:10) weekly to prevent fungal diseases.",
                    "Install yellow sticky traps to monitor whitefly and thrips.",
                    "Mulch with dry straw to retain soil moisture and reduce weeds."
                ]
            },
            {
                "stage":   "Flowering & Fruit Set",
                "days":    "Day 50–65",
                "actions": [
                    "Spray boron (0.2%) + zinc (0.5%) for better fruit set.",
                    "Reduce nitrogen, increase phosphorus and potassium.",
                    "Control fruit borer using Bacillus thuringiensis (Bt) spray.",
                    "Remove diseased or damaged leaves."
                ],
                "tips": [
                    "Avoid spraying during peak flower hours (9am–11am).",
                    "Release Trichogramma egg parasitoids for organic pest control.",
                    "Neem oil (2%) spray every 10 days prevents powdery mildew."
                ]
            },
            {
                "stage":   "Harvesting",
                "days":    "Day 70–80 onwards",
                "actions": [
                    "Harvest when fruits turn red or pink (depending on variety).",
                    "Harvest every 4–5 days to encourage continuous fruiting.",
                    "Use clean clippers; do not pull fruits by hand.",
                    "Grade fruits by size: A (>7cm), B (5–7cm), C (<5cm)."
                ],
                "tips": [
                    "Harvest in the early morning for longer shelf life.",
                    "Store in cool, shaded area at 12–15°C.",
                    "Avoid stacking more than 3 layers to prevent bruising."
                ]
            }
        ]
    },
    {
        "crop_name":      "Potato",
        "slug":           "potato",
        "emoji":          "🥔",
        "description":    "Potato is a Rabi crop grown in cool climates. India is the world's second largest producer. Organic potato fetches 30–40% premium price.",
        "season":         "Rabi",
        "duration_days":  90,
        "expected_yield": "25–30 tonnes/hectare",
        "soil_type":      "Sandy loam to loamy soil, pH 5.2–6.4",
        "climate":        "Cool climate, 15–18°C for tuber formation",
        "stages": [
            {
                "stage":   "Seed Selection & Treatment",
                "days":    "Day 1–7",
                "actions": [
                    "Select certified disease-free seed tubers (35–55 g each).",
                    "Cut large tubers ensuring each piece has 2–3 eyes.",
                    "Treat cut surfaces with wood ash or Trichoderma dust.",
                    "Cure cut seeds in shade for 2–3 days before planting."
                ],
                "tips": [
                    "Avoid using market potatoes as seed — they carry diseases.",
                    "Treat with Bordeaux mixture 1% to prevent fungal infections.",
                    "Pre-sprouted seed tubers establish faster — sprout for 2–3 weeks."
                ]
            },
            {
                "stage":   "Field Preparation",
                "days":    "Day 1–10",
                "actions": [
                    "Deep plow to 30–35 cm depth.",
                    "Add 25 tonnes/ha FYM during preparation.",
                    "Form ridges 60 cm apart and 20 cm high.",
                    "Apply neem cake 250 kg/ha to control soil pests."
                ],
                "tips": [
                    "Avoid heavy clay soils — they restrict tuber expansion.",
                    "Sub-soiling helps if there's a hard pan below 25 cm.",
                    "Incorporate green manure crop (dhaincha) if time permits."
                ]
            },
            {
                "stage":   "Planting",
                "days":    "Day 10–12",
                "actions": [
                    "Plant seed tubers on ridges 20–25 cm apart.",
                    "Planting depth: 8–10 cm.",
                    "Cover with soil and give light irrigation.",
                    "Apply bio-compost (2 tonnes/ha) in furrows."
                ],
                "tips": [
                    "Plant in the evening to reduce heat stress.",
                    "Ensure uniform depth for even germination.",
                    "Do not flood irrigate after planting — just moisten."
                ]
            },
            {
                "stage":   "Germination & Early Growth",
                "days":    "Day 12–30",
                "actions": [
                    "Irrigate lightly every 5–7 days.",
                    "Thin extra sprouts — keep only 2–3 strong ones per hill.",
                    "Hand weed between rows at 3-week stage.",
                    "Spray Jeevamrut (500 litres/ha) for microbial boost."
                ],
                "tips": [
                    "Monitor for late blight (dark brown spots) — treat with Bordeaux mix.",
                    "Avoid over-irrigation — causes rotting.",
                    "Install aphid traps (yellow sticky cards) at 25 per hectare."
                ]
            },
            {
                "stage":   "Earthing Up & Hilling",
                "days":    "Day 30–45",
                "actions": [
                    "Earth up soil around base of plants 30–35 days after planting.",
                    "Ridge height should reach halfway up the plant stem.",
                    "Second earthing up 15 days later.",
                    "Apply potassium-rich organic manure during earthing."
                ],
                "tips": [
                    "Hilling prevents greening of tubers exposed to sunlight.",
                    "Always earth up after rain or irrigation when soil is moist.",
                    "Use intercultivation to loosen soil and kill weeds simultaneously."
                ]
            },
            {
                "stage":   "Maturity & Harvesting",
                "days":    "Day 80–90",
                "actions": [
                    "Stop irrigation 10–15 days before harvest.",
                    "Haulm (top cutting) 10 days before harvest to harden skin.",
                    "Harvest when foliage turns yellow and tubers detach easily.",
                    "Cure harvested potatoes at 15–20°C for 10 days before storage."
                ],
                "tips": [
                    "Harvest on a dry day to reduce soil contamination.",
                    "Avoid harvesting in hot afternoon — causes sweating and decay.",
                    "Grade by size: Large (>55g), Medium (35–55g), Small (<35g)."
                ]
            }
        ]
    },
    {
        "crop_name":      "Onion",
        "slug":           "onion",
        "emoji":          "🧅",
        "description":    "Onion is a major cash crop in Maharashtra, Karnataka, and Gujarat. Organic onion commands premium prices in export markets.",
        "season":         "Rabi",
        "duration_days":  120,
        "expected_yield": "25–30 tonnes/hectare",
        "soil_type":      "Well-drained medium loamy soil, pH 6.0–7.5",
        "climate":        "Moderate, 13–24°C during growth; dry at maturity",
        "stages": [
            {
                "stage":   "Nursery Preparation",
                "days":    "Day 1–40",
                "actions": [
                    "Raise nursery beds 1m wide with fine tilth.",
                    "Mix FYM + compost (1:1) into nursery beds.",
                    "Sow seeds thinly at 2–3 cm spacing, 0.5 cm deep.",
                    "Treat seeds with Trichoderma viride before sowing."
                ],
                "tips": [
                    "Maintain uniform moisture — onion seeds need 10–12 days to germinate.",
                    "Provide 30–50% shade in hot weather.",
                    "Control damping-off with copper oxychloride spray seedlings weekly."
                ]
            },
            {
                "stage":   "Transplanting",
                "days":    "Day 40–45",
                "actions": [
                    "Transplant 40-day-old seedlings (15 cm tall).",
                    "Row spacing: 15 cm × 10 cm.",
                    "Irrigate immediately and daily for first week.",
                    "Apply Pseudomonas fluorescens at transplanting."
                ],
                "tips": [
                    "Trim roots to 2 cm and leaves to 8 cm for better establishment.",
                    "Transplant in the evening, not midday.",
                    "Avoid deep planting — bulb should be just below soil level."
                ]
            },
            {
                "stage":   "Bulb Development",
                "days":    "Day 60–100",
                "actions": [
                    "Apply liquid bio-fertilizer (panchagavya) every 20 days.",
                    "Weed manually at 30- and 60-day stages.",
                    "Control thrips with neem-based pesticides.",
                    "Drip irrigate weekly."
                ],
                "tips": [
                    "Thrips are the main enemy — monitor weekly with sticky traps.",
                    "Spray garlic-chilli extract for organic pest control.",
                    "Avoid overhead irrigation during bulbing — promotes disease."
                ]
            },
            {
                "stage":   "Maturity & Harvesting",
                "days":    "Day 110–120",
                "actions": [
                    "Stop irrigation 15 days before harvest.",
                    "Harvest when 50% of tops fall over naturally.",
                    "Cure onions in field for 7–10 days before storage.",
                    "Remove tops leaving 2–3 cm neck before storage."
                ],
                "tips": [
                    "Never harvest when soil is wet — causes rotting.",
                    "Cure in shade, not direct sun, to prevent sunscald.",
                    "Store in well-ventilated slatted crates, not jute bags."
                ]
            }
        ]
    },
    {
        "crop_name":      "Rice",
        "slug":           "rice",
        "emoji":          "🌾",
        "description":    "Rice is the staple food of India. Organic rice production using SRI (System of Rice Intensification) can yield 6–8 tonnes/hectare with minimal inputs.",
        "season":         "Kharif",
        "duration_days":  120,
        "expected_yield": "5–8 tonnes/hectare",
        "soil_type":      "Clayey or loamy soil with good water retention, pH 5.5–6.5",
        "climate":        "Tropical, 25–35°C, high humidity, needs 1200mm rainfall",
        "stages": [
            {
                "stage":   "Nursery (Wet Bed)",
                "days":    "Day 1–25",
                "actions": [
                    "Prepare wet nursery beds 1–1.5m wide.",
                    "Pre-soak seeds for 24 hours, drain and incubate 48 hours.",
                    "Broadcast pre-germinated seeds at 500 g/10m² nursery.",
                    "Apply Azospirillum + Phosphobacteria to nursery."
                ],
                "tips": [
                    "Use SRI nursery trays for single-seedling transplanting.",
                    "Nursery period should not exceed 20 days for SRI.",
                    "Seed treatment with cow dung + beejamrut promotes germination."
                ]
            },
            {
                "stage":   "Transplanting (Puddling)",
                "days":    "Day 25–30",
                "actions": [
                    "Puddle field thoroughly 2–3 days before transplanting.",
                    "Transplant 2 seedlings per hill, 25 × 25 cm spacing.",
                    "Maintain 2–3 cm water level after transplanting.",
                    "Apply Azolla as green manure (500 kg/ha) for nitrogen."
                ],
                "tips": [
                    "Single seedlings at young stage (15 days) works best in SRI.",
                    "Mark planting grid with rope to ensure even spacing.",
                    "Dip seedling roots in bio-slurry before transplanting."
                ]
            },
            {
                "stage":   "Tillering Phase",
                "days":    "Day 30–60",
                "actions": [
                    "Keep field alternately wet and dry (AWD method).",
                    "Weed with cono-weeder at 20 and 40 days.",
                    "Apply Jeevamrut (fermented cow manure) weekly.",
                    "Monitor for stem borers — use pheromone traps."
                ],
                "tips": [
                    "AWD reduces water use by 30% and improves grain quality.",
                    "Cono-weeding aerates the soil and boosts tillering.",
                    "Green leaf hopper monitoring: hang light traps at field edges."
                ]
            },
            {
                "stage":   "Flowering & Grain Filling",
                "days":    "Day 75–100",
                "actions": [
                    "Flood field to 5 cm during flowering.",
                    "Spray potassium silicate for stem strength.",
                    "Apply Bt-based pesticides for leaf folder control.",
                    "Drain field 15 days before harvest."
                ],
                "tips": [
                    "Do not disturb plants during flowering — avoid walking in field.",
                    "Silica sprays improve grain weight and reduce disease.",
                    "Early morning panicle emergence is normal — do not worry."
                ]
            },
            {
                "stage":   "Harvesting",
                "days":    "Day 115–125",
                "actions": [
                    "Harvest when 85% grains turn golden yellow.",
                    "Use sickle harvesting or mechanical reaper.",
                    "Thresh immediately or within 48 hours.",
                    "Dry grains to 14% moisture before storage."
                ],
                "tips": [
                    "Harvest in morning to reduce shattering losses.",
                    "Dry on clean threshing floor, not on roadside.",
                    "Store in hermetic bags or metal bins to prevent insect damage."
                ]
            }
        ]
    },
    {
        "crop_name":      "Wheat",
        "slug":           "wheat",
        "emoji":          "🌿",
        "description":    "Wheat is India's second most important cereal. Organic wheat from Punjab and Madhya Pradesh is in high demand. A good Rabi crop with simple inputs.",
        "season":         "Rabi",
        "duration_days":  110,
        "expected_yield": "3.5–5 tonnes/hectare",
        "soil_type":      "Well-drained loamy or clay-loam soil, pH 6.0–7.5",
        "climate":        "Cool and dry, 10–15°C at germination; warm dry at maturity",
        "stages": [
            {
                "stage":   "Soil Preparation & Seed Treatment",
                "days":    "Day 1–7",
                "actions": [
                    "Plow field 2–3 times after kharif harvest.",
                    "Apply 15–20 tonnes/ha compost or FYM.",
                    "Seed treatment: soak in cow urine (1:10) for 6 hours, then dry.",
                    "Treat with Trichoderma viride (4 g/kg)."
                ],
                "tips": [
                    "Beejamrut seed treatment with cow dung + cow urine promotes vigour.",
                    "Avoid over-deep plowing — 15 cm is sufficient.",
                    "Green manure crops turned in 3 weeks before sowing add nitrogen."
                ]
            },
            {
                "stage":   "Sowing",
                "days":    "Day 7–10",
                "actions": [
                    "Sow seeds at 100–120 kg/ha in rows 22.5 cm apart.",
                    "Seed depth: 5–6 cm.",
                    "Ensure uniform moisture at sowing time.",
                    "Apply Azotobacter + PSB bio-fertilizers in furrows."
                ],
                "tips": [
                    "Timely sowing (Nov 1–15 in North India) is critical for yield.",
                    "Late sowing reduces tiller number and grain weight.",
                    "Use seed drill for uniform depth and spacing."
                ]
            },
            {
                "stage":   "Germination & Tillering",
                "days":    "Day 10–40",
                "actions": [
                    "First irrigation (Crown Root Initiation) at 20–22 days.",
                    "Weed at 30 days — hand weeding or between-row hoeing.",
                    "Spray Jeevamrut or diluted panchagavya at tillering.",
                    "Monitor for aphids — spray neem oil 2% if infestation."
                ],
                "tips": [
                    "CRI irrigation is the most critical one for wheat — don't skip.",
                    "Intercrop with mustard (1:6 ratio) for additional income.",
                    "Aphid colonies start at leaf tips — inspect weekly from 40 days."
                ]
            },
            {
                "stage":   "Jointing to Heading",
                "days":    "Day 40–80",
                "actions": [
                    "Apply second irrigation at jointing (40–45 days).",
                    "Third irrigation at heading (60–65 days).",
                    "Apply vermicompost liquid (2%) as foliar spray.",
                    "Monitor for rust disease — apply sulphur dust if found."
                ],
                "tips": [
                    "Yellow rust appears as yellow stripes on leaves — act immediately.",
                    "Spray cow urine (1:10 dilution) as a preventive against rust.",
                    "Avoid lodging by reducing excessive nitrogen sources."
                ]
            },
            {
                "stage":   "Ripening & Harvest",
                "days":    "Day 100–115",
                "actions": [
                    "Stop irrigation 15 days before harvest.",
                    "Harvest when grains are golden yellow and hard (14% moisture).",
                    "Use harvester or sickle — harvest in cool morning hours.",
                    "Thresh and winnow to clean grain."
                ],
                "tips": [
                    "Avoid harvesting after rain — grains absorb moisture.",
                    "Test grain moisture with moisture meter before storage.",
                    "Store in clean, dry, ventilated gunny bags or metal silos."
                ]
            }
        ]
    },
    {
        "crop_name":      "Chilli",
        "slug":           "chilli",
        "emoji":          "🌶️",
        "description":    "Red chilli is a high-value spice crop. Andhra Pradesh, Maharashtra, and Karnataka are major producers. Organic chilli earns 2–3x premium in export markets.",
        "season":         "Kharif",
        "duration_days":  150,
        "expected_yield": "2–3 tonnes dry chilli/hectare",
        "soil_type":      "Well-drained loamy soil, pH 6.0–7.0",
        "climate":        "Hot and dry, 20–30°C; sensitive to frost and waterlogging",
        "stages": [
            {"stage": "Nursery", "days": "Day 1–35",
             "actions": ["Sow seeds in raised nursery beds.", "Treat seeds with Trichoderma.", "Water twice daily.", "Shade with 50% shade net."],
             "tips": ["Keep beds well-drained to prevent damping-off.", "Thin seedlings to 5 cm spacing.", "Spray copper oxychloride weekly."]},
            {"stage": "Transplanting", "days": "Day 35–40",
             "actions": ["Transplant 35-day-old seedlings at 60×45 cm spacing.", "Water immediately.", "Apply Pseudomonas drench.", "Mulch with straw."],
             "tips": ["Transplant in evening.", "Dip roots in cow dung slurry.", "Give shade for 3 days post-transplanting."]},
            {"stage": "Vegetative Growth", "days": "Day 40–75",
             "actions": ["Irrigate every 7–10 days.", "Apply panchagavya spray every 20 days.", "Weed 2–3 times.", "Install pheromone traps for fruit borer."],
             "tips": ["Yellow sticky traps for whitefly control.", "Neem oil spray fortnightly.", "Spray boron for bushy growth."]},
            {"stage": "Flowering & Fruiting", "days": "Day 75–100",
             "actions": ["Increase potassium to improve color.", "Release Chrysoperla larvae for aphid control.", "Spray zinc sulphate 0.5% to improve fruit set."],
             "tips": ["Avoid spraying during flowering hours.", "Remove yellowed leaves.", "Bt spray for fruit borer."]},
            {"stage": "Harvest (Green)", "days": "Day 90–120",
             "actions": ["Harvest green chillies every 8–10 days.", "Use sharp knife — don't pull.", "Grade and cool immediately after harvest."],
             "tips": ["Morning harvest gives longer shelf life.", "Use gloves to avoid skin irritation.", "Cool chain storage extends quality to 14 days."]},
            {"stage": "Red Chilli Harvest & Drying", "days": "Day 130–150",
             "actions": ["Let chillies turn fully red before harvesting.", "Harvest entire plants when 80% fruit is red.", "Sun dry on clean tarpaulin for 7–10 days.", "Moisture target: below 10% for storage."],
             "tips": ["Dry on raised platforms to avoid soil contamination.", "Turn chillies daily for even drying.", "Store in cool, dry godown in jute bags."]}
        ]
    },
    {
        "crop_name":      "Brinjal",
        "slug":           "brinjal",
        "emoji":          "🫆",
        "description":    "Brinjal (Eggplant) is grown throughout India year-round. Organic brinjal has excellent market demand in urban areas and is easy to grow with organic inputs.",
        "season":         "Year-round",
        "duration_days":  90,
        "expected_yield": "20–30 tonnes/hectare",
        "soil_type":      "Sandy loam to clay loam, pH 5.5–6.8",
        "climate":        "Warm climate, 25–30°C; frost-sensitive",
        "stages": [
            {"stage": "Nursery", "days": "Day 1–30",
             "actions": ["Prepare raised nursery beds.", "Sow seeds at 0.5 cm depth.", "Treat seeds with Trichoderma viride.", "Water daily; thin to 5 cm spacing."],
             "tips": ["Damping-off is the main nursery disease — ensure drainage.", "Use 50% shade net in summer.", "Compost tea foliar spray boosts nursery growth."]},
            {"stage": "Transplanting & Establishment", "days": "Day 30–45",
             "actions": ["Transplant at 60×60 cm spacing.", "Water daily for first week.", "Apply bio-fertilizer at transplanting.", "Mulch with crop residue."],
             "tips": ["Transplant healthy seedlings only.", "Stake tall varieties early.", "Neem cake application near roots prevents soil pests."]},
            {"stage": "Growth & Flowering", "days": "Day 45–70",
             "actions": ["Irrigate every 7 days.", "Spray panchagavya 3% every 15 days.", "Monitor for shoot and fruit borer.", "Apply Bacillus thuringiensis (Bt) for borer control."],
             "tips": ["Pheromone traps for shoot borer monitoring.", "Release Trichogramma parasitoids.", "Remove and destroy borer-infested shoots."]},
            {"stage": "Harvest", "days": "Day 70–90 (continuous)",
             "actions": ["Harvest fruits at 70–80% maturity (glossy appearance).", "Harvest every 5–7 days.", "Use sharp secateurs — leave 2 cm pedicel.", "Grade by size and colour."],
             "tips": ["Over-mature fruits become seedy and bitter.", "Morning harvest gives better shelf life.", "Store at 10–12°C with 90–95% humidity."]}
        ]
    },
    {
        "crop_name":      "Garlic",
        "slug":           "garlic",
        "emoji":          "🧄",
        "description":    "Garlic is a high-value spice crop grown in Rabi season. Madhya Pradesh and Rajasthan are major producers. Organic garlic exports to Europe and Gulf countries.",
        "season":         "Rabi",
        "duration_days":  150,
        "expected_yield": "8–12 tonnes/hectare",
        "soil_type":      "Well-drained sandy loam, pH 6.0–7.5",
        "climate":        "Cool and dry, 12–20°C; long day length for bulbing",
        "stages": [
            {"stage": "Clove Selection & Treatment", "days": "Day 1–3",
             "actions": ["Select large uniform cloves from best bulbs.", "Discard diseased or very small cloves.", "Treat with Trichoderma viride solution.", "Air-dry treated cloves before planting."],
             "tips": ["Large cloves produce bigger bulbs.", "Untreated small cloves cause crop failure.", "Cow urine soaking (4 hrs) before planting improves germination."]},
            {"stage": "Land Preparation & Planting", "days": "Day 3–10",
             "actions": ["Fine tilth preparation, 25 cm deep.", "Add 25 tonnes/ha well-decomposed FYM.", "Plant cloves 5 cm deep, 10×10 cm spacing.", "Cover with fine soil + mulch."],
             "tips": ["Broad beds (1m) with furrows help in drainage and irrigation.", "Plant cloves with pointed end up.", "Flat-planted cloves give poor results."]},
            {"stage": "Vegetative Growth", "days": "Day 10–90",
             "actions": ["Irrigate every 10–12 days.", "Weed 3–4 times — garlic cannot compete with weeds.", "Spray diluted Jeevamrut weekly for 60 days.", "Apply compost tea as foliar every 20 days."],
             "tips": ["Mulching reduces weed pressure significantly.", "Monitor for thrips — spray neem oil 2% fortnightly.", "Avoid water stress during bulb formation (60–90 days)."]},
            {"stage": "Bulbing & Maturity", "days": "Day 90–140",
             "actions": ["Stop nitrogen application after 90 days.", "Increase frequency of irrigation during bulbing.", "Stop irrigation 20 days before harvest.", "Leaf tips turn yellow naturally — sign of maturity."],
             "tips": ["Foliage falling over is the harvest signal, not yellowing.", "Two-thirds of leaves dry signals harvest time.", "Do not pull unnecessarily early — reduces bulb size."]},
            {"stage": "Harvest & Curing", "days": "Day 140–150",
             "actions": ["Harvest by lifting with fork, do not pull.", "Cure in shade with good airflow for 2–3 weeks.", "Clip roots and dry leaves leaving 2–3 cm.", "Grade by bulb size into A, B, C categories."],
             "tips": ["Never cure in direct sunlight — causes bleaching.", "Braid tops for hanging storage in farmers' tradition.", "Cold storage at 0–2°C extends shelf life to 6–8 months."]}
        ]
    },
    {
        "crop_name":      "Cauliflower",
        "slug":           "cauliflower",
        "emoji":          "🥦",
        "description":    "Cauliflower is a popular Rabi vegetable with high market value. Organic cauliflower is in high demand in supermarkets. Requires careful nutrition management for white curds.",
        "season":         "Rabi",
        "duration_days":  80,
        "expected_yield": "20–25 tonnes/hectare",
        "soil_type":      "Well-drained loamy to clay-loam, pH 5.5–6.8",
        "climate":        "Cool climate, 15–20°C; curd blanching needs moderate temperatures",
        "stages": [
            {"stage": "Nursery", "days": "Day 1–25",
             "actions": ["Prepare raised nursery beds with FYM.", "Sow treated seeds 5mm deep.", "Water twice daily.", "Provide shade net to prevent bolting."],
             "tips": ["Use protrays for less transplant shock.", "Damping-off control: Bordeaux mix 1%.", "Do not allow seedlings to exceed 20 cm."]},
            {"stage": "Transplanting", "days": "Day 25–30",
             "actions": ["Transplant at 60×45 cm spacing.", "Irrigate daily for first week.", "Apply Azospirillum at roots.", "Mulch inter-rows."],
             "tips": ["Transplant in evening.", "Avoid planting in hot weather — wait for cool nights.", "Water stressed plants after transplanting."]},
            {"stage": "Vegetative Growth", "days": "Day 30–55",
             "actions": ["Irrigate every 7–10 days.", "Spray seaweed extract every 15 days.", "Weed 2–3 times.", "Monitor for diamond-back moth — Bt spray."],
             "tips": ["Boron deficiency causes hollow stem — spray borax 0.2%.", "Molybdenum spray prevents whiptail disease.", "Yellow sticky traps for aphid and whitefly monitoring."]},
            {"stage": "Curd Development & Blanching", "days": "Day 55–70",
             "actions": ["Tie outer leaves over forming curd to protect whiteness.", "Irrigate regularly — water stress ruins curd quality.", "Spray calcium nitrate 0.5% for compact curd."],
             "tips": ["Check curd daily after tie-up — harvest when compact.", "Low temperatures give premium white curds.", "Do not let curds over-mature — they turn yellow and leafy."]},
            {"stage": "Harvest", "days": "Day 70–80",
             "actions": ["Harvest when curds are firm, white and 15–25 cm diameter.", "Cut with sharp knife, leaving 3–4 wrapper leaves.", "Harvest in early morning.", "Pack immediately in field crates."],
             "tips": ["Delay in harvest causes rice-grainy deterioration of curd.", "Cool harvested heads to 4–5°C within 4 hours.", "Use ventilated crates — not closed boxes — for transport."]}
        ]
    },
    {
        "crop_name":      "Spinach",
        "slug":           "spinach",
        "emoji":          "🥬",
        "description":    "Spinach is a fast-growing leafy vegetable that can be harvested in just 6–8 weeks. High demand in urban health markets, excellent for organic farmers near cities.",
        "season":         "Year-round",
        "duration_days":  45,
        "expected_yield": "10–15 tonnes/hectare",
        "soil_type":      "Fertile sandy loam to loamy soil, pH 6.5–7.0",
        "climate":        "Cool season leafy crop, 10–20°C optimal; tolerates light frost",
        "stages": [
            {"stage": "Land Preparation", "days": "Day 1–5",
             "actions": ["Prepare fine tilth with deep plowing.", "Mix 15 tonnes/ha compost or FYM.", "Make flat beds 1.2m wide.", "Apply neem cake for soil health."],
             "tips": ["Rich compost gives lush, dark green leaves.", "Raised beds ensure drainage.", "pH correction needed if soil is above 7.5."]},
            {"stage": "Seed Sowing", "days": "Day 5–7",
             "actions": ["Sow seeds in rows 25–30 cm apart at 2 cm depth.", "Seed rate: 25–30 kg/ha.", "Water gently after sowing — do not flood.", "Maintain soil moisture consistently."],
             "tips": ["Pre-soak seeds 12 hours in water for faster germination.", "Light mulching with dry straw prevents crust formation.", "Germination in 5–7 days in warm weather."]},
            {"stage": "Thinning & Weed Management", "days": "Day 15–25",
             "actions": ["Thin seedlings to 8–10 cm in-row spacing.", "Weed manually between rows.", "Apply diluted Jeevamrut (250 litres/ha).", "Check for leaf miners — remove infested leaves."],
             "tips": ["Thinned seedlings can be used as microgreens.", "Avoid overhead irrigation — causes leaf spot disease.", "Intercrop with radish or carrot for space efficiency."]},
            {"stage": "Harvest", "days": "Day 40–45",
             "actions": ["Harvest when leaves are 15–20 cm long.", "Cut leaves 3–5 cm from base for regrowth.", "Harvest in batches — cut outer leaves first.", "Wash immediately and pack in bundles."],
             "tips": ["Harvest in early morning when leaves are crisp.", "Post-harvest cooling in cold water extends shelf life.", "Multiple cuttings possible (3–4) before final uprooting."]}
        ]
    }
]


def seed_roadmaps():
    """Populate educational guides only; never create demo accounts on startup."""
    seeded_count = 0
    for crop_data in CROPS:
        existing = CropRoadmap.query.filter_by(slug=crop_data['slug']).first()
        if not existing:
            stages_json = json.dumps(crop_data.get('stages', []))
            crop = CropRoadmap(
                crop_name      = crop_data['crop_name'],
                slug           = crop_data['slug'],
                emoji          = crop_data['emoji'],
                description    = crop_data['description'],
                season         = crop_data['season'],
                duration_days  = crop_data['duration_days'],
                expected_yield = crop_data['expected_yield'],
                soil_type      = crop_data['soil_type'],
                climate        = crop_data['climate'],
                stages_json    = stages_json
            )
            db.session.add(crop)
            seeded_count += 1

    try:
        db.session.commit()
    except IntegrityError:
        # Two workers may seed a fresh database together. The unique slug is
        # authoritative; another completed seeder is safe to reuse.
        db.session.rollback()
        if all(CropRoadmap.query.filter_by(slug=crop['slug']).first() for crop in CROPS):
            return 0
        raise
    return seeded_count


def seed_database():
    db.create_all()

    # ---- Seed Farmer ----
    if not User.query.filter_by(email='farmer@test.com').first():
        farmer = User(
            name='Ramesh Patil',
            email='farmer@test.com',
            password=generate_password_hash('123456'),
            role='farmer'
        )
        db.session.add(farmer)
        db.session.flush()
        db.session.add(FarmerProfile(
            user_id=farmer.id,
            farm_location='Nashik, Maharashtra',
            soil_type='Loamy',
            farm_size='5 acres',
            phone='+91 98765 43210'
        ))
        print('[OK] Farmer created: farmer@test.com / 123456')

    # ---- Seed Buyer ----
    if not User.query.filter_by(email='buyer@test.com').first():
        buyer = User(
            name='Priya Sharma',
            email='buyer@test.com',
            password=generate_password_hash('123456'),
            role='buyer'
        )
        db.session.add(buyer)
        db.session.flush()
        db.session.add(BuyerProfile(
            user_id=buyer.id,
            location='Pune, Maharashtra',
            phone='+91 87654 32109'
        ))
        print('[OK] Buyer created:  buyer@test.com  / 123456')

    db.session.commit()

    seed_roadmaps()

    print('\n[OK] Database seeded successfully!')
    print('\nTest Credentials:')
    print('  Farmer: farmer@test.com  / 123456')
    print('  Buyer:  buyer@test.com   / 123456')

if __name__ == '__main__':
    from app import create_app
    if os.environ.get('APP_ENV') == 'production':
        raise SystemExit('Demo accounts cannot be seeded in production.')
    app = create_app()
    with app.app_context():
        seed_database()
