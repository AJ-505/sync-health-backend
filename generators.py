import json, random
from datetime import date, timedelta


def generate_summary(emp: dict) -> str:
    """
    Build a detailed, human-readable summary string from every field in the
    employee record.  No data point is omitted.
    """
    e = emp
    h = e["health"]
    fh = h["family_history"]
    mh = h["mental_health"]

    # ── Identity ──────────────────────────────────────────────────────────────
    lines = [
        f"{e['name']} (ID: {e['employee_id']}) is a {e['gender'] == 'M' and 'male' or 'female'} "
        f"employee born on {e['dob']}, currently based in {e['location_city']}. "
        f"They are {e['marital_status'].lower()} and work in the {e['department']} department "
        f"at the {e['job_level']} level."
    ]

    # ── Lifestyle ─────────────────────────────────────────────────────────────
    smoke_txt = (
        f"They smoke approximately {h['cigarettes_per_day']} cigarette(s) per day."
        if h["smokes"] else "They do not smoke."
    )
    vape_txt = "They vape." if h["vapes"] else "They do not vape."
    lines.append(
        f"{smoke_txt} {vape_txt} "
        f"Alcohol use is classified as '{h['alcohol_use']}' with approximately {h['drinks_per_week']} drink(s) per week. "
        f"They exercise {h['exercise_days_per_week']} day(s) per week and average {h['avg_steps_per_day']:,} steps per day. "
        f"Sleep averages {h['sleep_hours_avg']} hours per night with a quality score of {h['sleep_quality_1_10']}/10. "
        f"Their stress level is {h['stress_level_1_10']}/10."
    )

    # ── Diet / Nutrition ──────────────────────────────────────────────────────
    lines.append(
        f"Diet pattern is '{h['diet_pattern']}'. "
        f"They consume {h['fruit_veg_servings_per_day']} fruit/vegetable serving(s) per day, "
        f"{h['sugary_drinks_per_week']} sugary drink(s) per week, "
        f"{h['fast_food_meals_per_week']} fast-food meal(s) per week, "
        f"and drink {h['water_intake_liters_per_day']} litre(s) of water per day."
    )

    # ── Body Metrics ──────────────────────────────────────────────────────────
    lines.append(
        f"Physical measurements: height {h['height_cm']} cm, weight {h['weight_kg']} kg, "
        f"BMI {h['bmi']} (waist {h['waist_cm']} cm, hip {h['hip_cm']} cm, "
        f"waist-to-hip ratio {h['waist_to_hip_ratio']}, body fat {h['body_fat_percent']}%)."
    )

    # ── Vitals ────────────────────────────────────────────────────────────────
    lines.append(
        f"Vital signs: blood pressure {h['blood_pressure_systolic']}/{h['blood_pressure_diastolic']} mmHg, "
        f"resting heart rate {h['resting_heart_rate_bpm']} bpm, SpO2 {h['spo2_percent']}%."
    )

    # ── Blood Work ────────────────────────────────────────────────────────────
    lines.append(
        f"Blood work: fasting glucose {h['fasting_glucose_mg_dl']} mg/dL, "
        f"HbA1c {h['hba1c_percent']}%, "
        f"total cholesterol {h['total_cholesterol_mg_dl']} mg/dL "
        f"(LDL {h['ldl_mg_dl']}, HDL {h['hdl_mg_dl']}, triglycerides {h['triglycerides_mg_dl']} mg/dL)."
    )

    # ── Family History ────────────────────────────────────────────────────────
    fh_positives = [k for k, v in fh.items() if v]
    fh_txt = (
        f"Family history is positive for: {', '.join(fh_positives)}." if fh_positives
        else "No family history of hypertension, diabetes, heart disease, stroke, cancer, or asthma."
    )
    lines.append(fh_txt)

    # ── Medical History ───────────────────────────────────────────────────────
    past_txt = (
        f"Past conditions include: {', '.join(h['past_conditions'])}." if h["past_conditions"]
        else "No notable past conditions."
    )
    curr_txt = (
        f"Current conditions: {', '.join(h['current_conditions'])}." if h["current_conditions"]
        else "No current active conditions."
    )
    meds_txt = (
        f"Current medications: {', '.join(h['medications'])}." if h["medications"]
        else "Not on any medications."
    )
    allergy_txt = (
        f"Known allergies: {', '.join(h['allergies'])}." if h["allergies"]
        else "No known allergies."
    )
    lines.append(f"{past_txt} {curr_txt} {meds_txt} {allergy_txt}")

    # ── Other Medical Flags ───────────────────────────────────────────────────
    asthma_txt = "Has asthma." if h["asthma"] else "No asthma."
    tb_txt = "Has a history of tuberculosis." if h["tb_history"] else "No TB history."
    kidney_txt = "Has kidney disease." if h["kidney_disease"] else "No kidney disease."
    liver_txt = "Has liver disease." if h["liver_disease"] else "No liver disease."
    thyroid_txt = "Has a thyroid disorder." if h["thyroid_disorder"] else "No thyroid disorder."
    lines.append(
        f"{asthma_txt} {tb_txt} {kidney_txt} {liver_txt} {thyroid_txt} "
        f"Sickle cell status: {h['sickle_cell_status']}. "
        f"Hepatitis B status: {h['hepatitis_b_status']}. "
        f"HIV status: {h['hiv_status']}."
    )

    # ── Vaccinations / Reproductive ───────────────────────────────────────────
    covid_txt = (
        f"COVID-19 vaccinated (last dose: {h['last_covid_vaccine_year']})." if h["covid_vaccinated"]
        else "Not COVID-19 vaccinated."
    )
    hpv_txt = (
        "HPV vaccination status: not applicable." if h["hpv_vaccinated"] is None
        else ("HPV vaccinated." if h["hpv_vaccinated"] else "Not HPV vaccinated.")
    )
    preg_txt = (
        "Pregnancy status: not applicable." if h["pregnant"] is None
        else ("Currently pregnant." if h["pregnant"] else "Not currently pregnant.")
    )
    lines.append(f"{covid_txt} {hpv_txt} {preg_txt}")

    # ── Mental Health ─────────────────────────────────────────────────────────
    lines.append(
        f"Mental health: anxiety level '{mh['anxiety']}', "
        f"depression level '{mh['depression']}', "
        f"burnout risk '{mh['burnout_risk']}'."
    )

    # ── Work & Lifestyle Environment ──────────────────────────────────────────
    pain_txt = (
        f"Reported pain points: {', '.join(h['pain_points'])}." if h["pain_points"] and h["pain_points"] != ["None"]
        else "No reported pain points."
    )
    shift_txt = "Works shift hours." if h["shift_work"] else "Works standard (non-shift) hours."
    occ_exp = ", ".join(h["occupational_exposure"]) if h["occupational_exposure"] != ["None"] else "none"
    lines.append(
        f"{pain_txt} Screen time averages {h['screen_time_hours_per_day']} hours per day. "
        f"Works {h['work_hours_per_week']} hours per week. {shift_txt} "
        f"Commute is {h['commute_minutes_one_way']} minutes one way. "
        f"Air quality exposure: {h['air_quality_exposure'].lower()}. "
        f"Occupational exposure: {occ_exp}."
    )

    # ── Healthcare Utilisation ────────────────────────────────────────────────
    checkup_txt = (
        f"Had an annual checkup on {h['last_checkup_date']}." if h["annual_checkup_done"] and h["last_checkup_date"]
        else ("Annual checkup done (date unrecorded)." if h["annual_checkup_done"] else "Annual checkup not done.")
    )
    lines.append(
        f"{checkup_txt} Doctor visits in the last 12 months: {h['doctor_visits_last_12_months']}."
    )

    # ── Risk Flags ────────────────────────────────────────────────────────────
    rf_txt = (
        f"Identified health risk flags: {', '.join(h['risk_flags'])}." if h["risk_flags"]
        else "No health risk flags identified."
    )
    lines.append(rf_txt)

    return " ".join(lines)

