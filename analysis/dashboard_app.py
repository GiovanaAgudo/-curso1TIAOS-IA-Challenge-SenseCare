from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pandas as pd
import streamlit as st


# -----------------------------
# Config
# -----------------------------
st.set_page_config(layout="wide", page_title="Sense&Care – Dashboard (Sprint 3)")

PROJECT_ROOT = Path("..").resolve()
EXPORTS = PROJECT_ROOT / "analysis" / "exports"

EVENTS_CSV = EXPORTS / "events_flat.csv"
SESSIONS_CSV = EXPORTS / "session_metrics.csv"


# -----------------------------
# Helpers
# -----------------------------
def _safe_json_list(value: Any) -> List[Any]:
    """
    Converte um campo JSON (string) em lista.
    Retorna lista vazia se for NaN/None/inválido.
    """
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _parse_datetime(series: pd.Series) -> pd.Series:
    """
    Converte série para datetime com tolerância a erros.
    """
    return pd.to_datetime(series, errors="coerce", utc=True)


def _require_columns(df: pd.DataFrame, required: List[str], df_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(
            f"Arquivo '{df_name}' está sem colunas obrigatórias: {missing}. "
            f"Verifique o CSV em: {EXPORTS}"
        )
        st.stop()


@st.cache_data(show_spinner=False)
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carrega os CSVs gerados pelo ETL e prepara colunas derivadas.
    """
    if not EVENTS_CSV.exists() or not SESSIONS_CSV.exists():
        st.error(
            "Não encontrei os arquivos de exportação do ETL.\n\n"
            f"- Esperado: {EVENTS_CSV}\n"
            f"- Esperado: {SESSIONS_CSV}\n\n"
            "Execute o ETL (analysis/etl_events.ipynb) para gerar os CSVs."
        )
        st.stop()

    df_events = pd.read_csv(EVENTS_CSV)
    df_sessions = pd.read_csv(SESSIONS_CSV)

    # Validar colunas mínimas (para o que vamos usar no dashboard)
    _require_columns(
        df_events,
        required=["timestamp", "event_type", "channel", "session_id"],
        df_name="events_flat.csv",
    )
    _require_columns(
        df_sessions,
        required=["session_id", "session_start", "session_end", "channel_main", "modes_enabled", "dwell_ms", "csat_mean"],
        df_name="session_metrics.csv",
    )

    # Parse datetimes
    df_events["timestamp_dt"] = _parse_datetime(df_events["timestamp"])
    df_sessions["session_start_dt"] = _parse_datetime(df_sessions["session_start"])
    df_sessions["session_end_dt"] = _parse_datetime(df_sessions["session_end"])

    # Colunas temporais (hora e dia)
    df_events["hour"] = df_events["timestamp_dt"].dt.hour
    df_events["date"] = df_events["timestamp_dt"].dt.date

    df_sessions["hour"] = df_sessions["session_start_dt"].dt.hour
    df_sessions["date"] = df_sessions["session_start_dt"].dt.date

    # Acessibilidade habilitada? (modes_enabled lista não vazia)
    df_sessions["modes_list"] = df_sessions["modes_enabled"].apply(_safe_json_list)
    df_sessions["has_accessibility"] = df_sessions["modes_list"].apply(lambda x: len(x) > 0)

    return df_events, df_sessions


def apply_filters(
    df_events: pd.DataFrame,
    df_sessions: pd.DataFrame,
    date_range: Tuple[pd.Timestamp, pd.Timestamp],
    channel_filter: Optional[str],
    accessibility_filter: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aplica filtros de período/canal/acessibilidade.
    """
    start_dt, end_dt = date_range

    # Período (events)
    df_events_f = df_events.copy()
    df_events_f = df_events_f[df_events_f["timestamp_dt"].between(start_dt, end_dt, inclusive="both")]

    # Período (sessions)
    df_sessions_f = df_sessions.copy()
    df_sessions_f = df_sessions_f[df_sessions_f["session_start_dt"].between(start_dt, end_dt, inclusive="both")]

    # Canal
    if channel_filter and channel_filter != "Todos":
        # sessions tem channel_main; events tem channel
        df_sessions_f = df_sessions_f[df_sessions_f["channel_main"] == channel_filter]
        df_events_f = df_events_f[df_events_f["channel"] == channel_filter]

    # Acessibilidade
    if accessibility_filter == "Somente com acessibilidade":
        df_sessions_f = df_sessions_f[df_sessions_f["has_accessibility"]]
        # Para events, filtramos por session_id dessas sessões
        df_events_f = df_events_f[df_events_f["session_id"].isin(df_sessions_f["session_id"].unique())]
    elif accessibility_filter == "Somente sem acessibilidade":
        df_sessions_f = df_sessions_f[~df_sessions_f["has_accessibility"]]
        df_events_f = df_events_f[df_events_f["session_id"].isin(df_sessions_f["session_id"].unique())]

    return df_events_f, df_sessions_f


def peak_label(value: Any) -> str:
    return "-" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)


