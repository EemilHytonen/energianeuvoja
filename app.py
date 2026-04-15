import streamlit as st
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from modules.data_loader import load_consumption_data, load_customer_profile
from modules.llm_interface import DeepSeekLLM
from modules.analyzer import analyze_consumption, calculate_weekly_consumption, get_avg_consumption
from modules.tip_retriever import get_tips_raw
from modules.logger import get_logger, get_event_id

logger = get_logger("Energianeuvonta")
load_dotenv()

def format_links_in_text(text):
    pattern = r'\(Lähde:\s*([^,]+?),\s*(https?://[^\s\)]+)\)'
    def replace(match):
        nimi = match.group(1).strip()
        url = match.group(2).strip()
        url = re.sub(r'[.,;\)]+$', '', url)
        return f'(Lähde: <a href="{url}" target="_blank">{nimi}</a>)'
    return re.sub(pattern, replace, text)

def extract_used_sources(text, tips_list):
    # HUOM: Tämä funktio tunnistaa vinkit lähteen perusteella, ei yksittäisen vinkin sisällön.
    # Tarkempi toteutus vaatisi vinkkien tunnistamista otsikon tai sisällön perusteella,
    # mikä jätettiin pois demosta aikataulusyistä.
    used = {}
    used_ids = []
    clean_text = re.sub(r'<[^>]+>', '', text)
    for tip in tips_list:
        if tip['source'] in clean_text or tip['source_url'] in text:
            if tip['source'] not in used:
                used[tip['source']] = tip['source_url']
            used_ids.append(tip['id'])
    if used_ids:
        logger.info(f"Tekoälyn valitsemat vinkit ID:t: {sorted(set(used_ids))}")
    else:
        logger.debug("Ei tunnistettu käytettyjä vinkkejä (saattaa olla false flag)")
    return used

