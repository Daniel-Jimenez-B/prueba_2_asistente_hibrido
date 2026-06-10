import streamlit as st
import pandas as pd
import difflib
import altair as alt

st.set_page_config(
    page_title="Asistente Híbrido del Dashboard Financiero",
    page_icon="💬",
    layout="centered"
)

# =========================================================
# 1. DATOS DE EJEMPLO
# En una versión real, esta tabla vendría de CSV, Excel,
# base de datos, Google Sheets o una exportación del modelo.
# =========================================================

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

datos_trimestres = pd.DataFrame([
    {"region": "Norte", "trimestre": "Q1", "presupuesto_asignado": 18000000, "presupuesto_ejecutado": 14500000, "ingresos": 16000000},
    {"region": "Norte", "trimestre": "Q2", "presupuesto_asignado": 19500000, "presupuesto_ejecutado": 15800000, "ingresos": 17200000},
    {"region": "Norte", "trimestre": "Q3", "presupuesto_asignado": 18400000, "presupuesto_ejecutado": 16300000, "ingresos": 18000000},
    {"region": "Norte", "trimestre": "Q4", "presupuesto_asignado": 18700000, "presupuesto_ejecutado": 16000000, "ingresos": 19500000},

    {"region": "Centro", "trimestre": "Q1", "presupuesto_asignado": 21000000, "presupuesto_ejecutado": 17000000, "ingresos": 18500000},
    {"region": "Centro", "trimestre": "Q2", "presupuesto_asignado": 22500000, "presupuesto_ejecutado": 18100000, "ingresos": 19300000},
    {"region": "Centro", "trimestre": "Q3", "presupuesto_asignado": 19800000, "presupuesto_ejecutado": 16500000, "ingresos": 18700000},
    {"region": "Centro", "trimestre": "Q4", "presupuesto_asignado": 20100000, "presupuesto_ejecutado": 15700000, "ingresos": 20600000},

    {"region": "Este", "trimestre": "Q1", "presupuesto_asignado": 11000000, "presupuesto_ejecutado": 8700000, "ingresos": 9900000},
    {"region": "Este", "trimestre": "Q2", "presupuesto_asignado": 9800000, "presupuesto_ejecutado": 7900000, "ingresos": 9300000},
    {"region": "Este", "trimestre": "Q3", "presupuesto_asignado": 10400000, "presupuesto_ejecutado": 8500000, "ingresos": 10800000},
    {"region": "Este", "trimestre": "Q4", "presupuesto_asignado": 10500000, "presupuesto_ejecutado": 8000000, "ingresos": 11700000},

    {"region": "Oeste", "trimestre": "Q1", "presupuesto_asignado": 9200000, "presupuesto_ejecutado": 7100000, "ingresos": 8200000},
    {"region": "Oeste", "trimestre": "Q2", "presupuesto_asignado": 9600000, "presupuesto_ejecutado": 7400000, "ingresos": 8800000},
    {"region": "Oeste", "trimestre": "Q3", "presupuesto_asignado": 9700000, "presupuesto_ejecutado": 7600000, "ingresos": 9100000},
    {"region": "Oeste", "trimestre": "Q4", "presupuesto_asignado": 9800000, "presupuesto_ejecutado": 8000000, "ingresos": 9200000},

    {"region": "Sur", "trimestre": "Q1", "presupuesto_asignado": 8700000, "presupuesto_ejecutado": 6200000, "ingresos": 7600000},
    {"region": "Sur", "trimestre": "Q2", "presupuesto_asignado": 9100000, "presupuesto_ejecutado": 6800000, "ingresos": 8100000},
    {"region": "Sur", "trimestre": "Q3", "presupuesto_asignado": 9000000, "presupuesto_ejecutado": 7100000, "ingresos": 8500000},
    {"region": "Sur", "trimestre": "Q4", "presupuesto_asignado": 9500000, "presupuesto_ejecutado": 7400000, "ingresos": 8900000}
])

# =========================================================
# 2. NAVEGACIÓN Y GLOSARIO
# =========================================================

navegacion_dashboard = {
    "distribucion del presupuesto": (
        "La distribución del presupuesto se encuentra en la hoja **Resumen financiero**. "
        "Dirígete a la parte superior izquierda del dashboard y selecciona la pestaña "
        "**Resumen financiero**. Allí encontrarás el gráfico llamado "
        "**Distribución del presupuesto por región**."
    ),
    "presupuesto por region": (
        "El presupuesto por región se encuentra en la hoja **Regiones**. "
        "Usa el filtro de **Año fiscal** y revisa el gráfico de barras de presupuesto "
        "asignado y ejecutado por región."
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
    "ejecucion presupuestaria": (
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
    "ejecucion": (
        "La ejecución presupuestaria indica qué porcentaje del presupuesto asignado "
        "ya fue utilizado o comprometido."
    )
}

# =========================================================
# 3. FUNCIONES BASE
# =========================================================

def limpiar_texto(texto):
    texto = texto.lower()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n"
    }

    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)

    return texto