# -----------------------------
# UI – Header
# -----------------------------
st.title("Sense&Care – Dashboard de Uso (Sprint 3)")
st.markdown(
    """
Este dashboard lê os **exports do ETL** (`events_flat.csv` e `session_metrics.csv`) e apresenta:
- **KPIs** de uso (sessões, eventos, CSAT, dwell, acessibilidade)
- **Distribuições** (canais, conteúdos, modos)
- **Análises estatísticas temporais** (por hora e por dia) + **pico de uso**
"""
)

df_events, df_sessions = load_data()

# Determinar range disponível
min_dt = pd.concat([df_events["timestamp_dt"], df_sessions["session_start_dt"]]).min()
max_dt = pd.concat([df_events["timestamp_dt"], df_sessions["session_start_dt"]]).max()

if pd.isna(min_dt) or pd.isna(max_dt):
    st.error("Datas inválidas nos CSVs. Verifique colunas timestamp/session_start no ETL.")
    st.stop()

# Sidebar – filtros
st.sidebar.header("Filtros")

default_start = min_dt.to_pydatetime()
default_end = max_dt.to_pydatetime()

date_start, date_end = st.sidebar.date_input(
    "Período (UTC)",
    value=(default_start.date(), default_end.date()),
    min_value=default_start.date(),
    max_value=default_end.date(),
)

