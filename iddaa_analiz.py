import streamlit as st
import numpy as np
from scipy.stats import poisson
import requests

st.set_page_config(page_title="İddaa Quantum Ultimate", page_icon="⚽", layout="centered")

st.markdown("""<style>
.stApp{background-color:#FFFFFF;color:#111111}
h1,h2,h3,h4,p,label,.stMarkdown{color:#111111!important;font-family:'Segoe UI',sans-serif}
.red{color:#D90429!important;font-weight:bold}
.panel{background:#F8F9FA;border:1px solid #E0E0E0;border-radius:12px;padding:15px;margin-bottom:15px;box-shadow:0 2px 6px rgba(0,0,0,0.04)}
.best-card{background:#FFF0F3;border:2px solid #D90429;border-radius:12px;padding:14px;margin-bottom:16px}
div.stButton>button{background:#D90429!important;color:#FFF!important;border:none!important;font-weight:bold!important;width:100%;border-radius:8px;padding:10px}
div[data-testid="stRadio"]>div{flex-direction:row;justify-content:space-between;background:#EAECEF;padding:6px;border-radius:8px}
.bar-wrap{width:100%;height:25px;background:#E9ECEF;border-radius:6px;overflow:hidden;display:flex;margin-top:4px;margin-bottom:11px;font-size:12px;font-weight:bold;border:1px solid #DEE2E6}
.bar-left{background:#E9ECEF;color:#212529;display:flex;align-items:center;padding-left:8px;white-space:nowrap}
.bar-right{background:#D90429;color:#FFFFFF;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;white-space:nowrap}
.stat-box{background:#FFFFFF;border:1px solid #DEE2E6;border-radius:8px;padding:10px;text-align:center;font-size:13px}
</style>""", unsafe_allow_html=True)

def saf_oran_2(oa, ob):
    ia, ib = 1.0/oa, 1.0/ob
    top = ia + ib
    marj = max(round((top - 1.0) * 100, 1), 0.0)
    return round(1.0/(ia/top), 2), round(1.0/(ib/top), 2), marj

def saf_oran_3(o1, ox, o2):
    i1, ix, i2 = 1.0/o1, 1.0/ox, 1.0/o2
    top = i1 + ix + i2
    marj = max(round((top - 1.0) * 100, 1), 0.0)
    return round(1.0/(i1/top), 2), round(1.0/(ix/top), 2), round(1.0/(i2/top), 2), marj

def kelly_yuzde(ihtimal_yuzde, oran):
    p = ihtimal_yuzde / 100.0
    q = 1.0 - p
    b = oran - 1.0
    if b <= 0: return 0.0
    f = ((b * p) - q) / b
    return round(min(max(f * 0.25 * 100, 0.0), 15.0), 1)
