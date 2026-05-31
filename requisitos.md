
---

# Documento de Especificación del Sistema: LogiPulse

---

## 1. Ficha Técnica del Proyecto

*   **Nombre del Proyecto:** LogiPulse (Logistics Incident Remediation Platform)
*   **Enfoque Tecnológico:** Modern Data Stack local (libre de dependencias en la nube y geobloqueos).
*   **Lenguajes Principales:** Python 3, SQL estándar (sintaxis DuckDB/PostgreSQL).
*   **Arquitectura de Datos:** ELT (Extract, Load, Transform) local con almacenamiento analítico columnar.
*   **Control de Versiones y Automatización:** Git/GitHub y GitHub Actions.

---

## 2. Propósito y Caso de Negocio
En las plataformas de logística y entrega a domicilio, los retrasos operativos en las entregas de última milla deterioran severamente la experiencia del usuario, incrementando la tasa de abandono de la aplicación (*churn*). 

**LogiPulse** resuelve este problema mediante un proceso automatizado de tres fases:
1.  **Detección:** Capturar y persistir los eventos de entrega.
2.  **Identificación:** Modelar y clasificar qué pedidos experimentaron retrasos críticos (>15 minutos del estimado).
3.  **Remediación:** Disparar de forma automatizada un flujo de mitigación (Reverse ETL simulado) que envíe cupones de compensación a los usuarios afectados, restaurando la empatía de la marca en tiempo real.

---

## 3. Límites del Sistema (Scope)

Para garantizar un desarrollo ágil y exitoso en 24 horas, se establecen los siguientes límites estrictos:

### 3.1 Qué SÍ hará el sistema (In Scope)
*   Generar transacciones y eventos logísticos realistas mediante simulación determinista (Python).
*   Ingestar y persistir los eventos crudos de forma local en un archivo de base de datos columnar (`logipulse.duckdb`).
*   Construir transformaciones modulares con dbt Core (`stg_`, `int_`, `fct_`) aplicando buenas prácticas de modelado dimensional.
*   Garantizar la integridad de los datos mediante pruebas de unicidad, no-nulidad y consistencia de rangos (`dbt test`).
*   Automatizar las pruebas de integración de datos en cada pull request (CI/CD con GitHub Actions).
*   Proveer un tablero de control analítico local (Streamlit) para evaluar demoras, rendimiento y KPIs operativos.
*   Simular un proceso de Reverse ETL que extraiga clientes afectados de la base de datos y envíe un payload HTTP POST (cupón de descuento) a un receptor de webhooks (`Webhook.site`).

### 3.2 Qué NO hará el sistema (Out Scope)
*   No se conectará a APIs, bases de datos o sistemas de posicionamiento global (GPS) en producción real.
*   No manejará autenticación de usuarios, cifrado de credenciales de clientes o sistemas de control de acceso basados en roles (RBAC).
*   No gestionará el envío real de correos electrónicos, SMS o notificaciones push de marketing (la ejecución finaliza al enviar exitosamente el webhook).
*   No procesará streaming de datos en tiempo real de baja latencia (opera en micro-lotes gatillados por ejecuciones programadas).

---

## 4. Especificación de Requisitos

### 4.1 Requisitos Funcionales (RF)

*   **RF-01 (Simulación):** El generador de eventos en Python debe escribir registros en la tabla cruda respetando un esquema definido y simulando comportamientos de negocio lógicos (ej. picos de retraso en horas del almuerzo o cena).
*   **RF-02 (Persistencia Columnar):** El almacén de datos debe ser DuckDB para garantizar alta velocidad de consultas analíticas sobre los archivos persistidos de forma local.
*   **RF-03 (Transformación en Capas):** El pipeline de datos debe estructurarse estrictamente bajo el estándar dbt en tres capas de código SQL:
    *   **Staging:** Renombrado de columnas, casteo de tipos de datos (`timestamps`, `integers`) y filtrado inicial.
    *   **Intermediate:** Cálculo de métricas operacionales (tiempo real de entrega menos tiempo estimado de entrega).
    *   **Marts:** Generación de la tabla final de hechos (`fct_deliveries`) donde se clasifiquen los registros que cumplan con la regla de negocio de retraso crítico.
*   **RF-04 (Validación de Esquema):** Se deben compilar y ejecutar de forma automatizada las pruebas nativas de dbt para evitar fallas silenciosas en la base de datos de producción.
*   **RF-05 (Dashboard Analítico):** La interfaz en Streamlit debe leer el archivo local de DuckDB y presentar de forma visual los KPIs críticos de la operación logística.
*   **RF-06 (Activación / Reverse ETL):** El script de remediación debe consultar periódicamente la tabla final del Mart analítico, aislar a los clientes que aún no han recibido compensación, generar un código de cupón y enviar la petición HTTP POST a un endpoint externo de prueba.

### 4.2 Requisitos No Funcionales (RNF)

