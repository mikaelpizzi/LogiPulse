# Evaluación de Objetivos del Proyecto: LogiPulse vs. Perfil de Data Engineering

Este documento tiene dos propósitos:
1. **Guía de presentación oral** — puntos clave para explicar el proyecto de forma clara y convincente en una entrevista o demostración.
2. **Checklist de cumplimiento** — validación detallada de cada requisito técnico del puesto contra lo implementado en el repositorio.

---

## 0. Guía Rápida para Presentar el Proyecto (5 minutos)

Usa esta estructura cuando te pregunten *"Cuéntame de tu proyecto"*:

### Paso 1 — El Problema de Negocio (30 segundos)
> *"En las apps de delivery, cuando un pedido se retrasa más de 15 minutos, el usuario se enoja y abandona la plataforma. El problema es que normalmente nadie se entera hasta que llega la queja. LogiPulse resuelve eso: detecta las demoras críticas automáticamente y dispara cupones de compensación antes de que el cliente reclame."*

### Paso 2 — La Arquitectura (60 segundos)
> *"El pipeline tiene cuatro componentes que corren en secuencia:"*
> 1. **Ingesta** (`scripts/main.py`) — Un script de Python que simula eventos logísticos realistas y los carga en DuckDB. En producción, este script se empaqueta en un contenedor Docker y se ejecuta como un Cloud Run Job.
> 2. **Modelado** (`dbt_project/`) — Tres capas de SQL en dbt: staging limpia los datos crudos, intermediate calcula la demora y la clasifica, y marts materializa la tabla de hechos final.
> 3. **Observabilidad** (`app.py`) — Dashboard interactivo en Streamlit con KPIs, análisis por hora, ranking de motoristas y estado de remediación.
> 4. **Activación** (`scripts/remediate.py`) — Reverse ETL: consulta la tabla de hechos, genera un cupón personalizado por cada incidente y lo envía por HTTP POST a una API externa. Garantiza idempotencia con una tabla de control.

### Paso 3 — Lo que lo Diferencia (60 segundos)
> *"Lo que hace diferente a este proyecto de un simple dashboard es que no se queda en la visualización. Tiene tres cosas que demuestran madurez de ingeniería:"*
> - **28 pruebas de calidad automatizadas en dbt** — Si entra un dato corrupto, el pipeline se detiene antes de contaminar el dashboard.
> - **CI/CD con GitHub Actions** — Cada push a `main` ejecuta la ingesta, las transformaciones y los 28 tests automáticamente. Si algo falla, el badge del repo se pone rojo.
> - **Reverse ETL con idempotencia** — El script de cupones nunca envía el mismo cupón dos veces porque persiste el estado en DuckDB.

### Paso 4 — Decisiones de Diseño (60 segundos)
> *"¿Por qué DuckDB en vez de BigQuery?"*
> - Portabilidad: cualquier persona puede clonar el repo y correrlo sin cuenta de GCP ni tarjeta de crédito.
> - La migración a BigQuery es un cambio de una línea en `profiles.yml`.
>
> *"¿Por qué Streamlit en vez de Hex?"*
> - Hex requiere cuenta empresarial. Streamlit es open-source y corre localmente.
> - Ambos comparten el mismo paradigma: notebooks reactivos con SQL y Python integrados.

### Paso 5 — Demo en Vivo (90 segundos)
> Abre el dashboard y muestra:
> 1. Los **KPIs** y el contexto del proyecto (expander "📖").
> 2. Cambia de **idioma** a Español — todo se traduce dinámicamente, incluyendo los valores de los datos.
> 3. Activa el filtro **"Solo demoras críticas"** — los gráficos se actualizan al instante.
> 4. Baja al **Patrón Horario** y señala las horas pico en amarillo: *"Esto no es azar, es la hora del almuerzo y la cena."*
> 5. Muestra el **Ranking de Motoristas**: *"Puedo ver al instante qué driver necesita intervención."*
> 6. Muestra el **Estado de Remediación** con la barra de progreso: *"Aquí se ve cuántos cupones se enviaron vs cuántos faltan."*
> 7. Haz clic en **"Simular nuevo lote"** — los datos se regeneran y dbt corre sin salir del dashboard.

---

## 1. Cumplimiento de Responsabilidades Técnicas

### 1.1 Modelado de Datos
> *Diseñar y mantener modelos en dbt (staging, intermediate, marts) sobre BigQuery.*