def tam_analiz(eg, dg, dk, e_att, e_yed, d_att, d_yed, e_kor, d_kor, tempo, o1, ox, o2, o25_u, o25_a, okg_v, okg_y, okor_u, okor_a):
    oran = max(90 - dk, 1) / 90.0
    ev_guc = ((e_att + d_yed) / 2.0) * tempo
    dep_guc = ((d_att + e_yed) / 2.0) * tempo
    eb, db = ev_guc * oran, dep_guc * oran
    tb, mg = eb + db, eg + dg

    olas = {}
    for b in [1.5, 2.5, 3.5, 4.5]:
        gerek = int(np.floor(b) + 1) - mg
        ust = 99.9 if gerek <= 0 else (1 - poisson.cdf(gerek - 1, tb)) * 100
        olas[b] = round(min(max(ust, 0.1), 99.9), 1)

    iy_bek = (ev_guc + dep_guc) * 0.44
    iy_05_ust = round(min(max((1 - poisson.pmf(0, iy_bek)) * 100, 1.0), 99.0), 1) if dk <= 45 else (99.9 if mg > 0 else 1.0)

    if eg > 0 and dg > 0: kg = 99.9
    elif eg > 0: kg = round((1 - poisson.pmf(0, db)) * 100, 1)
    elif dg > 0: kg = round((1 - poisson.pmf(0, eb)) * 100, 1)
    else: kg = round(((1 - poisson.pmf(0, eb)) * (1 - poisson.pmf(0, db))) * 100, 1)
    kg = min(max(kg, 0.1), 99.9)

    skor_listesi = []
    p_ms1, p_msx, p_ms2 = 0.0, 0.0, 0.0
    for i in range(6):
        for j in range(6):
            p = poisson.pmf(i, eb) * poisson.pmf(j, db)
            fs_e, fs_d = eg + i, dg + j
            skor_listesi.append((f"{fs_e}-{fs_d}", p * 100))
            if fs_e > fs_d: p_ms1 += p
            elif fs_e == fs_d: p_msx += p
            else: p_ms2 += p

    skor_listesi.sort(key=lambda x: x[1], reverse=True)
    ms_olas = (round(p_ms1*100, 1), round(p_msx*100, 1), round(p_ms2*100, 1))
    kor_bek = (e_kor + d_kor) * tempo
    kor_95 = round(min(max((1 - poisson.cdf(9, kor_bek)) * 100, 1.0), 99.0), 1)

    saf_ms = saf_oran_3(o1, ox, o2)
    saf_25 = saf_oran_2(o25_u, o25_a)
    saf_kg = saf_oran_2(okg_v, okg_y)
    saf_kor = saf_oran_2(okor_u, okor_a)

    vals = ((ms_olas[0]/100)*o1, (olas[2.5]/100)*o25_u, (kg/100)*okg_v, (kor_95/100)*okor_u)
    return olas, iy_05_ust, kg, kor_95, skor_listesi[:3], ms_olas, vals, saf_ms, saf_25, saf_kg, saf_kor

