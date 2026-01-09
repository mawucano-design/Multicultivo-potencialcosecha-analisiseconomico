# app.py - VERSIÓN MODULAR FINAL
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Importar módulos propios
from config import (
    SATELITES_DISPONIBLES, METODOLOGIAS_NPK, VARIEDADES_MAIZ,
    VARIEDADES_SOYA, VARIEDADES_TRIGO, VARIEDADES_GIRASOL,
    PARAMETROS_CULTIVOS, PARAMETROS_ECONOMICOS,
    TEXTURA_SUELO_OPTIMA, CLASIFICACION_PENDIENTES,
    RECOMENDACIONES_TEXTURA, ICONOS_CULTIVOS,
    COLORES_CULTIVOS, PALETAS_GEE, IMAGENES_CULTIVOS
)

# Utilidades
from utils.file_handlers import cargar_archivo_parcela
from utils.geoprocessing import validar_y_corregir_crs, calcular_superficie, dividir_parcela_en_zonas
from utils.npk_calculations import calcular_indices_npk_avanzados, calcular_recomendaciones_npk_cientificas
from utils.yield_analysis import calcular_rendimiento_potencial, calcular_rendimiento_con_recomendaciones
from utils.economic_analysis import realizar_analisis_economico, mostrar_analisis_economico
from utils.nasa_power import obtener_datos_nasa_power
from utils.reports import generar_reporte_pdf, generar_reporte_docx

# Análisis
from analysis.soil_analysis import analizar_textura_suelo, mostrar_recomendaciones_textura
from analysis.terrain_analysis import (
    generar_dem_sintetico, calcular_pendiente_simple,
    generar_curvas_nivel_simple, calcular_riesgo_erosivo,
    crear_visualizacion_3d_terreno
)
from analysis.satellite_analysis import obtener_datos_satelitales

# Visualización
from visualization.styles import aplicar_estilos, mostrar_hero_banner
from visualization.maps import (
    crear_mapa_npk_con_esri, crear_mapa_fertilidad_integrada,
    crear_mapa_texturas_con_esri, crear_mapa_pendientes_simple,
    crear_mapa_calor_rendimiento_actual, crear_mapa_calor_rendimiento_proyectado
)
from visualization.charts import (
    crear_grafico_personalizado, crear_grafico_barras_personalizado,
    crear_grafico_npk_integrado, crear_grafico_rendimiento_comparativo,
    crear_grafico_nutrientes, crear_grafico_textura_triangulo
)

# ===== APLICAR ESTILOS =====
aplicar_estilos()
mostrar_hero_banner()

# ===== INICIALIZACIÓN DE VARIABLES =====
if 'variedad' not in st.session_state:
    st.session_state['variedad'] = None
if 'variedad_params' not in st.session_state:
    st.session_state['variedad_params'] = None

