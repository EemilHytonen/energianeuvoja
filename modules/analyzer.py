from modules.logger import get_logger

logger = get_logger("Analyzer")

AVG_WEEKLY_CONSUMPTION = {
    "kerrostalo": 100.0,
    "rivitalo": 180.0,
    "omakotitalo": 280.0
}

def calculate_weekly_consumption(consumption_data: dict) -> float:
    total = 0.0
    for day, hours in consumption_data.items():
        for hour, value in hours.items():
            total += value
    return round(total, 1)

def get_avg_consumption(asumismuoto: str) -> float:
    asumismuoto = asumismuoto.lower() if asumismuoto else ""
    if "kerrostalo" in asumismuoto:
        return AVG_WEEKLY_CONSUMPTION["kerrostalo"]
    elif "rivitalo" in asumismuoto:
        return AVG_WEEKLY_CONSUMPTION["rivitalo"]
    else:
        return AVG_WEEKLY_CONSUMPTION["omakotitalo"]

def analyze_consumption(consumption_data: dict, llm, customer_profile: dict = None) -> str:
    weekly_total = calculate_weekly_consumption(consumption_data)
    if customer_profile:
        asumismuoto = customer_profile.get("asumismuoto", "omakotitalo")
    else:
        asumismuoto = "omakotitalo"
    avg_weekly = get_avg_consumption(asumismuoto)
    data_text = ""
    for day, hours in consumption_data.items():
        data_text += f"{day}: {hours}\n"
    difference = weekly_total - avg_weekly
    diff_percent = round((difference / avg_weekly) * 100, 1)
    if difference > 0:
        comparison_text = f"Viikkokulutuksesi ({weekly_total} kWh) on {diff_percent} % KORKEAMPI kuin keskivertokulutus ({avg_weekly} kWh) saman tyyppisessä asunnossa."
    elif difference < 0:
        comparison_text = f"Viikkokulutuksesi ({weekly_total} kWh) on {abs(diff_percent)} % MATALAMPI kuin keskivertokulutus ({avg_weekly} kWh) saman tyyppisessä asunnossa. Hienoa!"
    else:
        comparison_text = f"Viikkokulutuksesi ({weekly_total} kWh) on TÄYSIN KESKIARVOSSA verrattuna saman tyyppiseen asuntoon ({avg_weekly} kWh)."
    
    prompt = f"""
    Olet energianeuvonnan asiantuntija.
    Asiakkaan asumismuoto: {asumismuoto}
    SÄHKÖNKULUTUSDATA (7 päivää):
    {data_text}
    VIKKOKULUTUSVERTAILU (Tilastokeskus):
    {comparison_text}
    Tehtäväsi:
    1. Kerro kolme suurinta kulutuspiikkiä (päivä ja kellonaika) ja niiden arvot.
    2. Tarkastele yökulutusta (klo 23–05). Onko siellä epätavallisen korkeita arvoja?
    3. Kommentoi lyhyesti vertailua: Miksi kulutus on korkeampi/matalampi/keskiarvossa? (Perustelu datan perusteella)
    4. Anna lyhyt, ytimekäs yhteenveto kulutuskäyttäytymisestä.
    
    Älä keksi ylimääräistä. Käytä vain annettua dataa.
    """
    logger.info(f"Lähetetään analyysipyyntö. Viikkokulutus: {weekly_total} kWh, vertailu: {avg_weekly} kWh")
    return llm.generate(prompt, temperature=0.2)