def cift_bar_ciz(baslik, sol_et, sol_y, sag_et, sag_y):
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:bold;color:#111;">
        <span>{baslik} | {sol_et} %{sol_y}</span>
        <span class="red">{sag_et} %{sag_y}</span>
    </div>
    <div class="bar-wrap">
        <div class="bar-left" style="width:{sol_y}%;">{sol_et} %{sol_y}</div>
        <div class="bar-right" style="width:{sag_y}%;">{sag_et} %{sag_y}</div>
    </div>""", unsafe_allow_html=True)

def bulten_getir(key=""):
    if key:
        try:
            r = requests.get(f"https://the-odds-api.com{key}&regions=eu&markets=h2h,totals", timeout=8)

            if r.status_code == 200:
                lst = []
                for idx, x in enumerate(r.json()[:15]):
                    o1, ox, o2, o25_u, o25_a = 2.10, 3.30, 3.20, 1.75, 1.95
                    for b in x.get("bookmakers",[]):
                        for m in b.get("markets",[]):
                            if m["key"]=="h2h":
                                for o in m["outcomes"]:
                                    if o["name"]==x["home_team"]: o1 = o["price"]
                                    elif o["name"]==x["away_team"]: o2 = o["price"]
                                    else: ox = o["price"]
                            if m["key"]=="totals":
                                for o in m["outcomes"]:
                                    if o["name"]=="Over" and o["point"]==2.5: o25_u = o["price"]
                                    if o["name"]=="Under" and o["point"]==2.5: o25_a = o["price"]
                    lst.append({"kod":str(500+idx),"ev":x["home_team"],"dep":x["away_team"],"dk":1,"eg":0,"dg":0,"e_att":1.8,"e_yed":1.1,"d_att":1.4,"d_yed":1.3,"e_kor":5.6,"d_kor":4.8,"o1":o1,"ox":ox,"o2":o2,"o25":o25_u,"o25_a":o25_a,"okg":1.80,"okg_y":1.85,"okor":1.75,"okor_a":1.85})
                if lst: return lst
        except: pass
    return [
        {"kod":"104","ev":"Galatasaray","dep":"Samsunspor","dk":1,"eg":0,"dg":0,"e_att":2.6,"e_yed":0.8,"d_att":1.4,"d_yed":1.6,"e_kor":6.8,"d_kor":4.4,"o1":1.42,"ox":4.30,"o2":5.80,"o25":1.52,"o25_a":2.15,"okg":1.85,"okg_y":1.75,"okor":1.65,"okor_a":1.95},
        {"kod":"112","ev":"Fenerbahçe","dep":"Göztepe","dk":34,"eg":0,"dg":1,"e_att":2.4,"e_yed":0.9,"d_att":1.3,"d_yed":1.5,"e_kor":6.4,"d_kor":4.2,"o1":1.85,"ox":3.50,"o2":3.60,"o25":1.55,"o25_a":2.10,"okg":1.60,"okg_y":2.05,"okor":1.70,"okor_a":1.90},
        {"kod":"208","ev":"Leganes","dep":"Burgos","dk":57,"eg":3,"dg":0,"e_att":1.9,"e_yed":0.7,"d_att":0.9,"d_yed":1.4,"e_kor":5.1,"d_kor":3.8,"o1":1.05,"ox":9.50,"o2":18.0,"o25":1.10,"o25_a":4.50,"okg":2.40,"okg_y":1.42,"okor":1.85,"okor_a":1.75},
        {"kod":"315","ev":"Arsenal","dep":"Chelsea","dk":1,"eg":0,"dg":0,"e_att":2.3,"e_yed":1.0,"d_att":2.0,"d_yed":1.4,"e_kor":6.5,"d_kor":5.4,"o1":1.92,"ox":3.45,"o2":3.40,"o25":1.68,"o25_a":1.95,"okg":1.62,"okg_y":2.00,"okor":1.72,"okor_a":1.88}
    ]
st.markdown("<h2 style='text-align:center;margin-bottom:5px;'>İddaa <span class='red'>Quantum</span> Ultimate</h2>", unsafe_allow_html=True)
api_key = st.sidebar.text_input("The Odds API Anahtarı (İsteğe Bağlı)", type="password")
kasa = st.sidebar.number_input("Toplam Kasa Bakiyeniz (TL)", min_value=50, max_value=1000000, value=1000, step=100)
maclar = bulten_getir(api_key)

firsatlar = []
for m in maclar:
    olas, iy05, kg, kor95, sk, ms_o, vals, sms, s25, skg, skor_s = tam_analiz(
        m["eg"],m["dg"],m["dk"],m["e_att"],m["e_yed"],m["d_att"],m["d_yed"],m["e_kor"],m["d_kor"],1.0,
        m["o1"],m["ox"],m["o2"],m["o25"],m["o25_a"],m["okg"],m["okg_y"],m["okor"],m["okor_a"]
    )
    adaylar = [
        (vals[0], f"MS 1 ({m['ev']})", m['o1'], sms[0], ms_o[0]),
        (vals[1], "2.5 GOL ÜST", m['o25'], s25[0], olas[2.5]),
        (vals[2], "KG VAR", m['okg'], skg[0], kg),
        (vals[3], "9.5 KORNER ÜST", m['okor'], skor_s[0], kor95)
    ]
    en_iyi = max(adaylar, key=lambda x: x[0])
    if en_iyi[0] > 1.05:
        firsatlar.append((en_iyi[0], m, en_iyi[1], en_iyi[2], en_iyi[3], en_iyi[4]))

firsatlar.sort(key=lambda x: x[0], reverse=True)

if firsatlar:
    val, m, tercih, oran_id, saf_or, iht = firsatlar[0]
    ky = kelly_yuzde(iht, oran_id)
    onerilen_tutar = int((kasa * ky) / 100)
    st.markdown(f"""
    <div class="best-card">
        <span class="red" style="font-size:12px;letter-spacing:1px;">🏆 GÜNÜN EN DEĞERLİ BANKO TERCİHİ</span><br>
        <span style="font-size:18px;font-weight:bold;">[{m['kod']}] {m['ev']} - {m['dep']}</span><br>
        <span class="red" style="font-size:15px;">🎯 {tercih} | İddaa: {oran_id} (Saf Oran: {saf_or} | İhtimal: %{iht})</span><br>
        <small style="color:#333;">Avantaj: <b>+%{int((val-1)*100)}</b> • Kelly Kasa Önerisi: <b>%{ky} ({onerilen_tutar} TL)</b></small>
    </div>""", unsafe_allow_html=True)

    if len(firsatlar) >= 2:
        v1, m1, t1, o1_k, _, _ = firsatlar[0]
        v2, m2, t2, o2_k, _, _ = firsatlar[1]
        toplam_oran = round(o1_k * o2_k, 2)
        st.markdown(f"""
        <div class="panel" style="border-left:5px solid #D90429;">
            <span class="red" style="font-size:12px;">🔥 AKILLI 2'Lİ KOMBİNE KUPON ÖNERİSİ (Toplam Oran: {toplam_oran})</span><br>
            <div style="font-size:13px;margin-top:5px;">
                1️⃣ <b>[{m1['kod']}] {m1['ev']} - {m1['dep']}</b> ➔ <span class="red">{t1} ({o1_k})</span><br>
                2️⃣ <b>[{m2['kod']}] {m2['ev']} - {m2['dep']}</b> ➔ <span class="red">{t2} ({o2_k})</span>
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div class='panel'>", unsafe_allow_html=True)
mod = st.radio("MOD", ["CANLI KAPALI (MANUEL)", "CANLI AÇIK", "GEÇMİŞ FORM"], index=1, horizontal=True)
mac_listesi = [f"[{m['kod']}] ({m['dk']}') {m['ev']} {m['eg']}-{m['dg']} {m['dep']}" for m in maclar]
secilen_str = st.selectbox("AKTİF İDDAA BÜLTENİNDEN MAÇ SEÇ", mac_listesi)
sec_m = maclar[mac_listesi.index(secilen_str)]

