import json
import os
import random

# Profiilien perusparametrit (keskimääräinen päiväkulutus kWh)
PROFILES = {
    "Matti": {
        "type": "omakotitalo_sahkolammitys",
        "base_day": 25.0,
        "weekend_factor": 1.2,
        "evening_peak": (18, 21, 3.0),
        "night_low": (23, 5, 0.5),
        "special": {"torstai": (19, 20, 4.2)}
    },
    "Laura": {
        "type": "kerrostalo_kaukolampo",
        "base_day": 12.0,
        "weekend_factor": 1.1,
        "evening_peak": (17, 21, 0.8),
        "night_low": (23, 6, 0.3),
        "special": {}
    },
    "Mikko": {
        "type": "rivitalo_perhe",
        "base_day": 20.0,
        "weekend_factor": 1.3,
        "evening_peak": (17, 20, 2.0),
        "night_low": (23, 5, 0.6),
        "special": {"torstai": (18, 19, 3.0), "sunnuntai": (18, 19, 2.5)}
    },
    "Jukka": {
        "type": "omakotitalo_sahkoauto_mokki",
        "base_day": 28.0,
        "weekend_factor": 0.5,
        "evening_peak": (17, 21, 2.5),
        "night_low": (23, 5, 0.8),
        "car_charging": (0, 4, 2.0),
        "special": {"torstai": (19, 20, 4.0)}
    },
    "Sari": {
        "type": "omakotitalo_maalampo_sahkoauto",
        "base_day": 22.0,
        "weekend_factor": 1.1,
        "evening_peak": (17, 21, 1.5),
        "night_low": (23, 5, 0.5),
        "car_charging": (10, 14, 3.5),
        "special": {}
    }
}

def generate_hourly_consumption(profile, day_name):
    """Palauttaa sanakirjan tunnit 00-23 -> kulutus kWh"""
    # Tarkistetaan onko viikonloppu (lauantai tai sunnuntai)
    is_weekend = day_name.lower() in ["lauantai", "sunnuntai"]
    base = profile["base_day"] / 24.0
    if is_weekend:
        base *= profile["weekend_factor"]
    
    consumption = {}
    for hour in range(24):
        val = base + random.uniform(-0.2, 0.2)
        # Yökulutus
        night_start, night_end, night_val = profile["night_low"]
        if night_start <= hour or hour < night_end:
            val = night_val + random.uniform(0, 0.2)
        # Iltahuippu
        peak_start, peak_end, peak_add = profile["evening_peak"]
        if peak_start <= hour < peak_end:
            val += peak_add + random.uniform(-0.3, 0.3)
        # Sähköauton lataus
        if "car_charging" in profile:
            ch_start, ch_end, ch_add = profile["car_charging"]
            if ch_start <= hour < ch_end:
                val += ch_add + random.uniform(-0.5, 0.5)
        # Erityispäivät
        special = profile.get("special", {})
        for day_key, (s_hour, e_hour, add) in special.items():
            if day_key.lower() == day_name.lower() and s_hour <= hour < e_hour:
                val += add
        consumption[f"{hour:02d}"] = round(max(0.1, val), 1)
    return consumption

def main():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    days = ["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]
    
    for name, profile in PROFILES.items():
        data = {}
        for day in days:
            data[day] = generate_hourly_consumption(profile, day)
        file_path = os.path.join(data_dir, f"consumption_{name.lower()}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Generoitu: {file_path}")

if __name__ == "__main__":
    main()