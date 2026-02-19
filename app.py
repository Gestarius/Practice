import streamlit as st
import pandas as pd

from datetime import datetime, date

# Google Sheets connection
from streamlit_gsheets import GSheetsConnection

# Charts
import altair as alt

# Exports / downloads
import io
import base64
import xlsxwriter

# PDF (reportlab)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# --------------------------------------------------------
# STREAMLIT CONFIG (İLK STREAMLIT KOMUTU OLMALI)
# --------------------------------------------------------
st.set_page_config(page_title="LİHKAB Yönetim", layout="wide", page_icon="🗺️")


# --------------------------------------------------------
# GLOBAL CSS (Tema + HTML tablo light gray)
# --------------------------------------------------------
st.markdown(
    """
<style>
:root {
    --bg-main: #2b2f36;      /* açık antrasit */
    --card-bg: #353a42;
    --text-main: #f1f5f9;
    --text-muted: #94a3b8;
    --primary: #3b82f6;
    --primary-soft: #1e293b;
    --success: #22c55e;
    --warning: #f59e0b;
    --border-soft: #3f4650;
}

/* App background */
[data-testid="stAppViewContainer"] {
    background-color: var(--bg-main);
}

/* Main content */
.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #020617 100%);
    border-right: 1px solid #020617;
}
section[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
section[data-testid="stSidebar"] button {
    background-color: #020617 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px;
}
section[data-testid="stSidebar"] button:hover {
    background-color: #1e293b !important;
}

/* Headers */
h1, h2, h3 {
    color: var(--text-main) !important;
    font-weight: 700;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: var(--card-bg);
    border-radius: 16px;
    padding: 22px;
    border: 1px solid var(--border-soft);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted);
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    color: var(--text-main);
    font-size: 30px;
}

/* Generic card box */
.card-box {
    background-color: var(--card-bg);
    border-radius: 16px;
    padding: 22px;
    border: 1px solid var(--border-soft);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

/* Buttons */
.stButton > button {
    background-color: var(--primary);
    color: white;
    border-radius: 12px;
    padding: 8px 20px;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #1d4ed8;
}

/* Altair chart */
.vega-embed {
    background-color: var(--card-bg) !important;
    border-radius: 16px;
    padding: 12px;
    border: 1px solid var(--border-soft);
}

/* ====== CUSTOM LIGHT GRAY TABLE (HTML) ====== */
.table-wrap{
  background:#e5e7eb;
  border:1px solid #cbd5e1;
  border-radius:14px;
  padding:10px;
  overflow:auto;
}
.table-wrap table{
  width:100%;
  border-collapse:collapse;
  font-size:14px;
  color:#111827;
}
.table-wrap thead th{
  background:#d1d5db;
  text-align:left;
  padding:10px;
  border-bottom:1px solid #cbd5e1;
}
.table-wrap tbody td{
  padding:10px;
  border-bottom:1px solid #e2e8f0;
}
.table-wrap tbody tr:nth-child(even){
  background:#f3f4f6;
}
.table-wrap tbody tr:hover{
  background:#e2e8f0;
}
</style>
""",
    unsafe_allow_html=True,
)


def html_table(df: pd.DataFrame) -> None:
    """Render dataframe as light-gray HTML table."""
    st.markdown(f'<div class="table-wrap">{df.to_html(index=False)}</div>', unsafe_allow_html=True)


# --------------------------------------------------------
# GOOGLE SHEETS – BAĞLANTI
# --------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Google Sheets bağlantı hatası: " + str(e))
    st.stop()


# --------------------------------------------------------
# LOGIN SESSION
# --------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.page = "main"


# --------------------------------------------------------
# USERS TABLOSU OKUMA
# --------------------------------------------------------
def load_users():
    try:
        users_df = conn.read(worksheet="Users", ttl=5).fillna("")
        users_df = users_df.astype(str)
        for col in users_df.columns:
            users_df[col] = users_df[col].str.strip()
        return users_df
    except Exception as e:
        st.error(f"⚠️ Users sayfası okunamadı: {e}")
        st.stop()


