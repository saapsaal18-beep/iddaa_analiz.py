import streamlit as st
import numpy as np
from scipy.stats import poisson
import requests

st.set_page_config(page_title="İddaa Quantum Pro", page_icon="⚽", layout="centered")
st.markdown("""<style>
.stApp{background-color:#0E0E0E;color:#FFF}h1,h2,h3,h4,p,label,.stMarkdown{color:#FFF!important}
.red{color:#FF1E1E!important;font-weight:bold}.card{background:#1A1A1A;border:1px solid #333;border-left:5px solid #FF1E1E;padding:12px;border-radius:8px;margin-bottom:12px}
div.stButton>button:first-child{background:#FF1E1E;color:#FFF;border:none;font-weight:bold;width:100%;padding:10px;border-radius:6px}
.stProgress>div>div>div>div{background:#FF1E1E}button[data-baseweb="tab"]{color:#FFF!important;font-weight:bold}
button[data-baseweb="tab"][aria-selected="true"]{border-bottom-color:#FF1E1E!important;color:#FF1E1E!important}
</style>""", unsafe_allow_html=True)

def analiz(eg, dg, dk, eguc, dguc, o25, okg):
    oran = max(90 - dk, 1) / 90.0
    eb, db = eguc * oran, dguc * oran
    tb, mg = eb + db, eg + dg
    olas = {b: round((99.9 if int(np.floor(b)+1)-mg <= 0 else (1 - poisson.cdf(int(np.floor(b)+1)-mg-1, tb))*100), 1) for b in [1.5, 2.5, 3.5, 4.5]}
    if eg > 0 and dg > 0: kg = 99.9
    elif eg > 0: kg = round((1 - poisson.pmf(0, db)) * 100, 1)
    elif dg > 0: kg = round((1 - poisson.pmf(0, eb)) * 100, 1)
    else: kg = round(((1 - poisson.pmf(0, eb)) * (1 - poisson.pmf(0, db))) * 100, 1)
    skorlar = sorted([(f"{eg+i}-{dg+j}", poisson.pmf(i, eb)*poisson.pmf(j, db)*100) for i in range(5) for j in range(5)], key=lambda x: x[1], reverse=True)[:3]
    return olas, kg, skorlar, (olas[2.5]/100)*o25, (kg/100)*okg