# ===== SIDEBAR MEJORADO =====
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ CONFIGURACIÓN</div>', unsafe_allow_html=True)
    
    # 1. Selección de cultivo
    cultivo = st.selectbox("Cultivo:", ["MAÍZ", "SOYA", "TRIGO", "GIRASOL"])
    
    # 2. Selección de variedad según cultivo
    if cultivo == "MAÍZ":
        variedad = st.selectbox(
            "Variedad de Maíz:", 
            list(VARIEDADES_MAIZ.keys()),
            index=1
        )
        st.session_state['variedad'] = variedad
        st.session_state['variedad_params'] = VARIEDADES_MAIZ[variedad]
        
    elif cultivo == "SOYA":
        variedad = st.selectbox(
            "Variedad de Soja:", 
            list(VARIEDADES_SOYA.keys()),
            index=0
        )
        st.session_state['variedad'] = variedad
        st.session_state['variedad_params'] = VARIEDADES_SOYA[variedad]
        
    elif cultivo == "TRIGO":
        variedad = st.selectbox(
            "Variedad de Trigo:", 
            list(VARIEDADES_TRIGO.keys()),
            index=0
        )
        st.session_state['variedad'] = variedad
        st.session_state['variedad_params'] = VARIEDADES_TRIGO[variedad]
        
    elif cultivo == "GIRASOL":
        variedad = st.selectbox(
            "Variedad de Girasol:", 
            list(VARIEDADES_GIRASOL.keys()),
            index=0
        )
        st.session_state['variedad'] = variedad
        st.session_state['variedad_params'] = VARIEDADES_GIRASOL[variedad]
    
    # 3. Mostrar información de la variedad seleccionada
    if 'variedad' in st.session_state and st.session_state['variedad']:
        params = st.session_state['variedad_params']
        st.info(f"""
        **📊 {st.session_state['variedad']}**
        - Potencial: {params['RENDIMIENTO_BASE']} - {params['RENDIMIENTO_OPTIMO']} ton/ha
        - Ciclo: {params.get('CICLO', 'N/D')} días
        - Región: {params.get('REGION', 'N/D')}
        """)
    
    # 4. Imagen del cultivo
    st.image(IMAGENES_CULTIVOS[cultivo], use_container_width=True)
    
    # 5. Tipo de análisis
    analisis_tipo = st.selectbox("Tipo de Análisis:", 
                                 ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", 
                                  "ANÁLISIS DE TEXTURA", "ANÁLISIS DE CURVAS DE NIVEL"])
    
    # 6. Nutriente (solo para recomendaciones NPK)
    nutriente = None
    if analisis_tipo == "RECOMENDACIONES NPK":
        nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    # 7. Fuente de datos satelitales
    st.subheader("🛰️ Fuente de Datos Satelitales")
    satelite_seleccionado = st.selectbox(
        "Satélite:",
        ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
        help="Selecciona la fuente de datos satelitales"
    )
    
    # 8. Mostrar información del satélite
    if satelite_seleccionado in SATELITES_DISPONIBLES:
        info_satelite = SATELITES_DISPONIBLES[satelite_seleccionado]
        st.info(f"""
        **{info_satelite['icono']} {info_satelite['nombre']}**
        - Resolución: {info_satelite['resolucion']}
        - Revisita: {info_satelite['revisita']}
        - Índices: {', '.join(info_satelite['indices'][:3])}
        """)
    
    # 9. Índices de vegetación (para análisis satelital)
    indice_seleccionado = "NDVI"
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        st.subheader("📊 Índices de Vegetación")
        if satelite_seleccionado == "SENTINEL-2":
            indice_seleccionado = st.selectbox("Índice:", SATELITES_DISPONIBLES['SENTINEL-2']['indices'])
        elif satelite_seleccionado == "LANDSAT-8":
            indice_seleccionado = st.selectbox("Índice:", SATELITES_DISPONIBLES['LANDSAT-8']['indices'])
        else:
            indice_seleccionado = st.selectbox("Índice:", SATELITES_DISPONIBLES['DATOS_SIMULADOS']['indices'])
    
    # 10. Rango temporal (para análisis satelital)
    fecha_inicio = datetime.now() - timedelta(days=30)
    fecha_fin = datetime.now()
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        st.subheader("📅 Rango Temporal")
        fecha_fin = st.date_input("Fecha fin", datetime.now())
        fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
    
    # 11. División de parcela
    st.subheader("🎯 División de Parcela")
    n_divisiones = st.slider("Número de zonas de manejo:", min_value=16, max_value=48, value=32)
    
    # 12. Configuración curvas de nivel
    intervalo_curvas = 5.0
    resolucion_dem = 10.0
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        st.subheader("🏔️ Configuración Curvas de Nivel")
        intervalo_curvas = st.slider("Intervalo entre curvas (metros):", 1.0, 20.0, 5.0, 1.0)
        resolucion_dem = st.slider("Resolución DEM (metros):", 5.0, 50.0, 10.0, 5.0)
    
    # 13. Subir archivo de parcela
    st.subheader("📤 Subir Parcela")
    uploaded_file = st.file_uploader("Subir archivo de tu parcela", type=['zip', 'kml', 'kmz'],
                                     help="Formatos aceptados: Shapefile (.zip), KML (.kml), KMZ (.kmz)")
    
    # 14. Configuración económica
    with st.sidebar.expander("💰 CONFIGURACIÓN ECONÓMICA"):
        st.markdown("#### Precios de Mercado (USD)")
        
        # Precios de cultivos
        st.subheader("🌾 Precios Cultivos")
        precio_maiz = st.number_input("Maíz (USD/ton)", value=180.0, min_value=100.0, max_value=300.0)
        precio_soya = st.number_input("Soja (USD/ton)", value=380.0, min_value=200.0, max_value=500.0)
        precio_trigo = st.number_input("Trigo (USD/ton)", value=220.0, min_value=150.0, max_value=350.0)
        precio_girasol = st.number_input("Girasol (USD/ton)", value=450.0, min_value=300.0, max_value=600.0)
        
        # Actualizar precios en parámetros
        PARAMETROS_ECONOMICOS['PRECIOS_CULTIVOS']['MAÍZ']['precio_ton'] = precio_maiz
        PARAMETROS_ECONOMICOS['PRECIOS_CULTIVOS']['SOYA']['precio_ton'] = precio_soya
        PARAMETROS_ECONOMICOS['PRECIOS_CULTIVOS']['TRIGO']['precio_ton'] = precio_trigo
        PARAMETROS_ECONOMICOS['PRECIOS_CULTIVOS']['GIRASOL']['precio_ton'] = precio_girasol
        
        # Precios de fertilizantes
        st.subheader("🧪 Precios Fertilizantes")
        precio_urea = st.number_input("Urea (USD/ton)", value=450.0, min_value=300.0, max_value=600.0)
        precio_fosfato = st.number_input("Fosfato (USD/ton)", value=650.0, min_value=400.0, max_value=800.0)
        precio_potasio = st.number_input("Potasio (USD/ton)", value=400.0, min_value=250.0, max_value=550.0)
        
        PARAMETROS_ECONOMICOS['PRECIOS_FERTILIZANTES']['UREA'] = precio_urea
        PARAMETROS_ECONOMICOS['PRECIOS_FERTILIZANTES']['FOSFATO_DIAMONICO'] = precio_fosfato
        PARAMETROS_ECONOMICOS['PRECIOS_FERTILIZANTES']['CLORURO_POTASIO'] = precio_potasio
        
        # Parámetros financieros
        st.subheader("📈 Parámetros Financieros")
        tasa_descuento = st.slider("Tasa Descuento (%)", 5.0, 20.0, 10.0, 0.5) / 100
        inflacion = st.slider("Inflación Esperada (%)", 0.0, 15.0, 8.0, 0.5) / 100
        
        PARAMETROS_ECONOMICOS['PARAMETROS_FINANCIEROS']['tasa_descuento'] = tasa_descuento
        PARAMETROS_ECONOMICOS['PARAMETROS_FINANCIEROS']['inflacion_esperada'] = inflacion