def plot_weekly_consumption(consumption_data, asumismuoto, has_cottage=False):
    values = []
    days_order = ["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]
    for day in days_order:
        if day in consumption_data:
            for hour in range(24):
                hour_str = f"{hour:02d}"
                if hour_str in consumption_data[day]:
                    values.append(consumption_data[day][hour_str])
    if not values:
        return None
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(values)), values, color='blue', linewidth=1.5, label='Sinun kulutuksesi')
    ax.set_xlabel('Aika (7 päivää)')
    ax.set_ylabel('Kulutus (kWh)')
    ax.set_title(f'Sähkönkulutus viikon aikana - {asumismuoto.capitalize()}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    # Päivien rajat (maanantai 0, tiistai 24, ..., sunnuntai 144)
    day_ticks = [0, 24, 48, 72, 96, 120, 144]
    day_labels = ["Ma", "Ti", "Ke", "To", "Pe", "La", "Su"]
    # Kellonajat 6 tunnin välein (0,6,12,18) jokaiselle päivälle
    hour_ticks = []
    hour_labels = []
    for day_offset in day_ticks:
        for hour in [0, 6, 12, 18]:
            hour_ticks.append(day_offset + hour)
            hour_labels.append(f"{hour:02d}")
    ax.set_xticks(day_ticks)
    ax.set_xticklabels(day_labels, fontsize=10)
    # Lisätään toinen akseli tuntimerkinnöille (pienellä fontilla)
    ax2 = ax.twiny()
    ax2.set_xticks(hour_ticks)
    ax2.set_xticklabels(hour_labels, fontsize=7, rotation=45)
    ax2.set_xlim(ax.get_xlim())
    if has_cottage:
        ax.text(0.98, 0.02, 'Huom: Mökkiä ei ole huomioitu tässä kuvaajassa', transform=ax.transAxes, fontsize=8, ha='right', style='italic', color='gray')
    plt.tight_layout()
    return fig

st.set_page_config(page_title="Energianeuvonantaja", page_icon="⚡")
st.title("⚡ Energianeuvonantaja")

customer_list = ["Matti", "Laura", "Mikko", "Jukka", "Sari"]
customer_id = st.selectbox("Valitse asiakas", customer_list)

if st.button("🔍 Analysoi kulutukseni", type="primary"):
    event_id = get_event_id()
    logger.info(f"=== ANALYYSI ALKAA - Event ID: {event_id} ===")
    with st.spinner("Analysoidaan..."):
        consumption_data = load_consumption_data(customer_id)
        profile = load_customer_profile(customer_id)
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            st.error("API-avain puuttuu")
            st.stop()
        llm = DeepSeekLLM(api_key=api_key)
        
        analysis = analyze_consumption(consumption_data, llm, profile)
        tips_list = get_tips_raw(analysis, profile)
        all_tip_ids = [tip['id'] for tip in tips_list]
        logger.info(f"Saatavilla olevat vinkit ID:t: {all_tip_ids}")
        tips_text = ""
        for tip in tips_list:
            tips_text += f"- **{tip['title']}**: {tip['content']} (Lähde: {tip['source']}, {tip['source_url']})\n"
        
        asumismuoto = profile.get('asumismuoto', 'omakotitalo')
        has_cottage = profile.get('mökki', False)
        weekly_total = calculate_weekly_consumption(consumption_data)
        avg_weekly = get_avg_consumption(asumismuoto)
        diff_percent = round(((weekly_total - avg_weekly) / avg_weekly) * 100, 1)
        
        profile_text = f"""
        Asiakas: {customer_id}
        Asumismuoto: {profile.get('asumismuoto', 'ei tiedossa')}
        Lämmitys: {profile.get('lämmitys_tapa', 'ei tiedossa')}
        Ilmalämpöpumppu: {'kyllä' if profile.get('ilmalämpöpumppu') else 'ei'}
        Sähköauto: {'kyllä' if profile.get('sähköauto') else 'ei'}
        Mökki: {'kyllä' if profile.get('mökki') else 'ei'}
        Sauna: {'kyllä' if profile.get('sauna') else 'ei'}
        Pörssisähkö: {'kyllä' if profile.get('pörssisähkö') else 'ei'}"""        
        
        final_prompt = f"""
        Olet energianeuvonnan asiantuntija.

        Saat:
        1. Asiakkaan profiilin
        2. Analyysin sähkönkulutuksesta (sisältää vertailun Tilastokeskuksen keskiarvoon)
        3. Listan energiansäästövinkkejä

        Kirjoita asiakkaalle **henkilökohtainen, ystävällinen vastaus** (max 8 virkettä).

        TÄRKEÄT OHJEET:
        - Älä keksi uusia vinkkejä. Käytä VAIN alla listattuja vinkkejä.
        - Jokaisen antamasi neuvon perässä on oltava (Lähde: Nimi, URL).
        - Valitse listalta **korkeintaan neljä** vinkkiä, jotka parhaiten sopivat asiakkaan kulutuskäyttäytymiseen ja profiiliin.
        - Aloita aina viestisi tervehtimällä asiakasta.
        - Pyri antamaan esimerkkejä säästöjen suuruudesta energiamäärällisesti tai rahallisesti jos se on valituissa vinkeissä saatavilla.
        - Pidä asiallinen kielensävy sekä sanavalinnat koko analyysin ajan kiinnittäen erityistä huomiota suomen kielioppiin.
        - Tee neljästä valitusta vinkistä aina numeroitu lista alkaen numerosta 1 loppuen numeroon 4.
        - Lopeta vastauksesi aina seuraavasti:
          1. Ensin lause: "Voit seurata kulutustasi kätevästi uudistuneesta [online-palvelustamme ja mobiilisovelluksestamme](https://www.vaasansahko.fi/asiakaspalvelu/sovellus-ja-online/)."
          2. Sitten lause uudessa kappaleessa: "Aurinkoista ja energiatehokasta päivänjatkoa!"

        PROFIILI:
        {profile_text}

        ANALYYSI:
        {analysis}

        VINKIT (valmiit, lähde ja URL mukana):
        {tips_text}"""
        
        final_response = llm.generate(final_prompt, temperature=0.2)
        formatted_response = format_links_in_text(final_response)
        used_sources = extract_used_sources(final_response, tips_list)
        fig = plot_weekly_consumption(consumption_data, asumismuoto, has_cottage)
        
    # NÄYTETÄÄN TULOKSET
    st.subheader("📊 Viikkokulutuksen vertailu")
    col1, col2, col3 = st.columns(3)
    
    asumismuoto_taivutus = {
        "kerrostalo": "kerrostalossa",
        "rivitalo": "rivitalossa",
        "omakotitalo": "omakotitalossa"
    }.get(asumismuoto, "asunnossa")
    
    col1.metric("Sinun kulutuksesi", f"{weekly_total} kWh")
    col1.caption("Lähde: oma sähkönkulutusdata")
    
    col2.metric(f"Keskiarvo {asumismuoto_taivutus}", f"{avg_weekly} kWh")
    col2.caption(f'Lähde: <a href="https://stat.fi/fi/tilasto/asen" target="_blank">Tilastokeskus</a>', unsafe_allow_html=True)
    
    if diff_percent < 0:
        col3.metric("Ero", f"{diff_percent} %", delta=f"{abs(diff_percent)} % vähemmän", delta_color="normal")
    elif diff_percent > 0:
        col3.metric("Ero", f"+{diff_percent} %", delta=f"{diff_percent} % enemmän", delta_color="inverse")
    else:
        col3.metric("Ero", "0 %", "Täsmälleen keskiarvossa")
    # Prosentuaalinen ero on laskennallinen, ei tarvitse erillistä lähdettä
    
    if fig:
        st.subheader("📈 Viikon sähkönkulutus")
        st.pyplot(fig)
    
    st.subheader("💡 Analyysi ja säästövinkit")
    st.markdown(formatted_response, unsafe_allow_html=True)
    
    # Lähdeluettelo (pääsivuille)
    MAIN_SITE_URLS = {
        "Vaasan Sähkö": "https://www.vaasansahko.fi/",
        "Energiavirasto": "https://energiavirasto.fi/etusivu",
        "Motiva": "https://www.motiva.fi/",
        "Tilastokeskus": "https://stat.fi/"
    }
    if used_sources:
        sources_html = "Lähteet: " + ", ".join([f'<a href="{MAIN_SITE_URLS.get(name, url)}" target="_blank">{name}</a>' for name, url in used_sources.items()])
        st.markdown(sources_html, unsafe_allow_html=True)
    else:
        st.caption("Lähteet: Motiva, Vaasan Sähkö, Energiavirasto, Tilastokeskus")
    
    logger.info(f"=== ANALYYSI PÄÄTTYY - Event ID: {event_id} ===")
    logger.info("")