def formatear_dinero(valor):
    return f"${valor:,.0f}"


def formatear_valor(valor, medida):
    if medida == "ejecucion_pct":
        return f"{valor:.1f}%"
    return formatear_dinero(valor)


def detectar_medida(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    if "porcentaje" in pregunta_limpia or "% ejecucion" in pregunta_limpia:
        return "ejecucion_pct"

    if "ingreso" in pregunta_limpia:
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
        "ingresos": "ingresos",
        "ejecucion_pct": "porcentaje de ejecución"
    }

    return nombres.get(medida, medida)


def buscar_region_en_pregunta(pregunta):
    regiones = datos_escuelas["region"].unique().tolist()
    pregunta_limpia = limpiar_texto(pregunta)

    for region in regiones:
        if limpiar_texto(region) in pregunta_limpia:
            return region

    return None


def buscar_regiones_mencionadas(pregunta):
    regiones = datos_escuelas["region"].unique().tolist()
    pregunta_limpia = limpiar_texto(pregunta)

    regiones_encontradas = []

    for region in regiones:
        if limpiar_texto(region) in pregunta_limpia:
            regiones_encontradas.append(region)

    return regiones_encontradas


def buscar_escuela_en_pregunta(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    escuelas_originales = datos_escuelas["escuela"].tolist()
    escuelas_limpias = [limpiar_texto(e) for e in escuelas_originales]

    for escuela_original, escuela_limpia in zip(escuelas_originales, escuelas_limpias):
        if escuela_limpia in pregunta_limpia:
            return escuela_original

    if "region" in pregunta_limpia and "escuela" not in pregunta_limpia:
        return None

    palabras_escuela = [
        "escuela", "colegio", "instituto", "liceo",
        "academia", "centro educativo", "vocacional"
    ]

    if not any(p in pregunta_limpia for p in palabras_escuela):
        return None

    coincidencias = difflib.get_close_matches(
        pregunta_limpia,
        escuelas_limpias,
        n=1,
        cutoff=0.65
    )

    if coincidencias:
        indice = escuelas_limpias.index(coincidencias[0])
        return escuelas_originales[indice]

    return None


def es_solicitud_grafica(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    palabras = [
        "grafica", "grafico", "barra", "barras", "chart",
        "visualiza", "visualizar", "muestrame", "mostrar",
        "distribucion", "torta", "pastel", "linea", "tendencia",
        "evolucion"
    ]

    return any(p in pregunta_limpia for p in palabras)


def es_solicitud_comparacion(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    palabras = [
        "compara", "comparame", "comparar", "comparacion",
        "vs", "versus", "contra", "diferencia"
    ]

    return any(p in pregunta_limpia for p in palabras)

# =========================================================
# 4. RESPUESTAS ANALÍTICAS EN TEXTO
# =========================================================

def responder_pregunta_analitica(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)
    region = buscar_region_en_pregunta(pregunta)

    if "mayor" in pregunta_limpia and "escuela" in pregunta_limpia:
        datos_filtrados = datos_escuelas.copy()

        if region:
            datos_filtrados = datos_filtrados[datos_filtrados["region"] == region]

        fila = datos_filtrados.sort_values(by=medida, ascending=False).iloc[0]

        if region:
            return (
                f"La escuela con mayor {nombre_medida(medida)} en la región **{region}** es "
                f"**{fila['escuela']}**, con **{formatear_valor(fila[medida], medida)}**."
            )

        return (
            f"La escuela con mayor {nombre_medida(medida)} es "
            f"**{fila['escuela']}**, ubicada en la región **{fila['region']}**, "
            f"con **{formatear_valor(fila[medida], medida)}**."
        )

    if "mayor" in pregunta_limpia and "region" in pregunta_limpia:
        resumen_region = datos_escuelas.groupby("region", as_index=False)[medida].sum()
        fila = resumen_region.sort_values(by=medida, ascending=False).iloc[0]

        return (
            f"La región con mayor {nombre_medida(medida)} es **{fila['region']}**, "
            f"con **{formatear_valor(fila[medida], medida)}**."
        )

    if region and ("region" in pregunta_limpia or "total" in pregunta_limpia):
        total = datos_escuelas[datos_escuelas["region"] == region][medida].sum()

        return (
            f"El total de {nombre_medida(medida)} para la región **{region}** "
            f"es de **{formatear_valor(total, medida)}**."
        )

    escuela = buscar_escuela_en_pregunta(pregunta)

    if escuela:
        fila = datos_escuelas[datos_escuelas["escuela"] == escuela].iloc[0]

        return (
            f"Para la escuela **{fila['escuela']}**, ubicada en la región **{fila['region']}**, "
            f"el {nombre_medida(medida)} es de **{formatear_valor(fila[medida], medida)}**."
        )

    if "top" in pregunta_limpia or "primeras" in pregunta_limpia or "principales" in pregunta_limpia:
        top = datos_escuelas.sort_values(by=medida, ascending=False).head(5)

        respuesta = f"Estas son las 5 escuelas con mayor {nombre_medida(medida)}:\n\n"

        for i, fila in enumerate(top.itertuples(), start=1):
            valor = getattr(fila, medida)
            respuesta += (
                f"{i}. **{fila.escuela}** - Región {fila.region}: "
                f"**{formatear_valor(valor, medida)}**\n"
            )

        return respuesta

    return None

# =========================================================
# 5. NAVEGACIÓN Y GLOSARIO
# =========================================================

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
        if limpiar_texto(termino) in pregunta_limpia:
            return definicion

    return None

# =========================================================
# 6. OBJETOS PARA TABLAS Y GRÁFICAS
# =========================================================

def construir_visualizacion(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)
    medida = detectar_medida(pregunta)
    regiones = buscar_regiones_mencionadas(pregunta)
    region = buscar_region_en_pregunta(pregunta)

    tipo = "bar"

    if "torta" in pregunta_limpia or "pastel" in pregunta_limpia or "distribucion" in pregunta_limpia:
        tipo = "pie"

    if "linea" in pregunta_limpia or "tendencia" in pregunta_limpia or "evolucion" in pregunta_limpia or "trimestre" in pregunta_limpia:
        tipo = "line"

    # Comparación entre regiones
    if es_solicitud_comparacion(pregunta) and len(regiones) >= 2:
        df = datos_escuelas.groupby("region", as_index=False)[medida].sum()
        df = df[df["region"].isin(regiones)]
        df = df.rename(columns={"region": "categoria", medida: "valor"})

        return {
            "tipo": "bar",
            "titulo": f"Comparación de {nombre_medida(medida)} entre regiones",
            "medida": medida,
            "datos": df.to_dict(orient="records")
        }

    # Evolución trimestral
    if tipo == "line":
        df = datos_trimestres.copy()

        if regiones:
            df = df[df["region"].isin(regiones)]

        df = df[["trimestre", "region", medida]].rename(
            columns={
                "trimestre": "categoria",
                "region": "grupo",
                medida: "valor"
            }
        )

        return {
            "tipo": "line",
            "titulo": f"Evolución trimestral de {nombre_medida(medida)}",
            "medida": medida,
            "datos": df.to_dict(orient="records")
        }

    # Gráfica por escuela dentro de una región
    if region and "escuela" in pregunta_limpia:
        df = datos_escuelas[datos_escuelas["region"] == region][["escuela", medida]].copy()
        df = df.rename(columns={"escuela": "categoria", medida: "valor"})

        return {
            "tipo": "bar",
            "titulo": f"{nombre_medida(medida).capitalize()} por escuela - Región {region}",
            "medida": medida,
            "datos": df.to_dict(orient="records")
        }

    # Top 5 escuelas
    if "top" in pregunta_limpia or "mayores" in pregunta_limpia or ("mayor" in pregunta_limpia and "escuela" in pregunta_limpia):
        df = datos_escuelas.sort_values(by=medida, ascending=False).head(5)[["escuela", medida]].copy()
        df = df.rename(columns={"escuela": "categoria", medida: "valor"})

        return {
            "tipo": "bar",
            "titulo": f"Top 5 escuelas por {nombre_medida(medida)}",
            "medida": medida,
            "datos": df.to_dict(orient="records")
        }

    # Distribución o gráfica por región
    if "region" in pregunta_limpia or tipo == "pie":
        df = datos_escuelas.groupby("region", as_index=False)[medida].sum()
        df = df.rename(columns={"region": "categoria", medida: "valor"})

        return {
            "tipo": tipo,
            "titulo": f"{nombre_medida(medida).capitalize()} por región",
            "medida": medida,
            "datos": df.to_dict(orient="records")
        }

    return None


def mostrar_visualizacion(visualizacion):
    df = pd.DataFrame(visualizacion["datos"])
    medida = visualizacion["medida"]
    tipo = visualizacion["tipo"]

    if df.empty:
        st.warning("No encontré datos para generar la visualización.")
        return

    st.subheader(visualizacion["titulo"])

    # Tabla formateada
    tabla = df.copy()
    tabla["valor_formateado"] = tabla["valor"].apply(lambda x: formatear_valor(x, medida))

    if "grupo" in tabla.columns:
        tabla_mostrar = tabla.rename(
            columns={
                "categoria": "Categoría",
                "grupo": "Grupo",
                "valor_formateado": "Valor"
            }
        )[["Categoría", "Grupo", "Valor"]]
    else:
        tabla_mostrar = tabla.rename(
            columns={
                "categoria": "Categoría",
                "valor_formateado": "Valor"
            }
        )[["Categoría", "Valor"]]

    st.dataframe(tabla_mostrar, use_container_width=True, hide_index=True)

    # Gráfica de barras
    if tipo == "bar":
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("valor:Q", title="Valor"),
                y=alt.Y("categoria:N", sort="-x", title=""),
                tooltip=[
                    alt.Tooltip("categoria:N", title="Categoría"),
                    alt.Tooltip("valor:Q", title="Valor", format=",.0f")
                ]
            )
            .properties(height=350)
        )

        st.altair_chart(chart, use_container_width=True)

    # Gráfica de torta / pastel
    elif tipo == "pie":
        chart = (
            alt.Chart(df)
            .mark_arc()
            .encode(
                theta=alt.Theta("valor:Q"),
                color=alt.Color("categoria:N", title="Categoría"),
                tooltip=[
                    alt.Tooltip("categoria:N", title="Categoría"),
                    alt.Tooltip("valor:Q", title="Valor", format=",.0f")
                ]
            )
            .properties(height=350)
        )

        st.altair_chart(chart, use_container_width=True)

    # Gráfica de línea
    elif tipo == "line":
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("categoria:N", title="Trimestre", sort=["Q1", "Q2", "Q3", "Q4"]),
                y=alt.Y("valor:Q", title="Valor"),
                color=alt.Color("grupo:N", title="Región"),
                tooltip=[
                    alt.Tooltip("categoria:N", title="Trimestre"),
                    alt.Tooltip("grupo:N", title="Región"),
                    alt.Tooltip("valor:Q", title="Valor", format=",.0f")
                ]
            )
            .properties(height=350)
        )

        st.altair_chart(chart, use_container_width=True)