*   **RNF-01 (Independencia de Nube y Geobloqueos):** El sistema debe instalarse, compilarse y ejecutarse de forma 100% local en la computadora del desarrollador. No se requerirán registros en plataformas de nube pública (como GCP o AWS) que exijan tarjetas de crédito o apliquen restricciones por IP regional.
*   **RNF-02 (Costo Financiero Cero):** El stack tecnológico debe componerse exclusivamente de herramientas de código abierto o con capas de desarrollo gratuitas sin límite de tiempo.
*   **RNF-03 (Modularidad e Idempotencia):** La ejecución del pipeline de datos debe ser idempotente. Repetir la ejecución sobre los mismos datos crudos de entrada debe producir exactamente el mismo estado final en las tablas de negocio sin duplicar información.
*   **RNF-04 (Control de Calidad Automatizado):** Las transformaciones de datos deben validarse automáticamente mediante pipelines de integración continua (GitHub Actions) en cada propuesta de cambio de código (PR).

---

## 5. Arquitectura y Esquema de Datos (Data Contract)

Para evitar que tu IA genere campos aleatorios o nombres de columnas incoherentes durante el desarrollo, utilizaremos el siguiente contrato de datos estricto para cada capa del sistema:

### 5.1 Capa Cruda (DuckDB: `raw_orders`)
*Representa los datos tal y como son generados por la aplicación de delivery.*

| Campo | Tipo de Dato | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR` | Identificador único del pedido | `'ord_77fa8f89'` |
| `user_id` | `VARCHAR` | Identificador único del cliente | `'usr_412'` |
| `driver_id` | `VARCHAR` | Identificador único del motorizado | `'drv_89'` |
| `status` | `VARCHAR` | Estado del pedido (`CREATED`, `DELIVERED`, `CANCELLED`) | `'DELIVERED'` |
| `amount` | `DOUBLE` | Monto de la transacción de compra | `24.50` |
| `created_at` | `VARCHAR` | Fecha y hora de creación de la orden | `'2026-05-31T12:30:00'` |
| `estimated_delivery_minutes` | `INTEGER` | Tiempo de entrega estimado prometido al usuario | `30` |
| `actual_delivery_minutes` | `INTEGER` | Tiempo de entrega real tomado (puede ser `NULL` si no se entregó) | `48` |

### 5.2 Capa de Staging (dbt: `stg_orders.sql`)
*Limpia formatos, remueve duplicados y castea los tipos de datos crudos a tipos analíticos.*

*   **Filtros obligatorios:** `order_id IS NOT NULL`
*   **Tipos de datos esperados:**
    *   `order_id` $\rightarrow$ `VARCHAR`
    *   `user_id` $\rightarrow$ `VARCHAR`
    *   `driver_id` $\rightarrow$ `VARCHAR`
    *   `status` $\rightarrow$ `VARCHAR`
    *   `amount` $\rightarrow$ `DOUBLE`
    *   `created_at` $\rightarrow$ `TIMESTAMP` (Casteado desde texto ISO 8601)
    *   `estimated_delivery_minutes` $\rightarrow$ `INTEGER`
    *   `actual_delivery_minutes` $\rightarrow$ `INTEGER`

### 5.3 Capa Intermediate (dbt: `int_delivery_perf.sql`)
*Calcula la métrica de demoras y la bandera booleana de retraso crítico.*

*   **Regla de Negocio:**
    *   `delay_minutes` = `actual_delivery_minutes` - `estimated_delivery_minutes`
    *   `is_severely_delayed` = `TRUE` si `delay_minutes > 15`, de lo contrario `FALSE`.
    *   Solo se evalúan pedidos con `status = 'DELIVERED'` y donde `actual_delivery_minutes` no sea nulo.

### 5.4 Capa de Marts (dbt: `fct_deliveries.sql`)
*La tabla de hechos final que consume el Dashboard y el módulo de Reverse ETL.*

*   **Campos esperados:**
    *   `order_id`
    *   `user_id`
    *   `driver_id`
    *   `amount`
    *   `created_at`
    *   `delay_minutes`
    *   `is_severely_delayed`

---

# Documento de Especificación del Sistema: LogiPulse (Parte 2)

---

## 6. Estructura del Repositorio (Directory Tree)

Para mantener una arquitectura limpia y ordenada, tu repositorio local debe estructurarse de la siguiente manera. Crea esta estructura de archivos antes de inicializar el código:

```text
logipulse/
│
├── .github/
│   └── workflows/
│       └── dbt_ci.yml           # Pipeline de Integración Continua (CI/CD)
│
├── dbt_project/                 # Directorio del proyecto dbt Core
│   ├── models/
│   │   ├── staging/
│   │   │   ├── schema.yml       # Definición de fuentes y pruebas de staging
│   │   │   └── stg_orders.sql   # Capa de preparación
│   │   │
│   │   ├── intermediate/
│   │   │   └── int_delivery_perf.sql # Capa de lógica de negocio
│   │   │
│   │   └── marts/
│   │       ├── schema.yml       # Pruebas de calidad para el Mart final
│   │       └── fct_deliveries.sql # Capa de hechos finales
│   │
│   ├── dbt_project.yml          # Configuración del proyecto dbt
│   └── profiles.yml             # Conexión local dbt -> DuckDB
│
├── scripts/
│   ├── main.py                  # Generador e Ingestor de eventos (Python)
│   └── remediate.py             # Script de activación / Reverse ETL (Python)
│
├── app.py                       # Dashboard de Operaciones (Streamlit)
├── requirements.txt             # Dependencias del proyecto Python
└── .gitignore                   # Archivos omitidos (ej. base de datos local)
```

---

## 7. Guía de Instalación e Inicialización del Entorno (Local)

Ejecuta los siguientes comandos en tu terminal (en Linux, macOS o Git Bash en Windows) desde la carpeta raíz del proyecto `logipulse/`.

### 7.1 Creación del Entorno Virtual e Instalación
```bash
# 1. Crear el entorno virtual de Python
python -m venv venv

