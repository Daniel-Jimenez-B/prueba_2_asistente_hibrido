import streamlit as st
import pandas as pd
import difflib
import re

st.set_page_config(
    page_title="Asistente Híbrido del Dashboard Financiero",
    page_icon="💬",
    layout="centered"
)

# ---------------------------------------------------------
# 1. DATOS SIMULADOS DEL DASHBOARD
# En una versión real, esta tabla podría venir de CSV, Excel,
# Google Sheets, base de datos o exportación desde Power BI.
# ---------------------------------------------------------

datos_escuelas = pd.DataFrame([
    {
        "escuela": "Escuela Superior Central",
        "region": "Centro",
        "presupuesto_asignado": 48600000,
        "presupuesto_ejecutado": 39200000,
        "ingresos": 48600000,
        "ejecucion_pct": 80.7
    },
    {
        "escuela": "Instituto Académico del Norte",
        "region": "Norte",
        "presupuesto_asignado": 45200000,
        "presupuesto_ejecutado": 38100000,
        "ingresos": 45200000,
        "ejecucion_pct": 84.3
    },
    {
        "escuela": "Colegio Técnico del Este",
        "region": "Este",
        "presupuesto_asignado": 41700000,
        "presupuesto_ejecutado": 32600000,
        "ingresos": 41700000,
        "ejecucion_pct": 78.2
    },
    {
        "escuela": "Liceo Innovación Oeste",
        "region": "Oeste",
        "presupuesto_asignado": 38300000,
        "presupuesto_ejecutado": 29300000,
        "ingresos": 38300000,
        "ejecucion_pct": 76.5
    },
    {
        "escuela": "Escuela Vocacional del Sur",
        "region": "Sur",
        "presupuesto_asignado": 36300000,
        "presupuesto_ejecutado": 26900000,
        "ingresos": 36300000,
        "ejecucion_pct": 74.1
    },
    {
        "escuela": "Academia Regional de Bayamón",
        "region": "Norte",
        "presupuesto_asignado": 29500000,
        "presupuesto_ejecutado": 24100000,
        "ingresos": 29500000,
        "ejecucion_pct": 81.7
    },
    {
        "escuela": "Centro Educativo San Juan",
        "region": "Centro",
        "presupuesto_asignado": 33200000,
        "presupuesto_ejecutado": 28100000,
        "ingresos": 33200000,
        "ejecucion_pct": 84.6
    }
])

# ---------------------------------------------------------
# 2. BASE DE NAVEGACIÓN DEL DASHBOARD
# Esta parte sí funciona como asistente guiado.
# ---------------------------------------------------------

navegacion_dashboard = {
    "distribución del presupuesto": (
        "La distribución del presupuesto se encuentra en la hoja **Resumen financiero**. "
        "Dirígete a la parte superior izquierda del dashboard y selecciona la pestaña "
        "**Resumen financiero**. Allí encontrarás el gráfico llamado "
        "**Distribución del presupuesto por región**."
    ),
    "presupuesto por región": (
        "El presupuesto por región se encuentra en la hoja **Regiones**. "
        "Usa el filtro de **Año fiscal** y luego revisa el gráfico de barras "
        "de presupuesto asignado y ejecutado por región."
    ),
    "escuelas": (
        "La información por escuela se encuentra en la hoja **Escuelas**. "
        "Allí puedes consultar el detalle por institución, presupuesto, ingresos "
        "y porcentaje de ejecución."
    ),
    "fondos federales": (
        "Los fondos federales se consultan en la hoja **Fondos**. "
        "También puedes usar el filtro **Tipo de fondo** y seleccionar **Federal**."
    ),
    "ejecución presupuestaria": (
        "La ejecución presupuestaria se encuentra en la hoja **Ejecución**. "
        "Allí puedes ver el porcentaje ejecutado por región, escuela o programa."
    ),
    "filtros": (
        "Los filtros principales se encuentran en la parte superior del dashboard. "
        "Desde allí puedes seleccionar año fiscal, trimestre, región, escuela "
        "o tipo de fondo."
    )
}