# Ajustar para timestamps completos do dia
start_dt = pd.to_datetime(date_start).tz_localize("UTC")
end_dt = pd.to_datetime(date_end).tz_localize("UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)

channels = sorted(set(df_sessions["channel_main"].dropna().unique()).union(set(df_events["channel"].dropna().unique())))
channel_filter = st.sidebar.selectbox("Canal", options=["Todos"] + channels, index=0)

accessibility_filter = st.sidebar.selectbox(
    "Acessibilidade",
    options=["Todos", "Somente com acessibilidade", "Somente sem acessibilidade"],
    index=0,
)

df_events_f, df_sessions_f = apply_filters(
    df_events=df_events,
    df_sessions=df_sessions,
    date_range=(start_dt, end_dt),
    channel_filter=channel_filter,
    accessibility_filter=accessibility_filter,
)

# -----------------------------
# KPIs
# -----------------------------
st.subheader("KPIs (Visão Geral)")

col1, col2, col3, col4, col5 = st.columns(5)

total_sessions = len(df_sessions_f)
total_events = len(df_events_f)

csat_mean = df_sessions_f["csat_mean"].mean() if total_sessions else float("nan")
dwell_mean = df_sessions_f["dwell_ms"].mean() if total_sessions else float("nan")
pct_access = df_sessions_f["has_accessibility"].mean() * 100 if total_sessions else 0.0

col1.metric("Total de sessões", total_sessions)
col2.metric("Total de eventos", total_events)
col3.metric("CSAT médio", "-" if pd.isna(csat_mean) else round(csat_mean, 2))
col4.metric("Dwell médio (ms)", "-" if pd.isna(dwell_mean) else int(dwell_mean))
col5.metric("% Sessões com acessibilidade", f"{round(pct_access, 1)}%")

st.divider()

# -----------------------------
# Distribuições (já existia, mas com filtros e robustez)
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Distribuição de Sessões por Canal")
    if total_sessions:
        st.bar_chart(df_sessions_f["channel_main"].value_counts())
    else:
        st.info("Sem sessões no período/filtro selecionado.")

with right:
    st.subheader("Top conteúdos acessados (event_type=content_selected)")
    if total_events and "payload__content_id" in df_events_f.columns:
        mask_content = df_events_f["event_type"] == "content_selected"
        df_contents = df_events_f[mask_content].copy()
        if len(df_contents):
            st.bar_chart(df_contents["payload__content_id"].value_counts())
        else:
            st.info("Sem eventos 'content_selected' no período/filtro selecionado.")
    else:
        st.info("Sem eventos no período/filtro selecionado, ou coluna payload__content_id ausente.")

st.subheader("Uso de modos de acessibilidade (por sessões)")
if total_sessions:
    rows = []
    for modes in df_sessions_f["modes_list"].tolist():
        for mode in modes:
            rows.append({"mode": mode})

    if rows:
        df_modes = pd.DataFrame(rows)
        st.bar_chart(df_modes["mode"].value_counts())
    else:
        st.info("Nenhum modo de acessibilidade habilitado nas sessões filtradas.")
else:
    st.info("Sem sessões no período/filtro selecionado.")

st.divider()

# -----------------------------
# NOVO – Análises Estatísticas Temporais + Pico de Uso
# -----------------------------
st.subheader("Análises Estatísticas Temporais (Hora/Dia) + Pico de Uso")

colA, colB = st.columns(2)

# Sessões por hora/dia
sessions_by_hour = df_sessions_f.dropna(subset=["hour"]).groupby("hour")["session_id"].count().reindex(range(24), fill_value=0)
sessions_by_day = df_sessions_f.dropna(subset=["date"]).groupby("date")["session_id"].count().sort_index()

# Eventos por hora/dia
events_by_hour = df_events_f.dropna(subset=["hour"]).groupby("hour")["id"].count().reindex(range(24), fill_value=0) if "id" in df_events_f.columns else df_events_f.dropna(subset=["hour"]).groupby("hour")["event_type"].count().reindex(range(24), fill_value=0)
events_by_day = df_events_f.dropna(subset=["date"]).groupby("date")["event_type"].count().sort_index()

# Pico de uso (hora e dia)
peak_session_hour = int(sessions_by_hour.idxmax()) if total_sessions else None
peak_session_day = sessions_by_day.idxmax() if len(sessions_by_day) else None

peak_event_hour = int(events_by_hour.idxmax()) if total_events else None
peak_event_day = events_by_day.idxmax() if len(events_by_day) else None

with colA:
    st.markdown("#### Sessões (tempo)")
    c1, c2 = st.columns(2)
    c1.metric("Pico de sessões (hora)", peak_label(peak_session_hour))
    c2.metric("Pico de sessões (dia)", peak_label(peak_session_day))

    st.caption("Sessões por hora (UTC)")
    st.bar_chart(sessions_by_hour)

    st.caption("Sessões por dia (UTC)")
    if len(sessions_by_day):
        st.line_chart(sessions_by_day)
    else:
        st.info("Sem dados suficientes para sessões por dia.")

with colB:
    st.markdown("#### Eventos (tempo)")
    c3, c4 = st.columns(2)
    c3.metric("Pico de eventos (hora)", peak_label(peak_event_hour))
    c4.metric("Pico de eventos (dia)", peak_label(peak_event_day))

    st.caption("Eventos por hora (UTC)")
    st.bar_chart(events_by_hour)

    st.caption("Eventos por dia (UTC)")
    if len(events_by_day):
        st.line_chart(events_by_day)
    else:
        st.info("Sem dados suficientes para eventos por dia.")

# (Opcional simples) – tabela “Top horas” para evidenciar pico
st.markdown("#### Top 5 Horas (ranking)")
top_hours = pd.DataFrame(
    {
        "hora_utc": range(24),
        "sessoes": sessions_by_hour.values,
        "eventos": events_by_hour.values,
    }
).sort_values(["sessoes", "eventos"], ascending=False).head(5)

st.dataframe(top_hours, use_container_width=True)

# -----------------------------
# Pico por Canal (Hora/Dia)
# -----------------------------
st.markdown("#### Pico por Canal (Hora/Dia)")

if total_sessions:
    st.markdown("##### Sessões: qual canal lidera em cada hora e em cada dia")

    # Sessões por canal e hora
    sess_ch_hour = (
        df_sessions_f.dropna(subset=["channel_main", "hour"])
        .groupby(["hour", "channel_main"])["session_id"]
        .count()
        .reset_index(name="sessions")
    )

    # Para cada hora, pegar o canal com mais sessões
    peak_sess_channel_by_hour = (
        sess_ch_hour.sort_values(["hour", "sessions"], ascending=[True, False])
        .groupby("hour")
        .head(1)
        .rename(columns={"channel_main": "peak_channel", "sessions": "peak_sessions"})
        .sort_values("hour")
    )

    # Sessões por canal e dia
    sess_ch_day = (
        df_sessions_f.dropna(subset=["channel_main", "date"])
        .groupby(["date", "channel_main"])["session_id"]
        .count()
        .reset_index(name="sessions")
    )

    # Para cada dia, pegar o canal com mais sessões
    peak_sess_channel_by_day = (
        sess_ch_day.sort_values(["date", "sessions"], ascending=[True, False])
        .groupby("date")
        .head(1)
        .rename(columns={"channel_main": "peak_channel", "sessions": "peak_sessions"})
        .sort_values("date")
    )

    cS1, cS2 = st.columns(2)

    with cS1:
        st.caption("Canal líder por hora (sessões)")
        # Mostra as 24 horas (mesmo se algumas estiverem vazias) quando possível
        st.dataframe(peak_sess_channel_by_hour, use_container_width=True)

    with cS2:
        st.caption("Canal líder por dia (sessões)")
        st.dataframe(peak_sess_channel_by_day, use_container_width=True)

    # (Opcional) Heatmap-like usando pivot (sem seaborn, só tabela)
    st.caption("Tabela: sessões por canal x hora (para evidenciar concentração)")
    sess_pivot_hour = (
        sess_ch_hour.pivot_table(index="hour", columns="channel_main", values="sessions", fill_value=0)
        .reindex(range(24), fill_value=0)
    )
    st.dataframe(sess_pivot_hour, use_container_width=True)

else:
    st.info("Sem sessões no período/filtro selecionado para calcular pico por canal.")

st.divider()

if total_events:
    st.markdown("##### Eventos: qual canal lidera em cada hora e em cada dia")

    # Eventos por canal e hora
    ev_ch_hour = (
        df_events_f.dropna(subset=["channel", "hour"])
        .groupby(["hour", "channel"])["event_type"]
        .count()
        .reset_index(name="events")
    )

    peak_ev_channel_by_hour = (
        ev_ch_hour.sort_values(["hour", "events"], ascending=[True, False])
        .groupby("hour")
        .head(1)
        .rename(columns={"channel": "peak_channel", "events": "peak_events"})
        .sort_values("hour")
    )

    # Eventos por canal e dia
    ev_ch_day = (
        df_events_f.dropna(subset=["channel", "date"])
        .groupby(["date", "channel"])["event_type"]
        .count()
        .reset_index(name="events")
    )

    peak_ev_channel_by_day = (
        ev_ch_day.sort_values(["date", "events"], ascending=[True, False])
        .groupby("date")
        .head(1)
        .rename(columns={"channel": "peak_channel", "events": "peak_events"})
        .sort_values("date")
    )

    cE1, cE2 = st.columns(2)

    with cE1:
        st.caption("Canal líder por hora (eventos)")
        st.dataframe(peak_ev_channel_by_hour, use_container_width=True)

    with cE2:
        st.caption("Canal líder por dia (eventos)")
        st.dataframe(peak_ev_channel_by_day, use_container_width=True)

    st.caption("Tabela: eventos por canal x hora (para evidenciar concentração)")
    ev_pivot_hour = (
        ev_ch_hour.pivot_table(index="hour", columns="channel", values="events", fill_value=0)
        .reindex(range(24), fill_value=0)
    )
    st.dataframe(ev_pivot_hour, use_container_width=True)

else:
    st.info("Sem eventos no período/filtro selecionado para calcular pico por canal.")

# -----------------------------
# Rodapé / evidências
# -----------------------------
with st.expander("Evidências e rastreabilidade (exports utilizados)"):
    st.write("Arquivos lidos pelo dashboard:")
    st.code(str(EVENTS_CSV))
    st.code(str(SESSIONS_CSV))
    st.write("Amostra (events):")
    st.dataframe(df_events_f.head(10), use_container_width=True)
    st.write("Amostra (sessions):")
    st.dataframe(df_sessions_f.head(10), use_container_width=True)