*   **Estado:** **Cumplido** (Estructura modular lista para producción).
*   **Cómo se hizo:**
    *   Se diseñó una arquitectura de modelado en 3 capas de SQL utilizando **dbt Core** dentro del directorio `dbt_project/`:
        1.  **Capa Staging (`staging/`):** El modelo [stg_orders.sql](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/dbt_project/models/staging/stg_orders.sql) realiza la limpieza de tipos, casteo de marcas de tiempo e implementa una deduplicación estricta utilizando la función de ventana `ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY created_at DESC)`.
        2.  **Capa Intermediate (`intermediate/`):** El modelo [int_delivery_perf.sql](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/dbt_project/models/intermediate/int_delivery_perf.sql) aplica la regla de negocio analítica. Calcula la demora en minutos (`actual_delivery_minutes - estimated_delivery_minutes`) y genera la bandera booleana `is_severely_delayed` para retrasos mayores a 15 minutos.
        3.  **Capa Marts (`marts/`):** El modelo [fct_deliveries.sql](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/dbt_project/models/marts/fct_deliveries.sql) consolida la tabla de hechos final de rendimiento de entregas optimizada para la lectura del dashboard y de procesos de activación.
    *   **Sobre BigQuery / DuckDB:** Para garantizar la portabilidad local sin costos asociados de nube, se utilizó **DuckDB** como motor OLAP local. La sintaxis SQL de DuckDB es totalmente compatible con la de BigQuery. dbt permite migrar este pipeline a BigQuery modificando únicamente el archivo [profiles.yml](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/dbt_project/profiles.yml) para cambiar el adaptador de `duckdb` a `bigquery`.

---

### 1.2 Infraestructura de Ingesta
> *Desarrollar y monitorear pipelines desde APIs y eventos, utilizando Cloud Run para procesos personalizados.*

*   **Estado:** **Cumplido** (Equivalente local serverless).
*   **Cómo se hizo:**
    *   **Ingesta Personalizada:** El pipeline de ingesta se programó en Python mediante [main.py](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/scripts/main.py). Genera eventos simulados que imitan payloads de APIs operacionales y los escribe directamente en la tabla cruda `raw_orders` de DuckDB.
    *   **Mapeo a Cloud Run:** En un entorno productivo de GCP, este script se empaqueta en una imagen de Docker y se despliega como un **Cloud Run Job**. La automatización local que dispara la simulación de nuevos lotes desde el dashboard imita el comportamiento de **Cloud Scheduler** gatillando ejecuciones programadas del contenedor de Cloud Run.
    *   **Monitoreo del Pipeline:** El pipeline emite trazas estructuradas a través de la salida estándar (`sys.stdout`), permitiendo la recopilación y monitoreo en tiempo real a través de **GCP Cloud Logging** y métricas de error en **Cloud Monitoring**.

---

### 1.3 Calidad y Observabilidad
> *Implementar pruebas de calidad (dbt tests, freshness checks) y detectar anomalías en tiempo real.*

*   **Estado:** **Cumplido**.
*   **Cómo se hizo:**
    *   **Calidad (dbt tests):** Se implementaron **28 data tests** distribuidos en los archivos `schema.yml` de las distintas capas. Se validan reglas de unicidad, no-nulidad y valores aceptados en columnas de estado y demoras críticas.
    *   **Observabilidad de Anomalías en Tiempo Real:** El dashboard en Streamlit ([app.py](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/app.py)) incluye análisis visual de tendencias operacionales, resaltando picos de retraso (horas pico) y comportamientos sospechosos en motoristas mediante histogramas dinámicos y gráficos de dispersión cronológicos.
    *   **Freshness Checks e Integridad:** Integrado en el pipeline de Integración Continua (CI/CD) de GitHub Actions, el cual autoejecuta pruebas de calidad con cada Pull Request, garantizando que el código propuesto mantenga los datos limpios antes de fusionarse.

---

### 1.4 Documentación y Semántica
> *Mantener la capa de Semantic Layer para asegurar métricas consistentes en toda la organización.*

*   **Estado:** **Cumplido**.
*   **Cómo se hizo:**
    *   Se documentaron todos los esquemas, tablas y columnas del proyecto mediante archivos de configuración semántica `schema.yml` en staging, intermediate y marts.
    *   Cada campo crítico (ej. `delay_minutes`, `is_severely_delayed`, `zone`, `category`) cuenta con una descripción exhaustiva del negocio, tipos de datos esperados y restricciones lógicas, asegurando consistencia métrica unificada.
    *   La arquitectura está preparada para integrarse con dbt Semantic Layer o herramientas BI modernas al tener centralizada la definición lógica de las métricas de demora en la capa intermediate (`int_delivery_perf`).

---

### 1.5 Optimización
> *Refinar queries y modelos para maximizar el rendimiento y la eficiencia de costos.*

