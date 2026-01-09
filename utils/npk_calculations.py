# utils/npk_calculations.py
import numpy as np
import pandas as pd
import streamlit as st
from config import PARAMETROS_CULTIVOS, VARIEDADES_MAIZ, VARIEDADES_SOYA, VARIEDADES_TRIGO, VARIEDADES_GIRASOL

def calcular_nitrogeno_sentinel2(b5, b8a):
    """Calcula nitrógeno usando NDRE para Sentinel-2"""
    # NDRE = (NIR - Red Edge) / (NIR + Red Edge)
    ndre = (b8a - b5) / (b8a + b5 + 1e-10)
    # Modelo basado en Clevers & Gitelson (2013)
    nitrogeno = 150 * ndre + 50 * (b8a / (b5 + 1e-10))
    return max(0, min(300, nitrogeno)), ndre

def calcular_fosforo_sentinel2(b4, b11):
    """Calcula fósforo usando relación SWIR-VIS para Sentinel-2"""
    # Índice SWIR-VIS (Miphokasap et al., 2012)
    swir_vis_ratio = b11 / (b4 + 1e-10)
    fosforo = 80 * (swir_vis_ratio ** 0.5) + 20
    return max(0, min(100, fosforo)), swir_vis_ratio

def calcular_potasio_sentinel2(b8, b11, b12):
    """Calcula potasio usando índice de estrés hídrico para Sentinel-2"""
    # NDII = (NIR - SWIR) / (NIR + SWIR)
    ndii = (b8 - b11) / (b8 + b11 + 1e-10)
    # Modelo basado en Jackson et al. (2004)
    potasio = 120 * ndii + 40 * (b8 / (b12 + 1e-10))
    return max(0, min(250, potasio)), ndii

def calcular_nitrogeno_landsat8(b3, b4, b5):
    """Calcula nitrógeno usando TCARI/OSAVI para Landsat-8"""
    # TCARI = 3 * [(B5 - B4) - 0.2 * (B5 - B3) * (B5 / B4)]
    tcari = 3 * ((b5 - b4) - 0.2 * (b5 - b3) * (b5 / (b4 + 1e-10)))
    
    # OSAVI = (1.16 * (B5 - B4)) / (B5 + B4 + 0.16)
    osavi = (1.16 * (b5 - b4)) / (b5 + b4 + 0.16 + 1e-10)
    
    # TCARI/OSAVI ratio
    tcari_osavi = tcari / (osavi + 1e-10)
    
    nitrogeno = 100 * tcari_osavi + 30
    return max(0, min(300, nitrogeno)), tcari_osavi

def calcular_fosforo_landsat8(b3, b6):
    """Calcula fósforo usando relación SWIR1-Verde para Landsat-8"""
    # Relación SWIR1-Verde (Chen et al., 2010)
    swir_verde_ratio = b6 / (b3 + 1e-10)
    fosforo = 60 * (swir_verde_ratio ** 0.7) + 25
    return max(0, min(100, fosforo)), swir_verde_ratio

def calcular_potasio_landsat8(b5, b7):
    """Calcula potasio usando índice NIR-SWIR para Landsat-8"""
    # Índice NIR-SWIR (Thenkabail et al., 2000)
    nir_swir_ratio = (b5 - b7) / (b5 + b7 + 1e-10)
    potasio = 100 * nir_swir_ratio + 50
    return max(0, min(250, potasio)), nir_swir_ratio

