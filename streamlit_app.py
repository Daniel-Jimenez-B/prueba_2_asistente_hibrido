import streamlit as st
import pandas as pd
import altair as alt
import unicodedata
import re
import difflib
from pathlib import Path

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Asistente Híbrido del Dashboard Financiero",
    page_icon="💬",
    layout="wide"
)

RUTA_EXCEL = Path("data/prueba_global.xlsx")


# =========================================================
# FUNCIONES DE LIMPIEZA
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
    """
    Convierte columnas numéricas exportadas desde Power BI.
    Maneja valores con $, comas, espacios y porcentajes.
    """
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
    try:
        return f"${valor:,.0f}"
    except Exception:
        return "$0"


def formatear_porcentaje(valor):
    try:
        return f"{valor:,.1f}%"
    except Exception:
        return "0.0%"


def formatear_valor(valor, medida):
    if medida == "ejecucion_pct":
        return formatear_porcentaje(valor)
    return formatear_dinero(valor)


# =========================================================
# CARGA AUTOMÁTICA DEL EXCEL
# =========================================================

@st.cache_data(show_spinner="Cargando datos del archivo Excel...")
def cargar_datos_automatico(ruta_excel, fecha_modificacion):
    ruta_excel = Path(ruta_excel)

    if not ruta_excel.exists():
        st.error(
            f"No se encontró el archivo en la ruta: {ruta_excel}. "
            "Verifica que el archivo esté dentro de la carpeta data."
        )
        st.stop()

    df = pd.read_excel(ruta_excel, engine="openpyxl")

    df = df.copy()
    df.columns = [limpiar_nombre_columna(c) for c in df.columns]

    # Mapeo flexible de columnas exportadas desde Power BI
    mapa_columnas = {
        "tipo_de_fondo": "tipo_de_fondo",
        "tipo_fondo": "tipo_de_fondo",
        "fondo": "tipo_de_fondo",

        "descripcion_programa_project_final": "programa",
        "descripcion_programa_project_agrupado": "programa",
        "descripcion_programa": "programa",
        "programa": "programa",
        "project": "programa",

        "ejecutado": "presupuesto_ejecutado",
        "presupuesto_ejecutado": "presupuesto_ejecutado",

        "presupuesto": "presupuesto_asignado",
        "presupuesto_asignado": "presupuesto_asignado",
        "asignado": "presupuesto_asignado",

        "escuelas_unificados": "escuela",
        "escuela": "escuela",
        "nombre_escuela": "escuela",
        "school": "escuela",

        "region": "region",
        "region_consolidado": "region",
        "region_educativa": "region",
        "ore": "region",

        "ingresos": "ingresos",
        "ingreso": "ingresos",
        "ingresos_totales": "ingresos"
    }

    df = df.rename(columns={c: mapa_columnas[c] for c in df.columns if c in mapa_columnas})

    columnas_minimas = [
        "tipo_de_fondo",
        "programa",
        "presupuesto_asignado",
        "presupuesto_ejecutado",
        "escuela"
    ]

    faltantes = [c for c in columnas_minimas if c not in df.columns]

    if faltantes:
        st.error("El archivo no tiene las columnas mínimas requeridas.")
        st.write("Columnas faltantes:")
        st.write(faltantes)
        st.write("Columnas detectadas en el archivo:")
        st.write(list(df.columns))
        st.stop()

    # Si no existe región, se crea para evitar errores.
    # En este archivo de prueba no viene región.
    if "region" not in df.columns:
        df["region"] = "Sin región"

    # Si no existe ingresos, no la inventamos. La dejamos como no disponible.
    if "ingresos" not in df.columns:
        df["ingresos"] = pd.NA

    # Limpieza de texto
    df["tipo_de_fondo"] = df["tipo_de_fondo"].astype(str).str.strip()
    df["programa"] = df["programa"].astype(str).str.strip()
    df["escuela"] = df["escuela"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip()

    # Limpieza numérica
    df["presupuesto_asignado"] = convertir_numero(df["presupuesto_asignado"])
    df["presupuesto_ejecutado"] = convertir_numero(df["presupuesto_ejecutado"])

    if df["ingresos"].isna().all():
        df["ingresos_disponible"] = False
        df["ingresos"] = 0
    else:
        df["ingresos_disponible"] = True
        df["ingresos"] = convertir_numero(df["ingresos"])

    # Métricas calculadas
    df["balance"] = df["presupuesto_asignado"] - df["presupuesto_ejecutado"]

    df["ejecucion_pct"] = df.apply(
        lambda row: (
            row["presupuesto_ejecutado"] / row["presupuesto_asignado"] * 100
            if row["presupuesto_asignado"] != 0 else 0
        ),
        axis=1
    )

    # Eliminar filas totalmente vacías en escuela o programa
    df = df[df["escuela"].notna()]
    df = df[df["escuela"].astype(str).str.strip() != ""]
    df = df[df["escuela"].astype(str).str.lower() != "nan"]

    return df


def obtener_fecha_modificacion(ruta):
    if ruta.exists():
        return ruta.stat().st_mtime
    return 0


# =========================================================
# CARGA DE DATOS
# =========================================================

datos = cargar_datos_automatico(
    str(RUTA_EXCEL),
    obtener_fecha_modificacion(RUTA_EXCEL)
)


# =========================================================
# NAVEGACIÓN Y GLOSARIO
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
    ),
    "programa": (
        "El programa o project permite clasificar los recursos según el destino presupuestario o funcional."
    )
}