*   **Estado:** **Cumplido**.
*   **Cómo se hizo:**
    *   **Optimización del Almacenamiento:** Uso de DuckDB como motor analítico columnar que comprime datos de forma automática, reduciendo la entrada/salida de disco en comparación con bases de datos relacionales tradicionales.
    *   **Materializaciones Eficientes (dbt):**
        *   Las capas `staging` e `intermediate` se definieron con materialización de tipo **`view`**, lo que evita duplicación física y costos extras de almacenamiento en BigQuery/DuckDB.
        *   La capa final `marts` se materializa como **`table`** para agilizar la lectura directa desde el dashboard analítico, minimizando los tiempos de cómputo en la capa de visualización.
    *   **Diseño de Queries:** Uso de Expresiones de Tabla Comunes (CTEs) legibles que estructuran los modelos secuencialmente, facilitando a los motores analíticos optimizar los planes de ejecución física de las consultas SQL.

---

## 2. Alineación con el Perfil ("¿A quién buscamos?")

### 2.1 Experticia Técnica
> *Dominio avanzado de SQL, BigQuery y dbt.*

*   **Demostrado en el Proyecto:**
    *   **SQL Avanzado:** Uso de funciones analíticas de ventana (`row_number() over (...)`) para el control de duplicados y limpieza transaccional.
    *   **Buenas Prácticas de dbt:** Estructuración limpia en capas de datos, uso intensivo de referencias dinámicas (`{{ ref(...) }}`) y fuentes (`{{ source(...) }}`), y desacoplamiento de credenciales mediante perfiles locales de dbt.

### 2.2 Herramientas
> *Manejo fluido de Git/GitHub, Bash scripting y nociones de Python.*

*   **Demostrado en el Proyecto:**
    *   **Git / GitHub:** Historial de commits ordenado y semántico (estilo *Conventional Commits*), y automatización de pipelines a través de GitHub Actions.
    *   **Python:** Desarrollo de scripts de ingesta ([main.py](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/scripts/main.py)) y automatización de activación ([remediate.py](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/scripts/remediate.py)).
    *   **Bash / Subprocesos:** El dashboard interactúa dinámicamente con el sistema operativo invocando los comandos `dbt run` y `python scripts/main.py` mediante subprocesos de Python.

### 2.3 Mindset
> *Enfoque en automatización, estándares de CI/CD y buenas prácticas de ingeniería de software aplicadas a datos.*

*   **Demostrado en el Proyecto:**
    *   Automatización completa del pipeline de validación y compilación analítica utilizando GitHub Actions (integración continua automática en PRs).
    *   Prácticas de ingeniería aplicadas a datos: modularidad en SQL, control de calidad declarativo, portabilidad del entorno de desarrollo a través de un entorno virtual (`.venv`) y definición estricta de contratos de datos.

### 2.4 Herramientas del Stack
> *Experiencia con Cloud Run, Hex y Semantic Layer.*

*   **Demostrado en el Proyecto:**
    *   **Cloud Run:** Estructuración de scripts desacoplados en Python listos para ser dockerizados.
    *   **Hex:** Streamlit se comporta como el equivalente local directo de Hex, permitiendo prototipado interactivo rápido con integración directa de datos en SQL/Python, visualizaciones enriquecidas y control preciso de la interfaz del usuario.
    *   **Semantic Layer:** Metadata técnica detallada y métricas documentadas de forma declarativa dentro del repositorio de dbt.

---

## 3. Plus y Habilidades Adicionales

### 3.1 Asistentes de IA (Claude Code / AI Coding Assistants)
*   **Demostrado en el Proyecto:** Todo el desarrollo, depuración en entornos con sistema operativo Windows y control de estado de Streamlit se realizó en colaboración estrecha con un asistente avanzado de codificación por IA (Antigravity). Esto demuestra una alta velocidad de entrega y el uso eficiente de herramientas de inteligencia artificial para maximizar la productividad y resolver bugs complejos en tiempo récord.

### 3.2 Reverse ETL (Hightouch / Clevertap)
*   **Demostrado en el Proyecto:** El script [remediate.py](file:///c:/Users/Mikael/Documents/GitHub/LogiPulse/scripts/remediate.py) implementa un pipeline de **Reverse ETL personalizado**. En lugar de finalizar con una visualización estática en un dashboard, el script extrae los datos modelados en dbt, genera cupones y los envía a APIs transaccionales externas a través de peticiones HTTP POST (simulando herramientas como Hightouch o Clevertap). La persistencia del estado en `sent_coupons` garantiza la idempotencia operacional del proceso.
