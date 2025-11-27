import json
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(layout="wide", page_title="Sense&Care – Dashboard")

PROJECT_ROOT = Path("..").resolve()
EXPORTS = PROJECT_ROOT / "analysis" / "exports"

df_events = pd.read_csv(EXPORTS / "events_flat.csv")
df_sessions = pd.read_csv(EXPORTS / "session_metrics.csv")

st.title("🟦 Sense&Care – Dashboard de Uso")
st.markdown("Sprint 2 – Análise e Visualização de Métricas")

# ---- KPIs ----
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total de sessões", len(df_sessions))
col2.metric("Total de eventos", len(df_events))
col3.metric("CSAT médio", round(df_sessions["csat_mean"].mean(),2))
col4.metric("Dwell médio (ms)", int(df_sessions["dwell_ms"].mean()))
col5.metric(
    "% Sessões com acessibilidade",
    str(round(
        df_sessions["modes_enabled"].apply(lambda x: len(json.loads(x))).gt(0).mean() * 100, 1
    )) + "%"
)

# ---- GRÁFICOS ----
st.subheader("Distribuição de Sessões por Canal")
st.bar_chart(df_sessions["channel_main"].value_counts())

st.subheader("Top conteúdos acessados")
mask_content = df_events["event_type"] == "content_selected"
df_contents = df_events[mask_content]
st.bar_chart(df_contents["payload__content_id"].value_counts())

st.subheader("Uso de modos de acessibilidade")
rows = []
for _, row in df_sessions.iterrows():
    try:
        modes = json.loads(row["modes_enabled"])
        for mode in modes:
            rows.append({"mode": mode})
    except:
        pass

df_modes = pd.DataFrame(rows)
st.bar_chart(df_modes["mode"].value_counts())