# =========================================================
# FUNCIONES DE DETECCIÓN
# =========================================================

def obtener_valores_unicos(df, columna):
    valores = (
        df[columna]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    valores = [v for v in valores if v and v.lower() != "nan"]
    return sorted(valores)


def buscar_valor_en_pregunta(pregunta, valores):
    pregunta_limpia = limpiar_texto(pregunta)

    valores_originales = valores
    valores_limpios = [limpiar_texto(v) for v in valores_originales]

    # Coincidencia directa
    for original, limpio in zip(valores_originales, valores_limpios):
        if limpio and limpio in pregunta_limpia:
            return original

    # Coincidencia aproximada solo para textos relativamente largos
    if len(pregunta_limpia) < 8:
        return None

    coincidencias = difflib.get_close_matches(
        pregunta_limpia,
        valores_limpios,
        n=1,
        cutoff=0.72
    )

    if coincidencias:
        indice = valores_limpios.index(coincidencias[0])
        return valores_originales[indice]

    return None


def detectar_medida(pregunta):
    p = limpiar_texto(pregunta)

    if "ingreso" in p or "ingresos" in p:
        if datos["ingresos_disponible"].any():
            return "ingresos"
        return "ingresos_no_disponible"

    if "ejecucion" in p and ("%" in p or "porcentaje" in p):
        return "ejecucion_pct"

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
        "ejecucion_pct": "porcentaje de ejecución",
        "ingresos": "ingresos",
        "ingresos_no_disponible": "ingresos"
    }

    return nombres.get(medida, medida)


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
        "ranking"
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


# =========================================================
# RESPUESTAS DE NAVEGACIÓN Y GLOSARIO
# =========================================================

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
# RESPUESTAS ANALÍTICAS
# =========================================================