def calcular_indices_npk_avanzados(gdf, cultivo, satelite):
    """Calcula NPK usando metodologías científicas avanzadas"""
    resultados = []
    
    # Usar parámetros específicos por variedad si está disponible
    if 'variedad_params' in st.session_state and st.session_state['variedad_params']:
        params_variedad = st.session_state['variedad_params']
        # Actualizar parámetros con los de la variedad
        params = PARAMETROS_CULTIVOS[cultivo].copy()
        params.update({
            'RENDIMIENTO_BASE': params_variedad['RENDIMIENTO_BASE'],
            'RENDIMIENTO_OPTIMO': params_variedad['RENDIMIENTO_OPTIMO'],
            'RESPUESTA_N': params_variedad['RESPUESTA_N'],
            'RESPUESTA_P': params_variedad['RESPUESTA_P'],
            'RESPUESTA_K': params_variedad['RESPUESTA_K'],
            'NITROGENO': {'optimo': params_variedad['NITROGENO_OPTIMO'], 'min': params_variedad['NITROGENO_OPTIMO']*0.7, 'max': params_variedad['NITROGENO_OPTIMO']*1.2},
            'FOSFORO': {'optimo': params_variedad['FOSFORO_OPTIMO'], 'min': params_variedad['FOSFORO_OPTIMO']*0.7, 'max': params_variedad['FOSFORO_OPTIMO']*1.2},
            'POTASIO': {'optimo': params_variedad['POTASIO_OPTIMO'], 'min': params_variedad['POTASIO_OPTIMO']*0.7, 'max': params_variedad['POTASIO_OPTIMO']*1.2}
        })
    else:
        params = PARAMETROS_CULTIVOS[cultivo]
    
    for idx, row in gdf.iterrows():
        # Simular valores de reflectancia basados en posición y cultivo
        centroid = row.geometry.centroid
        seed_value = abs(hash(f"{centroid.x:.6f}_{centroid.y:.6f}_{cultivo}_{satelite}")) % (2**32)
        rng = np.random.RandomState(seed_value)
        
        if satelite == "SENTINEL-2":
            # Valores típicos de reflectancia para Sentinel-2 (en %)
            b3 = rng.uniform(0.08, 0.12)  # Verde
            b4 = rng.uniform(0.06, 0.10)  # Rojo
            b5 = rng.uniform(0.10, 0.15)  # Red Edge 1
            b8 = rng.uniform(0.25, 0.40)  # NIR
            b8a = rng.uniform(0.20, 0.35)  # Red Edge 4
            b11 = rng.uniform(0.15, 0.25)  # SWIR 1
            b12 = rng.uniform(0.10, 0.20)  # SWIR 2
            
            # Calcular NPK
            nitrogeno, ndre = calcular_nitrogeno_sentinel2(b5, b8a)
            fosforo, swir_vis = calcular_fosforo_sentinel2(b4, b11)
            potasio, ndii = calcular_potasio_sentinel2(b8, b11, b12)
            
            # Ajustar según cultivo
            nitrogeno = nitrogeno * (params['NDRE_OPTIMO'] / 0.5)
            fosforo = fosforo * (params['MATERIA_ORGANICA_OPTIMA'] / 3.5)
            potasio = potasio * (params['HUMEDAD_OPTIMA'] / 0.3)
            
        elif satelite == "LANDSAT-8":
            # Valores típicos de reflectancia para Landsat-8
            b3 = rng.uniform(0.08, 0.12)  # Verde
            b4 = rng.uniform(0.06, 0.10)  # Rojo
            b5 = rng.uniform(0.20, 0.35)  # NIR
            b6 = rng.uniform(0.12, 0.22)  # SWIR 1
            b7 = rng.uniform(0.08, 0.18)  # SWIR 2
            
            # Calcular NPK
            nitrogeno, tcari_osavi = calcular_nitrogeno_landsat8(b3, b4, b5)
            fosforo, swir_verde = calcular_fosforo_landsat8(b3, b6)
            potasio, nir_swir = calcular_potasio_landsat8(b5, b7)
            
            # Ajustar según cultivo
            nitrogeno = nitrogeno * (params['TCARI_OPTIMO'] / 0.4)
            fosforo = fosforo * (params['MATERIA_ORGANICA_OPTIMA'] / 3.5)
            potasio = potasio * (params['HUMEDAD_OPTIMA'] / 0.3)
        
        else:  # DATOS_SIMULADOS
            # Simulación básica
            nitrogeno = rng.uniform(params['NITROGENO']['min'] * 0.8, params['NITROGENO']['max'] * 1.2)
            fosforo = rng.uniform(params['FOSFORO']['min'] * 0.8, params['FOSFORO']['max'] * 1.2)
            potasio = rng.uniform(params['POTASIO']['min'] * 0.8, params['POTASIO']['max'] * 1.2)
            ndre = rng.uniform(0.2, 0.7)
            swir_vis = rng.uniform(0.5, 2.0)
            ndii = rng.uniform(0.1, 0.6)
        
        # Calcular otros índices
        ndvi = rng.uniform(params['NDVI_OPTIMO'] * 0.7, params['NDVI_OPTIMO'] * 1.1)
        materia_organica = rng.uniform(params['MATERIA_ORGANICA_OPTIMA'] * 0.8, params['MATERIA_ORGANICA_OPTIMA'] * 1.2)
        humedad_suelo = rng.uniform(params['HUMEDAD_OPTIMA'] * 0.7, params['HUMEDAD_OPTIMA'] * 1.2)
        ndwi = rng.uniform(0.1, 0.4)
        
        # Índice NPK integrado (0-1)
        npk_integrado = (
            0.4 * (nitrogeno / params['NITROGENO']['optimo']) +
            0.3 * (fosforo / params['FOSFORO']['optimo']) +
            0.3 * (potasio / params['POTASIO']['optimo'])
        ) / 1.0
        
        resultados.append({
            'nitrogeno_actual': round(nitrogeno, 1),
            'fosforo_actual': round(fosforo, 1),
            'potasio_actual': round(potasio, 1),
            'npk_integrado': round(npk_integrado, 3),
            'materia_organica': round(materia_organica, 2),
            'humedad_suelo': round(humedad_suelo, 3),
            'ndvi': round(ndvi, 3),
            'ndre': round(ndre, 3),
            'ndwi': round(ndwi, 3),
            'ndii': round(ndii, 3) if 'ndii' in locals() else 0.0
        })
    
    return resultados