random.seed(42)

first_names_m = ["Chinedu","Emeka","Tunde","Seyi","Ibrahim","Samuel","Kelechi","Kunle","Olamide","David","Gideon","Chukwuemeka","Femi","Yakubu","Uche"]
first_names_f = ["Aisha","Ngozi","Ifeoma","Zainab","Adaeze","Blessing","Halima","Chioma","Folasade","Damilola","Maryam","Amaka","Khadijah","Esther","Tomiwa"]
last_names = ["Okafor","Balogun","Adewale","Nwachukwu","Okonkwo","Eze","Ojo","Iroegbu","Danjuma","Lawal","Umeh","Nnaji","Bello","Ibrahim","Ogunleye","Abdullahi","Chukwu","Akinyemi","Oladipo","Onyekachi","Ajayi","Obi","Umar","Sule","Ezekwe"]

departments = ["Engineering","Finance","Operations","Marketing","Sales","Customer Support","Executive","HR","Field Ops","Product","Data","Security"]
job_levels = ["Junior","Mid","Senior","Lead"]
cities = ["Lagos","Abuja","Ibadan","Port Harcourt"]
diet_patterns = ["Balanced","Mixed","High-carb","High-salt","Mostly home-cooked"]
alcohol = ["None","Rare","Occasional","Moderate"]
air_exposure = ["Low","Moderate","High"]
sickle = ["AA","AS","SS"]