def responder_analitica(df, pregunta):
    p = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    if medida == "ingresos_no_disponible":
        return (
            "El archivo cargado no contiene una columna de **ingresos**. "
            "Con la estructura actual puedo responder sobre presupuesto, ejecutado, balance, "
            "escuelas, programas y tipo de fondo."
        )

    escuelas = obtener_valores_unicos(df, "escuela")
    programas = obtener_valores_unicos(df, "programa")
    fondos = obtener_valores_unicos(df, "tipo_de_fondo")
    regiones = obtener_valores_unicos(df, "region")

    escuela = buscar_valor_en_pregunta(pregunta, escuelas)
    programa = buscar_valor_en_pregunta(pregunta, programas)
    fondo = buscar_valor_en_pregunta(pregunta, fondos)

    region = None
    if not (len(regiones) == 1 and regiones[0] == "Sin región"):
        region = buscar_valor_en_pregunta(pregunta, regiones)

    # Si preguntan por región y el archivo no tiene región real
    if "region" in p and region is None and "Sin región" in regiones:
        return (
            "El archivo cargado no contiene una columna de **región**. "
            "Por ahora puedo responder por escuela, programa y tipo de fondo."
        )

    # Escuela con mayor medida
    if "mayor" in p and "escuela" in p:
        resumen = (
            df.groupby("escuela", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
        )

        fila = resumen.iloc[0]

        return (
            f"La escuela con mayor {nombre_medida(medida)} es **{fila['escuela']}**, "
            f"con **{formatear_valor(fila[medida], medida)}**."
        )

    # Programa con mayor medida
    if "mayor" in p and "programa" in p:
        resumen = (
            df.groupby("programa", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
        )

        fila = resumen.iloc[0]

        return (
            f"El programa con mayor {nombre_medida(medida)} es **{fila['programa']}**, "
            f"con **{formatear_valor(fila[medida], medida)}**."
        )

    # Tipo de fondo con mayor medida
    if "mayor" in p and "fondo" in p:
        resumen = (
            df.groupby("tipo_de_fondo", as_index=False)[medida]
            .sum()
            .sort_values(by=medida, ascending=False)
        )

        fila = resumen.iloc[0]

        return (
            f"El tipo de fondo con mayor {nombre_medida(medida)} es **{fila['tipo_de_fondo']}**, "
            f"con **{formatear_valor(fila[medida], medida)}**."
        )

    # Consulta por escuela específica
    if escuela:
        total = df[df["escuela"] == escuela][medida].sum()

        return (
            f"Para la escuela **{escuela}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_valor(total, medida)}**."
        )

    # Consulta por programa específico
    if programa:
        total = df[df["programa"] == programa][medida].sum()

        return (
            f"Para el programa **{programa}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_valor(total, medida)}**."
        )

    # Consulta por tipo de fondo específico
    if fondo:
        total = df[df["tipo_de_fondo"] == fondo][medida].sum()

        return (
            f"Para el tipo de fondo **{fondo}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_valor(total, medida)}**."
        )

    # Consulta por región específica
    if region:
        total = df[df["region"] == region][medida].sum()

        return (
            f"Para la región **{region}**, el total de {nombre_medida(medida)} "
            f"es **{formatear_valor(total, medida)}**."
        )

    # Total general
    if "total" in p or "cuanto" in p or "cual es" in p:
        total = df[medida].sum()

        return (
            f"El total general de {nombre_medida(medida)} en el archivo cargado es "
            f"**{formatear_valor(total, medida)}**."
        )

    return None


# =========================================================
# VISUALIZACIONES
# =========================================================

def construir_visualizacion(df, pregunta):
    p = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    if medida == "ingresos_no_disponible":
        return None, (
            "El archivo cargado no contiene una columna de **ingresos**, "
            "por lo tanto no puedo generar una gráfica de ingresos con esta estructura."
        )

    tipo = "bar"

    if "torta" in p or "pastel" in p or "distribucion" in p:
        tipo = "pie"

    # Definir dimensión
    if "programa" in p or "project" in p:
        categoria = "programa"
        titulo = f"Top 10 programas por {nombre_medida(medida)}"
        limite = 10

    elif "fondo" in p or "fondos" in p:
        categoria = "tipo_de_fondo"
        titulo = f"{nombre_medida(medida).capitalize()} por tipo de fondo"
        limite = None

    elif "region" in p:
        if df["region"].nunique() == 1 and df["region"].iloc[0] == "Sin región":
            return None, (
                "El archivo cargado no contiene una columna de **región**, "
                "por lo tanto no puedo generar una gráfica por región."
            )

        categoria = "region"
        titulo = f"{nombre_medida(medida).capitalize()} por región"
        limite = None

    else:
        categoria = "escuela"
        titulo = f"Top 10 escuelas por {nombre_medida(medida)}"
        limite = 10

    resumen = (
        df.groupby(categoria, as_index=False)[medida]
        .sum()
        .sort_values(by=medida, ascending=False)
    )

    if limite:
        resumen = resumen.head(limite)

    visualizacion = {
        "tipo": tipo,
        "titulo": titulo,
        "categoria": categoria,
        "valor": medida,
        "datos": resumen.to_dict(orient="records")
    }

    return visualizacion, None


def mostrar_visualizacion(visualizacion):
    df_viz = pd.DataFrame(visualizacion["datos"])

    tipo = visualizacion["tipo"]
    titulo = visualizacion["titulo"]
    categoria = visualizacion["categoria"]
    valor = visualizacion["valor"]

    st.subheader(titulo)

    tabla = df_viz.copy()
    tabla["valor_formateado"] = tabla[valor].apply(lambda x: formatear_valor(x, valor))

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

    if tipo == "pie":
        chart = (
            alt.Chart(df_viz)
            .mark_arc()
            .encode(
                theta=alt.Theta(f"{valor}:Q"),
                color=alt.Color(f"{categoria}:N", title="Categoría"),
                tooltip=[
                    alt.Tooltip(f"{categoria}:N", title="Categoría"),
                    alt.Tooltip(f"{valor}:Q", title="Valor", format=",.0f")
                ]
            )
            .properties(height=400)
        )

    else:
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
            .properties(height=450)
        )

    st.altair_chart(chart, use_container_width=True)


# =========================================================
# RESPUESTA GENERAL
# =========================================================

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
        "ejecutado, balance, escuela, programa, tipo de fondo o pedirme una gráfica.",
        None
    )


