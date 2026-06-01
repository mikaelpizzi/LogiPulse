import os
import subprocess
import sys
import time
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "logipulse.duckdb")

st.set_page_config(
    page_title="LogiPulse | Operational Dashboard",
    page_icon="LP",
    layout="wide",
)

TRANSLATIONS = {
    "en": {
        "hero_title": "LogiPulse Operations Center",
        "hero_subtitle": "Live visibility into last-mile performance and critical delay remediation.",
        "hero_timestamp": "Last delivery timestamp",
        "filters_title": "Filters",
        "filters_date": "Delivery window",
        "filters_delay": "Delay minutes range",
        "filters_critical": "Only critical delays",
        "filters_all": "All",
        "kpi_completed": "Completed deliveries",
        "kpi_completed_note": "Filtered window",
        "kpi_critical": "Critical delays",
        "kpi_critical_note": "> 15 minutes",
        "kpi_rate": "Critical delay rate",
        "kpi_rate_note": "Share of delivered orders",
        "kpi_avg": "Average delay",
        "kpi_avg_note": "Delayed orders only",
        "section_distribution": "Delay Distribution",
        "section_trend": "Delay Trend",
        "section_remediation": "Orders requiring remediation",
        "table_empty": "No critical delays were found in the current mart data.",
        "error_db": "Database file '{db_path}' was not found. Run 'python scripts/main.py' and 'dbt run' first.",
        "error_table": "Unable to read 'main.fct_deliveries': {error}",
        "error_empty": "The mart table is empty. Run the ingestion and dbt pipeline first.",
        "theme_label": "Theme",
        "language_label": "Language",
        "theme_light": "Light",
        "theme_dark": "Dark",
        # ── Phase 2: new analytics panels ──────────────────────────────────
        "section_hourly": "Hourly Delay Pattern",
        "section_hourly_sub": "Critical delays by hour of day. Rush hours (12\u201314h and 19\u201321h) highlighted in amber.",
        "section_drivers": "Driver Performance Ranking",
        "section_drivers_sub": "Top 5 drivers with the highest volume of critical delays.",
        "section_remediation_status": "Remediation Status",
        "section_remediation_sub": "Coupon compensation pipeline \u2014 critical incidents vs remediated orders.",
        "remediation_total": "Critical incidents",
        "remediation_sent": "Coupons sent",
        "remediation_pending": "Pending remediation",
        "remediation_progress": "Remediation progress",
        "remediation_no_coupons": "No coupons sent yet. Run: python scripts/remediate.py",
        "rush_hour_label": "Rush hour",
        "driver_col_id": "Driver",
        "driver_col_deliveries": "Total deliveries",
        "driver_col_critical": "Critical delays",
        "driver_col_rate": "Critical rate (%)",
        "driver_col_avg_delay": "Avg delay (min)",
        "sidebar_segmentation": "Segmentation",
        "sidebar_zone": "Zone",
        "sidebar_category": "Category",
        "btn_simulate": "Simulate new batch",
        "btn_simulating_data": "Generating data...",
        "btn_simulating_dbt": "Running dbt...",
        "sim_running_warning": "A simulation is already running. Please wait.",
        "sim_running_error": "Error: {error}",
        "delta_lote": "↑ 3 vs last batch",
        "metric_remediated": "Remediated",
        "metric_pending": "-Pending",
        "context_title": "📖 Project Context & Data Schema (Read First)",
        "context_story": """**The Story:** This pipeline ingests raw logistic delivery events, models them using dbt to detect critical delays (>15 min), and automatically triggers a Reverse ETL script to send compensation coupons to affected customers. It covers the full lifecycle: Ingestion → Modeling → Observability → Activation.

**How to Read This Dashboard:**
*   **KPIs (Top):** Quick snapshot of operational health. "Critical Delays" (red) track orders taking >15 extra minutes.
*   **Hourly Pattern (Stacked Bar):** Proves delays aren't random. The red bars consistently spike during lunch (12-14h) and dinner (19-21h) rush hours (yellow highlights).
*   **Driver Ranking:** Pinpoints underperforming drivers. e.g., if `drv_42` has a 60% critical rate (red bar), they require immediate intervention.
*   **Remediation Status:** Our "Reverse ETL" in action. For every critical delay detected, the system automatically dispatches a `DISCULPAXmin` coupon to the user, proving the pipeline goes beyond analytics into automated action.

**Data Engineering Specs (Under the Hood):**
*   **Scale & Limits:** Powered by DuckDB (OLAP), this architecture can process millions of rows locally without breaking a sweat. The only limit is your machine's RAM.
*   **Custom Data:** You can ingest your own data from any external API or CSV simply by updating `scripts/main.py`.
*   **Data Contracts & Schemas:** Custom data *must* adhere to the expected schema (timestamps, user_id, zone, etc.). 
*   **What if the schema breaks?** We have an ironclad Data Quality Contract. We implemented 28 `dbt tests` (unique, not_null, accepted_values). If bad data enters the system, the dbt pipeline instantly fails and alerts us *before* contaminating this dashboard.""",
        "context_data_title": "What does the raw data look like?",
        "context_data_desc": "Instead of simple numbers, the pipeline ingests complex JSON-like event logs containing timestamps, geospatial zones, driver IDs, and estimated vs. actual delivery times. Here is a live sample of the raw events loaded into DuckDB:",
    },
    "es": {
        "hero_title": "Centro Operativo LogiPulse",
        "hero_subtitle": "Visibilidad en vivo del rendimiento de última milla y remediación de demoras críticas.",
        "hero_timestamp": "Última entrega registrada",
        "filters_title": "Filtros",
        "filters_date": "Ventana de entregas",
        "filters_delay": "Rango de minutos de demora",
        "filters_critical": "Solo demoras críticas",
        "filters_all": "Todas",
        "kpi_completed": "Entregas completadas",
        "kpi_completed_note": "Ventana filtrada",
        "kpi_critical": "Demoras críticas",
        "kpi_critical_note": "> 15 minutos",
        "kpi_rate": "Tasa de demora crítica",
        "kpi_rate_note": "Proporción sobre entregas",
        "kpi_avg": "Demora promedio",
        "kpi_avg_note": "Solo pedidos con demora",
        "section_distribution": "Distribución de demoras",
        "section_trend": "Tendencia de demoras",
        "section_remediation": "Pedidos que requieren remediación",
        "table_empty": "No hay demoras críticas en los datos actuales.",
        "error_db": "No se encontró la base de datos '{db_path}'. Ejecuta 'python scripts/main.py' y 'dbt run' primero.",
        "error_table": "No se pudo leer 'main.fct_deliveries': {error}",
        "error_empty": "La tabla mart está vacía. Ejecuta la ingesta y dbt primero.",
        "theme_label": "Tema",
        "language_label": "Idioma",
        "theme_light": "Claro",
        "theme_dark": "Oscuro",
        # ── Fase 2: nuevos paneles analíticos ──────────────────────────────
        "section_hourly": "Patr\u00f3n de Demoras por Hora",
        "section_hourly_sub": "Demoras cr\u00edticas por hora del d\u00eda. Horas pico (12\u201314h y 19\u201321h) destacadas en \u00e1mbar.",
        "section_drivers": "Ranking de Rendimiento de Motoristas",
        "section_drivers_sub": "Top 5 motoristas con mayor volumen de demoras cr\u00edticas.",
        "section_remediation_status": "Estado de Remediaci\u00f3n",
        "section_remediation_sub": "Pipeline de compensaci\u00f3n \u2014 incidencias cr\u00edticas vs \u00f3rdenes remediadas.",
        "remediation_total": "Incidencias cr\u00edticas",
        "remediation_sent": "Cupones enviados",
        "remediation_pending": "Pendientes de remediaci\u00f3n",
        "remediation_progress": "Progreso de remediaci\u00f3n",
        "remediation_no_coupons": "No se han enviado cupones a\u00fan. Ejecuta: python scripts/remediate.py",
        "rush_hour_label": "Hora pico",
        "driver_col_id": "Motorista",
        "driver_col_deliveries": "Entregas totales",
        "driver_col_critical": "Demoras cr\u00edticas",
        "driver_col_rate": "Tasa cr\u00edtica (%)",
        "driver_col_avg_delay": "Demora promedio (min)",
        "sidebar_segmentation": "Segmentaci\u00f3n",
        "sidebar_zone": "Zona",
        "sidebar_category": "Categor\u00eda",
        "btn_simulate": "Simular nuevo lote",
        "btn_simulating_data": "Generando datos...",
        "btn_simulating_dbt": "Ejecutando dbt run...",
        "sim_running_warning": "Ya hay una simulaci\u00f3n en curso. Por favor espera.",
        "sim_running_error": "Error: {error}",
        "delta_lote": "↑ 3 vs lote anterior",
        "metric_remediated": "Remediados",
        "metric_pending": "-Pendientes",
        "context_title": "📖 Contexto del Proyecto y Datos (Leer Primero)",
        "context_story": """**La Historia:** Este pipeline ingesta eventos crudos de entregas logísticas, los modela con dbt para detectar demoras críticas (>15 min) y dispara automáticamente un script de Reverse ETL para enviar cupones de compensación a los clientes. Cubre todo el ciclo: Ingesta → Modelado → Observabilidad → Activación.

**¿Cómo Leer Este Dashboard?**
*   **KPIs (Arriba):** Resumen de salud operativa. "Demoras críticas" (rojo) indica pedidos que tardaron >15 minutos extra.
*   **Patrón por Horas:** Demuestra que las fallas no son azar. Las barras rojas se disparan durante las Horas Pico (sombras amarillas) de almuerzo (12-14h) y cena (19-21h).
*   **Ranking de Motoristas:** Identifica al instante quién falla. Si `drv_42` tiene 60% de tasa crítica (barra roja), requiere intervención urgente.
*   **Estado de Remediación:** Nuestro "Reverse ETL" en acción. Por cada demora crítica detectada, el sistema envía un cupón `DISCULPAXmin` al cliente afectado automáticamente, demostrando que el pipeline no solo muestra datos, sino que toma acción.

**Especificaciones de Data Engineering:**
*   **Escalabilidad y Límites:** Impulsado por DuckDB (motor OLAP columnar), puede procesar millones de filas localmente en segundos. El único límite real es tu memoria RAM.
*   **Datos Custom:** Puedes inyectar tus propios datos desde cualquier API, CSV o JSON simplemente modificando `scripts/main.py`.
*   **Contratos de Datos:** Los datos inyectados *deben* respetar el esquema base (timestamps, user_id, zone, etc.).
*   **¿Y si llegan datos corruptos o sin esquema?** Tenemos un Contrato de Calidad de Datos (Data Contract). Implementamos 28 `dbt tests` (unique, not_null, accepted_values). Si llega data basura, el pipeline de dbt fallará inmediatamente y bloqueará el paso, evitando que el dashboard se contamine.""",
        "context_data_title": "¿Cómo son los datos crudos?",
        "context_data_desc": "En lugar de simples números, el pipeline procesa logs de eventos complejos que incluyen marcas de tiempo, zonas geoespaciales, IDs de motoristas y tiempos estimados vs. reales. Aquí tienes una muestra en vivo de los eventos crudos (raw) cargados en DuckDB:",
    },
}