c1, c2, c3 = st.columns([2, 2, 1.5])
ev_ad = c1.text_input("Ev Sahibi", value=sec_m["ev"], label_visibility="collapsed")
dep_ad = c2.text_input("Deplasman", value=sec_m["dep"], label_visibility="collapsed")
c3.button("ANALİZ ET")

tempo_secim = st.select_slider("⚡ Maç İçi Baskı & Tempo Durumu", options=["Düşük Tempo (0.85x)", "Normal Tempo (1.0x)", "Yüksek Baskı (1.15x)", "Tek Kale / Çok Yüksek (1.30x)"], value="Normal Tempo (1.0x)")
tempo_map = {"Düşük Tempo (0.85x)": 0.85, "Normal Tempo (1.0x)": 1.0, "Yüksek Baskı (1.15x)": 1.15, "Tek Kale / Çok Yüksek (1.30x)": 1.30}
tempo = tempo_map[tempo_secim]

if mod == "CANLI KAPALI (MANUEL)":
    ca, cb, cc = st.columns(3)
    dk = ca.number_input("Dakika", 1, 90, sec_m["dk"])
    eg = cb.number_input("Ev Gol", 0, 15, sec_m["eg"])
    dg = cc.number_input("Dep Gol", 0, 15, sec_m["dg"])
    s1, s2, s3 = st.columns(3)
    e_att = s1.number_input("Ev Attığı", 0.0, 5.0, sec_m["e_att"], 0.1)
    e_yed = s2.number_input("Ev Yediği", 0.0, 5.0, sec_m["e_yed"], 0.1)
    e_kor = s3.number_input("Ev Korner", 0.0, 15.0, sec_m["e_kor"], 0.2)
    d1, d2, d3 = st.columns(3)
    d_att = d1.number_input("Dep Attığı", 0.0, 5.0, sec_m["d_att"], 0.1)
    d_yed = d2.number_input("Dep Yediği", 0.0, 5.0, sec_m["d_yed"], 0.1)
    d_kor = d3.number_input("Dep Korner", 0.0, 15.0, sec_m["d_kor"], 0.2)
    m1_o, mx_o, m2_o = st.columns(3)
    o1 = m1_o.number_input("MS 1", 1.01, 30.0, sec_m["o1"], 0.05)
    ox = mx_o.number_input("MS X", 1.01, 30.0, sec_m["ox"], 0.05)
    o2 = m2_o.number_input("MS 2", 1.01, 30.0, sec_m["o2"], 0.05)
    o_a, o_b = st.columns(2)
    o25_u = o_a.number_input("2.5 Üst", 1.01, 20.0, sec_m["o25"], 0.05)
    o25_a = o_b.number_input("2.5 Alt", 1.01, 20.0, sec_m["o25_a"], 0.05)
    o_c, o_d = st.columns(2)
    okg_v = o_c.number_input("KG Var", 1.01, 20.0, sec_m["okg"], 0.05)
    okg_y = o_d.number_input("KG Yok", 1.01, 20.0, sec_m["okg_y"], 0.05)
    o_e, o_f = st.columns(2)
    okor_u = o_e.number_input("9.5 Korner Üst", 1.01, 20.0, sec_m["okor"], 0.05)
    okor_a = o_f.number_input("9.5 Korner Alt", 1.01, 20.0, sec_m["okor_a"], 0.05)
