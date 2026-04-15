import json
import os
import random
from modules.logger import get_logger

logger = get_logger("TipRetriever")

def get_tips_raw(analysis: str, profile: dict = None, max_categories: int = 6) -> list:
    """
    Palauttaa listan vinkkejä, jotka sopivat asiakkaan profiiliin.
    Suodatus perustuu vinkin target_audience-kenttään ja profiilin tietoihin.
    Lopuksi tehdään kerrostettu otanta: jokaisesta kategoriasta valitaan yksi satunnainen vinkki.
    """
    file_path = os.path.join("data", "tips.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tips_data = json.load(f)
        all_tips = tips_data["tips"]
    except Exception as e:
        logger.error(f"Tips.json virhe: {e}")
        return []

    if not profile:
        logger.info("Profiilia ei annettu, palautetaan kaikki vinkit")
        return all_tips

    # Muodostetaan lista asiakkaan ominaisuuksista (kuten aiemmin)
    asiakas_ominaisuudet = set()
    asumismuoto = profile.get("asumismuoto", "").lower()
    if asumismuoto:
        asiakas_ominaisuudet.add(asumismuoto)
    if profile.get("lämmitys_tapa") == "sähkö":
        asiakas_ominaisuudet.add("sähkölämmitys")
    if profile.get("ilmalämpöpumppu"):
        asiakas_ominaisuudet.add("ilmalämpöpumppu")
    if profile.get("sähköauto"):
        asiakas_ominaisuudet.add("sähköauto")
    if profile.get("mökki"):
        asiakas_ominaisuudet.add("mökki")
    if profile.get("sauna"):
        asiakas_ominaisuudet.add("sauna")
    if asumismuoto == "kerrostalo":
        asiakas_ominaisuudet.add("lattialämmitys")
    if profile.get("pörssisähkö", True):
        asiakas_ominaisuudet.add("pörssisähkö")

    logger.info(f"Asiakkaan ominaisuudet: {asiakas_ominaisuudet}")

    # Suodatetaan vinkit
    filtered = []
    for tip in all_tips:
        target = tip.get("target_audience", [])
        if not target or "kaikki" in target:
            filtered.append(tip)
            continue
        if any(ominaisuus in target for ominaisuus in asiakas_ominaisuudet):
            filtered.append(tip)
        else:
            if tip["category"] in [
                "huonelämpötila", "valaistus", "viihde-elektroniikka",
                "sähkönkulutuksen_seuranta", "ikkunat_ja_ovet", "vedenkulutus"
            ]:
                filtered.append(tip)
            else:
                logger.debug(f"Vinkki {tip['id']} ei sovi profiiliin, jätetään pois")

    logger.info(f"Profiilisuodatuksen jälkeen {len(filtered)} vinkkiä (alkuperäisiä {len(all_tips)})")

    # --- KERROSTETTU OTANTA ---
    # Ryhmitellään vinkit kategorioittain
    category_to_tips = {}
    for tip in filtered:
        cat = tip["category"]
        if cat not in category_to_tips:
            category_to_tips[cat] = []
        category_to_tips[cat].append(tip)

    logger.info(f"Löytyi {len(category_to_tips)} eri kategoriaa: {list(category_to_tips.keys())}")

    # Valitaan enintään max_categories kategoriaa (satunnaisesti, mutta priorisoidaan tärkeät? Tässä satunnaisesti)
    # Jos haluat aina mukaan tietyt kategoriat (esim. lämmitys), voit lisätä logiikan. Nyt yksinkertainen.
    selected_categories = list(category_to_tips.keys())
    if len(selected_categories) > max_categories:
        selected_categories = random.sample(selected_categories, max_categories)
        logger.info(f"Valittiin satunnaisesti {max_categories} kategoriaa: {selected_categories}")
    else:
        logger.info(f"Kaikki {len(selected_categories)} kategoriaa valittu")

    # Valitaan jokaisesta valitusta kategoriasta yksi satunnainen vinkki
    stratified_tips = []
    for cat in selected_categories:
        tips_in_cat = category_to_tips[cat]
        chosen = random.choice(tips_in_cat)
        stratified_tips.append(chosen)
        logger.debug(f"Kategoriasta '{cat}' valittiin vinkki {chosen['id']}: {chosen['title']}")

    # Sekoitetaan lopullinen lista (järjestys)
    random.shuffle(stratified_tips)
    logger.info(f"Kerrostetun otannan jälkeen {len(stratified_tips)} vinkkiä")
    return stratified_tips