# --------------------------------------------------------
# LOGIN KONTROLÜ
# --------------------------------------------------------
def check_login(username, password):
    users = load_users()

    username = str(username).strip().lower()
    password = str(password).strip()

    users["username"] = users["username"].astype(str).str.strip().str.lower()
    users["password"] = (
        users["password"].astype(str).str.strip().str.replace(".0", "", regex=False)
    )

    match = users[(users["username"] == username) & (users["password"] == password)]
    if len(match) == 1:
        return match.iloc[0]["role"]
    return None


# --------------------------------------------------------
# LOGIN EKRANI
# --------------------------------------------------------
def login_screen():
    st.title("🔐 LİHKAB Yönetim Giriş")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")

    if st.button("Giriş Yap", type="primary"):
        role = check_login(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.success(f"Giriş başarılı ✔ Rol: {role}")
            st.rerun()
        else:
            st.error("❌ Kullanıcı adı veya şifre yanlış")


if not st.session_state.logged_in:
    login_screen()
    st.stop()


# --------------------------------------------------------
# SAYFA1 VERİLERİNİ YÜKLE
# --------------------------------------------------------
try:
    df = conn.read(worksheet="Sayfa1", ttl=5).fillna("")
    df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce").dt.date
    df["Tarih_Dt"] = pd.to_datetime(df["Tarih"], errors="coerce")
except Exception as e:
    st.error("Google Sheets okuma hatası: " + str(e))
    st.stop()


# --------------------------------------------------------
# SABİT LİSTELER
# --------------------------------------------------------
IS_TURU_LIST = [
    "Aplikasyon", "Yapı Aplikasyonu", "Ecri-misil", "Kübaj", "Tus",
    "Kat İrtifağı", "Kat Mülkiyeti", "Cins Değişikliği", "İntikal",
    "İfraz", "Yola Terk", "İhtas", "Tevhit", "Oturma Raporu Takip",
    "Numarataj", "Zemin Tespit", "İmar Barışı (Kat Mülkiyeti)",
    "Hatalı Bağımsız Düzeltme", "41 uygulaması", "Plankote"
]

DURUM_LIST = [
    "Başvuru Alındı",
    "Araziye gidildi",
    "Evraklar hazırlanıyor",
    "Tamamlandı"
]

df["Durum"] = df["Durum"].astype(str)
df.loc[~df["Durum"].isin(DURUM_LIST), "Durum"] = "Başvuru Alındı"


# --------------------------------------------------------
# ANASAYFA DASHBOARD
# --------------------------------------------------------
def render_anasayfa(df):
    st.subheader("📌 Genel Durum Özeti")

    bekleyen_is = df[df["Durum"] != "Tamamlandı"]
    bekleyen_odeme = df[df["Ödeme Durumu"] == "Bekliyor"]
    odenen = df[df["Ödeme Durumu"] == "Ödendi"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📂 Bekleyen İş", len(bekleyen_is))
    col2.metric("💰 Bekleyen Ödeme", f"{bekleyen_odeme['Ücret'].sum():,.0f} TL")
    col3.metric("🟢 Ödenen Toplam", f"{odenen['Ücret'].sum():,.0f} TL")
    col4.metric("📦 Toplam İş", len(df))

    st.divider()

    st.subheader("📊 Aylık Gelir")
    if not odenen.empty:
        odenen = odenen.copy()
        odenen["Ay"] = pd.to_datetime(odenen["Tarih"]).dt.to_period("M").astype(str)
        aylik = odenen.groupby("Ay")["Ücret"].sum().reset_index()

        chart = alt.Chart(aylik).mark_bar(cornerRadius=6).encode(
            x="Ay:N",
            y="Ücret:Q",
            tooltip=["Ay", "Ücret"]
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Henüz ödenmiş iş yok.")

    st.divider()

    st.subheader("🟡 Bekleyen Son İşler")
    tbl1 = bekleyen_is.sort_values("Tarih", ascending=False).head(10)[
        ["Tarih", "Müşteri", "İş Türü", "Ada_Parsel", "Ücret"]
    ].copy()
    html_table(tbl1)

    st.divider()

    st.subheader("💸 Bekleyen Son Ödemeler")
    tbl2 = bekleyen_odeme.sort_values("Tarih", ascending=False).head(10)[
        ["Tarih", "Müşteri", "Ada_Parsel", "Ücret"]
    ].copy()
    html_table(tbl2)


# --------------------------------------------------------
# SIDEBAR MENÜ
# --------------------------------------------------------
with st.sidebar:
    st.header("📌 Menü")

    if st.button("🏠 Anasayfa"):
        st.session_state.page = "main"
        st.rerun()

    if st.button("📄 İş Takip Paneli"):
        st.session_state.page = "is_takip"
        st.rerun()

    if st.session_state.role == "admin":
        if st.button("👥 Kullanıcı Yönetimi"):
            st.session_state.page = "users"
            st.rerun()

    if st.button("💰 Ödeme Paneli"):
        st.session_state.page = "odeme"
        st.rerun()

    if st.button("🚪 Çıkış Yap"):
        st.session_state.logged_in = False
        st.rerun()


# --------------------------------------------------------
# SAYFA: KULLANICI YÖNETİMİ (ADMIN)
# --------------------------------------------------------
if st.session_state.page == "users":
    if st.session_state.role != "admin":
        st.error("Bu sayfa sadece admin kullanıcılar içindir!")
        st.stop()

    st.title("👥 Kullanıcı Yönetimi")

    users_df = load_users()
    st.subheader("Kayıtlı Kullanıcılar")
    html_table(users_df)

    st.subheader("➕ Yeni Kullanıcı Ekle")
    u = st.text_input("Kullanıcı Adı")
    p = st.text_input("Şifre")
    r = st.selectbox("Rol", ["user", "admin"])

    if st.button("Kaydet"):
        new_row = pd.DataFrame([{"username": u, "password": p, "role": r}])
        updated = pd.concat([users_df, new_row], ignore_index=True)
        conn.update(worksheet="Users", data=updated)
        st.success("Kullanıcı eklendi ✔")
        st.rerun()

    st.subheader("🗑 Kullanıcı Sil")
    del_user = st.selectbox("Silinecek Kullanıcı", users_df["username"])

    if st.button("❌ Sil"):
        updated = users_df[users_df["username"] != del_user]
        conn.update(worksheet="Users", data=updated)
        st.success("Silindi ✔")
        st.rerun()

    st.stop()


# --------------------------------------------------------
# ÖDEME PANELİ
# --------------------------------------------------------
def render_odeme_paneli(conn):
    st.title("💰 Ödeme Paneli")

    dfp = conn.read(worksheet="Sayfa1", ttl=5).fillna("")
    dfp["Tarih"] = pd.to_datetime(dfp["Tarih"], errors="coerce")

    st.subheader("🔎 Filtreler")
    col_yil, col_ay, col_musteri = st.columns(3)

    yillar = sorted(dfp["Tarih"].dt.year.dropna().unique())
    aylar = ["Tümü"] + [f"{i:02d}" for i in range(1, 13)]

    sec_yil = col_yil.selectbox("Yıl", ["Tümü"] + list(map(str, yillar)))
    sec_ay = col_ay.selectbox("Ay", aylar)

    musteriler = (
        dfp["Müşteri"]
        .astype(str).str.strip()
        .loc[dfp["Müşteri"].astype(str).str.strip() != ""]
        .unique()
    )
    musteriler = sorted(musteriler, key=str.lower)

    sec_musteri = col_musteri.selectbox(
        "Müşteri (isim yazarak arayabilirsiniz)",
        options=["Tümü"] + list(musteriler),
        index=0
    )

    df_f = dfp.copy()
    if sec_yil != "Tümü":
        df_f = df_f[df_f["Tarih"].dt.year == int(sec_yil)]
    if sec_ay != "Tümü":
        df_f = df_f[df_f["Tarih"].dt.strftime("%m") == sec_ay]
    if sec_musteri != "Tümü":
        df_f = df_f[df_f["Müşteri"].astype(str).str.strip() == sec_musteri]

    bekleyen = df_f[df_f["Ödeme Durumu"] == "Bekliyor"].copy()
    odenen = df_f[df_f["Ödeme Durumu"] == "Ödendi"].copy()

    today = datetime.now()
    if not bekleyen.empty:
        bekleyen["Gecikme (Gün)"] = (today - bekleyen["Tarih"]).dt.days
    else:
        bekleyen["Gecikme (Gün)"] = []

    col1, col2, col3 = st.columns(3)
    col1.metric("🟡 Bekleyen Tahsilat", f"{bekleyen['Ücret'].sum():,.0f} TL")
    col2.metric("🟢 Ödenen Toplam", f"{odenen['Ücret'].sum():,.0f} TL")
    col3.metric("📦 Kayıt Sayısı", len(df_f))

    st.divider()

    st.subheader("📊 Aylık Gelir")
    if not odenen.empty:
        odenen = odenen.copy()
        odenen["Ay"] = odenen["Tarih"].dt.to_period("M").astype(str)
        aylik = odenen.groupby("Ay")["Ücret"].sum().reset_index()
        chart = alt.Chart(aylik).mark_bar(cornerRadius=6).encode(
            x="Ay:N",
            y="Ücret:Q",
            tooltip=["Ay", "Ücret"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

    st.subheader("🟡 Bekleyen Ödemeler")
    if not bekleyen.empty:
        html_table(bekleyen[["Tarih", "Müşteri", "Ada_Parsel", "Ücret", "Gecikme (Gün)"]])
    else:
        st.info("Bekleyen ödeme yok.")

    # PDF export
    if not bekleyen.empty:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)

        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph("<b>Bekleyen Ödemeler Raporu</b>", styles["Title"]))
        elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", styles["Normal"]))
        elements.append(Paragraph(" ", styles["Normal"]))

        table_data = [["Tarih", "Müşteri", "Ada / Parsel", "Ücret (TL)", "Gecikme (Gün)"]]
        for _, row in bekleyen.iterrows():
            table_data.append([
                row["Tarih"].strftime("%d.%m.%Y") if pd.notnull(row["Tarih"]) else "",
                str(row["Müşteri"]),
                str(row["Ada_Parsel"]),
                f"{float(row['Ücret']):,.0f} TL",
                str(row["Gecikme (Gün)"])
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]))
        elements.append(table)
        doc.build(elements)

        st.download_button(
            "📄 Bekleyen Ödemeleri PDF İndir",
            data=pdf_buffer.getvalue(),
            file_name="bekleyen_odemeler.pdf",
            mime="application/pdf"
        )

    st.subheader("🟢 Ödenmiş İşler")
    if not odenen.empty:
        html_table(odenen[["Tarih", "Müşteri", "Ada_Parsel", "Ücret"]])
    else:
        st.info("Ödenmiş iş yok.")

    # Excel export
    st.divider()
    st.subheader("📥 Rapor İndirme")

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("Ödeme Raporu")

    header = workbook.add_format({"bold": True, "bg_color": "#E6EEF8", "border": 1})
    money = workbook.add_format({"num_format": '#,##0 "TL"'})
    date_fmt = workbook.add_format({"num_format": "dd.mm.yyyy"})

    for col_i, col_name in enumerate(df_f.columns):
        worksheet.write(0, col_i, col_name, header)

    for row_i, row in df_f.iterrows():
        for col_i, val in enumerate(row):
            if isinstance(val, pd.Timestamp):
                worksheet.write_datetime(row_i + 1, col_i, val, date_fmt)
            elif df_f.columns[col_i] == "Ücret":
                try:
                    worksheet.write(row_i + 1, col_i, float(val), money)
                except Exception:
                    worksheet.write(row_i + 1, col_i, str(val))
            else:
                worksheet.write(row_i + 1, col_i, str(val))

    workbook.close()

    st.download_button(
        "📊 Excel (XLSX) İndir",
        data=output.getvalue(),
        file_name="odeme_raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# --------------------------------------------------------
# NAVIGATION
# --------------------------------------------------------
if st.session_state.page == "main":
    render_anasayfa(df)
    st.stop()

if st.session_state.page == "odeme":
    render_odeme_paneli(conn)
    st.stop()

# --------------------------------------------------------
# İŞ TAKİP PANELİ (interaktif data_editor)
# --------------------------------------------------------
st.subheader("📊 Ay Bazlı İş & Ciro Analizi")

ay_liste = {
    "Tümü": None,
    "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4,
    "Mayıs": 5, "Haziran": 6, "Temmuz": 7, "Ağustos": 8,
    "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
}

yil_liste = sorted({d.year for d in df["Tarih"] if pd.notnull(d)}, reverse=True)
yil_liste = ["Tümü"] + [str(y) for y in yil_liste]

colA, colB = st.columns(2)
secili_ay = colA.selectbox("Ay Seçiniz", list(ay_liste.keys()))
secili_yil = colB.selectbox("Yıl Seçiniz", yil_liste)

df_kpi = df.copy()
if secili_yil != "Tümü":
    df_kpi = df_kpi[df_kpi["Tarih_Dt"].dt.year == int(secili_yil)]
if ay_liste[secili_ay] is not None:
    df_kpi = df_kpi[df_kpi["Tarih_Dt"].dt.month == ay_liste[secili_ay]]

bekleyen = len(df_kpi[df_kpi["Durum"] != "Tamamlandı"])
gelen_is = len(df_kpi)
tahsilat_bekleyen = df_kpi[df_kpi["Ödeme Durumu"] == "Bekliyor"]["Ücret"].sum()
ciro = df_kpi[df_kpi["Ödeme Durumu"] == "Ödendi"]["Ücret"].sum()

label = f"{secili_ay} {secili_yil}" if secili_yil != 'Tümü' else secili_ay

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"📂 Bekleyen İş ({label})", bekleyen)
c2.metric(f"📅 Gelen İş ({label})", gelen_is)
c3.metric(f"💰 Tahsilat Bekleyen ({label})", f"{tahsilat_bekleyen:.0f} TL")
c4.metric(f"🏦 Ciro ({label})", f"{ciro:.0f} TL")

st.divider()

st.subheader("➕ Yeni İş Ekle")

ilce_mahalle_map = {
    "Karaburun": ["Merkez","Yayla","Eğlenhoca","İnecik","Kösedere","Karareis","Saip","Sarpıncık","Hasseki","İhsaniye","Küçükbahçe","Yeniköy","Bozköy"],
    "Çeşme": ["Alaçatı","Ilıca","Ovacık","Şifne","Reisdere","Üniversite","Musalla"],
    "Urla": ["Merkez","Gülbahçe","Zeytinalanı","Kuşçular","Bademler","Balıklıova"],
    "Güzelbahçe": ["Yaka","Siteler","Çamlık","Yelki"],
    "Narlıdere": ["Çatalkaya","Limanreis","Yenikale","Altıevler"],
    "Balçova": ["Merkez","Korutürk","Onur","İnciraltı"],
    "Konak": ["Alsancak","Güzelyalı","Göztepe","Karataş","Kemeraltı","Basmane"],
    "Karabağlar": ["Bahçelievler","Gülyaka","Cennetçeşme","Esenyalı"],
    "Buca": ["Kuruçeşme","Buttepe","Gediz","Yıldız","Hürriyet"],
    "Bornova": ["Kazımdirik","Erzene","Evka 3","Işıkkent","Çamdibi"],
    "Bayraklı": ["Adalet","Mansuroğlu","Anadolu","Soğukkuyu"],
    "Karşıyaka": ["Bostanlı","Mavişehir","Alaybey","Bahariye"],
    "Çiğli": ["Sasalı","Balatçık","Ataşehir","Evka 5"],
    "Menemen": ["Merkez","Asarlık","Türkelli","Seyrek"],
    "Aliağa": ["Yeni Mahalle","Kazım Dirik","Hürriyet"],
    "Foça": ["Yeni Foça","Eski Foça","Gökçealan"],
    "Dikili": ["Salihler","Bademli","Kabakum"],
    "Bergama": ["Atmaca","Bozköy","Zağnos"],
    "Kınık": ["Merkez","Poyracık"],
    "Tire": ["Derekahve","İpekçiler","Yeni Mahalle"],
    "Ödemiş": ["Mescitli","Karadoğan","Hürriyet"],
    "Kiraz": ["Irmak","Haliller","Cevizli"],
    "Beydağ": ["Atatürk","Menderes"],
    "Torbalı": ["Tepeköy","Yazıbaşı","Muratbey"],
    "Selçuk": ["İsa Bey","14 Mayıs","Zafer"],
    "Menderes": ["Gümüldür","Özdere","Tekeli"],
    "Kemalpaşa": ["Ulucak","Bağyurdu","Yukarıkızılca"]
}

ilceler = list(ilce_mahalle_map.keys())

st.markdown('<div class="card-box">', unsafe_allow_html=True)
st.markdown('<div style="font-size:18px;font-weight:700;margin-bottom:10px;color:var(--text-main);">📝 İş Detayları</div>', unsafe_allow_html=True)

col_loc1, col_loc2 = st.columns(2)
ilce_yeni = col_loc1.selectbox("İlçe", ilceler, key="ilce_yeni")
mahalle_listesi = ilce_mahalle_map.get(ilce_yeni, [])
mahalle_yeni = col_loc2.selectbox("Mahalle", mahalle_listesi, key="mahalle_yeni")

with st.form("yeni_is_form"):
    c1, c2, c3 = st.columns(3)
    tarih_yeni = c1.date_input("Tarih", value=datetime.now().date())
    musteri_yeni = c2.text_input("Müşteri")
    is_turu_yeni = c3.selectbox("İş Türü", IS_TURU_LIST)

    c4, c5, c6 = st.columns(3)
    ada_parsel_yeni = c4.text_input("Ada / Parsel")
    durum_yeni = c5.selectbox("Durum", DURUM_LIST)
    odeme_yeni = c6.selectbox("Ödeme Durumu", ["Seçiniz", "Bekliyor", "Ödendi"], index=0)

    c7, _ = st.columns([1, 3])
    ucret_yeni = c7.number_input("Ücret (₺)", min_value=0, step=100)

    submitted = st.form_submit_button("💾 İşi Kaydet")

    if submitted:
        if not musteri_yeni:
            st.warning("Müşteri adı boş bırakılamaz.")
        elif odeme_yeni == "Seçiniz":
            st.warning("Ödeme durumu seçilmelidir.")
        else:
            new_row = pd.DataFrame([{
                "Tarih": tarih_yeni,
                "Müşteri": musteri_yeni,
                "İş Türü": is_turu_yeni,
                "Ada_Parsel": ada_parsel_yeni,
                "İlçe": ilce_yeni,
                "Mahalle": mahalle_yeni,
                "Durum": durum_yeni,
                "Ödeme Durumu": odeme_yeni,
                "Ücret": ucret_yeni
            }])

            df_new = pd.concat([df, new_row], ignore_index=True)
            df_new["Tarih"] = df_new["Tarih"].astype(str)

            conn.update(worksheet="Sayfa1", data=df_new)
            st.success("✔ Yeni iş başarıyla eklendi")
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

st.subheader("📋 İş Listesi")

arama = st.text_input("🔍 Arama")
df_view = df.copy()

if "Tarih_Dt" in df_view.columns:
    df_view = df_view.drop(columns=["Tarih_Dt"])

if arama:
    df_view = df_view[
        df_view["Müşteri"].astype(str).str.contains(arama, case=False, na=False) |
        df_view["Ada_Parsel"].astype(str).str.contains(arama, case=False, na=False)
    ]

df_view["Sil"] = False

def highlight_odeme_hucre(val):
    if val == "Ödendi":
        return "background-color: #1f7a1f; color: white;"
    return ""

styled_df = df_view.style.applymap(highlight_odeme_hucre, subset=["Ödeme Durumu"])

edited = st.data_editor(
    styled_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "İş Türü": st.column_config.SelectboxColumn("İş Türü", options=IS_TURU_LIST),
        "Durum": st.column_config.SelectboxColumn("Durum", options=DURUM_LIST),
        "Ödeme Durumu": st.column_config.SelectboxColumn("Ödeme Durumu", options=["Bekliyor", "Ödendi"]),
        "Ücret": st.column_config.NumberColumn("Ücret", format="%d ₺"),
        "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
        "Ada_Parsel": st.column_config.TextColumn("Ada / Parsel"),
        "Müşteri": st.column_config.TextColumn("Müşteri"),
        "Sil": st.column_config.CheckboxColumn("🗑 Sil")
    }
)

edited_no_flag = edited.drop(columns=["Sil"])
edited_no_flag["Tarih"] = edited_no_flag["Tarih"].astype(str)

if st.button("💾 Kaydet", type="primary"):
    conn.update(worksheet="Sayfa1", data=edited_no_flag)
    st.success("Kaydedildi ✔")
    st.rerun()