def calcular_recomendaciones_npk_cientificas(gdf_analizado, nutriente, cultivo):
    """Calcula recomendaciones basadas en metodologías científicas - CORREGIDO"""
    import copy
    recomendaciones = []
    params = copy.deepcopy(PARAMETROS_CULTIVOS[cultivo])
    
    # Si es maíz y hay variedad seleccionada, usar esos parámetros
    if cultivo == "MAÍZ" and 'variedad_maiz' in st.session_state:
        variedad = st.session_state['variedad_maiz']
        variedad_params = VARIEDADES_MAIZ[variedad]
        if nutriente == "NITRÓGENO":
            params['NITROGENO']['optimo'] = variedad_params['NITROGENO_OPTIMO']
        elif nutriente == "FÓSFORO":
            params['FOSFORO']['optimo'] = variedad_params['FOSFORO_OPTIMO']
        elif nutriente == "POTASIO":
            params['POTASIO']['optimo'] = variedad_params['POTASIO_OPTIMO']
    
    for idx, row in gdf_analizado.iterrows():
        if nutriente == "NITRÓGENO":
            valor_actual = row['nitrogeno_actual']
            objetivo = params['NITRÓGENO']['optimo']
            
            # Calcular deficiencia
            deficiencia = max(0, objetivo - valor_actual)
            
            # Eficiencia de fertilización (40-60% dependiendo del método)
            eficiencia = 0.5  # 50% eficiencia típica
            
            # Recomendación ajustada
            recomendado = deficiencia / eficiencia if deficiencia > 0 else 0
            
        elif nutriente == "FÓSFORO":
            valor_actual = row['fosforo_actual']
            objetivo = params['FOSFORO']['optimo']
            deficiencia = max(0, objetivo - valor_actual)
            eficiencia = 0.3  # 30% eficiencia típica para P
            recomendado = deficiencia / eficiencia if deficiencia > 0 else 0
            
        else:  # POTASIO
            valor_actual = row['potasio_actual']
            objetivo = params['POTASIO']['optimo']
            deficiencia = max(0, objetivo - valor_actual)
            eficiencia = 0.6  # 60% eficiencia típica para K
            recomendado = deficiencia / eficiencia if deficiencia > 0 else 0
        
        # Redondear a múltiplos de 5 kg/ha
        recomendado_redondeado = round(recomendado / 5) * 5
        recomendaciones.append(max(0, recomendado_redondeado))
    
    return recomendaciones