def goster(ev, dep, eg, dg, dk, kod, lig, o25, okg, olas, kg, skorlar, v25, vkg):
    st.markdown(f"<div class='card' style='text-align:center'><span class='red'>● ANALİZ ({dk}')</span><h2>{ev} <span class='red'>{eg}-{dg}</span> {dep}</h2><span>Kod: <b>{kod}</b> | {lig}</span></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, (s, p), idx in zip([c1, c2, c3], skorlar, [1, 2, 3]): col.metric(f"{idx}. Olası Skor", s, f"%{p:.1f}")
    for b, y in olas.items():
        st.markdown(f"**{b} Gol** — Alt: `%{round(100-y,1)}` | <span class='red'>Üst: %{y}</span>", unsafe_allow_html=True)
        st.progress(min(int(y), 100))
    st.markdown(f"**KG** — Yok: `%{round(100-kg,1)}` | <span class='red'>Var: %{kg}</span>", unsafe_allow_html=True)
    st.progress(min(int(kg), 100))
    if v25 > 1.05: st.success(f"✅ 2.5 ÜST VALUE! İhtimal: %{olas[2.5]} | Oran: {o25} (+%{int((v25-1)*100)})")
    if vkg > 1.05: st.success(f"✅ KG VAR VALUE! İhtimal: %{kg} | Oran: {okg} (+%{int((vkg-1)*100)})")

def bulten(key=""):
    if key:
        try:
            r = requests.get(f"https://the-odds-api.com{key}&regions=eu&markets=totals", timeout=5)
            if r.status_code == 200:
                lst = []
                for idx, x in enumerate(r.json()[:15]):
                    o25 = next((o["price"] for b in x.get("bookmakers",[]) for m in b.get("markets",[]) if m["key"]=="totals" for o in m["outcomes"] if o["name"]=="Over" and o["point"]==2.5), 1.75)
                    lst.append({"kod": str(500+idx), "lig": x.get("sport_title","Lig"), "ev": x["home_team"], "dep": x["away_team"], "dk": 1, "eg": 0, "dg": 0, "eguc": 1.6, "dguc": 1.3, "o25": o25, "okg": 1.80})
                if lst: return lst, True
        except: pass
    return [
        {"kod":"104","lig":"Süper Lig","ev":"Galatasaray","dep":"Samsunspor","dk":58,"eg":2,"dg":0,"eguc":2.4,"dguc":1.1,"o25":1.45,"okg":1.95},
        {"kod":"112","lig":"Süper Lig","ev":"Fenerbahçe","dep":"Göztepe","dk":34,"eg":0,"dg":1,"eguc":2.6,"dguc":1.3,"o25":1.55,"okg":1.60},
        {"kod":"208","lig":"La Liga","ev":"Leganes","dep":"Burgos","dk":57,"eg":3,"dg":0,"eguc":2.1,"dguc":0.9,"o25":1.10,"okg":2.40},
        {"kod":"315","lig":"Premier Lig","ev":"Arsenal","dep":"Chelsea","dk":66,"eg":1,"dg":1,"eguc":2.2,"dguc":1.9,"o25":1.50,"okg":1.05}
    ], False

st.markdown("<h1>⚽ İDDAA <span class='red'>QUANTUM</span> PRO</h1>", unsafe_allow_html=True)
key = st.sidebar.text_input("The Odds API Anahtarı", type="password")
maclar, aktif = bulten(key)
t1, t2 = st.tabs(["📡 CANLI BÜLTEN", "✍️ MANUEL GİRİŞ"])

with t1:
    st.info("🟢 Canlı API Aktif" if aktif else "ℹ️ İddaa Demo Bülteni Aktif (Canlı veri için sol menüden API girin)")
    for m in maclar:
        olas, kg, sk, v25, vkg = analiz(m["eg"], m["dg"], m["dk"], m["eguc"], m["dguc"], m["o25"], m["okg"])
        if v25 > 1.12 or vkg > 1.12:
            sec = f"2.5 ÜST ({m['o25']} | +%{int((v25-1)*100)})" if v25 >= vkg else f"KG VAR ({m['okg']} | +%{int((vkg-1)*100)})"
            st.markdown(f"<div class='card'><small>Kod: {m['kod']} | {m['lig']} • {m['dk']}'</small><br><b>{m['ev']} {m['eg']}-{m['dg']} {m['dep']}</b><br><span class='red'>🎯 {sec}</span> | Skor: <b>{sk[0][0]}</b></div>", unsafe_allow_html=True)
    isimler = [f"[{m['kod']}] {m['ev']} - {m['dep']} ({m['dk']}')" for m in maclar]
    sec_m = maclar[isimler.index(st.selectbox("Maç Seçin:", isimler))]
    if st.button("SEÇİLİ MAÇI ANALİZ ET"):
        goster(sec_m["ev"], sec_m["dep"], sec_m["eg"], sec_m["dg"], sec_m["dk"], sec_m["kod"], sec_m["lig"], sec_m["o25"], sec_m["okg"], *analiz(sec_m["eg"], sec_m["dg"], sec_m["dk"], sec_m["eguc"], sec_m["dguc"], sec_m["o25"], sec_m["okg"]))

with t2:
    c1, c2 = st.columns(2)
    ev = c1.text_input("Ev Sahibi", "Beşiktaş")
    eg = c1.number_input("Ev Gol", 0, 15, 1)
    eguc = c1.slider("Ev Hücum Gücü", 0.5, 3.5, 1.9, 0.1)
    o25 = c1.number_input("2.5 ÜST Oranı", 1.01, 15.0, 1.65, 0.05)
    dep = c2.text_input("Deplasman", "Trabzonspor")
    dg = c2.number_input("Dep Gol", 0, 15, 0)
    dguc = c2.slider("Dep Hücum Gücü", 0.5, 3.5, 1.4, 0.1)
    okg = c2.number_input("KG VAR Oranı", 1.01, 15.0, 1.85, 0.05)
    dk = st.slider("Dakika", 1, 89, 45)
    if st.button("MANUEL ANALİZ ET"):
        goster(ev, dep, eg, dg, dk, "MANUEL", "Özel Analiz", o25, okg, *analiz(eg, dg, dk, eguc, dguc, o25, okg))