# =========================================================
# INTERFAZ STREAMLIT
# =========================================================

st.title("💬 Asistente Híbrido del Dashboard Financiero")

st.write(
    "Este asistente lee automáticamente un archivo Excel exportado desde Power BI "
    "y permite consultar información presupuestaria de forma guiada."
)

st.info(
    "Versión de prueba sin IA generativa. No usa API Key y no genera costo por consulta."
)

st.sidebar.success("Datos cargados automáticamente.")
st.sidebar.write(f"Archivo leído: `{RUTA_EXCEL}`")
st.sidebar.write(f"Filas cargadas: `{len(datos):,}`")
st.sidebar.write(f"Columnas cargadas: `{len(datos.columns):,}`")

with st.sidebar.expander("Resumen de datos"):
    st.write("Presupuesto total:")
    st.write(formatear_dinero(datos["presupuesto_asignado"].sum()))

    st.write("Ejecutado total:")
    st.write(formatear_dinero(datos["presupuesto_ejecutado"].sum()))

    st.write("Balance total:")
    st.write(formatear_dinero(datos["balance"].sum()))

with st.expander("Ver datos normalizados que usa el asistente"):
    st.dataframe(datos.head(100), use_container_width=True)

st.markdown("### Preguntas sugeridas")

preguntas_sugeridas = [
    "¿Cuál es el presupuesto total?",
    "¿Cuál es la escuela con mayor presupuesto?",
    "Haz una gráfica de presupuesto por escuela",
    "Haz una gráfica de ejecutado por programa",
    "Muéstrame presupuesto por tipo de fondo",
    "Haz una distribución del presupuesto por tipo de fondo",
    "¿Dónde encuentro la distribución del presupuesto?",
    "¿Qué significa ejecutado?"
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
                "¡Hola! Soy el asistente híbrido del dashboard financiero. "
                "Ya tengo cargados los datos del archivo Excel. Puedes preguntarme por "
                "presupuesto, ejecutado, balance, escuelas, programas, tipo de fondo "
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