# =========================================================
# 7. RESPUESTA GENERAL
# =========================================================

def generar_respuesta(pregunta):
    pregunta_limpia = limpiar_texto(pregunta)

    if es_solicitud_comparacion(pregunta) or es_solicitud_grafica(pregunta):
        visualizacion = construir_visualizacion(pregunta)

        if visualizacion:
            return (
                f"Claro. Generé una tabla y una gráfica para: "
                f"**{visualizacion['titulo']}**.",
                visualizacion
            )

        return (
            "Puedo generar gráficas por escuela, por región, top 5, distribución o evolución. "
            "Ejemplo: **'gráfica del presupuesto por escuela de la región Norte'**.",
            None
        )

    palabras_navegacion = [
        "donde", "encuentro", "ver", "hoja", "pagina",
        "pestana", "filtro", "ubico", "dirijo"
    ]

    if any(palabra in pregunta_limpia for palabra in palabras_navegacion):
        respuesta_nav = responder_navegacion(pregunta)
        if respuesta_nav:
            return respuesta_nav, None

    respuesta_analitica = responder_pregunta_analitica(pregunta)
    if respuesta_analitica:
        return respuesta_analitica, None

    respuesta_glosario = responder_glosario(pregunta)
    if respuesta_glosario:
        return respuesta_glosario, None

    return (
        "Por ahora no encontré una respuesta exacta. Puedes preguntarme por presupuesto, "
        "ingresos, ejecución, escuela, región, navegación del dashboard o pedirme una gráfica.",
        None
    )

