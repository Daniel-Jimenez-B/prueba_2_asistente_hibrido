import streamlit as st
import pandas as pd
import altair as alt
import unicodedata
import re
import difflib
from pathlib import Path
from io import StringIO

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Dashboard Fondos",
    page_icon="💬",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main {
        background-color: #f7f9fc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e6eaf0;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e6eaf0;
    }

    .dashboard-card {
        background-color: white;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e6eaf0;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
        margin-bottom: 18px;
    }

    .subtitle {
        font-size: 18px;
        color: #475569;
        margin-bottom: 18px;
    }

    .small-note {
        font-size: 13px;
        color: #64748b;
    }
    </style>
    """,
    unsafe_allow_html=True
)

ARCHIVO_ESPERADO = Path("data/1. SIFDE_Unificados_prueba.xlsx")
CARPETA_DATOS = Path("data")

EXCLUIR_NO_ESCUELAS_EN_RANKINGS = True

VALORES_NO_ESCUELA = [
    "NIVEL CENTRAL Y OTRAS ALOCACIONES",
    "SIN ESCUELA",
    "NO APLICA",
    "N/A"
]

COLORES = [
    "#0B3D91",
    "#2563EB",
    "#06B6D4",
    "#10B981",
    "#84CC16",
    "#F59E0B",
    "#F97316",
    "#EF4444",
    "#A855F7",
    "#64748B",
    "#14B8A6",
    "#7C3AED"
]


# =========================================================
# FUNCIONES DE LIMPIEZA Y FORMATO
# =========================================================

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = texto.replace("ñ", "n")
    return texto


def limpiar_nombre_columna(columna):
    columna = limpiar_texto(columna)
    columna = re.sub(r"[^a-z0-9]+", "_", columna)
    columna = columna.strip("_")
    return columna


def convertir_numero(serie):
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").fillna(0)

    serie_limpia = (
        serie.astype(str)
        .str.strip()
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("(", "-", regex=False)
        .str.replace(")", "", regex=False)
        .replace({"": "0", "nan": "0", "None": "0"})
    )

    return pd.to_numeric(serie_limpia, errors="coerce").fillna(0)


def formatear_dinero(valor):
    """
    Formato resumido:
    1,200,000 -> $1.2 mill
    45,000 -> $45.0 mil
    """
    try:
        valor = float(valor)

        if abs(valor) >= 1_000_000:
            return f"${valor / 1_000_000:,.1f} mill"

        if abs(valor) >= 1_000:
            return f"${valor / 1_000:,.1f} mil"

        return f"${valor:,.0f}"

    except Exception:
        return "$0"


def formatear_dinero_completo(valor):
    try:
        return f"${float(valor):,.0f}"
    except Exception:
        return "$0"


def formatear_porcentaje(valor):
    try:
        return f"{float(valor):,.1f}%"
    except Exception:
        return "0.0%"


def formatear_valor(valor, medida):
    if medida == "ejecucion_pct":
        return formatear_porcentaje(valor)

    return formatear_dinero(valor)


# =========================================================
# LOCALIZAR ARCHIVO
# =========================================================

def resolver_ruta_archivo():
    if ARCHIVO_ESPERADO.exists():
        return ARCHIVO_ESPERADO

    if CARPETA_DATOS.exists():
        archivos = (
            list(CARPETA_DATOS.glob("*.xlsx")) +
            list(CARPETA_DATOS.glob("*.xls")) +
            list(CARPETA_DATOS.glob("*.csv"))
        )

        if archivos:
            return archivos[0]

    st.error(
        "No se encontró el archivo de datos. "
        "Sube el archivo a la carpeta `data` con el nombre "
        "`1. SIFDE_Unificados_prueba.xlsx`."
    )
    st.stop()


def obtener_fecha_modificacion(ruta):
    ruta = Path(ruta)
    if ruta.exists():
        return ruta.stat().st_mtime
    return 0


# =========================================================
# CARGA AUTOMÁTICA DE DATOS
# =========================================================

@st.cache_data(show_spinner="Cargando datos del dashboard de fondos...")
def cargar_datos(ruta_archivo, fecha_modificacion):
    ruta_archivo = Path(ruta_archivo)

    if ruta_archivo.suffix.lower() == ".csv":
        df = pd.read_csv(ruta_archivo, sep=None, engine="python")
    else:
        df = pd.read_excel(ruta_archivo, engine="openpyxl")

    df = df.copy()

    # Corrección por si el archivo queda como una sola columna separada por delimitadores
    if df.shape[1] == 1:
        nombre_columna_original = str(df.columns[0])
        muestra_filas = "\n".join(df.iloc[:20, 0].astype(str).tolist())
        muestra_total = nombre_columna_original + "\n" + muestra_filas

        posibles_separadores = [",", ";", "\t", "|"]
        separador_detectado = max(
            posibles_separadores,
            key=lambda sep: muestra_total.count(sep)
        )

        if muestra_total.count(separador_detectado) > 3:
            contenido = "\n".join(
                [nombre_columna_original] +
                df.iloc[:, 0].astype(str).tolist()
            )

            df = pd.read_csv(
                StringIO(contenido),
                sep=separador_detectado,
                engine="python"
            )

    df.columns = [limpiar_nombre_columna(c) for c in df.columns]

    mapa_columnas = {
        "tipo_de_fondo": "tipo_de_fondo",
        "tipo_fondo": "tipo_de_fondo",
        "fondo": "tipo_de_fondo",

        "presupuesto": "presupuesto",
        "presupuesto_asignado": "presupuesto",
        "asignado": "presupuesto",

        "ejecutado": "ejecutado",
        "presupuesto_ejecutado": "ejecutado",

        "tabla_programas_descripcion_programa": "programa_tabla",
        "descripcion_programa_project_final": "programa_project_final",
        "descripcion_programa_project_agrupado": "programa_project_agrupado",
        "descripcion_programa": "programa",

        "region_consolidado": "region",
        "region": "region",
        "ore": "region",

        "escuelas_unificados": "escuela",
        "escuela": "escuela",
        "nombre_escuela": "escuela",

        "agrupador": "agrupador"
    }

    df = df.rename(columns={c: mapa_columnas[c] for c in df.columns if c in mapa_columnas})

    columnas_requeridas = [
        "tipo_de_fondo",
        "presupuesto",
        "region",
        "escuela",
        "programa_project_final",
        "agrupador",
        "ejecutado"
    ]

    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        st.error("El archivo no tiene las columnas mínimas requeridas.")
        st.write("Columnas faltantes después de normalizar:")
        st.write(faltantes)
        st.write("Columnas detectadas:")
        st.write(list(df.columns))
        st.stop()

    if "programa_tabla" not in df.columns:
        df["programa_tabla"] = "Sin programa tabla"

    columnas_texto = [
        "tipo_de_fondo",
        "region",
        "escuela",
        "programa_project_final",
        "programa_tabla",
        "agrupador"
    ]

    for col in columnas_texto:
        df[col] = df[col].fillna(f"Sin {col}").astype(str).str.strip()
        df[col] = df[col].replace({"": f"Sin {col}", "nan": f"Sin {col}"})

    df["presupuesto"] = convertir_numero(df["presupuesto"])
    df["ejecutado"] = convertir_numero(df["ejecutado"])

    df["balance"] = df["presupuesto"] - df["ejecutado"]

    df["ejecucion_pct"] = df.apply(
        lambda row: (
            row["ejecutado"] / row["presupuesto"] * 100
            if row["presupuesto"] != 0 else 0
        ),
        axis=1
    )

    return df


# =========================================================
# FUNCIONES ANALÍTICAS
# =========================================================

def nombre_medida(medida):
    nombres = {
        "presupuesto": "presupuesto",
        "ejecutado": "ejecutado",
        "balance": "balance",
        "ejecucion_pct": "porcentaje de ejecución"
    }
    return nombres.get(medida, medida)


def detectar_medida(pregunta):
    p = limpiar_texto(pregunta)

    if "ingreso" in p or "ingresos" in p:
        return "ingresos_no_disponible"

    if "porcentaje" in p or "% ejecucion" in p or "% de ejecucion" in p:
        return "ejecucion_pct"

    if "ejecutado" in p or "ejecucion" in p:
        return "ejecutado"

    if "balance" in p or "disponible" in p or "disponibilidad" in p:
        return "balance"

    if "presupuesto" in p or "asignado" in p:
        return "presupuesto"

    return "presupuesto"


def detectar_dimension(pregunta):
    p = limpiar_texto(pregunta)

    if "region" in p or "regional" in p or "ore" in p:
        return "region"

    if "fondo" in p or "fondos" in p:
        return "tipo_de_fondo"

    if "agrupador" in p or "agrupacion" in p:
        return "agrupador"

    if "programa" in p or "project" in p or "proyecto" in p:
        return "programa_project_final"

    if "escuela" in p or "escuelas" in p or "institucion" in p:
        return "escuela"

    return None


def obtener_valores_unicos(df, columna):
    valores = (
        df[columna]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    return sorted([v for v in valores if v and v.lower() != "nan"])


def buscar_valor_en_pregunta(pregunta, valores):
    p = limpiar_texto(pregunta)

    valores_originales = valores
    valores_limpios = [limpiar_texto(v) for v in valores_originales]

    for original, limpio in zip(valores_originales, valores_limpios):
        if limpio and limpio in p:
            return original

    if len(p) < 8:
        return None

    if len(valores_limpios) > 5000:
        return None

    coincidencias = difflib.get_close_matches(
        p,
        valores_limpios,
        n=1,
        cutoff=0.75
    )

    if coincidencias:
        indice = valores_limpios.index(coincidencias[0])
        return valores_originales[indice]

    return None


def detectar_filtros(df, pregunta):
    filtros = {}

    columnas_busqueda = {
        "tipo_de_fondo": obtener_valores_unicos(df, "tipo_de_fondo"),
        "region": obtener_valores_unicos(df, "region"),
        "escuela": obtener_valores_unicos(df, "escuela"),
        "programa_project_final": obtener_valores_unicos(df, "programa_project_final"),
        "programa_tabla": obtener_valores_unicos(df, "programa_tabla"),
        "agrupador": obtener_valores_unicos(df, "agrupador")
    }

    for columna, valores in columnas_busqueda.items():
        valor = buscar_valor_en_pregunta(pregunta, valores)
        if valor:
            filtros[columna] = valor

    return filtros


def aplicar_filtros(df, filtros):
    df_filtrado = df.copy()

    for columna, valor in filtros.items():
        df_filtrado = df_filtrado[df_filtrado[columna] == valor]

    return df_filtrado


def datos_para_rankings_escuelas(df):
    if not EXCLUIR_NO_ESCUELAS_EN_RANKINGS:
        return df

    no_escuelas_limpias = [limpiar_texto(x) for x in VALORES_NO_ESCUELA]

    return df[
        ~df["escuela"].apply(lambda x: limpiar_texto(x) in no_escuelas_limpias)
    ]


def agrupar_por_dimension(df, dimension):
    resumen = (
        df.groupby(dimension, as_index=False)
        .agg(
            presupuesto=("presupuesto", "sum"),
            ejecutado=("ejecutado", "sum"),
            balance=("balance", "sum")
        )
    )

    resumen["ejecucion_pct"] = resumen.apply(
        lambda row: (
            row["ejecutado"] / row["presupuesto"] * 100
            if row["presupuesto"] != 0 else 0
        ),
        axis=1
    )

    return resumen


# =========================================================
# NAVEGACIÓN Y GLOSARIO
# =========================================================

navegacion_dashboard = {
    "distribucion del presupuesto": (
        "La distribución del presupuesto la puedes encontrar en la hoja o sección de "
        "**Resumen** del dashboard. Allí se muestra cómo se distribuye el presupuesto "
        "por fondo, región, programa o categoría, según los filtros aplicados."
    ),
    "fondos": (
        "La información de fondos se consulta en la sección **Fondos** del dashboard. "
        "También puedes usar el filtro **Tipo de fondo** para revisar fondos estatales, "
        "estatales especiales o federales."
    ),
    "escuelas": (
        "La información por escuela se encuentra en la sección **Escuelas**. "
        "Allí puedes revisar presupuesto, ejecutado y balance por institución."
    ),
    "regiones": (
        "La información por región se encuentra en la sección **Regiones**. "
        "Usa el filtro de región para revisar ARECIBO, BAYAMÓN, CAGUAS, HUMACAO, "
        "MAYAGÜEZ, PONCE, SAN JUAN u otras categorías disponibles."
    ),
    "programas": (
        "La información por programa se encuentra en la sección **Programas** o "
        "en la visual donde se agrupan los recursos por descripción de programa o project."
    ),
    "filtros": (
        "Los filtros principales suelen ubicarse en la parte superior del dashboard. "
        "Desde allí puedes seleccionar tipo de fondo, región, escuela, programa o agrupador."
    )
}


glosario = {
    "presupuesto": (
        "El presupuesto corresponde al monto asignado o autorizado para un fondo, "
        "región, escuela, programa o agrupador."
    ),
    "ejecutado": (
        "El ejecutado representa los recursos que ya fueron utilizados, comprometidos "
        "o registrados como ejecución dentro de la información disponible."
    ),
    "balance": (
        "El balance es la diferencia entre el presupuesto y el ejecutado. "
        "En términos simples, muestra cuánto presupuesto queda disponible según la información cargada."
    ),
    "tipo de fondo": (
        "El tipo de fondo permite identificar el origen o clasificación del recurso, "
        "por ejemplo estatal, estatal especial o federal."
    ),
    "agrupador": (
        "El agrupador clasifica la información en categorías generales como escuelas públicas, "
        "otros gastos, adulto y post-secundario, escuelas privadas o pensiones."
    )
}


def responder_navegacion(pregunta):
    p = limpiar_texto(pregunta)

    for tema, respuesta in navegacion_dashboard.items():
        palabras = limpiar_texto(tema).split()
        if any(palabra in p for palabra in palabras):
            return respuesta

    return None


def responder_glosario(pregunta):
    p = limpiar_texto(pregunta)

    for termino, definicion in glosario.items():
        if limpiar_texto(termino) in p:
            return definicion

    return None


# =========================================================
# RESPUESTAS Y VISUALIZACIONES
# =========================================================

def es_solicitud_grafica(pregunta):
    p = limpiar_texto(pregunta)

    palabras = [
        "grafica",
        "grafico",
        "barra",
        "barras",
        "chart",
        "visualiza",
        "visualizar",
        "muestrame",
        "mostrar",
        "distribucion",
        "top",
        "ranking",
        "tabla"
    ]

    return any(palabra in p for palabra in palabras)


def es_solicitud_navegacion(pregunta):
    p = limpiar_texto(pregunta)

    palabras = [
        "donde",
        "encuentro",
        "ubico",
        "dirijo",
        "hoja",
        "pagina",
        "pestana",
        "ver"
    ]

    return any(palabra in p for palabra in palabras)


def responder_analitica(df, pregunta):
    p = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    if medida == "ingresos_no_disponible":
        return (
            "El archivo cargado no contiene una columna de **ingresos**. "
            "Con la estructura actual puedo responder sobre presupuesto, ejecutado, balance, "
            "tipo de fondo, región, escuela, programa y agrupador."
        )

    dimension = detectar_dimension(pregunta)
    filtros = detectar_filtros(df, pregunta)

    df_filtrado = aplicar_filtros(df, filtros)

    if df_filtrado.empty:
        return (
            "No encontré datos con los filtros detectados en tu pregunta. "
            "Intenta escribir el nombre de la escuela, región, fondo o programa tal como aparece en el dashboard."
        )

    if "mayor" in p or "mas alto" in p or "mayores" in p:
        if dimension is None:
            dimension = "escuela"

        df_ranking = df_filtrado

        if dimension == "escuela":
            df_ranking = datos_para_rankings_escuelas(df_ranking)

        resumen = agrupar_por_dimension(df_ranking, dimension)
        resumen = resumen.sort_values(by=medida, ascending=False)

        if resumen.empty:
            return "No encontré datos suficientes para calcular el ranking solicitado."

        fila = resumen.iloc[0]

        return (
            f"El mayor {nombre_medida(medida)} por **{dimension}** corresponde a "
            f"**{fila[dimension]}**, con **{formatear_valor(fila[medida], medida)}**."
        )

    if "menor" in p or "mas bajo" in p:
        if dimension is None:
            dimension = "escuela"

        df_ranking = df_filtrado

        if dimension == "escuela":
            df_ranking = datos_para_rankings_escuelas(df_ranking)

        resumen = agrupar_por_dimension(df_ranking, dimension)
        resumen = resumen.sort_values(by=medida, ascending=True)

        if resumen.empty:
            return "No encontré datos suficientes para calcular el ranking solicitado."

        fila = resumen.iloc[0]

        return (
            f"El menor {nombre_medida(medida)} por **{dimension}** corresponde a "
            f"**{fila[dimension]}**, con **{formatear_valor(fila[medida], medida)}**."
        )

    if filtros:
        total = df_filtrado[medida].sum()
        detalle_filtros = ", ".join([f"{k}: {v}" for k, v in filtros.items()])

        return (
            f"Para **{detalle_filtros}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_valor(total, medida)}**."
        )

    total = df_filtrado[medida].sum()

    return (
        f"El total general de {nombre_medida(medida)} es "
        f"**{formatear_valor(total, medida)}**."
    )


def construir_visualizacion(df, pregunta):
    p = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    if medida == "ingresos_no_disponible":
        return None, (
            "El archivo cargado no contiene una columna de **ingresos**, "
            "por lo tanto no puedo generar una gráfica de ingresos."
        )

    dimension = detectar_dimension(pregunta)

    if dimension is None:
        dimension = "tipo_de_fondo"

    filtros = detectar_filtros(df, pregunta)

    filtros_para_visual = {
        k: v for k, v in filtros.items() if k != dimension
    }

    df_filtrado = aplicar_filtros(df, filtros_para_visual)

    if df_filtrado.empty:
        return None, "No encontré datos suficientes para generar la visualización."

    if dimension == "escuela":
        df_filtrado = datos_para_rankings_escuelas(df_filtrado)

    resumen = agrupar_por_dimension(df_filtrado, dimension)
    resumen = resumen.sort_values(by=medida, ascending=False)

    if dimension in ["escuela", "programa_project_final", "programa_tabla"]:
        resumen = resumen.head(10)

    tipo = "bar"

    if "torta" in p or "pastel" in p or "distribucion" in p:
        tipo = "pie"

    titulo = f"{nombre_medida(medida).capitalize()} por {dimension}"

    return {
        "tipo": tipo,
        "titulo": titulo,
        "dimension": dimension,
        "medida": medida,
        "datos": resumen.to_dict(orient="records")
    }, None


def mostrar_visualizacion(visualizacion):
    df_viz = pd.DataFrame(visualizacion["datos"])

    tipo = visualizacion["tipo"]
    titulo = visualizacion["titulo"]
    dimension = visualizacion["dimension"]
    medida = visualizacion["medida"]

    if df_viz.empty:
        st.warning("No encontré datos para mostrar.")
        return

    df_viz = df_viz.sort_values(by=medida, ascending=False).copy()

    total = df_viz[medida].sum()
    df_viz["valor_formateado"] = df_viz[medida].apply(lambda x: formatear_valor(x, medida))
    df_viz["valor_completo"] = df_viz[medida].apply(formatear_dinero_completo)

    if total != 0:
        df_viz["participacion"] = df_viz[medida] / total * 100
    else:
        df_viz["participacion"] = 0

    df_viz["participacion_txt"] = df_viz["participacion"].apply(lambda x: f"{x:,.1f}%")

    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)

    st.subheader(titulo)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=f"Total {nombre_medida(medida)}",
            value=formatear_valor(total, medida)
        )

    with col2:
        st.metric(
            label="Categorías",
            value=f"{len(df_viz):,}"
        )

    with col3:
        mayor = df_viz.iloc[0]
        st.metric(
            label="Mayor valor",
            value=formatear_valor(mayor[medida], medida)
        )

    tabla = df_viz[[dimension, "valor_formateado", "participacion_txt"]].copy()
    tabla = tabla.rename(
        columns={
            dimension: "Categoría",
            "valor_formateado": "Valor",
            "participacion_txt": "Participación"
        }
    )

    st.markdown("#### Tabla resumen")
    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Visualización")

    if tipo == "pie":
        base = alt.Chart(df_viz).encode(
            theta=alt.Theta(f"{medida}:Q", stack=True),
            color=alt.Color(
                f"{dimension}:N",
                title="Categoría",
                scale=alt.Scale(range=COLORES)
            ),
            tooltip=[
                alt.Tooltip(f"{dimension}:N", title="Categoría"),
                alt.Tooltip("valor_completo:N", title="Valor"),
                alt.Tooltip("participacion_txt:N", title="Participación")
            ]
        )

        chart = (
            base.mark_arc(innerRadius=70, outerRadius=150)
            .properties(height=430)
        )

        text = (
            base.mark_text(radius=185, size=12, fontWeight="bold")
            .encode(
                text=alt.Text("participacion_txt:N")
            )
        )

        st.altair_chart(chart + text, use_container_width=True)

    else:
        if medida == "ejecucion_pct":
            axis_expr = "format(datum.value, ',.1f') + '%'"
        else:
            axis_expr = "'$' + format(datum.value / 1000000, ',.1f') + ' mill'"

        bars = (
            alt.Chart(df_viz)
            .mark_bar(
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6
            )
            .encode(
                x=alt.X(
                    f"{medida}:Q",
                    title=nombre_medida(medida).capitalize(),
                    axis=alt.Axis(labelExpr=axis_expr)
                ),
                y=alt.Y(
                    f"{dimension}:N",
                    sort="-x",
                    title="",
                    axis=alt.Axis(labelLimit=280)
                ),
                color=alt.Color(
                    f"{dimension}:N",
                    legend=None,
                    scale=alt.Scale(range=COLORES)
                ),
                tooltip=[
                    alt.Tooltip(f"{dimension}:N", title="Categoría"),
                    alt.Tooltip("valor_completo:N", title="Valor"),
                    alt.Tooltip("participacion_txt:N", title="Participación")
                ]
            )
            .properties(height=max(380, min(720, len(df_viz) * 46)))
        )

        etiquetas = (
            alt.Chart(df_viz)
            .mark_text(
                align="left",
                baseline="middle",
                dx=6,
                fontSize=12,
                fontWeight="bold",
                color="#111827"
            )
            .encode(
                x=alt.X(f"{medida}:Q"),
                y=alt.Y(f"{dimension}:N", sort="-x"),
                text=alt.Text("valor_formateado:N")
            )
        )

        st.altair_chart(bars + etiquetas, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def generar_respuesta(df, pregunta):
    if es_solicitud_grafica(pregunta):
        visualizacion, error_visual = construir_visualizacion(df, pregunta)

        if error_visual:
            return error_visual, None

        return (
            f"Claro. Generé una tabla y una gráfica para **{visualizacion['titulo']}**.",
            visualizacion
        )

    if es_solicitud_navegacion(pregunta):
        respuesta_nav = responder_navegacion(pregunta)

        if respuesta_nav:
            return respuesta_nav, None

    respuesta_analitica = responder_analitica(df, pregunta)

    if respuesta_analitica:
        return respuesta_analitica, None

    respuesta_glosario = responder_glosario(pregunta)

    if respuesta_glosario:
        return respuesta_glosario, None

    return (
        "Por ahora no encontré una respuesta exacta. Puedes preguntarme por presupuesto, "
        "ejecutado, balance, tipo de fondo, región, escuela, programa, agrupador "
        "o pedirme una gráfica.",
        None
    )


# =========================================================
# INTERFAZ
# =========================================================

ruta_datos = resolver_ruta_archivo()

datos = cargar_datos(
    str(ruta_datos),
    obtener_fecha_modificacion(ruta_datos)
)

st.title("Dashboard Fondos")

st.markdown(
    '<p class="subtitle">Este asistente te dará las respuestas que necesitas sobre el dashboard de fondos del Departamento de Educación de Puerto Rico.</p>',
    unsafe_allow_html=True
)

st.info(
    "Versión de prueba sin IA generativa. El asistente consulta automáticamente el archivo de datos "
    "y no genera costo por consulta."
)

# Sidebar
st.sidebar.success("Datos cargados automáticamente")
st.sidebar.write(f"Archivo leído: `{ruta_datos}`")
st.sidebar.write(f"Filas cargadas: `{len(datos):,}`")
st.sidebar.write(f"Columnas cargadas: `{len(datos.columns):,}`")

with st.sidebar.expander("Resumen general"):
    presupuesto_total = datos["presupuesto"].sum()
    ejecutado_total = datos["ejecutado"].sum()
    balance_total = datos["balance"].sum()

    ejecucion_total = (
        ejecutado_total / presupuesto_total * 100
        if presupuesto_total != 0 else 0
    )

    st.write("Presupuesto total:")
    st.write(formatear_dinero(presupuesto_total))

    st.write("Ejecutado total:")
    st.write(formatear_dinero(ejecutado_total))

    st.write("Balance total:")
    st.write(formatear_dinero(balance_total))

    st.write("Ejecución total:")
    st.write(formatear_porcentaje(ejecucion_total))

with st.expander("Ver datos normalizados que usa el asistente"):
    st.dataframe(datos.head(100), use_container_width=True)

st.markdown("### Preguntas sugeridas")

preguntas_sugeridas = [
    "¿Cuál es el presupuesto total?",
    "¿Cuál es el ejecutado total?",
    "¿Cuál es el balance total?",
    "¿Cuál es la escuela con mayor presupuesto?",
    "¿Cuál es la región con mayor presupuesto?",
    "Muéstrame una gráfica de presupuesto por tipo de fondo",
    "Haz una gráfica de ejecutado por región",
    "Haz una distribución del presupuesto por agrupador",
    "Muéstrame una gráfica de presupuesto por programa",
    "¿Dónde encuentro la distribución del presupuesto?"
]

cols = st.columns(2)

for i, pregunta_sugerida in enumerate(preguntas_sugeridas):
    with cols[i % 2]:
        if st.button(pregunta_sugerida):
            st.session_state.pregunta_actual = pregunta_sugerida

if "historial" not in st.session_state:
    st.session_state.historial = [
        {
            "rol": "assistant",
            "contenido": (
                "¡Hola! Soy el asistente del Dashboard Fondos. "
                "Ya tengo cargados los datos del archivo. Puedes preguntarme por presupuesto, "
                "ejecutado, balance, tipo de fondo, región, escuela, programa, agrupador "
                "o pedirme una gráfica."
            )
        }
    ]

for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["contenido"])

        if "visualizacion" in mensaje and mensaje["visualizacion"] is not None:
            mostrar_visualizacion(mensaje["visualizacion"])

pregunta = st.chat_input("Escribe tu pregunta aquí...")

if "pregunta_actual" in st.session_state:
    pregunta = st.session_state.pregunta_actual
    del st.session_state.pregunta_actual

if pregunta:
    st.session_state.historial.append(
        {
            "rol": "user",
            "contenido": pregunta
        }
    )

    respuesta, visualizacion = generar_respuesta(datos, pregunta)

    st.session_state.historial.append(
        {
            "rol": "assistant",
            "contenido": respuesta,
            "visualizacion": visualizacion
        }
    )

    st.rerun()