# 2. Activar el entorno virtual
# En Windows (Git Bash / Command Prompt):
source venv/Scripts/activate
# En macOS / Linux:
source venv/bin/activate

# 3. Crear el archivo requirements.txt
cat <<EOT > requirements.txt
duckdb==1.1.3
dbt-core>=1.7.0
dbt-duckdb>=1.7.0
streamlit==1.32.0
pandas>=2.0.0
requests==2.31.0
plotly==5.18.0
EOT

# 4. Instalar las dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 8. Infraestructura de Ingesta y Simulación (`scripts/main.py`)

Este script de Python creará automáticamente la base de datos local `logipulse.duckdb`, estructurará la tabla cruda `raw_orders` y generará un set de datos de prueba realista (simulando demoras pico durante las horas del almuerzo y la cena).

Crea el archivo `scripts/main.py` y pega el siguiente código:

```python
# scripts/main.py
import os
import duckdb
import random
import uuid
from datetime import datetime, timedelta

# Ruta de la base de datos local (ubicada en la raíz del proyecto)
DB_PATH = os.path.join(os.path.dirname(__file__), "../logipulse.duckdb")

def init_database():
    """Inicializa la base de datos DuckDB y crea la tabla cruda si no existe."""
    print(f"Conectando a la base de datos en: {DB_PATH}")
    conn = duckdb.connect(DB_PATH)
    
    # Crear tabla de eventos crudos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_orders (
            order_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            driver_id VARCHAR,
            status VARCHAR,
            amount DOUBLE,
            created_at VARCHAR,
            estimated_delivery_minutes INTEGER,
            actual_delivery_minutes INTEGER
        )
    """)
    conn.close()
    print("Base de datos e infraestructura de tabla inicializada con éxito.")

def generate_mock_events(num_orders=100):
    """Genera una lista de diccionarios que simulan pedidos de entrega de última milla."""
    orders = []
    base_time = datetime.now() - timedelta(days=2) # Comenzar simulación hace 2 días
    
    statuses = ["DELIVERED", "DELIVERED", "DELIVERED", "CANCELLED", "CREATED"]
    
    for i in range(num_orders):
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        user_id = f"usr_{random.randint(100, 999)}"
        driver_id = f"drv_{random.randint(10, 99)}"
        status = random.choice(statuses)
        amount = round(random.uniform(8.0, 55.0), 2)
        
        # Simular avance del tiempo para cada orden secuencial
        order_time = base_time + timedelta(minutes=random.randint(15, 1440))
        hour = order_time.hour
        
        # Regla de Negocio Simulada: Las horas pico (almuerzo 12-14 y cena 19-21) tienen más retrasos
        is_rush_hour = (12 <= hour <= 14) or (19 <= hour <= 21)
        
        estimated_delivery = random.choice([20, 30, 40, 45])
        
        if status == "DELIVERED":
            if is_rush_hour:
                # Mayor probabilidad de retrasos severos en hora pico
                actual_delivery = estimated_delivery + random.randint(5, 50)
            else:
                # Entregas mayormente normales fuera de hora pico
                actual_delivery = estimated_delivery + random.randint(-5, 12)
                # Asegurar que el tiempo real de entrega no sea menor a 10 minutos
                actual_delivery = max(10, actual_delivery)
        else:
            # Los pedidos cancelados o creados no tienen tiempo de entrega real
            actual_delivery = None
            
        orders.append((
            order_id,
            user_id,
            driver_id,
            status,
            amount,
            order_time.isoformat(),
            estimated_delivery,
            actual_delivery
        ))
    return orders

def ingest_data():
    """Genera los eventos simulados y los inserta en la base de datos DuckDB."""
    init_database()
    conn = duckdb.connect(DB_PATH)
    
    orders = generate_mock_events(200) # Generar 200 órdenes de prueba
    
    print(f"Insertando {len(orders)} órdenes simuladas en raw_orders...")
    
    # Inserción masiva en DuckDB
    conn.executemany("""
        INSERT OR REPLACE INTO raw_orders 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, orders)
    
    # Mostrar conteo actual de registros en la base de datos
    total_rows = conn.execute("SELECT COUNT(*) FROM raw_orders").fetchone()[0]
    conn.close()
    
    print(f"Ingesta completada. Filas totales en la tabla 'raw_orders': {total_rows}")

if __name__ == "__main__":
    ingest_data()
```

---

## 9. Configuración del Proyecto dbt (`dbt_project/`)

Para que dbt Core sepa cómo compilar tus modelos de SQL y dónde encontrar la base de datos local de DuckDB, configuraremos los archivos estructurales de dbt.

