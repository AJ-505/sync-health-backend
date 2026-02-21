import json, random
from datetime import date, timedelta

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

    return {
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