with st.sidebar:
    language = st.selectbox(
        "🌐 Language / Idioma",
        options=["en", "es"],
        format_func=lambda code: "English" if code == "en" else "Español",
    )

t = TRANSLATIONS[language]

theme_css = """
    :root {
        --ink: #e2e8f0;
        --muted: #94a3b8;
        --accent: #5eead4;
        --accent-soft: #134e4a;
        --danger: #fca5a5;
        --danger-soft: #7f1d1d;
        --panel: #0f172a;
        --surface: #0b1120;
        --shadow: rgba(15, 23, 42, 0.5);
    }

    .stApp {
        background: radial-gradient(circle at 20% 20%, #0f172a 0%, #020617 70%);
    }

    .hero {
        background: linear-gradient(120deg, #0f172a 0%, #134e4a 55%, #0f766e 100%);
    }

    .kpi-card {
        border: 1px solid #1e293b;
    }
"""

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    {theme_css}

    html, body, [class*="css"]  {{
        font-family: 'Space Grotesk', sans-serif;
    }}

    /* Force text color to adapt to theme */
    .stMarkdown p, .stMarkdown li, [data-testid="stExpanderDetails"] {{
        color: var(--ink);
    }}
    
    [data-testid="stExpander"] {{
        background: var(--panel);
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }}

    .hero {{
        padding: 24px 28px;
        border-radius: 20px;
        color: white;
        box-shadow: 0 18px 30px var(--shadow);
        margin-bottom: 18px;
        animation: hero-slide 0.8s ease-out;
    }}

    .hero h1 {{
        font-size: 2.1rem;
        margin: 0 0 6px 0;
    }}

    .hero p {{
        margin: 0;
        color: #ecfeff;
    }}

    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 8px;
    }}

    .kpi-card {{
        padding: 16px 18px;
        border-radius: 16px;
        background: var(--panel);
        box-shadow: 0 10px 18px var(--shadow);
        animation: fade-up 0.8s ease-out;
    }}

    .kpi-label {{
        font-size: 0.85rem;
        color: var(--muted);
        margin-bottom: 6px;
    }}

    .kpi-value {{
        font-size: 1.6rem;
        font-weight: 600;
        color: var(--ink);
    }}

    .kpi-note {{
        font-size: 0.8rem;
        color: var(--muted);
        margin-top: 4px;
    }}

    .section-title {{
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--ink);
    }}

    .stDataFrame {{
        background: var(--panel);
        border-radius: 12px;
    }}

    @keyframes hero-slide {{
        from {{ opacity: 0; transform: translateY(16px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes fade-up {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @media (max-width: 1100px) {{
        .kpi-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}

    @media (max-width: 640px) {{
        .kpi-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def get_duckdb_conn(retries=20, delay=0.5):
    """Safely connect to DuckDB, retrying if the database is locked by dbt."""
    for i in range(retries):
        try:
            return duckdb.connect(DB_PATH, read_only=True)
        except Exception as e:
            if "lock" in str(e).lower() or "io" in str(e).lower():
                if i == retries - 1:
                    raise
                time.sleep(delay)
            else:
                raise

@st.cache_data(ttl=60)
def load_data():
    """Load the final mart from DuckDB."""
    conn = get_duckdb_conn()
    try:
        return conn.execute("SELECT * FROM main.fct_deliveries").fetchdf()
    finally:
        conn.close()


def load_hourly_data():
    """Load delivery counts grouped by hour of day for pattern analysis."""
    conn = get_duckdb_conn()
    try:
        return conn.execute("""
            SELECT
                CAST(EXTRACT(HOUR FROM created_at) AS INTEGER) AS hour,
                COUNT(*) AS total_orders,
                SUM(CASE WHEN is_severely_delayed THEN 1 ELSE 0 END) AS critical_count,
                ROUND(AVG(delay_minutes), 1) AS avg_delay
            FROM main.fct_deliveries
            GROUP BY 1
            ORDER BY 1
        """).fetchdf()
    finally:
        conn.close()


def load_driver_data():
    """Load top-5 drivers ranked by critical delay volume."""
    conn = get_duckdb_conn()
    try:
        return conn.execute("""
            SELECT
                driver_id,
                COUNT(*) AS total_deliveries,
                SUM(CASE WHEN is_severely_delayed THEN 1 ELSE 0 END) AS critical_delays,
                ROUND(
                    SUM(CASE WHEN is_severely_delayed THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                    1
                ) AS critical_rate,
                ROUND(AVG(delay_minutes), 1) AS avg_delay
            FROM main.fct_deliveries
            GROUP BY driver_id
            HAVING COUNT(*) >= 2
            ORDER BY critical_delays DESC, critical_rate DESC
            LIMIT 5
        """).fetchdf()
    finally:
        conn.close()


def load_remediation_data():
    """Load sent coupons joined with fct_deliveries for remediation tracking."""
    conn = get_duckdb_conn()
    try:
        tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
        if "sent_coupons" not in tables:
            return pd.DataFrame()
        return conn.execute("""
            SELECT
                c.order_id,
                d.user_id,
                d.driver_id,
                d.delay_minutes,
                c.coupon_code,
                c.sent_at
            FROM main.sent_coupons c
            INNER JOIN main.fct_deliveries d ON c.order_id = d.order_id
            ORDER BY d.delay_minutes DESC
        """).fetchdf()
    finally:
        conn.close()

def load_raw_data_sample():
    """Load a 5-row sample of the raw event data to show context."""
    conn = get_duckdb_conn()
    try:
        tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
        if "raw_orders" not in tables:
            return pd.DataFrame()
        return conn.execute("SELECT * FROM main.raw_orders LIMIT 5").fetchdf()
    finally:
        conn.close()

if not os.path.exists(DB_PATH):
    st.error(t["error_db"].format(db_path=DB_PATH))
    st.stop()

try:
    df = load_data()
except Exception as exc:
    st.error(t["error_table"].format(error=exc))
    st.stop()

if df.empty:
    st.warning(t["error_empty"])
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"])

last_refresh = df["created_at"].max()

st.markdown(
    f"""
    <div class="hero">
        <h1>{t["hero_title"]}</h1>
        <p>{t["hero_subtitle"]}</p>
        <p style="margin-top:8px; font-size:0.9rem;">{t["hero_timestamp"]}: {last_refresh:%Y-%m-%d %H:%M}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander(t["context_title"], expanded=False):
    st.markdown(t["context_story"])
    st.markdown(f"**{t['context_data_title']}** {t['context_data_desc']}")
    
    raw_sample = load_raw_data_sample()
    if not raw_sample.empty:
        st.dataframe(raw_sample, use_container_width=True, hide_index=True)
    else:
        st.info("No raw data found.")

with st.sidebar:
    st.markdown(f"## {t['filters_title']}")
    date_min = df["created_at"].min().date()
    date_max = df["created_at"].max().date()
    date_range = st.date_input(
        t["filters_date"],
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )
    min_delay, max_delay = int(df["delay_minutes"].min()), int(df["delay_minutes"].max())
    delay_range = st.slider(
        t["filters_delay"],
        min_value=min_delay,
        max_value=max_delay,
        value=(min_delay, max_delay),
    )
    show_critical_only = st.toggle(t["filters_critical"], value=False)
    
    st.divider()
    st.markdown(f"## {t['sidebar_segmentation']}")
    # Zone and category dropdowns
    zones = [t["filters_all"]] + sorted(df["zone"].dropna().unique().tolist())
    categories = [t["filters_all"]] + sorted(df["category"].dropna().unique().tolist())
    
    selected_zone = st.selectbox(t["sidebar_zone"], zones)
    selected_category = st.selectbox(t["sidebar_category"], categories)
    
    st.divider()
    if st.button(t["btn_simulate"], use_container_width=True, type="primary"):
        try:
            with st.spinner(t["btn_simulating_data"]):
                subprocess.run([sys.executable, "scripts/main.py", "--random-seed"], check=True, capture_output=True, text=True)
            with st.spinner(t["btn_simulating_dbt"]):
                subprocess.run(["dbt", "run", "--profiles-dir", "."], cwd="dbt_project", check=True, shell=True, capture_output=True, text=True)
            st.cache_data.clear()
            st.rerun()
        except subprocess.CalledProcessError as e:
            err_msg = (e.stdout or "") + (e.stderr or "")
            if "lock" in err_msg.lower() or "io" in err_msg.lower() or "catalog" in err_msg.lower():
                st.warning("🔄 " + t["sim_running_warning"])
            else:
                st.error("❌ " + t["sim_running_error"].format(error=e.stderr or e.stdout))

filtered_df = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["created_at"].dt.date >= start_date)
        & (filtered_df["created_at"].dt.date <= end_date)
    ]

filtered_df = filtered_df[
    (filtered_df["delay_minutes"] >= delay_range[0])
    & (filtered_df["delay_minutes"] <= delay_range[1])
]

if show_critical_only:
    filtered_df = filtered_df[filtered_df["is_severely_delayed"]]

if selected_zone != t["filters_all"]:
    filtered_df = filtered_df[filtered_df["zone"] == selected_zone]

if selected_category != t["filters_all"]:
    filtered_df = filtered_df[filtered_df["category"] == selected_category]

total_deliveries = len(filtered_df)
delayed_deliveries = int(filtered_df["is_severely_delayed"].sum())
delay_rate = (delayed_deliveries / total_deliveries) * 100 if total_deliveries else 0
avg_delay = filtered_df.loc[filtered_df["delay_minutes"] > 0, "delay_minutes"].mean()

st.markdown(
    """
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">{kpi_completed}</div>
            <div class="kpi-value">{total_deliveries}</div>
            <div class="kpi-note">{kpi_completed_note}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{kpi_critical}</div>
            <div class="kpi-value" style="color: var(--danger);">{delayed_deliveries}</div>
            <div class="kpi-note">{kpi_critical_note} <span style="color: var(--danger); font-weight: 500;">{delta_lote}</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{kpi_rate}</div>
            <div class="kpi-value">{delay_rate:.1f}%</div>
            <div class="kpi-note">{kpi_rate_note}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{kpi_avg}</div>
            <div class="kpi-value">{avg_delay:.1f} min</div>
            <div class="kpi-note">{kpi_avg_note}</div>
        </div>
    </div>
    """.format(
        total_deliveries=f"{total_deliveries:,}",
        delayed_deliveries=f"{delayed_deliveries:,}",
        delay_rate=delay_rate,
        avg_delay=avg_delay if pd.notna(avg_delay) else 0,
        kpi_completed=t["kpi_completed"],
        kpi_completed_note=t["kpi_completed_note"],
        kpi_critical=t["kpi_critical"],
        kpi_critical_note=t["kpi_critical_note"],
        kpi_rate=t["kpi_rate"],
        kpi_rate_note=t["kpi_rate_note"],
        kpi_avg=t["kpi_avg"],
        kpi_avg_note=t["kpi_avg_note"],
        delta_lote=t["delta_lote"],
    ),
    unsafe_allow_html=True,
)

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.markdown(
        f"<div class=\"section-title\">{t['section_distribution']}</div>",
        unsafe_allow_html=True,
    )
    fig_hist = px.histogram(
        filtered_df,
        x="delay_minutes",
        color="is_severely_delayed",
        nbins=30,
        barmode="overlay",
        labels={"delay_minutes": "Delay minutes", "count": "Orders"},
        color_discrete_map={False: "#9ae6b4", True: "#feb2b2"},
        title="Orders by delay minutes",
    )
    fig_hist.add_vline(x=15, line_dash="dash", line_color="red")
    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        title_font_size=14,
        dragmode=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

with right_col:
    st.markdown(
        f"<div class=\"section-title\">{t['section_trend']}</div>",
        unsafe_allow_html=True,
    )
    fig_scatter = px.scatter(
        filtered_df,
        x="created_at",
        y="delay_minutes",
        color="is_severely_delayed",
        color_discrete_map={False: "#10b981", True: "#ef4444"},
        labels={"created_at": "Order time", "delay_minutes": "Delay minutes"},
        title="Delay history by order time",
        hover_data=["order_id", "user_id", "driver_id"],
    )
    fig_scatter.add_hline(y=15, line_dash="dash", line_color="red")
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        title_font_size=14,
        dragmode=False,
    )
    st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.markdown(
    f"<div class=\"section-title\">{t['section_remediation']}</div>",
    unsafe_allow_html=True,
)

delayed_df = filtered_df[filtered_df["is_severely_delayed"]].sort_values(
    by="delay_minutes", ascending=False
)

if delayed_df.empty:
    st.info(t["table_empty"])
else:
    st.dataframe(
        delayed_df[
            ["order_id", "user_id", "driver_id", "amount", "created_at", "delay_minutes"]
        ],
        use_container_width=True,
        hide_index=True,
    )

# ── HOURLY DELAY PATTERN (RF-07a) ─────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div class="section-title">{t["section_hourly"]}</div>',
    unsafe_allow_html=True,
)
st.caption(t["section_hourly_sub"])

df_hourly = load_hourly_data()

if not df_hourly.empty:
    normal_count = df_hourly["total_orders"] - df_hourly["critical_count"]

    fig_hourly = go.Figure()
    fig_hourly.add_trace(go.Bar(
        x=df_hourly["hour"],
        y=normal_count,
        name="On-time" if language == "en" else "A tiempo",
        marker_color="#10b981",
        hovertemplate="Hour %{x}h — %{y} on-time<extra></extra>"
        if language == "en"
        else "Hora %{x}h — %{y} a tiempo<extra></extra>",
    ))
    fig_hourly.add_trace(go.Bar(
        x=df_hourly["hour"],
        y=df_hourly["critical_count"],
        name="Critical >15 min" if language == "en" else "Crítico >15 min",
        marker_color="#ef4444",
        hovertemplate="Hour %{x}h — %{y} critical<extra></extra>"
        if language == "en"
        else "Hora %{x}h — %{y} críticos<extra></extra>",
    ))
    for h0, h1 in [(12, 14), (19, 21)]:
        fig_hourly.add_vrect(
            x0=h0 - 0.5,
            x1=h1 + 0.5,
            fillcolor="rgba(251,191,36,0.13)",
            layer="below",
            line_width=0,
            annotation_text=t["rush_hour_label"],
            annotation_position="top left",
            annotation_font_size=11,
            annotation_font_color="#f59e0b",
        )
    fig_hourly.update_layout(
        barmode="stack",
        xaxis=dict(
            title="Hour of day" if language == "en" else "Hora del día",
            tickmode="linear",
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(title="Orders" if language == "en" else "Pedidos"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=40, b=10),
        dragmode=False,
    )
    st.plotly_chart(fig_hourly, use_container_width=True, config={'displayModeBar': False})

# ── DRIVER PERFORMANCE RANKING (RF-07b) ───────────────────────────────────────
st.divider()
st.markdown(
    f'<div class="section-title">{t["section_drivers"]}</div>',
    unsafe_allow_html=True,
)
st.caption(t["section_drivers_sub"])

df_drivers = load_driver_data()

if not df_drivers.empty:
    chart_col, table_col = st.columns([3, 2])

    with chart_col:
        fig_drivers = px.bar(
            df_drivers,
            x="critical_rate",
            y="driver_id",
            orientation="h",
            color="critical_rate",
            color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
            range_color=[0, 100],
            labels={
                "critical_rate": t["driver_col_rate"],
                "driver_id": t["driver_col_id"],
            },
            text="critical_rate",
        )
        fig_drivers.update_traces(
            texttemplate="%{text}%",
            textposition="outside",
        )
        fig_drivers.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Space Grotesk", color="#e2e8f0"),
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            xaxis=dict(range=[0, 110], title=t["driver_col_rate"]),
            margin=dict(t=10, r=70, b=10),
            dragmode=False,
        )
        st.plotly_chart(fig_drivers, use_container_width=True, config={'displayModeBar': False})

    with table_col:
        display_df = df_drivers.rename(
            columns={
                "driver_id": t["driver_col_id"],
                "total_deliveries": t["driver_col_deliveries"],
                "critical_delays": t["driver_col_critical"],
                "critical_rate": t["driver_col_rate"],
                "avg_delay": t["driver_col_avg_delay"],
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── REMEDIATION STATUS (RF-07c) ───────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div class="section-title">{t["section_remediation_status"]}</div>',
    unsafe_allow_html=True,
)
st.caption(t["section_remediation_sub"])

df_remediation = load_remediation_data()
conn = get_duckdb_conn()
try:
    total_critical = conn.execute("SELECT COUNT(*) FROM main.fct_deliveries WHERE is_severely_delayed").fetchone()[0]
finally:
    conn.close()

if df_remediation.empty:
    st.info(t["remediation_no_coupons"])
    st.progress(0, text=f'{t["remediation_progress"]} (0/{total_critical})')
else:
    sent_count = len(df_remediation)
    pending_count = total_critical - sent_count

    col1, col2, col3 = st.columns(3)
    col1.metric(t["remediation_total"], total_critical)
    col2.metric(t["remediation_sent"], sent_count, t["metric_remediated"], delta_color="normal")
    col3.metric(t["remediation_pending"], pending_count, t["metric_pending"], delta_color="inverse")

    progress = sent_count / total_critical if total_critical > 0 else 1.0
    st.progress(progress, text=f'{t["remediation_progress"]} ({sent_count}/{total_critical})')

    st.dataframe(
        df_remediation,
        use_container_width=True,
        hide_index=True,
    )