else:
    dk, eg, dg = sec_m["dk"], sec_m["eg"], sec_m["dg"]
    e_att, e_yed, e_kor = sec_m["e_att"], sec_m["e_yed"], sec_m["e_kor"]
    d_att, d_yed, d_kor = sec_m["d_att"], sec_m["d_yed"], sec_m["d_kor"]
    o1, ox, o2 = sec_m["o1"], sec_m["ox"], sec_m["o2"]
    o25_u, o25_a, okg_v, okg_y, okor_u, okor_a = sec_m["o25"], sec_m["o25_a"], sec_m["okg"], sec_m["okg_y"], sec_m["okor"], sec_m["okor_a"]

st.markdown(f"<span class='red' style='font-size:14px;'>● SEÇİLİ MAÇ ({dk}') {ev_ad} {eg}-{dg} {dep_ad}</span>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("<span class='red' style='font-size:13px;letter-spacing:1px;'>📊 SON 5 MAÇ FORMU (İÇ / DIŞ SAHA) & KORNER</span>", unsafe_allow_html=True)
f1, f2 = st.columns(2)
f1.markdown(f"<div class='stat-box'><b>🏠 {ev_ad} (Ev Son 5)</b><br>Attığı: <span class='red'>{e_att}</span> | Yediği: <b>{e_yed}</b><br>Korner Ort: <span class='red'>{e_kor}</span></div>", unsafe_allow_html=True)
f2.markdown(f"<div class='stat-box'><b>✈️ {dep_ad} (Dep Son 5)</b><br>Attığı: <span class='red'>{d_att}</span> | Yediği: <b>{d_yed}</b><br>Korner Ort: <span class='red'>{d_kor}</span></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

olas, iy05, kg, kor95, skorlar, ms_o, vals, sms, s25, skg, skor_s = tam_analiz(
    eg, dg, dk, e_att, e_yed, d_att, d_yed, e_kor, d_kor, tempo, o1, ox, o2, o25_u, o25_a, okg_v, okg_y, okor_u, okor_a
)

st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("<span class='red' style='font-size:13px;letter-spacing:1px;'>💎 SAF ORAN (KOMİSYONSUZ ADİL ORAN) & MS 1-X-2 ANALİZİ</span>", unsafe_allow_html=True)
st.markdown(f"""
<div class='stat-box' style='text-align:left;margin-top:6px;line-height:1.8;'>
    <b>• Maç Sonu (1-X-2) İhtimal:</b> MS1 <b>%{ms_o[0]}</b> | MSX <b>%{ms_o[1]}</b> | MS2 <b>%{ms_o[2]}</b><br>
    <b>• Maç Sonu Saf Oran:</b> İddaa: <b>{o1} / {ox} / {o2}</b> ➔ <span class='red'>Saf: {sms[0]} / {sms[1]} / {sms[2]}</span> <small>(Marj: %{sms[3]})</small><br>
    <b>• 2.5 Gol Üst / Alt:</b> İddaa: <b>{o25_u} / {o25_a}</b> ➔ <span class='red'>Saf: {s25[0]} / {s25[1]}</span> <small>(Marj: %{s25[2]})</small><br>
    <b>• KG Var / Yok:</b> İddaa: <b>{okg_v} / {okg_y}</b> ➔ <span class='red'>Saf: {skg[0]} / {skg[1]}</span> <small>(Marj: %{skg[2]})</small><br>
    <b>• 9.5 Korner Üst / Alt:</b> İddaa: <b>{okor_u} / {okor_a}</b> ➔ <span class='red'>Saf: {skor_s[0]} / {skor_s[1]}</span> <small>(Marj: %{skor_s[2]})</small>
</div>""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("<span class='red' style='font-size:13px;letter-spacing:1px;'>🎯 GOL, İLK YARI, KG VE KORNER TAHMİNLERİ</span>", unsafe_allow_html=True)
cift_bar_ciz("İlk Yarı 0.5 Gol", "Alt", round(100 - iy05, 1), "Üst", iy05)
for b in [1.5, 2.5, 3.5, 4.5]:
    ust = olas[b]
    cift_bar_ciz(f"{b} Gol", "Alt", round(100 - ust, 1), "Üst", ust)
cift_bar_ciz("KG (Karşılıklı Gol)", "Yok", round(100 - kg, 1), "Var", kg)
cift_bar_ciz(f"9.5 Korner (Beklenti: {round((e_kor+d_kor)*tempo,1)})", "Alt", round(100 - kor95, 1), "Üst", kor95)

st.divider()
cs1, cs2, cs3 = st.columns(3)
cs1.metric("1. Olası Skor", skorlar[0][0], f"%{skorlar[0][1]:.1f}")
cs2.metric("2. Olası Skor", skorlar[1][0], f"%{skorlar[1][1]:.1f}")
cs3.metric("3. Olası Skor", skorlar[2][0], f"%{skorlar[2][1]:.1f}")

secenekler_bu = [
    (vals[0], f"MS 1 ({ev_ad})", o1, sms[0], ms_o[0]),
    (vals[1], "2.5 GOL ÜST", o25_u, s25[0], olas[2.5]),
    (vals[2], "KG VAR", okg_v, skg[0], kg),
    (vals[3], "9.5 KORNER ÜST", okor_u, skor_s[0], kor95)
]
en_iyi_bu = max(secenekler_bu, key=lambda x: x[0])
if en_iyi_bu[0] > 1.05:
    v_b, t_b, o_b, s_b, i_b = en_iyi_bu
    ky_b = kelly_yuzde(i_b, o_b)
    tutar_b = int((kasa * ky_b) / 100)
    st.markdown(f"""
    <div class='best-card' style='margin-top:12px;margin-bottom:0;text-align:center;'>
        <span class='red'>🔥 BU MAÇTA OYNANMASI GEREKEN TERCİH: {t_b}</span><br>
        <b>İddaa Oranı: {o_b}</b> (Saf Oran: {s_b}) • Avantaj: <span class='red'>+%{int((v_b-1)*100)}</span><br>
        <small>💰 Kasa Önerisi (Kelly): Kasanın <b>%{ky_b}</b>'i (<b>{tutar_b} TL</b>) ile oynanması uygundur.</small>
    </div>""", unsafe_allow_html=True)
else:
    st.info("ℹ️ Bu maçtaki oranlar şirket marjı arındırıldığında matematiksel olarak sınırda görünüyor.")
st.markdown("</div>", unsafe_allow_html=True)
