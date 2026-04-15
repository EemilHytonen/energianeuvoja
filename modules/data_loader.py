import json
import os
from modules.logger import get_logger

logger = get_logger("DataLoader")

def load_consumption_data(customer_id: str) -> dict:
    """
    Lataa asiakkaan kulutusdatan JSON-tiedostosta.
    Tiedoston oletetaan olevan muodossa: data/consumption_nimi.json
    """
    file_path = os.path.join("data", f"consumption_{customer_id.lower()}.json")
    logger.info(f"Ladataan kulutusdataa: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Kulutusdata ladattu, päiviä: {len(data)}")
        return data
    except FileNotFoundError:
        logger.error(f"Kulutustiedostoa ei löydy: {file_path}")
        # Fallback: palautetaan pieni mock, jotta sovellus ei kaadu
        fallback = {
            "Maanantai": {"00": 0.5, "12": 1.0, "18": 1.5},
            "Tiistai": {"00": 0.5, "12": 1.0, "18": 1.5},
            "Keskiviikko": {"00": 0.5, "12": 1.0, "18": 1.5},
            "Torstai": {"00": 0.5, "12": 1.0, "18": 1.5},
            "Perjantai": {"00": 0.5, "12": 1.0, "18": 1.5},
            "Lauantai": {"00": 0.5, "12": 1.0, "18": 1.5},
            "Sunnuntai": {"00": 0.5, "12": 1.0, "18": 1.5}
        }
        logger.warning("Käytetään fallback-dataa")
        return fallback
    except json.JSONDecodeError as e:
        logger.exception(f"JSON-virhe tiedostossa {file_path}: {e}")
        raise

def load_customer_profile(customer_id: str) -> dict:
    file_path = os.path.join("data", "profiles.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        profile = profiles.get(customer_id, {})
        
        # Yhteensopivuus: jos vanha "lämmitys" on olemassa, muunna uuteen muotoon
        if "lämmitys" in profile and "lämmitys_tapa" not in profile:
            old = profile["lämmitys"].lower()
            if "sähkö" in old and "ilmalämpöpumppu" in old:
                profile["lämmitys_tapa"] = "sähkö"
                profile["ilmalämpöpumppu"] = True
            elif "sähkö" in old:
                profile["lämmitys_tapa"] = "sähkö"
                profile["ilmalämpöpumppu"] = False
            elif "kaukolämpö" in old:
                profile["lämmitys_tapa"] = "kaukolämpö"
                profile["ilmalämpöpumppu"] = False
            elif "maalämpö" in old:
                profile["lämmitys_tapa"] = "maalämpö"
                profile["ilmalämpöpumppu"] = False
            else:
                profile["lämmitys_tapa"] = "muu"
                profile["ilmalämpöpumppu"] = False
            # Poistetaan vanha kenttä
            del profile["lämmitys"]
        
        # Oletusarvot jos puuttuu
        if "ilmalämpöpumppu" not in profile:
            profile["ilmalämpöpumppu"] = False
        if "sauna" not in profile:
            profile["sauna"] = False
        if "pörssisähkö" not in profile:
            profile["pörssisähkö"] = True
            
        return profile
    except FileNotFoundError:
        logger.error(f"Profiilitiedostoa ei löydy: {file_path}")
        return {}