def rand_dob(min_age=19, max_age=55):
    today = date(2026,2,21)
    age = random.randint(min_age, max_age)
    start = today - timedelta(days=365*age)
    # random day in that year range
    dob = start - timedelta(days=random.randint(0, 365))
    return dob.isoformat()

def bmi(weight, height_cm):
    h = height_cm / 100.0
    return round(weight / (h*h), 1)

def make_employee(prefix, i):
    gender = random.choice(["M","F"])
    fn = random.choice(first_names_m if gender=="M" else first_names_f)
    ln = random.choice(last_names)
    height = random.randint(155, 190) if gender=="M" else random.randint(150, 180)
    weight = round(random.uniform(50, 110), 1)
    b = bmi(weight, height)

    sys = random.randint(105, 155)
    dia = random.randint(68, 100)

    fasting = random.randint(80, 125)
    a1c = round(random.uniform(4.9, 6.3), 1)

    tc = random.randint(150, 260)
    ldl = random.randint(70, 180)
    hdl = random.randint(30, 70)
    tg  = random.randint(60, 240)

    smokes = random.random() < 0.18
    cigs = random.randint(1, 10) if smokes else 0
    vapes = (not smokes) and (random.random() < 0.10)

    stress = random.randint(3, 9)
    sleep = round(random.uniform(5.2, 7.8), 1)
    steps = random.randint(3000, 12000)

    fam_htn = random.random() < 0.55
    fam_dm  = random.random() < 0.35
    fam_hd  = random.random() < 0.25
    fam_str = random.random() < 0.18
    fam_ca  = random.random() < 0.10
    fam_as  = random.random() < 0.12

    allergies_pool = ["Dust","Pollen","Peanuts","Shellfish","Penicillin","Cat dander","None"]
    allergy = random.choice(allergies_pool)
    allergies = [] if allergy=="None" else [allergy]

    past_pool = ["Malaria (recurrent)","Malaria (occasional)","Typhoid (past)","Gastritis","Ulcer","Anemia (resolved)","Back strain (work-related)","None"]
    past = random.choice(past_pool)
    past_conditions = [] if past=="None" else [past]

    current_conditions = []
    if sys >= 140 or dia >= 90:
        current_conditions.append("Hypertension (suspected)")
    if a1c >= 5.7:
        current_conditions.append("Prediabetes risk")
    if random.random() < 0.12:
        current_conditions.append("Seasonal allergies")

    meds = []
    if "Hypertension (suspected)" in current_conditions and random.random() < 0.30:
        meds.append("Amlodipine")

    whr = round(random.uniform(0.72, 1.02), 2)

    risk_flags = []
    if smokes: risk_flags.append("Smoker")
    if b >= 30: risk_flags.append("Obesity")
    elif b >= 25: risk_flags.append("Overweight")
    if sys >= 140 or dia >= 90: risk_flags.append("High BP")
    elif sys >= 130 or dia >= 85: risk_flags.append("Borderline BP")
    if a1c >= 5.7: risk_flags.append("Prediabetes range A1c")
    if ldl >= 160: risk_flags.append("High LDL")
    if tg >= 180: risk_flags.append("High triglycerides")
    if stress >= 8: risk_flags.append("High stress")
    if sleep < 6.0: risk_flags.append("Low sleep")

    emp = {
        "employee_id": f"{prefix}-{i:04d}",
        "name": f"{fn} {ln}",
        "gender": gender,
        "dob": rand_dob(),
        "department": random.choice(departments),
        "job_level": random.choice(job_levels),
        "location_city": random.choice(cities),
        "marital_status": random.choice(["Single","Married"]),
        "health": {
            "smokes": smokes,
            "cigarettes_per_day": cigs,
            "vapes": vapes,
            "alcohol_use": random.choice(alcohol),
            "drinks_per_week": random.randint(0, 8),
            "exercise_days_per_week": random.randint(0, 5),
            "avg_steps_per_day": steps,
            "sleep_hours_avg": sleep,
            "sleep_quality_1_10": random.randint(4, 9),
            "stress_level_1_10": stress,
            "diet_pattern": random.choice(diet_patterns),
            "fruit_veg_servings_per_day": random.randint(0, 6),
            "sugary_drinks_per_week": random.randint(0, 8),
            "fast_food_meals_per_week": random.randint(0, 6),
            "water_intake_liters_per_day": round(random.uniform(1.0, 3.0), 1),

            "height_cm": height,
            "weight_kg": weight,
            "bmi": b,
            "waist_cm": random.randint(70, 115),
            "hip_cm": random.randint(90, 125),
            "waist_to_hip_ratio": whr,
            "body_fat_percent": round(random.uniform(12, 38), 1),

            "blood_pressure_systolic": sys,
            "blood_pressure_diastolic": dia,
            "resting_heart_rate_bpm": random.randint(58, 95),
            "spo2_percent": random.randint(96, 100),

            "fasting_glucose_mg_dl": fasting,
            "hba1c_percent": a1c,

            "total_cholesterol_mg_dl": tc,
            "ldl_mg_dl": ldl,
            "hdl_mg_dl": hdl,
            "triglycerides_mg_dl": tg,

            "family_history": {
                "hypertension": fam_htn,
                "diabetes": fam_dm,
                "heart_disease": fam_hd,
                "stroke": fam_str,
                "cancer": fam_ca,
                "asthma": fam_as
            },

            "past_conditions": past_conditions,
            "current_conditions": current_conditions,
            "medications": meds,
            "allergies": allergies,

            "asthma": random.random() < 0.10,
            "sickle_cell_status": random.choice(sickle),
            "hepatitis_b_status": random.choice(["Vaccinated","Unknown"]),
            "hiv_status": "Not disclosed",
            "tb_history": random.random() < 0.03,
            "covid_vaccinated": True,
            "last_covid_vaccine_year": random.choice([2021,2022,2023]),
            "hpv_vaccinated": (gender=="F" and random.random() < 0.55) if gender=="F" else None,
            "pregnant": (gender=="F" and random.random() < 0.08) if gender=="F" else None,

            "kidney_disease": random.random() < 0.03,
            "liver_disease": random.random() < 0.02,
            "thyroid_disorder": random.random() < 0.03,

            "mental_health": {
                "anxiety": random.choice(["None","Mild","Moderate"]),
                "depression": random.choice(["None","Mild"]),
                "burnout_risk": random.choice(["Low","Moderate","High"])
            },

            "pain_points": random.sample(["Headaches","Back pain","Neck pain","Fatigue","Snoring","None"], k=1),
            "screen_time_hours_per_day": random.randint(3, 12),
            "work_hours_per_week": random.randint(40, 65),
            "shift_work": random.random() < 0.35,
            "commute_minutes_one_way": random.randint(10, 90),
            "air_quality_exposure": random.choice(air_exposure),
            "occupational_exposure": random.sample(["Sedentary desk work","Vehicle fumes","Jet fuel fumes","Shift work","None"], k=1),

            "annual_checkup_done": random.random() < 0.65,
            "last_checkup_date": random.choice(["2025-06-14","2025-08-09","2025-09-29","2025-10-19","2025-11-02","2025-12-06", None]),
            "doctor_visits_last_12_months": random.randint(0, 4),

            "risk_flags": risk_flags
        }
    }
    emp["summary"] = generate_summary(emp)
    return emp

def make_org(name, industry, hq_city, hr1_name, hr1_email, hr2_name, hr2_email, prefix):
    return {
        "name": name,
        "industry": industry,
        "hq_city": hq_city,
        "hrs": [
            {"name": hr1_name, "email": hr1_email, "password": "ChangeMe!2026", "role": "HR Lead"},
            {"name": hr2_name, "email": hr2_email, "password": "ChangeMe!2026", "role": "HR Generalist"}
        ],
        "employees": [make_employee(prefix, i) for i in range(1, 51)]
    }

data = {
    "organizations": [
        make_org("ChowStack","FoodTech","Lagos","Jennie Okafor","jennie@chowstack.ng","Tomiwa Adeyemi","tomiwa.hr@chowstack.ng","CS"),
        make_org("FlyWave","Logistics/AviationTech","Abuja","Emmanuel Ibe","emmanuel@flywave.ng","Chioma Ogunleye","chioma.hr@flywave.ng","FW"),
        make_org("PayDeck","Fintech","Lagos","Christie Okonkwo","christie@paydeck.ng","Folasade Bello","folasade.hr@paydeck.ng","PD")
    ]
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Saved to data.json")