glosario = {
    "presupuesto asignado": (
        "El presupuesto asignado corresponde al monto autorizado para una escuela, "
        "región, programa o fondo durante el periodo fiscal seleccionado."
    ),
    "presupuesto ejecutado": (
        "El presupuesto ejecutado representa los recursos que ya fueron utilizados "
        "o comprometidos según la información disponible."
    ),
    "ingresos": (
        "Los ingresos representan los recursos registrados para una escuela, región "
        "o programa dentro del dashboard."
    ),
    "ejecución": (
        "La ejecución presupuestaria indica qué porcentaje del presupuesto asignado "
        "ya fue utilizado o comprometido."
    )
}

# ---------------------------------------------------------
# 3. FUNCIONES DE APOYO
# ---------------------------------------------------------

def formatear_dinero(valor):
    return f"${valor:,.0f}"


def limpiar_texto(texto):
    texto = texto.lower()
    texto = texto.replace("á", "a")
    texto = texto.replace("é", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")
    texto = texto.replace("ñ", "n")
    return texto


def buscar_escuela_en_pregunta(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    escuelas_originales = datos_escuelas["escuela"].tolist()
    escuelas_limpias = [limpiar_texto(e) for e in escuelas_originales]

    # Primero intenta encontrar coincidencia directa
    for escuela_original, escuela_limpia in zip(escuelas_originales, escuelas_limpias):
        if escuela_limpia in pregunta_limpia:
            return escuela_original

    # Luego intenta coincidencia aproximada
    coincidencias = difflib.get_close_matches(
        pregunta_limpia,
        escuelas_limpias,
        n=1,
        cutoff=0.35
    )

    if coincidencias:
        indice = escuelas_limpias.index(coincidencias[0])
        return escuelas_originales[indice]

    return None


def buscar_region_en_pregunta(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    regiones = datos_escuelas["region"].unique().tolist()
    regiones_limpias = [limpiar_texto(r) for r in regiones]

    for region_original, region_limpia in zip(regiones, regiones_limpias):
        if region_limpia in pregunta_limpia:
            return region_original

    return None


def detectar_medida(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    if "ingreso" in pregunta_limpia or "ingresos" in pregunta_limpia:
        return "ingresos"

    if "ejecutado" in pregunta_limpia or "ejecucion" in pregunta_limpia:
        return "presupuesto_ejecutado"

    if "presupuesto" in pregunta_limpia or "asignado" in pregunta_limpia:
        return "presupuesto_asignado"

    return "presupuesto_asignado"


def nombre_medida(medida):
    nombres = {
        "presupuesto_asignado": "presupuesto asignado",
        "presupuesto_ejecutado": "presupuesto ejecutado",
        "ingresos": "ingresos"
    }
    return nombres.get(medida, medida)


def responder_pregunta_analitica(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)

    # Caso 1: escuela con mayor valor
    if "mayor" in pregunta_limpia and "escuela" in pregunta_limpia:
        fila = datos_escuelas.sort_values(by=medida, ascending=False).iloc[0]
        return (
            f"La escuela con mayor {nombre_medida(medida)} es "
            f"**{fila['escuela']}**, ubicada en la región **{fila['region']}**, "
            f"con un valor de **{formatear_dinero(fila[medida])}**."
        )

    # Caso 2: región con mayor valor
    if "mayor" in pregunta_limpia and "region" in pregunta_limpia:
        resumen_region = datos_escuelas.groupby("region", as_index=False)[medida].sum()
        fila = resumen_region.sort_values(by=medida, ascending=False).iloc[0]

        return (
            f"La región con mayor {nombre_medida(medida)} es **{fila['region']}**, "
            f"con un total de **{formatear_dinero(fila[medida])}**."
        )

    # Caso 3: presupuesto o ingreso para escuela específica
    escuela = buscar_escuela_en_pregunta(pregunta)

    if escuela:
        fila = datos_escuelas[datos_escuelas["escuela"] == escuela].iloc[0]

        if "ejecucion" in pregunta_limpia or "porcentaje" in pregunta_limpia:
            return (
                f"La escuela **{fila['escuela']}**, ubicada en la región **{fila['region']}**, "
                f"tiene una ejecución presupuestaria de **{fila['ejecucion_pct']}%**."
            )

        return (
            f"Para la escuela **{fila['escuela']}**, ubicada en la región **{fila['region']}**, "
            f"el {nombre_medida(medida)} es de **{formatear_dinero(fila[medida])}**."
        )

    # Caso 4: total por región específica
    region = buscar_region_en_pregunta(pregunta)

    if region:
        total = datos_escuelas[datos_escuelas["region"] == region][medida].sum()
        return (
            f"El total de {nombre_medida(medida)} para la región **{region}** "
            f"es de **{formatear_dinero(total)}**."
        )

    # Caso 5: top 5 escuelas
    if "top" in pregunta_limpia or "primeras" in pregunta_limpia or "principales" in pregunta_limpia:
        top = datos_escuelas.sort_values(by=medida, ascending=False).head(5)

        respuesta = f"Estas son las 5 escuelas con mayor {nombre_medida(medida)}:\n\n"

        for i, fila in enumerate(top.itertuples(), start=1):
            valor = getattr(fila, medida)
            respuesta += (
                f"{i}. **{fila.escuela}** - Región {fila.region}: "
                f"**{formatear_dinero(valor)}**\n"
            )

        return respuesta

    return None


def responder_navegacion(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    for tema, respuesta in navegacion_dashboard.items():
        tema_limpio = limpiar_texto(tema)

        palabras_tema = tema_limpio.split()
        coincidencias = sum(1 for palabra in palabras_tema if palabra in pregunta_limpia)

        if coincidencias >= 1:
            return respuesta

    return None


def responder_glosario(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    for termino, definicion in glosario.items():
        termino_limpio = limpiar_texto(termino)

        if termino_limpio in pregunta_limpia:
            return definicion

    return None


def generar_respuesta(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    # Primero detectar si es una pregunta de navegación
    palabras_navegacion = [
        "donde",
        "encuentro",
        "ver",
        "hoja",
        "pagina",
        "pestana",
        "filtro",
        "ubico",
        "dirijo"
    ]

    if any(palabra in pregunta_limpia for palabra in palabras_navegacion):
        respuesta_nav = responder_navegacion(pregunta)
        if respuesta_nav:
            return respuesta_nav

    # Luego intentar responder con datos
    respuesta_analitica = responder_pregunta_analitica(pregunta)
    if respuesta_analitica:
        return respuesta_analitica

    # Luego intentar responder glosario
    respuesta_glosario = responder_glosario(pregunta)
    if respuesta_glosario:
        return respuesta_glosario

    # Respuesta por defecto
    return (
        "Por ahora no encontré una respuesta exacta para esa pregunta. "
        "Puedes intentar preguntarme por presupuesto, ingresos, ejecución, escuela, región "
        "o ubicación de información dentro del dashboard."
    )


# ---------------------------------------------------------
# 4. INTERFAZ DE LA APP
# ---------------------------------------------------------

st.title("💬 Asistente Híbrido del Dashboard Financiero")

st.write(
    "Este asistente combina respuestas guiadas de navegación con consultas simples "
    "sobre una tabla de datos agregada."
)

st.info(
    "Versión de prueba sin IA generativa. No usa API Key y no genera costo por consulta."
)

with st.expander("Ver datos de ejemplo que consulta el asistente"):
    st.dataframe(datos_escuelas)

st.markdown("### Preguntas sugeridas")

preguntas_sugeridas = [
    "¿Cuál es el presupuesto para la Escuela Superior Central?",
    "¿Cuál es el presupuesto total para la región Norte?",
    "¿Cuál es la escuela con mayor presupuesto?",
    "¿Cuál es la región con mayor presupuesto?",
    "¿Dónde encuentro la distribución del presupuesto?",
    "¿Dónde veo los fondos federales?"
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
                "Puedo ayudarte a consultar datos por escuela o región, y también a navegar por el dashboard."
            )
        }
    ]

for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["contenido"])

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

    respuesta = generar_respuesta(pregunta)

    st.session_state.historial.append(
        {
            "rol": "assistant",
            "contenido": respuesta
        }
    )

    st.rerun()

    