# =========================================================
# 8. INTERFAZ STREAMLIT
# =========================================================

st.title("💬 Asistente Híbrido del Dashboard Financiero")

st.write(
    "Este asistente combina consultas a datos, navegación guiada del dashboard "
    "y generación de tablas y gráficas."
)

st.info(
    "Versión de prueba sin IA generativa. No usa API Key y no genera costo por consulta."
)

with st.expander("Ver datos de ejemplo que consulta el asistente"):
    st.dataframe(datos_escuelas, use_container_width=True)

st.markdown("### Preguntas sugeridas")

preguntas_sugeridas = [
    "¿Cuál es el presupuesto para la Escuela Superior Central?",
    "Presupuesto total región Norte",
    "Quiero una gráfica del presupuesto por escuela de la región Norte",
    "Muéstrame una gráfica de ingresos por región",
    "Compárame Norte vs Centro por presupuesto",
    "Muéstrame la evolución trimestral del presupuesto ejecutado por región",
    "Haz una distribución del presupuesto por región",
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
                "¡Hola! Soy el asistente híbrido del dashboard financiero. "
                "Puedo responder preguntas, ayudarte a navegar por el dashboard "
                "y generar tablas o gráficas básicas."
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

    respuesta, visualizacion = generar_respuesta(pregunta)

    st.session_state.historial.append(
        {
            "rol": "assistant",
            "contenido": respuesta,
            "visualizacion": visualizacion
        }
    )

    st.rerun()
