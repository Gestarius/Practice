import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import altair as alt
from datetime import datetime
import io
import xlsxwriter
import base64

st.set_page_config(
    page_title="Ödeme Paneli",
    layout="wide",
    page_icon="💰"
)

st.title("💰 Ödeme Paneli")

# ------------------------------------------------------
# GOOGLE SHEETS
# ------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Sayfa1", ttl=5)
df = df.fillna("")
df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")

# ------------------------------------------------------
# FİLTRELER
# ------------------------------------------------------
st.subheader("🔎 Filtreler")

col_yil, col_ay, col_musteri = st.columns(3)

yillar = sorted(df["Tarih"].dt.year.dropna().unique())
aylar = ["Tümü"] + [f"{i:02d}" for i in range(1, 13)]

sec_yil = col_yil.selectbox("Yıl", ["Tümü"] + list(map(str, yillar)))
sec_ay = col_ay.selectbox("Ay", aylar)
musteriler = sorted(df["Müşteri"].astype(str).unique())
sec_musteri = col_musteri.selectbox("Müşteri", ["Tümü"] + musteriler)

df_f = df.copy()

if sec_yil != "Tümü":
    df_f = df_f[df_f["Tarih"].dt.year == int(sec_yil)]

if sec_ay != "Tümü":
    df_f = df_f[df_f["Tarih"].dt.strftime("%m") == sec_ay]

if sec_musteri != "Tümü":
    df_f = df_f[df_f["Müşteri"] == sec_musteri]

# ------------------------------------------------------
# KPI
# ------------------------------------------------------
bekleyen = df_f[df_f["Ödeme Durumu"] == "Bekliyor"]
odenen = df_f[df_f["Ödeme Durumu"] == "Ödendi"]

col1, col2, col3 = st.columns(3)
col1.metric("🟡 Bekleyen Tahsilat", f"{bekleyen['Ücret'].sum():,.0f} ₺")
col2.metric("🟢 Ödenen Toplam", f"{odenen['Ücret'].sum():,.0f} ₺")
col3.metric("📦 Kayıt Sayısı", len(df_f))

st.divider()

# ------------------------------------------------------
# GRAFİK
# ------------------------------------------------------
st.subheader("📊 Aylık Gelir")

odenen["Ay"] = odenen["Tarih"].dt.to_period("M").astype(str)
aylik = odenen.groupby("Ay")["Ücret"].sum().reset_index()

if not aylik.empty:
    chart = (
        alt.Chart(aylik)
        .mark_bar(cornerRadius=6)
        .encode(
            x="Ay:N",
            y="Ücret:Q",
            tooltip=["Ay", "Ücret"],
            color=alt.Color("Ücret:Q", scale=alt.Scale(scheme="greens"))
        )
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Veri yok")

st.divider()

# ------------------------------------------------------
# TABLOLAR
# ------------------------------------------------------
st.subheader("🟡 Bekleyen Ödemeler")
st.dataframe(bekleyen, use_container_width=True)

st.subheader("🟢 Ödenmiş İşler")
st.dataframe(odenen, use_container_width=True)