### 9.1 Perfil de Conexión (`dbt_project/profiles.yml`)
Este archivo le indica a dbt que utilizaremos el adaptador de DuckDB sobre el archivo local que genera el simulador.

Crea el archivo `dbt_project/profiles.yml` y pega el siguiente contenido:

```yaml
# dbt_project/profiles.yml
logipulse_profile:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "../logipulse.duckdb" # Ruta relativa a la ubicación del proyecto dbt
      schema: main
```

### 9.2 Configuración del dbt Project (`dbt_project/dbt_project.yml`)
Configura las propiedades del proyecto dbt y asócialo con el perfil de conexión.

Crea el archivo `dbt_project/dbt_project.yml` y pega el siguiente contenido:

```yaml
# dbt_project/dbt_project.yml
name: 'logipulse_transformation'
version: '1.0.0'
config-version: 2

# Enlaza con el perfil definido en profiles.yml
profile: 'logipulse_profile'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - "target"
  - "dbt_packages"

# Configuración de materialización por carpetas
models:
  logipulse_transformation:
    staging:
      +materialized: view # Staging se compila preferiblemente como vistas para ahorrar almacenamiento
    intermediate:
      +materialized: view
    marts:
      +materialized: table # El Mart de hechos se consolida como tabla física para mayor velocidad en consultas
```

---

# Documento de Especificación del Sistema: LogiPulse (Parte 3)

---

## 10. Definición de Fuentes y Capa Staging (`dbt_project/models/staging/`)

Esta capa se encarga de definir la base de datos de origen (`raw_orders` en DuckDB), renombrar columnas si fuera necesario, castear tipos de datos (como fechas en texto a tipo `timestamp`) y realizar los primeros filtros de limpieza.

### 10.1 Definición de Fuentes y Pruebas Básicas (`dbt_project/models/staging/schema.yml`)
Este archivo le indica a dbt dónde encontrar la tabla cruda que crea tu script de Python y añade pruebas de calidad básicas a nivel de staging.

Crea el archivo `dbt_project/models/staging/schema.yml` y añade el siguiente contenido:

```yaml
# dbt_project/models/staging/schema.yml
version: 2

sources:
  - name: raw_logipulse
    schema: main
    tables:
      - name: raw_orders

models:
  - name: stg_orders
    description: "Capa de preparación. Limpia, formatea y castea los eventos crudos de pedidos."
    columns:
      - name: order_id
        description: "Clave primaria del pedido."
        tests:
          - unique
          - not_null
      - name: status
        description: "Estado del pedido."
        tests:
          - accepted_values:
              values: ['CREATED', 'ASSIGNED', 'PICKED_UP', 'DELIVERED', 'CANCELLED']
```

### 10.2 Modelo de Staging (`dbt_project/models/staging/stg_orders.sql`)
Crea el archivo `dbt_project/models/staging/stg_orders.sql` con el siguiente código:

```sql
-- dbt_project/models/staging/stg_orders.sql
with source_data as (
    select * from {{ source('raw_logipulse', 'raw_orders') }}
)

select
    order_id,
    user_id,
    driver_id,
    status,
    amount,
    -- Convertir la fecha en formato texto ISO 8601 a tipo TIMESTAMP de DuckDB
    cast(created_at as timestamp) as created_at,
    estimated_delivery_minutes,
    actual_delivery_minutes
from source_data
where order_id is not null
```

---

## 11. Capa Intermediate (`dbt_project/models/intermediate/`)

En esta capa combinamos tablas y aplicamos la lógica de negocio matemática. En este caso, calcularemos la diferencia de tiempo en minutos y clasificaremos los pedidos demorados.

### 11.1 Modelo de Rendimiento de Entregas (`dbt_project/models/intermediate/int_delivery_perf.sql`)
Crea el archivo `dbt_project/models/intermediate/int_delivery_perf.sql` con el siguiente código:

```sql
-- dbt_project/models/intermediate/int_delivery_perf.sql
with staging_orders as (
    select * from {{ ref('stg_orders') }}
)

select
    order_id,
    user_id,
    driver_id,
    status,
    amount,
    created_at,
    estimated_delivery_minutes,
    actual_delivery_minutes,
    -- Regla de Negocio: Calcular retrasos únicamente para pedidos entregados con éxito
    (actual_delivery_minutes - estimated_delivery_minutes) as delay_minutes,
    -- Regla de Negocio: Si el retraso supera los 15 minutos del estimado, es un retraso crítico
    case
        when (actual_delivery_minutes - estimated_delivery_minutes) > 15 then true
        else false
    end as is_severely_delayed
from staging_orders
where status = 'DELIVERED'
  and actual_delivery_minutes is not null
```

---

## 12. Capa de Hechos Finales: Marts (`dbt_project/models/marts/`)

Esta es la capa expuesta al negocio. Los dashboards de Streamlit y el script de Reverse ETL consultarán exclusivamente esta tabla para evitar recalcular la lógica de negocio en cada consulta.

### 12.1 Modelo Final de Hechos (`dbt_project/models/marts/fct_deliveries.sql`)
Crea el archivo `dbt_project/models/marts/fct_deliveries.sql` con el siguiente código:

```sql
-- dbt_project/models/marts/fct_deliveries.sql
with delivery_performance as (
    select * from {{ ref('int_delivery_perf') }}
)

select
    order_id,
    user_id,
    driver_id,
    amount,
    created_at,
    delay_minutes,
    is_severely_delayed
from delivery_performance
```

### 12.2 Pruebas de Calidad del Mart Final (`dbt_project/models/marts/schema.yml`)
Este archivo valida la integridad de los resultados del modelo final de negocio antes de que sean consumidos por otros sistemas.

Crea el archivo `dbt_project/models/marts/schema.yml` con el siguiente contenido:

```yaml
# dbt_project/models/marts/schema.yml
version: 2

models:
  - name: fct_deliveries
    description: "Tabla de hechos final de entregas. Utilizada para analítica de demoras y activación de cupones."
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: is_severely_delayed
        tests:
          - not_null
          - accepted_values:
              values: [true, false]
```

---

## 13. Cómo Ejecutar e Interactuar con dbt Core

Una vez que tengas creados los archivos anteriores y hayas ejecutado la ingesta de datos con tu script de Python (`python scripts/main.py`), debes compilar y probar tus transformaciones en dbt.

Ejecuta estos comandos en tu terminal **desde la carpeta `dbt_project/`** (asegúrate de tener tu entorno virtual activo):

```bash
# 1. Moverse a la carpeta del proyecto dbt
cd dbt_project

# 2. Verificar la conexión a la base de datos DuckDB
dbt debug --profiles-dir .

# 3. Compilar y ejecutar las transformaciones (creará las vistas y tablas en DuckDB)
dbt run --profiles-dir .

# 4. Ejecutar las pruebas de calidad automatizadas
dbt test --profiles-dir .
```

*Nota: El parámetro `--profiles-dir .` le indica a dbt que busque el archivo `profiles.yml` directamente en la carpeta actual en lugar de buscarlo en la carpeta raíz del usuario del sistema, garantizando la portabilidad del proyecto.*

---

# Documento de Especificación del Sistema: LogiPulse (Parte 4)

---

## 14. Dashboard de Operaciones (`app.py`)

Este archivo creará una aplicación web local interactiva utilizando **Streamlit** y **Plotly**. Consumirá los datos estructurados por dbt directamente desde el archivo `logipulse.duckdb` para mostrar métricas clave del negocio y la distribución de las demoras logísticas.

Crea el archivo `app.py` en la **raíz de tu proyecto** y pega el siguiente código:

```python
# app.py
import os
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# Configuración inicial de la página de Streamlit
st.set_page_config(
    page_title="LogiPulse | Operational Dashboard",
    page_icon="📦",
    layout="wide"
)

DB_PATH = "logipulse.duckdb"

# Verificar si la base de datos existe antes de intentar conectarse
if not os.path.exists(DB_PATH):
    st.error(f"No se encontró el archivo de base de datos '{DB_PATH}'. Por favor, ejecuta primero: 'python scripts/main.py' y 'dbt run' dentro de la carpeta dbt_project.")
    st.stop()

@st.cache_data(ttl=60) # Almacenar datos en caché por 60 segundos
def load_data():
    """Conecta a DuckDB y extrae el Mart de entregas finales."""
    conn = duckdb.connect(DB_PATH)
    try:
        # Consultar la tabla final consolidada por dbt
        df = conn.execute("SELECT * FROM main.fct_deliveries").fetchdf()
    except Exception as e:
        st.error(f"Error al leer la tabla 'fct_deliveries': {e}. ¿Ejecutaste 'dbt run'?")
        st.stop()
    finally:
        conn.close()
    
    # Formatear la columna de tiempo a tipo datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

df = load_data()

# --- HEADER DEL DASHBOARD ---
st.title("📦 LogiPulse: Panel de Control de Operaciones")
st.markdown("Análisis de rendimiento y remediación automática de demoras críticas de entrega de última milla.")
st.write("---")

# --- SECCIÓN DE METRICAS CLAVE (KPIs) ---
total_deliveries = len(df)
delayed_deliveries = df['is_severely_delayed'].sum()
delay_rate = (delayed_deliveries / total_deliveries) * 100 if total_deliveries > 0 else 0
avg_delay = df[df['delay_minutes'] > 0]['delay_minutes'].mean()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Entregas exitosas", value=f"{total_deliveries:,}")
with col2:
    st.metric(label="Entregas con Retraso Crítico", value=f"{delayed_deliveries:,}", delta_color="inverse")
with col3:
    st.metric(label="Tasa de Retraso Crítico", value=f"{delay_rate:.1f}%")
with col4:
    # Si no hay retrasos, mostrar 0
    st.metric(label="Demora Promedio (Retrasados)", value=f"{avg_delay:.1f} min" if not pd.isna(avg_delay) else "0 min")

st.write("---")

# --- SECCIÓN DE GRÁFICOS INTERACTIVOS ---
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.subheader("Distribución de Tiempos de Demora")
    st.markdown("La línea punteada roja representa el umbral crítico de tolerancia (15 minutos).")
    
    # Crear histograma de demoras con Plotly
    fig_hist = px.histogram(
        df, 
        x="delay_minutes", 
        color="is_severely_delayed",
        labels={"delay_minutes": "Minutos de Demora / Adelanto", "count": "Cantidad de Pedidos"},
        color_discrete_map={False: "#a7f3d0", True: "#fecaca"}, # Colores consistentes con Excalidraw
        title="Pedidos según minutos de diferencia respecto al estimado"
    )
    fig_hist.add_vline(x=15, line_dash="dash", line_color="red", annotation_text="Umbral Crítico")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_graph2:
    st.subheader("Evolución Temporal de las Demoras")
    st.markdown("Monitoreo cronológico de los minutos de demora de cada entrega realizada.")
    
    # Crear gráfico de dispersión temporal con Plotly
    fig_scatter = px.scatter(
        df,
        x="created_at",
        y="delay_minutes",
        color="is_severely_delayed",
        color_discrete_map={False: "#10b981", True: "#ef4444"},
        labels={"created_at": "Hora del Pedido", "delay_minutes": "Minutos de Demora"},
        title="Historial cronológico de entregas"
    )
    fig_scatter.add_hline(y=15, line_dash="dash", line_color="red")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.write("---")

# --- SECCIÓN DE DETALLE DE INCIDENTES ---
st.subheader("Filtro Operativo: Pedidos Afectados para Remediación")
st.markdown("Listado detallado de clientes con demoras superiores a 15 minutos que requieren atención prioritaria:")

# Mostrar tabla filtrada solo con los pedidos críticos
df_delayed = df[df['is_severely_delayed'] == True].sort_values(by="delay_minutes", ascending=False)
st.dataframe(
    df_delayed[["order_id", "user_id", "driver_id", "amount", "created_at", "delay_minutes"]],
    use_container_width=True,
    hide_index=True
)
```

