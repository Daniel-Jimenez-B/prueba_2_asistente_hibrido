import streamlit as st
import pandas as pd
import altair as alt
import difflib
import unicodedata
import re

st.set_page_config(
    page_title="Asistente Híbrido del Dashboard Financiero",
    page_icon="💬",
    layout="wide"
)

# =========================================================
# 1. FUNCIONES DE LIMPIEZA Y CARGA DE DATOS
# =========================================================

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = texto.replace("ñ", "n")
    return texto


def limpiar_nombre_columna(col):
    col = limpiar_texto(col)
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = col.strip("_")
    return col


def formatear_dinero(valor):
    try:
        return f"${valor:,.0f}"
    except Exception:
        return "$0"


def formatear_valor(valor, medida):
    return formatear_dinero(valor)


def convertir_numero(serie):
    return (
        serie.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace({"": "0", "nan": "0", "None": "0"})
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


@st.cache_data
def cargar_archivo(archivo):
    if archivo.name.lower().endswith(".csv"):
        df = pd.read_csv(archivo)
    else:
        df = pd.read_excel(archivo, engine="openpyxl")

    df = df.copy()
    df.columns = [limpiar_nombre_columna(c) for c in df.columns]

    # Mapeo flexible de nombres de columnas
    mapa_columnas = {
        "escuelas_unificados": "escuela",
        "escuela": "escuela",
        "nombre_escuela": "escuela",
        "school": "escuela",

        "tipo_de_fondo": "tipo_de_fondo",
        "tipo_fondo": "tipo_de_fondo",
        "fondo": "tipo_de_fondo",

        "descripcion_programa_project_final": "programa",
        "descripcion_programa_project_agrupado": "programa",
        "programa": "programa",
        "project": "programa",

        "presupuesto": "presupuesto_asignado",
        "presupuesto_asignado": "presupuesto_asignado",
        "asignado": "presupuesto_asignado",

        "ejecutado": "presupuesto_ejecutado",
        "presupuesto_ejecutado": "presupuesto_ejecutado",

        "region": "region",
        "region_consolidado": "region",
        "region_educativa": "region"
    }

    df = df.rename(columns={c: mapa_columnas[c] for c in df.columns if c in mapa_columnas})

    columnas_minimas = [
        "escuela",
        "tipo_de_fondo",
        "programa",
        "presupuesto_asignado",
        "presupuesto_ejecutado"
    ]

    faltantes = [c for c in columnas_minimas if c not in df.columns]

    if faltantes:
        st.error(
            "El archivo no tiene las columnas mínimas esperadas. "
            f"Faltan estas columnas después de normalizar: {faltantes}"
        )
        st.write("Columnas detectadas en el archivo:")
        st.write(list(df.columns))
        st.stop()

    # Si no hay región, se crea columna para evitar errores
    if "region" not in df.columns:
        df["region"] = "Sin región"

    df["escuela"] = df["escuela"].astype(str).str.strip()
    df["tipo_de_fondo"] = df["tipo_de_fondo"].astype(str).str.strip()
    df["programa"] = df["programa"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip()

    df["presupuesto_asignado"] = convertir_numero(df["presupuesto_asignado"])
    df["presupuesto_ejecutado"] = convertir_numero(df["presupuesto_ejecutado"])

    # Calculamos balance y % ejecución
    df["balance"] = df["presupuesto_asignado"] - df["presupuesto_ejecutado"]

    df["ejecucion_pct"] = df.apply(
        lambda row: (row["presupuesto_ejecutado"] / row["presupuesto_asignado"] * 100)
        if row["presupuesto_asignado"] != 0 else 0,
        axis=1
    )

    return df


# =========================================================
# 2. NAVEGACIÓN DEL DASHBOARD
# =========================================================

navegacion_dashboard = {
    "distribucion del presupuesto": (
        "La distribución del presupuesto se encuentra en la hoja **Resumen financiero**. "
        "Dirígete a la parte superior izquierda del dashboard y selecciona esa hoja. "
        "Allí encontrarás el gráfico de distribución del presupuesto."
    ),
    "escuelas": (
        "La información por escuela se encuentra en la hoja **Escuelas**. "
        "Allí puedes consultar presupuesto, ejecutado y balance por institución."
    ),
    "programas": (
        "La información por programa se encuentra en la hoja **Programas** o en la sección "
        "donde se agrupan los recursos por programa o proyecto."
    ),
    "fondos": (
        "La información por tipo de fondo se encuentra en la hoja **Fondos**. "
        "También puedes usar el filtro **Tipo de fondo** para seleccionar Estatal, Federal "
        "u otro tipo disponible."
    ),
    "filtros": (
        "Los filtros principales están en la parte superior del dashboard. "
        "Desde allí puedes seleccionar año fiscal, tipo de fondo, programa, escuela "
        "u otros filtros disponibles."
    )
}


glosario = {
    "presupuesto": (
        "El presupuesto corresponde al monto asignado o autorizado para una escuela, "
        "programa o tipo de fondo."
    ),
    "ejecutado": (
        "El ejecutado representa los recursos ya utilizados o comprometidos según la información disponible."
    ),
    "balance": (
        "El balance corresponde a la diferencia entre el presupuesto asignado y el presupuesto ejecutado."
    ),
    "tipo de fondo": (
        "El tipo de fondo permite identificar el origen del recurso, por ejemplo estatal, federal o especial."
    )
}


# =========================================================
# 3. FUNCIONES DE DETECCIÓN
# =========================================================

def detectar_medida(pregunta):
    p = limpiar_texto(pregunta)

    if "ejecutado" in p or "ejecucion" in p:
        return "presupuesto_ejecutado"

    if "balance" in p or "disponible" in p or "disponibilidad" in p:
        return "balance"

    if "presupuesto" in p or "asignado" in p:
        return "presupuesto_asignado"

    return "presupuesto_asignado"


def nombre_medida(medida):
    nombres = {
        "presupuesto_asignado": "presupuesto asignado",
        "presupuesto_ejecutado": "presupuesto ejecutado",
        "balance": "balance",
        "ejecucion_pct": "porcentaje de ejecución"
    }

    return nombres.get(medida, medida)


def obtener_valores_unicos(df, columna):
    return sorted([x for x in df[columna].dropna().astype(str).unique().tolist() if x and x.lower() != "nan"])


def buscar_valor_en_pregunta(pregunta, valores, exigir_palabra=None):
    p = limpiar_texto(pregunta)

    if exigir_palabra and exigir_palabra not in p:
        return None

    valores_originales = valores
    valores_limpios = [limpiar_texto(v) for v in valores_originales]

    # Coincidencia directa
    for original, limpio in zip(valores_originales, valores_limpios):
        if limpio in p:
            return original

    # Coincidencia aproximada solo si la pregunta parece específica
    coincidencias = difflib.get_close_matches(
        p,
        valores_limpios,
        n=1,
        cutoff=0.65
    )

    if coincidencias:
        indice = valores_limpios.index(coincidencias[0])
        return valores_originales[indice]

    return None


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
        "top"
    ]

    return any(x in p for x in palabras)


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

    return any(x in p for x in palabras)


# =========================================================
# 4. RESPUESTAS ANALÍTICAS
# =========================================================

def responder_navegacion(pregunta):
    p = limpiar_texto(pregunta)

    for tema, respuesta in navegacion_dashboard.items():
        tema_limpio = limpiar_texto(tema)
        palabras = tema_limpio.split()

        if any(palabra in p for palabra in palabras):
            return respuesta

    return None


def responder_glosario(pregunta):
    p = limpiar_texto(pregunta)

    for termino, definicion in glosario.items():
        if limpiar_texto(termino) in p:
            return definicion

    return None


def responder_analitica(df, pregunta):
    p = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    escuelas = obtener_valores_unicos(df, "escuela")
    programas = obtener_valores_unicos(df, "programa")
    fondos = obtener_valores_unicos(df, "tipo_de_fondo")
    regiones = obtener_valores_unicos(df, "region")

    escuela = buscar_valor_en_pregunta(pregunta, escuelas)
    programa = buscar_valor_en_pregunta(pregunta, programas)
    fondo = buscar_valor_en_pregunta(pregunta, fondos)
    region = buscar_valor_en_pregunta(pregunta, regiones) if "Sin región" not in regiones else None

    # Mayor escuela
    if "mayor" in p and "escuela" in p:
        resumen = df.groupby("escuela", as_index=False)[medida].sum()
        fila = resumen.sort_values(by=medida, ascending=False).iloc[0]

        return (
            f"La escuela con mayor {nombre_medida(medida)} es **{fila['escuela']}**, "
            f"con **{formatear_dinero(fila[medida])}**."
        )

    # Total por escuela
    if escuela:
        total = df[df["escuela"] == escuela][medida].sum()

        return (
            f"Para la escuela **{escuela}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_dinero(total)}**."
        )

    # Total por programa
    if programa and ("programa" in p or "project" in p or "vocacional" in p or "administracion" in p):
        total = df[df["programa"] == programa][medida].sum()

        return (
            f"Para el programa **{programa}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_dinero(total)}**."
        )

    # Total por tipo de fondo
    if fondo and ("fondo" in p or "estatal" in p or "federal" in p):
        total = df[df["tipo_de_fondo"] == fondo][medida].sum()

        return (
            f"Para el tipo de fondo **{fondo}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_dinero(total)}**."
        )

    # Total por región si existe
    if region and "region" in p:
        total = df[df["region"] == region][medida].sum()

        return (
            f"Para la región **{region}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_dinero(total)}**."
        )

    # Total general
    if "total" in p:
        total = df[medida].sum()

        return (
            f"El total general de {nombre_medida(medida)} en el archivo cargado es "
            f"**{formatear_dinero(total)}**."
        )

    return None


# =========================================================
# 5. VISUALIZACIONES
# =========================================================

def construir_visualizacion(df, pregunta):
    p = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    # Top escuelas
    if "escuela" in p or "escuelas" in p:
        resumen = (
            df.groupby("escuela", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
            .head(10)
        )

        return {
            "titulo": f"Top 10 escuelas por {nombre_medida(medida)}",
            "df": resumen,
            "categoria": "escuela",
            "valor": medida
        }

    # Por programa
    if "programa" in p or "project" in p:
        resumen = (
            df.groupby("programa", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
            .head(10)
        )

        return {
            "titulo": f"Top 10 programas por {nombre_medida(medida)}",
            "df": resumen,
            "categoria": "programa",
            "valor": medida
        }

    # Por tipo de fondo
    if "fondo" in p or "fondos" in p:
        resumen = (
            df.groupby("tipo_de_fondo", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
        )

        return {
            "titulo": f"{nombre_medida(medida).capitalize()} por tipo de fondo",
            "df": resumen,
            "categoria": "tipo_de_fondo",
            "valor": medida
        }

    # Por región si existe
    if "region" in p and "region" in df.columns:
        resumen = (
            df.groupby("region", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
        )

        return {
            "titulo": f"{nombre_medida(medida).capitalize()} por región",
            "df": resumen,
            "categoria": "region",
            "valor": medida
        }

    # Si no detecta categoría, por defecto muestra fondos
    resumen = (
        df.groupby("tipo_de_fondo", as_index=False)[medida]
        .sum()
        .sort_values(by=medida, ascending=False)
    )

    return {
        "titulo": f"{nombre_medida(medida).capitalize()} por tipo de fondo",
        "df": resumen,
        "categoria": "tipo_de_fondo",
        "valor": medida
    }


def mostrar_visualizacion(obj):
    df_viz = obj["df"].copy()
    categoria = obj["categoria"]
    valor = obj["valor"]

    st.subheader(obj["titulo"])

    tabla = df_viz.copy()
    tabla["valor_formateado"] = tabla[valor].apply(formatear_dinero)

    st.dataframe(
        tabla[[categoria, "valor_formateado"]].rename(
            columns={
                categoria: "Categoría",
                "valor_formateado": "Valor"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

    chart = (
        alt.Chart(df_viz)
        .mark_bar()
        .encode(
            x=alt.X(f"{valor}:Q", title="Valor"),
            y=alt.Y(f"{categoria}:N", sort="-x", title=""),
            tooltip=[
                alt.Tooltip(f"{categoria}:N", title="Categoría"),
                alt.Tooltip(f"{valor}:Q", title="Valor", format=",.0f")
            ]
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)


def generar_respuesta(df, pregunta):
    if es_solicitud_grafica(pregunta):
        visual = construir_visualizacion(df, pregunta)

        return (
            f"Claro. Generé una tabla y una gráfica para **{visual['titulo']}**.",
            visual
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
        "ejecutado, balance, escuela, programa, tipo de fondo o pedirme una gráfica.",
        None
    )


# =========================================================
# 6. INTERFAZ STREAMLIT
# =========================================================

st.title("💬 Asistente Híbrido del Dashboard Financiero")

st.write(
    "Carga un archivo Excel o CSV exportado desde Power BI para que el asistente consulte datos reales."
)

st.info(
    "Esta versión no usa IA generativa, no requiere API Key y no genera costo por consulta."
)

archivo = st.sidebar.file_uploader(
    "Sube el archivo exportado desde Power BI",
    type=["xlsx", "csv"]
)

if archivo is None:
    st.warning("Por favor sube el archivo Excel o CSV para iniciar la prueba.")
    st.stop()

datos = cargar_archivo(archivo)

st.sidebar.success("Archivo cargado correctamente.")
st.sidebar.write(f"Filas cargadas: {len(datos):,}")
st.sidebar.write(f"Columnas disponibles: {len(datos.columns)}")

with st.expander("Ver datos normalizados que está usando el asistente"):
    st.dataframe(datos.head(100), use_container_width=True)

st.markdown("### Preguntas sugeridas")

preguntas_sugeridas = [
    "¿Cuál es el presupuesto total?",
    "¿Cuál es la escuela con mayor presupuesto?",
    "Haz una gráfica de presupuesto por escuela",
    "Haz una gráfica de ejecutado por programa",
    "Muéstrame presupuesto por tipo de fondo",
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
                "¡Hola! Soy el asistente híbrido. Ya puedes preguntarme sobre presupuesto, "
                "ejecutado, balance, escuelas, programas o tipo de fondo."
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