# ===== LÓGICA PRINCIPAL DE LA APLICACIÓN =====
if uploaded_file:
    with st.spinner("Cargando parcela..."):
        try:
            # Cargar archivo de parcela
            gdf = cargar_archivo_parcela(uploaded_file)
            
            if gdf is not None:
                st.success(f"✅ **Parcela cargada exitosamente:** {len(gdf)} polígono(s)")
                area_total = calcular_superficie(gdf)
                
                # Mostrar información de la parcela
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**📊 INFORMACIÓN DE LA PARCELA:**")
                    st.write(f"- Polígonos: {len(gdf)}")
                    st.write(f"- Área total: {area_total:.1f} ha")
                    st.write(f"- CRS: {gdf.crs}")
                    st.write(f"- Formato: {uploaded_file.name.split('.')[-1].upper()}")
                    
                    # Vista previa de la parcela
                    st.write("**📍 Vista Previa:**")
                    fig, ax = plt.subplots(figsize=(8, 6))
                    fig.patch.set_facecolor('#0f172a')
                    ax.set_facecolor('#0f172a')
                    gdf.plot(ax=ax, color='lightgreen', edgecolor='white', alpha=0.7)
                    ax.set_title(f"Parcela: {uploaded_file.name}", color='white')
                    ax.set_xlabel("Longitud", color='white')
                    ax.set_ylabel("Latitud", color='white')
                    ax.tick_params(colors='white')
                    ax.grid(True, alpha=0.3, color='#475569')
                    st.pyplot(fig)
                
                with col2:
                    st.write("**🎯 CONFIGURACIÓN GEE:**")
                    st.write(f"- Cultivo: {ICONOS_CULTIVOS[cultivo]} {cultivo}")
                    if st.session_state.get('variedad'):
                        st.write(f"- Variedad: {st.session_state['variedad']}")
                    st.write(f"- Análisis: {analisis_tipo}")
                    st.write(f"- Zonas: {n_divisiones}")
                    
                    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                        st.write(f"- Satélite: {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}")
                        st.write(f"- Índice: {indice_seleccionado}")
                        st.write(f"- Período: {fecha_inicio} a {fecha_fin}")
                    elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                        st.write(f"- Intervalo curvas: {intervalo_curvas} m")
                        st.write(f"- Resolución DEM: {resolucion_dem} m")
                
                # Botón para ejecutar análisis
                if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary"):
                    with st.spinner("Ejecutando análisis..."):
                        
                        # ===== ANÁLISIS DE TEXTURA DEL SUELO =====
                        if analisis_tipo == "ANÁLISIS DE TEXTURA":
                            st.subheader("🏗️ ANÁLISIS DE TEXTURA DEL SUELO (USDA)")
                            
                            # Ejecutar análisis
                            gdf_analizado = analizar_textura_suelo(gdf, cultivo)
                            
                            # Mostrar estadísticas
                            st.subheader("📊 ESTADÍSTICAS DE TEXTURA (USDA)")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "Sin datos"
                                st.metric("🏗️ Textura Predominante", textura_predominante)
                            with col2:
                                avg_arena = gdf_analizado['arena'].mean()
                                st.metric("🏖️ Arena Promedio", f"{avg_arena:.1f}%")
                            with col3:
                                avg_limo = gdf_analizado['limo'].mean()
                                st.metric("🌫️ Limo Promedio", f"{avg_limo:.1f}%")
                            with col4:
                                avg_arcilla = gdf_analizado['arcilla'].mean()
                                st.metric("🧱 Arcilla Promedio", f"{avg_arcilla:.1f}%")
                            
                            # Mostrar gráficos
                            st.subheader("📈 COMPOSICIÓN GRANULOMÉTRICA (USDA)")
                            fig = crear_grafico_textura_triangulo(gdf_analizado)
                            if fig:
                                st.pyplot(fig)
                            
                            # Mostrar mapa de texturas
                            st.subheader("🗺️ MAPA DE TEXTURAS USDA CON ESRI SATELLITE")
                            mapa_texturas = crear_mapa_texturas_con_esri(gdf_analizado, cultivo)
                            if mapa_texturas:
                                st.image(mapa_texturas, use_container_width=True)
                            
                            # Mostrar recomendaciones
                            st.subheader("💡 RECOMENDACIONES DE MANEJO POR TEXTURA USDA")
                            mostrar_recomendaciones_textura(textura_predominante)
                        
                        # ===== ANÁLISIS DE CURVAS DE NIVEL =====
                        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                            st.subheader("🏔️ ANÁLISIS DE CURVAS DE NIVEL")
                            
                            # Generar DEM sintético
                            X, Y, Z, bounds = generar_dem_sintetico(gdf, resolucion_dem)
                            pendiente_grid = calcular_pendiente_simple(X, Y, Z, resolucion_dem)
                            curvas, elevaciones = generar_curvas_nivel_simple(X, Y, Z, intervalo_curvas, gdf)
                            
                            # Mostrar estadísticas
                            st.subheader("📊 ESTADÍSTICAS TOPOGRÁFICAS")
                            elevaciones_flat = Z.flatten()
                            elevaciones_flat = elevaciones_flat[~np.isnan(elevaciones_flat)]
                            
                            if len(elevaciones_flat) > 0:
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    elevacion_promedio = np.mean(elevaciones_flat)
                                    st.metric("🏔️ Elevación Promedio", f"{elevacion_promedio:.1f} m")
                                with col2:
                                    rango_elevacion = np.max(elevaciones_flat) - np.min(elevaciones_flat)
                                    st.metric("📏 Rango de Elevación", f"{rango_elevacion:.1f} m")
                                with col3:
                                    stats_pendiente = calcular_estadisticas_pendiente_simple(pendiente_grid)
                                    st.metric("📐 Pendiente Promedio", f"{stats_pendiente['promedio']:.1f}%")
                                with col4:
                                    num_curvas = len(curvas) if curvas else 0
                                    st.metric("🔄 Número de Curvas", f"{num_curvas}")
                            
                            # Mostrar mapa de pendientes
                            st.subheader("🔥 MAPA DE CALOR DE PENDIENTES")
                            mapa_pendientes = crear_mapa_pendientes_simple(X, Y, pendiente_grid, gdf)
                            if mapa_pendientes:
                                st.image(mapa_pendientes, use_container_width=True)
                            
                            # Mostrar visualización 3D
                            st.subheader("📈 VISUALIZACIÓN 3D DEL TERRENO")
                            fig_3d = crear_visualizacion_3d_terreno(X, Y, Z, cultivo)
                            if fig_3d:
                                st.pyplot(fig_3d)
                        
                        # ===== ANÁLISIS SATELITAL (FERTILIDAD O NPK) =====
                        else:
                            st.subheader(f"{ICONOS_CULTIVOS[cultivo]} ANÁLISIS SATELITAL - {cultivo}")
                            
                            # Obtener datos satelitales
                            datos_satelitales = obtener_datos_satelitales(
                                gdf, satelite_seleccionado, fecha_inicio, 
                                fecha_fin, indice_seleccionado, cultivo
                            )
                            
                            # Dividir parcela en zonas
                            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
                            
                            # Calcular NPK usando metodologías científicas
                            indices_npk = calcular_indices_npk_avanzados(gdf_dividido, cultivo, satelite_seleccionado)
                            
                            # Crear GeoDataFrame con resultados
                            gdf_analizado = gdf_dividido.copy()
                            for idx, indice_data in enumerate(indices_npk):
                                for key, value in indice_data.items():
                                    gdf_analizado.loc[gdf_analizado.index[idx], key] = value
                            
                            # Calcular áreas
                            areas_ha_list = []
                            for idx, row in gdf_analizado.iterrows():
                                area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=gdf_analizado.crs)
                                area_ha = calcular_superficie(area_gdf)
                                if hasattr(area_ha, 'iloc'):
                                    area_ha = float(area_ha.iloc[0])
                                elif hasattr(area_ha, '__len__') and len(area_ha) > 0:
                                    area_ha = float(area_ha[0])
                                else:
                                    area_ha = float(area_ha)
                                areas_ha_list.append(area_ha)
                            
                            gdf_analizado['area_ha'] = areas_ha_list
                            gdf_analizado['id_zona'] = range(1, len(gdf_analizado) + 1)
                            
                            # Mostrar metodología científica
                            if analisis_tipo == "RECOMENDACIONES NPK" and nutriente:
                                st.subheader("🔬 METODOLOGÍA CIENTÍFICA APLICADA")
                                if satelite_seleccionado in METODOLOGIAS_NPK and nutriente in METODOLOGIAS_NPK[satelite_seleccionado]:
                                    metodologia = METODOLOGIAS_NPK[satelite_seleccionado][nutriente]
                                    col_m1, col_m2 = st.columns(2)
                                    with col_m1:
                                        st.info(f"**Método:** {metodologia['metodo']}")
                                        st.write(f"**Fórmula:** {metodologia['formula']}")
                                    with col_m2:
                                        st.write(f"**Bandas utilizadas:** {', '.join(metodologia['bandas'])}")
                                        st.write(f"**Referencia:** {metodologia['referencia']}")
                            
                            # Calcular recomendaciones si es necesario
                            if analisis_tipo == "RECOMENDACIONES NPK" and nutriente:
                                recomendaciones_npk = calcular_recomendaciones_npk_cientificas(gdf_analizado, nutriente, cultivo)
                                gdf_analizado['valor_recomendado'] = recomendaciones_npk
                                
                                # Calcular rendimientos
                                rendimientos_actual = calcular_rendimiento_potencial(gdf_analizado, cultivo)
                                rendimientos_proyectado = calcular_rendimiento_con_recomendaciones(gdf_analizado, cultivo)
                                gdf_analizado['rendimiento_actual'] = rendimientos_actual
                                gdf_analizado['rendimiento_proyectado'] = rendimientos_proyectado
                                gdf_analizado['incremento_rendimiento'] = gdf_analizado['rendimiento_proyectado'] - gdf_analizado['rendimiento_actual']
                            
                            # Para fertilidad actual también calcular rendimiento
                            elif analisis_tipo == "FERTILIDAD ACTUAL":
                                rendimientos_actual = calcular_rendimiento_potencial(gdf_analizado, cultivo)
                                gdf_analizado['rendimiento_actual'] = rendimientos_actual
                            
                            # Mostrar métricas principales
                            st.subheader("📊 MÉTRICAS PRINCIPALES")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Zonas Analizadas", len(gdf_analizado))
                            with col2:
                                st.metric("Área Total", f"{area_total:.1f} ha")
                            with col3:
                                if analisis_tipo == "FERTILIDAD ACTUAL":
                                    valor_prom = gdf_analizado['npk_integrado'].mean()
                                    st.metric("Índice NPK Integrado", f"{valor_prom:.3f}")
                                else:
                                    valor_prom = gdf_analizado['valor_recomendado'].mean()
                                    st.metric(f"{nutriente} Recomendado", f"{valor_prom:.0f} kg/ha")
                            with col4:
                                if analisis_tipo == "RECOMENDACIONES NPK" and 'rendimiento_actual' in gdf_analizado.columns:
                                    incremento = gdf_analizado['incremento_rendimiento'].mean()
                                    st.metric("Incremento Rendimiento", f"{incremento:.1f} ton/ha")
                            
                            # Mostrar gráficos
                            st.subheader("📈 VISUALIZACIÓN GRÁFICA")
                            
                            if analisis_tipo == "FERTILIDAD ACTUAL":
                                fig_npk = crear_grafico_npk_integrado(gdf_analizado)
                                st.pyplot(fig_npk)
                                
                                # Mostrar mapa de fertilidad
                                st.subheader("🗺️ MAPA DE FERTILIDAD INTEGRADA")
                                mapa_fertilidad = crear_mapa_fertilidad_integrada(gdf_analizado, cultivo, satelite_seleccionado)
                                if mapa_fertilidad:
                                    st.image(mapa_fertilidad, use_container_width=True)
                            
                            elif analisis_tipo == "RECOMENDACIONES NPK":
                                # Mostrar gráfico de nutrientes
                                fig_nutrientes = crear_grafico_nutrientes(gdf_analizado)
                                st.pyplot(fig_nutrientes)
                                
                                # Mostrar gráfico comparativo de rendimiento
                                fig_rendimiento = crear_grafico_rendimiento_comparativo(gdf_analizado)
                                if fig_rendimiento:
                                    st.pyplot(fig_rendimiento)
                                
                                # Mostrar mapa NPK
                                st.subheader(f"🗺️ MAPA DE {nutriente}")
                                mapa_npk = crear_mapa_npk_con_esri(gdf_analizado, nutriente, cultivo, satelite_seleccionado)
                                if mapa_npk:
                                    st.image(mapa_npk, use_container_width=True)
                                
                                # Mostrar mapas de calor de rendimiento
                                st.subheader("🔥 MAPAS DE CALOR DE RENDIMIENTO")
                                
                                col_m1, col_m2 = st.columns(2)
                                with col_m1:
                                    st.markdown("**🌾 RENDIMIENTO ACTUAL**")
                                    mapa_actual = crear_mapa_calor_rendimiento_actual(gdf_analizado, cultivo)
                                    if mapa_actual:
                                        st.image(mapa_actual, use_container_width=True)
                                
                                with col_m2:
                                    st.markdown("**🚀 RENDIMIENTO PROYECTADO**")
                                    mapa_proyectado = crear_mapa_calor_rendimiento_proyectado(gdf_analizado, cultivo)
                                    if mapa_proyectado:
                                        st.image(mapa_proyectado, use_container_width=True)
                                
                                # ===== ANÁLISIS ECONÓMICO =====
                                st.markdown("---")
                                resultados_economicos = realizar_analisis_economico(
                                    gdf_analizado, cultivo, 
                                    st.session_state['variedad_params'], 
                                    area_total
                                )
                                mostrar_analisis_economico(resultados_economicos)
                            
                            # ===== DATOS NASA POWER =====
                            if satelite_seleccionado:
                                df_power = obtener_datos_nasa_power(gdf, fecha_inicio, fecha_fin)
                                if df_power is not None:
                                    st.subheader("🌤️ DATOS METEOROLÓGICOS NASA POWER")
                                    
                                    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
                                    with col_n1:
                                        st.metric("Radiación Solar", f"{df_power['radiacion_solar'].mean():.1f} kWh/m²/día")
                                    with col_n2:
                                        st.metric("Temperatura", f"{df_power['temperatura'].mean():.1f} °C")
                                    with col_n3:
                                        st.metric("Precipitación", f"{df_power['precipitacion'].mean():.2f} mm/día")
                                    with col_n4:
                                        st.metric("Viento", f"{df_power['viento_2m'].mean():.2f} m/s")
                                    
                                    # Mostrar gráficos de datos meteorológicos
                                    st.subheader("📊 GRÁFICOS METEOROLÓGICOS")
                                    
                                    col_g1, col_g2 = st.columns(2)
                                    with col_g1:
                                        fig_radiacion = crear_grafico_personalizado(
                                            df_power.set_index('fecha')['radiacion_solar'],
                                            "Radiación Solar Diaria",
                                            "kWh/m²/día",
                                            "#FFA500"
                                        )
                                        st.pyplot(fig_radiacion)
                                    
                                    with col_g2:
                                        fig_precip = crear_grafico_barras_personalizado(
                                            df_power.set_index('fecha')['precipitacion'],
                                            "Precipitación Diaria",
                                            "mm/día",
                                            "#3b82f6"
                                        )
                                        st.pyplot(fig_precip)
                            
                            # ===== GENERACIÓN DE REPORTES =====
                            st.markdown("---")
                            st.subheader("📥 GENERACIÓN DE REPORTES")
                            
                            col_r1, col_r2 = st.columns(2)
                            
                            with col_r1:
                                if st.button("📄 Generar Reporte PDF"):
                                    with st.spinner("Generando PDF..."):
                                        estadisticas = {
                                            'Área Total': f"{area_total:.1f} ha",
                                            'Zonas Analizadas': str(len(gdf_analizado)),
                                            'Índice NPK Promedio': f"{gdf_analizado['npk_integrado'].mean():.3f}",
                                            'NDVI Promedio': f"{gdf_analizado['ndvi'].mean():.3f}"
                                        }
                                        
                                        if analisis_tipo == "RECOMENDACIONES NPK" and 'rendimiento_actual' in gdf_analizado.columns:
                                            estadisticas['Rendimiento Actual'] = f"{gdf_analizado['rendimiento_actual'].mean():.1f} ton/ha"
                                            estadisticas['Rendimiento Proyectado'] = f"{gdf_analizado['rendimiento_proyectado'].mean():.1f} ton/ha"
                                            estadisticas['Incremento'] = f"{gdf_analizado['incremento_rendimiento'].mean():.1f} ton/ha"
                                        
                                        # Generar recomendaciones
                                        recomendaciones = [
                                            "Realizar análisis de suelo de laboratorio para validar resultados",
                                            "Aplicar fertilización según recomendaciones por zona",
                                            "Considerar agricultura de precisión para aplicación variable"
                                        ]
                                        
                                        # Seleccionar mapa para el reporte
                                        mapa_reporte = None
                                        if analisis_tipo == "FERTILIDAD ACTUAL":
                                            mapa_reporte = crear_mapa_fertilidad_integrada(gdf_analizado, cultivo, satelite_seleccionado)
                                        elif analisis_tipo == "RECOMENDACIONES NPK" and nutriente:
                                            mapa_reporte = crear_mapa_npk_con_esri(gdf_analizado, nutriente, cultivo, satelite_seleccionado)
                                        
                                        # Generar PDF
                                        pdf = generar_reporte_pdf(
                                            gdf_analizado, cultivo, analisis_tipo, area_total,
                                            nutriente, satelite_seleccionado, indice_seleccionado,
                                            mapa_reporte, estadisticas, recomendaciones
                                        )
                                        
                                        if pdf:
                                            st.download_button(
                                                label="📥 Descargar Reporte PDF",
                                                data=pdf,
                                                file_name=f"reporte_{cultivo}_{analisis_tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                                mime="application/pdf"
                                            )
                            
                            with col_r2:
                                if st.button("📝 Generar Reporte DOCX"):
                                    with st.spinner("Generando DOCX..."):
                                        docx = generar_reporte_docx(
                                            gdf_analizado, cultivo, analisis_tipo, area_total,
                                            nutriente, satelite_seleccionado, indice_seleccionado
                                        )
                                        
                                        if docx:
                                            st.download_button(
                                                label="📥 Descargar Reporte DOCX",
                                                data=docx,
                                                file_name=f"reporte_{cultivo}_{analisis_tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                            )
                            
                            # ===== EXPORTAR DATOS =====
                            st.subheader("💾 EXPORTAR DATOS")
                            
                            # Exportar a CSV
                            columnas_exportar = ['id_zona', 'area_ha']
                            if 'npk_integrado' in gdf_analizado.columns:
                                columnas_exportar.append('npk_integrado')
                            if 'nitrogeno_actual' in gdf_analizado.columns:
                                columnas_exportar.append('nitrogeno_actual')
                            if 'fosforo_actual' in gdf_analizado.columns:
                                columnas_exportar.append('fosforo_actual')
                            if 'potasio_actual' in gdf_analizado.columns:
                                columnas_exportar.append('potasio_actual')
                            if 'valor_recomendado' in gdf_analizado.columns:
                                columnas_exportar.append('valor_recomendado')
                            if 'rendimiento_actual' in gdf_analizado.columns:
                                columnas_exportar.extend(['rendimiento_actual', 'rendimiento_proyectado', 'incremento_rendimiento'])
                            
                            df_exportar = gdf_analizado[columnas_exportar].copy()
                            csv_data = df_exportar.to_csv(index=False)
                            
                            st.download_button(
                                label="📊 Descargar Datos (CSV)",
                                data=csv_data,
                                file_name=f"datos_{cultivo}_{analisis_tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv"
                            )
                        
        except Exception as e:
            st.error(f"❌ Error en el análisis: {str(e)}")
            import traceback
            st.error(f"Detalle: {traceback.format_exc()}")
else:
    st.info("👈 Por favor, sube un archivo de parcela para comenzar el análisis.")