---

## 15. Pipeline de Integración Continua (`.github/workflows/dbt_ci.yml`)

Este flujo de trabajo se ejecutará de forma automática en los servidores gratuitos de GitHub cada vez que tú o la IA abran un *Pull Request* o suban cambios a la rama principal. 

Simulará la base de datos de forma temporal, compilará dbt y ejecutará las pruebas de validación. Si escribiste una consulta SQL inválida o si los datos generados rompen una prueba de unicidad o nulidad, el flujo de GitHub fallará, bloqueando la integración y evitando fallas en producción.

Crea el archivo `.github/workflows/dbt_ci.yml` y pega el siguiente código:

```yaml
# .github/workflows/dbt_ci.yml
name: LogiPulse CI Pipeline

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  run_data_tests:
    runs-on: ubuntu-latest

    steps:
      # 1. Descargar el código del repositorio
      - name: Checkout Repository
        uses: actions/checkout@v3

      # 2. Configurar el entorno de Python
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      # 3. Instalar las dependencias del proyecto
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # 4. Ejecutar la ingesta para crear la base de datos DuckDB de prueba
      - name: Generate Mock Database for Testing
        run: |
          python scripts/main.py

      # 5. Ejecutar la validación de dbt Core
      - name: Run and Test dbt Models
        run: |
          cd dbt_project
          # Verificar configuración de perfiles
          dbt debug --profiles-dir .
          # Compilar todos los modelos (staging, intermediate, marts)
          dbt run --profiles-dir .
          # Ejecutar las pruebas de aserción y calidad de datos
          dbt test --profiles-dir .
```

---

## 16. Cómo Ejecutar el Dashboard Localmente

Para levantar el servidor local de Streamlit y ver el panel interactivo en tu navegador web, ejecuta el siguiente comando en tu terminal **desde la carpeta raíz de tu proyecto** `logipulse/`:

```bash
# Asegúrate de tener el entorno virtual activo (venv)
streamlit run app.py
```

Streamlit abrirá de forma automática una pestaña en tu navegador, usualmente en la dirección `http://localhost:8501`, mostrando la visualización de los datos que procesaste con dbt Core.

---

# Documento de Especificación del Sistema: LogiPulse (Parte 5)

---

## 17. Módulo de Activación y Remediación (`scripts/remediate.py`)

Este módulo simula la función de una herramienta de Reverse ETL (como Hightouch). Se conecta a la base de datos `logipulse.duckdb`, busca las entregas con retraso crítico de la tabla `fct_deliveries`, genera cupones personalizados y los envía vía HTTP POST a un sistema de marketing externo (representado por Webhook.site).

Para garantizar el requisito de **idempotencia (RNF-03)**, el script crea una tabla de control local llamada `sent_coupons`. Si un cupón es enviado con éxito, el sistema lo registra y nunca volverá a procesarlo, garantizando que el usuario final reciba una sola compensación por cada incidencia.

Crea el archivo `scripts/remediate.py` y añade el siguiente código:

```python
# scripts/remediate.py
import os
import duckdb
import requests
from datetime import datetime

# Ruta de la base de datos local
DB_PATH = os.path.join(os.path.dirname(__file__), "../logipulse.duckdb")

# Obtener la URL de destino de la variable de entorno
WEBHOOK_URL = os.environ.get("LOGIPULSE_WEBHOOK_URL")

def init_remediation_table(conn):
    """Crea la tabla de control de cupones enviados si no existe para asegurar idempotencia."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS main.sent_coupons (
            order_id VARCHAR PRIMARY KEY,
            sent_at VARCHAR,
            coupon_code VARCHAR
        )
    """)

def run_remediation():
    """Ejecuta el pipeline de Reverse ETL hacia la API de marketing."""
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en '{DB_PATH}'.")
        print("Asegúrate de ejecutar primero: 'python scripts/main.py' y 'dbt run'.")
        return

    if not WEBHOOK_URL:
        print("AVISO: No se detectó la variable de entorno 'LOGIPULSE_WEBHOOK_URL'.")
        print("El script se ejecutará en modo 'SIMULACIÓN' (imprimiendo los cupones en consola).")
        print("Para realizar envíos reales, configura la variable en tu terminal.")
        print("Ejemplo: export LOGIPULSE_WEBHOOK_URL='https://webhook.site/tu-codigo-unico'\n")

    conn = duckdb.connect(DB_PATH)
    init_remediation_table(conn)

    # Consulta de Control de Calidad / Idempotencia: 
    # Solo seleccionamos registros marcados como retraso crítico que NO existan en la tabla de enviados.
    query = """
        SELECT d.order_id, d.user_id, d.delay_minutes
        FROM main.fct_deliveries d
        LEFT JOIN main.sent_coupons c ON d.order_id = c.order_id
        WHERE d.is_severely_delayed = TRUE
          AND c.order_id IS NULL
    """
    
    try:
        pending_incidents = conn.execute(query).fetchall()
    except Exception as e:
        print(f"Error al consultar el Mart final: {e}")
        print("Por favor, ejecuta 'dbt run' antes de correr este script.")
        conn.close()
        return

    if not pending_incidents:
        print("No se encontraron nuevos incidentes que requieran remediación.")
        conn.close()
        return

    print(f"Se encontraron {len(pending_incidents)} incidentes nuevos sin procesar.")

    for order_id, user_id, delay_minutes in pending_incidents:
        # Lógica de Negocio: Generar un código de cupón único y proporcional a la demora
        coupon_code = f"DISCULPA{delay_minutes}MIN"
        
        # Estructura del Payload que recibirá la API externa de marketing (Clevertap)
        payload = {
            "event_type": "operational_delay_remediation",
            "user_id": user_id,
            "order_id": order_id,
            "delay_minutes": int(delay_minutes),
            "coupon_code": coupon_code,
            "processed_at": datetime.utcnow().isoformat()
        }

        success = True
        
        # Envío HTTP POST si el Webhook está configurado
        if WEBHOOK_URL:
            try:
                response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
                # Webhook.site devuelve HTTP 200 cuando recibe datos exitosamente
                if response.status_code in [200, 201]:
                    print(f"✓ Cupón {coupon_code} enviado con éxito para el pedido {order_id} (Usuario {user_id}).")
                else:
                    print(f"✗ Error al enviar petición para el pedido {order_id}. Código HTTP: {response.status_code}")
                    success = False
            except Exception as ex:
                print(f"✗ Falla de red al intentar conectar con la API de destino para el pedido {order_id}: {ex}")
                success = False
        else:
            # Modo Simulación (Impresión local por consola)
            print(f"[SIMULADO] Alerta enviada: Cupón {coupon_code} generado para el usuario {user_id}.")

        # Si el envío fue exitoso, se registra en la tabla de control
        if success:
            conn.execute("""
                INSERT INTO main.sent_coupons (order_id, sent_at, coupon_code)
                VALUES (?, ?, ?)
            """, (order_id, datetime.utcnow().isoformat(), coupon_code))

    conn.close()
    print("\nProceso de Reverse ETL y mitigación operacional completado.")

if __name__ == "__main__":
    run_remediation()
```

---

## 18. Prueba del Pipeline de Datos Extremo a Extremo (E2E)

Una vez que tengas todos los componentes del sistema codificados, puedes probar todo el flujo de datos unificado ejecutando esta secuencia de comandos en tu terminal **desde la raíz de tu proyecto**:

```bash
# Paso 1: Generar nuevos datos simulados e ingresarlos en DuckDB
python scripts/main.py

# Paso 2: Compilar y correr las transformaciones de dbt Core
cd dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..

# Paso 3: Configurar tu webhook de destino de forma opcional
# (Ingresa a https://webhook.site/ en tu navegador, copia tu URL única y configúrala)
export LOGIPULSE_WEBHOOK_URL="https://webhook.site/tu-codigo-unico"

# Paso 4: Ejecutar la remediación automatizada de incidencias (Reverse ETL)
python scripts/remediate.py

# Paso 5: Levantar el Dashboard para visualizar los resultados
streamlit run app.py
```

*Si visitas tu pestaña de Webhook.site después de ejecutar el Paso 4, verás las peticiones entrantes con los datos de los usuarios afectados y sus cupones de disculpa generados automáticamente.*

---

## 19. Instrucciones para utilizar este documento con tu IA asistente (como Claude Code)

Para levantar este proyecto en pocas horas con el apoyo de tu asistente de inteligencia artificial, puedes inicializar tu sesión de desarrollo copiando este mensaje de contexto:

> **PROMPT DE INICIO DE CONTEXTO:**
> *"Hola. Estoy construyendo un proyecto llamado **LogiPulse** de forma 100% local, utilizando Python, dbt Core con DuckDB (`dbt-duckdb`) y Streamlit para la visualización. Tengo una especificación detallada del proyecto que consta de requisitos funcionales, un contrato de datos estricto de BigQuery/DuckDB y toda la estructura de archivos en un documento de ingeniería de software estructurado en 5 partes.
> 
> Quiero que actúes como un Ingeniero de Datos Senior con excelente conocimiento de buenas prácticas de desarrollo. Te iré proporcionando los requerimientos de cada archivo y de cada fase para que me ayudes a desarrollarlos, resolver posibles bugs locales y documentar el repositorio de forma óptima. Confírmame si estás listo para recibir el código base para comenzar a trabajar en el proyecto."*

---

¡Felicidades! Tienes en tus manos la especificación de ingeniería completa de **LogiPulse**. Este proyecto cubre cada una de las necesidades técnicas y operacionales del perfil solicitado en la vacante de Yummy, asegurando un entorno de ejecución robusto, 100% accesible y de costo cero.
---

## 1. Estructura de un Commit Profesional (Conventional Commits)

El estándar dicta que cada mensaje de commit debe seguir una estructura clara que permita automatizar registros y que cualquier desarrollador entienda el cambio de un vistazo.

### El Formato
```text
<tipo>(<alcance>): <descripción corta en minúsculas y en presente>
```

*   **`<tipo>` (Type):** Define qué tipo de cambio estás introduciendo. Los más comunes son:
    *   `feat`: Una nueva característica o funcionalidad (ej. crear el simulador).
    *   `fix`: Solución a un error o bug en el código.
    *   `refactor`: Cambios en el código que no corrigen un error ni añaden una funcionalidad, sino que mejoran su estructura o legibilidad.
    *   `test`: Añadir o modificar pruebas de calidad (como los archivos `schema.yml` de dbt).
    *   `docs`: Cambios exclusivos en la documentación (como el `README.md`).
    *   `chore`: Tareas de mantenimiento que no afectan el código de producción (instalar librerías en `requirements.txt`, actualizar `.gitignore`).
*   **`<alcance>` (Scope - Opcional):** El módulo específico que estás modificando. En **LogiPulse** tus alcances lógicos serían: `ingest`, `dbt`, `dash` (Streamlit), `ci` (GitHub Actions) o `remediate`.
*   **`<descripción>`:** Una explicación breve del cambio. Se escribe en **presente e imperativo** (como si fuera una orden: *"add"* en lugar de *"added"*, o *"añadir"* en lugar de *"añadido"*), sin punto al final.

### Ejemplos reales para tu proyecto LogiPulse:
*   `chore(env): add project dependencies to requirements`
*   `feat(ingest): implement python script for database simulation`
*   `feat(dbt): create staging and intermediate sql models`
*   `test(dbt): add uniqueness and non-null tests to schema`
*   `feat(dash): build streamlit operational dashboard`
*   `fix(dash): resolve database connection lock on refresh`
*   `docs(readme): add system architecture diagram and setup guide`

---

## 2. Frecuencia: ¿Cada cuánto hacer un commit? (Commits Atómicos)

El principio profesional es el de **Commit Atómico**: *Cada commit debe representar un único cambio lógico que funcione.*

### La regla de oro:
**Nunca acumules el trabajo de todo el día para subirlo en un solo commit gigante.** Si haces eso y algo falla, revertir el error sin dañar el resto del código es sumamente complejo. Tampoco debes subir commits con código roto que no compile o no pase las pruebas.

### Cuándo debes hacer un commit durante tu desarrollo:
Debes hacer un commit cada vez que completes una pequeña "unidad de trabajo" que sea funcional. Siguiendo tu plan de 24 horas, deberías hacer un commit en estos momentos exactos:

1.  **Al iniciar:** Creas `requirements.txt` y `.gitignore` $\rightarrow$ *Commit.*
2.  **Ingesta:** Escribes `scripts/main.py` y genera datos exitosamente en la consola $\rightarrow$ *Commit.*
3.  **Configuración dbt:** Inicializas dbt y configuras `profiles.yml` $\rightarrow$ *Commit.*
4.  **Modelado:** Escribes `stg_orders.sql` y compila bien con `dbt run` $\rightarrow$ *Commit.*
5.  **Lógica:** Escribes `int_delivery_perf.sql` y `fct_deliveries.sql` y corren bien $\rightarrow$ *Commit.*
6.  **Calidad:** Creas los archivos `schema.yml` y las pruebas pasan con `dbt test` $\rightarrow$ *Commit.*
7.  **Dashboard:** Terminas la primera versión funcional del dashboard de Streamlit $\rightarrow$ *Commit.*
8.  **Activación:** Terminas el script de Reverse ETL y envía el primer webhook con éxito $\rightarrow$ *Commit.*

### Malas prácticas que debes evitar (Red Flags para reclutadores):
*   Mensajes vagos como `"fix"`, `"cambios"`, `"update"` o `"un error corregido"`.
*   Commits gigantescos donde modificaste 15 archivos de módulos totalmente diferentes al mismo tiempo.
*   Dejar un commit a medias con código que no ejecuta, obligándote a hacer otro commit inmediatamente después llamado `"ahora sí funciona"`.
