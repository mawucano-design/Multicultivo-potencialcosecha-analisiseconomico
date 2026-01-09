# config.py

# ===== CONFIGURACIÓN DE SATÉLITES DISPONIBLES =====
SATELITES_DISPONIBLES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8', 'B8A', 'B11', 'B12'],
        'indices': ['NDVI', 'NDRE', 'GNDVI', 'OSAVI', 'MCARI', 'TCARI', 'NDII'],
        'icono': '🛰️',
        'bandas_np': {
            'N': ['B5', 'B8A'],  # Red Edge para NDRE
            'P': ['B4', 'B11'],  # Rojo y SWIR para fósforo
            'K': ['B8', 'B11', 'B12']  # NIR y SWIR para potasio
        }
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8',
        'resolucion': '30m',
        'revisita': '16 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B10', 'B11'],
        'indices': ['NDVI', 'NDWI', 'EVI', 'SAVI', 'MSAVI', 'NDII'],
        'icono': '🛰️',
        'bandas_np': {
            'N': ['B4', 'B5'],  # Rojo y NIR para NDRE alternativo
            'P': ['B3', 'B6'],  # Verde y SWIR1
            'K': ['B5', 'B6', 'B7']  # NIR y SWIR
        }
    },
    'DATOS_SIMULADOS': {
        'nombre': 'Datos Simulados',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8'],
        'indices': ['NDVI', 'NDRE', 'GNDVI'],
        'icono': '🔬'
    }
}

# ===== NUEVAS METODOLOGÍAS PARA ESTIMAR NPK CON TELEDETECCIÓN =====
METODOLOGIAS_NPK = {
    'SENTINEL-2': {
        'NITRÓGENO': {
            'metodo': 'NDRE + Regresión Espectral',
            'formula': 'N = 150 * NDRE + 50 * (B8A/B5)',
            'bandas': ['B5', 'B8A'],
            'r2_esperado': 0.75,
            'referencia': 'Clevers & Gitelson, 2013'
        },
        'FÓSFORO': {
            'metodo': 'Índice SWIR-VIS',
            'formula': 'P = 80 * (B11/B4)^0.5 + 20',
            'bandas': ['B4', 'B11'],
            'r2_esperado': 0.65,
            'referencia': 'Miphokasap et al., 2012'
        },
        'POTASIO': {
            'metodo': 'Índice de Estrés Hídrico',
            'formula': 'K = 120 * (B8 - B11)/(B8 + B12) + 40',
            'bandas': ['B8', 'B11', 'B12'],
            'r2_esperado': 0.70,
            'referencia': 'Jackson et al., 2004'
        }
    },
    'LANDSAT-8': {
        'NITRÓGENO': {
            'metodo': 'TCARI/OSAVI',
            'formula': 'N = 3*[(B5-B4)-0.2*(B5-B3)*(B5/B4)] / (1.16*(B5-B4)/(B5+B4+0.16))',
            'bandas': ['B3', 'B4', 'B5'],
            'r2_esperado': 0.72,
            'referencia': 'Haboudane et al., 2002'
        },
        'FÓSFORO': {
            'metodo': 'Relación SWIR1-Verde',
            'formula': 'P = 60 * (B6/B3)^0.7 + 25',
            'bandas': ['B3', 'B6'],
            'r2_esperado': 0.68,
            'referencia': 'Chen et al., 2010'
        },
        'POTASIO': {
            'metodo': 'Índice NIR-SWIR',
            'formula': 'K = 100 * (B5 - B7)/(B5 + B7) + 50',
            'bandas': ['B5', 'B7'],
            'r2_esperado': 0.69,
            'referencia': 'Thenkabail et al., 2000'
        }
    }
}

# ===== CONFIGURACIÓN =====
# PARÁMETROS GEE POR CULTIVO - ACTUALIZADO CON NUEVOS CULTIVOS Y RENDIMIENTO
# VARIEDADES DE MAÍZ ESPECÍFICAS
VARIEDADES_MAIZ = {
    'HÍBRIDO TEMPRANO (90-100 días)': {
        'RENDIMIENTO_BASE': 7.0,
        'RENDIMIENTO_OPTIMO': 10.0,
        'RESPUESTA_N': 0.04,
        'RESPUESTA_P': 0.06,
        'RESPUESTA_K': 0.03,
        'NITROGENO_OPTIMO': 160,
        'FOSFORO_OPTIMO': 45,
        'POTASIO_OPTIMO': 120
    },
    'HÍBRIDO INTERMEDIO (110-120 días)': {
        'RENDIMIENTO_BASE': 8.0,
        'RENDIMIENTO_OPTIMO': 12.0,
        'RESPUESTA_N': 0.05,
        'RESPUESTA_P': 0.08,
        'RESPUESTA_K': 0.04,
        'NITROGENO_OPTIMO': 180,
        'FOSFORO_OPTIMO': 50,
        'POTASIO_OPTIMO': 150
    },
    'HÍBRIDO TARDÍO (130-140 días)': {
        'RENDIMIENTO_BASE': 9.0,
        'RENDIMIENTO_OPTIMO': 14.0,
        'RESPUESTA_N': 0.06,
        'RESPUESTA_P': 0.09,
        'RESPUESTA_K': 0.05,
        'NITROGENO_OPTIMO': 200,
        'FOSFORO_OPTIMO': 55,
        'POTASIO_OPTIMO': 180
    },
    'VARIEDAD CRIOLLA': {
        'RENDIMIENTO_BASE': 4.0,
        'RENDIMIENTO_OPTIMO': 6.0,
        'RESPUESTA_N': 0.02,
        'RESPUESTA_P': 0.03,
        'RESPUESTA_K': 0.02,
        'NITROGENO_OPTIMO': 120,
        'FOSFORO_OPTIMO': 30,
        'POTASIO_OPTIMO': 80
    }
}

# ===== VARIEDADES DE SOYA PARA ARGENTINA =====
VARIEDADES_SOYA = {
    'DM 53i72 IPRO (GRUPO V)': {
        'RENDIMIENTO_BASE': 3.2,
        'RENDIMIENTO_OPTIMO': 4.5,
        'RESPUESTA_N': 0.015,
        'RESPUESTA_P': 0.025,
        'RESPUESTA_K': 0.020,
        'NITROGENO_OPTIMO': 25,
        'FOSFORO_OPTIMO': 35,
        'POTASIO_OPTIMO': 90,
        'CICLO': 115,
        'TECNOLOGIA': 'Intacta RR2 PRO',
        'REGION': 'Núcleo Sur'
    },
    'NS 4619 IPRO (GRUPO IV)': {
        'RENDIMIENTO_BASE': 3.5,
        'RENDIMIENTO_OPTIMO': 5.0,
        'RESPUESTA_N': 0.018,
        'RESPUESTA_P': 0.028,
        'RESPUESTA_K': 0.022,
        'NITROGENO_OPTIMO': 28,
        'FOSFORO_OPTIMO': 38,
        'POTASIO_OPTIMO': 95,
        'CICLO': 105,
        'TECNOLOGIA': 'Intacta RR2 PRO',
        'REGION': 'Núcleo Norte'
    },
    'A 4910 RG (GRUPO IV)': {
        'RENDIMIENTO_BASE': 3.0,
        'RENDIMIENTO_OPTIMO': 4.2,
        'RESPUESTA_N': 0.014,
        'RESPUESTA_P': 0.023,
        'RESPUESTA_K': 0.019,
        'NITROGENO_OPTIMO': 22,
        'FOSFORO_OPTIMO': 32,
        'POTASIO_OPTIMO': 85,
        'CICLO': 100,
        'TECNOLOGIA': 'RR1',
        'REGION': 'Norte Argentino'
    },
    'SYN 1359 IPRO (GRUPO V)': {
        'RENDIMIENTO_BASE': 3.8,
        'RENDIMIENTO_OPTIMO': 5.3,
        'RESPUESTA_N': 0.020,
        'RESPUESTA_P': 0.030,
        'RESPUESTA_K': 0.024,
        'NITROGENO_OPTIMO': 30,
        'FOSFORO_OPTIMO': 40,
        'POTASIO_OPTIMO': 100,
        'CICLO': 120,
        'TECNOLOGIA': 'Intacta RR2 PRO',
        'REGION': 'Sudeste Bonaerense'
    }
}

# ===== VARIEDADES DE TRIGO PARA ARGENTINA =====
VARIEDADES_TRIGO = {
    'BIOINTA 3004 (PANADERO)': {
        'RENDIMIENTO_BASE': 4.0,
        'RENDIMIENTO_OPTIMO': 6.5,
        'RESPUESTA_N': 0.025,
        'RESPUESTA_P': 0.040,
        'RESPUESTA_K': 0.030,
        'NITROGENO_OPTIMO': 140,
        'FOSFORO_OPTIMO': 45,
        'POTASIO_OPTIMO': 95,
        'CICLO': 125,
        'CALIDAD': 'Panadero Superior',
        'REGION': 'Sudeste Bonaerense'
    },
    'KLEIN CAPRICORNIO (CÁNDIDO)': {
        'RENDIMIENTO_BASE': 4.5,
        'RENDIMIENTO_OPTIMO': 7.0,
        'RESPUESTa_N': 0.028,
        'RESPUESTA_P': 0.045,
        'RESPUESTA_K': 0.035,
        'NITROGENO_OPTIMO': 150,
        'FOSFORO_OPTIMO': 48,
        'POTASIO_OPTIMO': 100,
        'CICLO': 120,
        'CALIDAD': 'Panadero',
        'REGION': 'Núcleo Norte'
    },
    'BUCK GUARANÍ (SINTÉTICO)': {
        'RENDIMIENTO_BASE': 3.8,
        'RENDIMIENTO_OPTIMO': 6.0,
        'RESPUESTA_N': 0.022,
        'RESPUESTA_P': 0.038,
        'RESPUESTA_K': 0.028,
        'NITROGENO_OPTIMO': 135,
        'FOSFORO_OPTIMO': 42,
        'POTASIO_OPTIMO': 90,
        'CICLO': 115,
        'CALIDAD': 'Panadero',
        'REGION': 'Norte Argentino'
    },
    'ACA 303 PLUS (DOBLE PROPÓSITO)': {
        'RENDIMIENTO_BASE': 4.2,
        'RENDIMIENTO_OPTIMO': 6.8,
        'RESPUESTA_N': 0.026,
        'RESPUESTA_P': 0.042,
        'RESPUESTA_K': 0.032,
        'NITROGENO_OPTIMO': 145,
        'FOSFORO_OPTIMO': 46,
        'POTASIO_OPTIMO': 98,
        'CICLO': 130,
        'CALIDAD': 'Panadero/Forrajero',
        'REGION': 'Centro Sur'
    }
}

# ===== VARIEDADES DE GIRASOL PARA ARGENTINA =====
VARIEDADES_GIRASOL = {
    'DK 4045 CL (ALTO OLEICO)': {
        'RENDIMIENTO_BASE': 2.5,
        'RENDIMIENTO_OPTIMO': 3.8,
        'RESPUESTA_N': 0.012,
        'RESPUESTA_P': 0.018,
        'RESPUESTA_K': 0.015,
        'NITROGENO_OPTIMO': 85,
        'FOSFORO_OPTIMO': 35,
        'POTASIO_OPTIMO': 115,
        'CICLO': 105,
        'ACEITE': 'Alto Oleico (82%)',
        'REGION': 'Núcleo Norte'
    },
    'SY VERT 854 CL (CONVENCIONAL)': {
        'RENDIMIENTO_BASE': 2.8,
        'RENDIMIENTO_OPTIMO': 4.2,
        'RESPUESTA_N': 0.014,
        'RESPUESTA_P': 0.020,
        'RESPUESTA_K': 0.017,
        'NITROGENO_OPTIMO': 90,
        'FOSFORO_OPTIMO': 38,
        'POTASIO_OPTIMO': 120,
        'CICLO': 110,
        'ACEITE': 'Convencional (48%)',
        'REGION': 'Sudeste Bonaerense'
    },
    'NIDER A 6620 CL (TOLERANTE)': {
        'RENDIMIENTO_BASE': 2.3,
        'RENDIMIENTO_OPTIMO': 3.5,
        'RESPUESTA_N': 0.011,
        'RESPUESTA_P': 0.017,
        'RESPUESTA_K': 0.014,
        'NITROGENO_OPTIMO': 80,
        'FOSFORO_OPTIMO': 32,
        'POTASIO_OPTIMO': 110,
        'CICLO': 100,
        'ACEITE': 'Convencional (46%)',
        'REGION': 'Norte Argentino'
    },
    'ACA 861 CL (ALTO RENDIMIENTO)': {
        'RENDIMIENTO_BASE': 3.0,
        'RENDIMIENTO_OPTIMO': 4.5,
        'RESPUESTA_N': 0.016,
        'RESPUESTA_P': 0.022,
        'RESPUESTA_K': 0.019,
        'NITROGENO_OPTIMO': 95,
        'FOSFORO_OPTIMO': 40,
        'POTASIO_OPTIMO': 125,
        'CICLO': 115,
        'ACEITE': 'Alto Oleico (80%)',
        'REGION': 'Centro Sur'
    }
}

PARAMETROS_CULTIVOS = {
    'MAÍZ': {
        'NITROGENO': {'min': 150, 'max': 200, 'optimo': 180},
        'FOSFORO': {'min': 40, 'max': 60, 'optimo': 50},
        'POTASIO': {'min': 120, 'max': 180, 'optimo': 150},
        'MATERIA_ORGANICA_OPTIMA': 3.5,
        'HUMEDAD_OPTIMA': 0.3,
        'NDVI_OPTIMO': 0.85,
        'NDRE_OPTIMO': 0.5,
        'TCARI_OPTIMO': 0.4,
        'OSAVI_OPTIMO': 0.6,
        # PARÁMETROS BASE (HÍBRIDO INTERMEDIO POR DEFECTO)
        'RENDIMIENTO_BASE': 8.0,
        'RENDIMIENTO_OPTIMO': 12.0,
        'RESPUESTA_N': 0.05,
        'RESPUESTA_P': 0.08,
        'RESPUESTA_K': 0.04,
        'FACTOR_CLIMA': 0.7,
        'VARIEDAD_DEFAULT': 'HÍBRIDO INTERMEDIO (110-120 días)'
    },
    'SOYA': {
        'NITROGENO': {'min': 20, 'max': 40, 'optimo': 30},
        'FOSFORO': {'min': 30, 'max': 50, 'optimo': 40},
        'POTASIO': {'min': 80, 'max': 120, 'optimo': 100},
        'MATERIA_ORGANICA_OPTIMA': 4.0,
        'HUMEDAD_OPTIMA': 0.25,
        'NDVI_OPTIMO': 0.8,
        'NDRE_OPTIMO': 0.45,
        'TCARI_OPTIMO': 0.35,
        'OSAVI_OPTIMO': 0.55,
        'RENDIMIENTO_BASE': 2.5,
        'RENDIMIENTO_OPTIMO': 4.0,
        'RESPUESTA_N': 0.02,
        'RESPUESTA_P': 0.03,
        'RESPUESTA_K': 0.025,
        'FACTOR_CLIMA': 0.75
    },
    'TRIGO': {
        'NITROGENO': {'min': 120, 'max': 180, 'optimo': 150},
        'FOSFORO': {'min': 40, 'max': 60, 'optimo': 50},
        'POTASIO': {'min': 80, 'max': 120, 'optimo': 100},
        'MATERIA_ORGANICA_OPTIMA': 3.0,
        'HUMEDAD_OPTIMA': 0.28,
        'NDVI_OPTIMO': 0.75,
        'NDRE_OPTIMO': 0.4,
        'TCARI_OPTIMO': 0.3,
        'OSAVI_OPTIMO': 0.5,
        'RENDIMIENTO_BASE': 3.5,
        'RENDIMIENTO_OPTIMO': 6.0,
        'RESPUESTA_N': 0.03,
        'RESPUESTA_P': 0.05,
        'RESPUESTA_K': 0.035,
        'FACTOR_CLIMA': 0.8
    },
    'GIRASOL': {
        'NITRÓGENO': {'min': 80, 'max': 120, 'optimo': 100},
        'FÓSFORO': {'min': 35, 'max': 50, 'optimo': 42},
        'POTASIO': {'min': 100, 'max': 150, 'optimo': 125},
        'MATERIA_ORGANICA_OPTIMA': 3.2,
        'HUMEDAD_OPTIMA': 0.22,
        'NDVI_OPTIMO': 0.7,
        'NDRE_OPTIMO': 0.35,
        'TCARI_OPTIMO': 0.25,
        'OSAVI_OPTIMO': 0.45,
        'RENDIMIENTO_BASE': 2.0,
        'RENDIMIENTO_OPTIMO': 3.5,
        'RESPUESTA_N': 0.015,
        'RESPUESTA_P': 0.02,
        'RESPUESTA_K': 0.018,
        'FACTOR_CLIMA': 0.65
    }
}

# ===== PARÁMETROS ECONÓMICOS PARA ARGENTINA (2025) =====
PARAMETROS_ECONOMICOS = {
    'PRECIOS_CULTIVOS': {
        'MAÍZ': {
            'precio_ton': 180,  # USD/ton
            'costo_semilla': 250,  # USD/ha
            'costo_herbicidas': 80,
            'costo_insecticidas': 40,
            'costo_labores': 120,
            'costo_cosecha': 60,
            'costo_otros': 50
        },
        'SOYA': {
            'precio_ton': 380,  # USD/ton
            'costo_semilla': 180,
            'costo_herbicidas': 90,
            'costo_insecticidas': 50,
            'costo_labores': 100,
            'costo_cosecha': 70,
            'costo_otros': 40
        },
        'TRIGO': {
            'precio_ton': 220,  # USD/ton
            'costo_semilla': 150,
            'costo_herbicidas': 70,
            'costo_insecticidas': 30,
            'costo_labores': 110,
            'costo_cosecha': 55,
            'costo_otros': 45
        },
        'GIRASOL': {
            'precio_ton': 450,  # USD/ton
            'costo_semilla': 140,
            'costo_herbicidas': 75,
            'costo_insecticidas': 35,
            'costo_labores': 95,
            'costo_cosecha': 65,
            'costo_otros': 35
        }
    },
    'PRECIOS_FERTILIZANTES': {
        'UREA': 450,  # USD/ton
        'FOSFATO_DIAMONICO': 650,  # USD/ton
        'CLORURO_POTASIO': 400,  # USD/ton
        'SULFATO_AMONICO': 350,  # USD/ton
        'SUPERFOSFATO': 420  # USD/ton
    },
    'CONVERSION_NUTRIENTES': {
        'NITRÓGENO': {
            'fuente_principal': 'UREA',
            'contenido_nutriente': 0.46,  # 46% N
            'eficiencia': 0.6  # 60% eficiencia
        },
        'FÓSFORO': {
            'fuente_principal': 'FOSFATO_DIAMONICO',
            'contenido_nutriente': 0.18,  # 18% P2O5 (46% P)
            'eficiencia': 0.3  # 30% eficiencia
        },
        'POTASIO': {
            'fuente_principal': 'CLORURO_POTASIO',
            'contenido_nutriente': 0.60,  # 60% K2O (50% K)
            'eficiencia': 0.5  # 50% eficiencia
        }
    },
    'PARAMETROS_FINANCIEROS': {
        'tasa_descuento': 0.10,  # 10% anual
        'periodo_analisis': 5,  # 5 años
        'inflacion_esperada': 0.08,  # 8% anual
        'impuestos': 0.35,  # 35%
        'subsidios': 0.05  # 5% de subsidios
    }
}

# ===== PARÁMETROS DE TEXTURA DEL SUELO POR CULTIVO - ACTUALIZADO A USDA =====
TEXTURA_SUELO_OPTIMA = {
    'MAÍZ': {
        'textura_optima': 'Franco limoso',
        'arena_optima': 43,
        'limo_optima': 37,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.3,
        'porosidad_optima': 0.5
    },
    'SOYA': {
        'textura_optima': 'Franco',
        'arena_optima': 40,
        'limo_optima': 40,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.2,
        'porosidad_optima': 0.55
    },
    'TRIGO': {
        'textura_optima': 'Franco arcilloso limoso',
        'arena_optima': 30,
        'limo_optima': 50,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.25,
        'porosidad_optima': 0.52
    },
    'GIRASOL': {
        'textura_optima': 'Franco arenoso',
        'arena_optima': 60,
        'limo_optima': 25,
        'arcilla_optima': 15,
        'densidad_aparente_optima': 1.35,
        'porosidad_optima': 0.48
    }
}

# CLASIFICACIÓN DE PENDIENTES
CLASIFICACION_PENDIENTES = {
    'PLANA (0-2%)': {'min': 0, 'max': 2, 'color': '#4daf4a', 'factor_erosivo': 0.1},
    'SUAVE (2-5%)': {'min': 2, 'max': 5, 'color': '#a6d96a', 'factor_erosivo': 0.3},
    'MODERADA (5-10%)': {'min': 5, 'max': 10, 'color': '#ffffbf', 'factor_erosivo': 0.6},
    'FUERTE (10-15%)': {'min': 10, 'max': 15, 'color': '#fdae61', 'factor_erosivo': 0.8},
    'MUY FUERTE (15-25%)': {'min': 15, 'max': 25, 'color': '#f46d43', 'factor_erosivo': 0.9},
    'EXTREMA (>25%)': {'min': 25, 'max': 100, 'color': '#d73027', 'factor_erosivo': 1.0}
}

# ===== RECOMENDACIONES POR TIPO DE TEXTURA USDA - ACTUALIZADO =====
RECOMENDACIONES_TEXTURA = {
    'Franco limoso': {
        'propiedades': [
            "Equilibrio ideal arena-limo-arcilla",
            "Excelente estructura y porosidad",
            "Alta capacidad de retención de agua",
            "Fertilidad natural alta"
        ],
        'limitantes': [
            "Puede compactarse con maquinaria pesada",
            "Moderadamente susceptible a erosión"
        ],
        'manejo': [
            "Labranza mínima o conservacionista",
            "Rotación de cultivos",
            "Uso de coberturas vegetales",
            "Fertilización balanceada"
        ]
    },
    'Franco': {
        'propiedades': [
            "Buena aireación y drenaje",
            "Fácil labranza",
            "Calentamiento rápido en primavera",
            "Retención moderada de nutrientes"
        ],
        'limitantes': [
            "Menor retención de agua que suelos más arcillosos",
            "Requiere riego más frecuente"
        ],
        'manejo': [
            "Riego por goteo o aspersión",
            "Fertilización fraccionada",
            "Mulching para conservar humedad"
        ]
    },
    'Franco arcilloso limoso': {
        'propiedades': [
            "Alta capacidad de retención de agua",
            "Excelente retención de nutrientes",
            "Estructura estable",
            "Resistente a la erosión"
        ],
        'limitantes': [
            "Lento drenaje",
            "Difícil labranza en condiciones húmedas",
            "Lento calentamiento en primavera"
        ],
        'manejo': [
            "Sistemas de drenaje",
            "Labranza en condiciones óptimas de humedad",
            "Incorporación de materia orgánica"
        ]
    },
    'Franco arenoso': {
        'propiedades': [
            "Excelente drenaje",
            "Fácil labranza en cualquier condición",
            "Rápido calentamiento",
            "Buen desarrollo radicular"
        ],
        'limitantes': [
            "Baja retención de agua y nutrientes",
            "Alta lixiviación de fertilizantes",
            "Baja materia orgánica"
        ],
        'manejo': [
            "Riego frecuente en pequeñas cantidades",
            "Fertilización fraccionada",
            "Aplicación de materia orgánica",
            "Cultivos de cobertura"
        ]
    },
    'Arcilla': {
        'propiedades': [
            "Alta capacidad de retención de agua y nutrientes",
            "Estructura estable",
            "Alta fertilidad potencial"
        ],
        'limitantes': [
            "Muy pesada cuando está húmeda",
            "Drenaje muy lento",
            "Difícil labranza",
            "Propensa a compactación"
        ],
        'manejo': [
            "Drenaje artificial obligatorio",
            "Labranza en condiciones óptimas",
            "Encalamiento para mejorar estructura",
            "Cultivos tolerantes a humedad"
        ]
    },
    'Arena franca': {
        'propiedades': [
            "Drenaje muy rápido",
            "Fácil labranza",
            "Rápido calentamiento",
            "Bajo riesgo de compactación"
        ],
        'limitantes': [
            "Muy baja retención de agua",
            "Alta lixiviación de nutrientes",
            "Baja fertilidad natural"
        ],
        'manejo': [
            "Riego por goteo con alta frecuencia",
            "Fertilización en múltiples aplicaciones",
            "Aplicación intensiva de materia orgánica",
            "Mulching para conservar humedad"
        ]
    },
    'Arcilla limosa': {
        'propiedades': [
            "Muy alta retención de agua y nutrientes",
            "Estructura muy estable",
            "Excelente para cultivos exigentes"
        ],
        'limitantes': [
            "Drenaje extremadamente lento",
            "Muy pesada para labranza",
            "Requiere manejo especializado"
        ],
        'manejo': [
            "Sistemas de drenaje avanzados",
            "Labranza solo en condiciones óptimas",
            "Aplicación de yeso para mejorar estructura",
            "Camas elevadas para cultivos"
        ]
    },
    'Limo': {
        'propiedades': [
            "Alta capacidad de retención de agua",
            "Fácil labranza",
            "Buena fertilidad natural"
        ],
        'limitantes': [
            "Susceptible a compactación",
            "Propenso a formación de costra superficial",
            "Baja estabilidad estructural"
        ],
        'manejo': [
            "Evitar labranza en condiciones húmedas",
            "Uso de coberturas vegetales",
            "Aplicación de materia orgánica",
            "Riego por aspersión ligera"
        ]
    }
}

# ICONOS Y COLORES POR CULTIVO - ACTUALIZADO
ICONOS_CULTIVOS = {
    'MAÍZ': '🌽',
    'SOYA': '🫘',
    'TRIGO': '🌾',
    'GIRASOL': '🌻'
}

COLORES_CULTIVOS = {
    'MAÍZ': '#FFD700',
    'SOYA': '#90EE90',
    'TRIGO': '#DAA520',
    'GIRASOL': '#FFA500'
}

# PALETAS GEE MEJORADAS
PALETAS_GEE = {
    'FERTILIDAD': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'],
    'NITROGENO': ['#00ff00', '#80ff00', '#ffff00', '#ff8000', '#ff0000'],
    'FOSFORO': ['#0000ff', '#4040ff', '#8080ff', '#c0c0ff', '#ffffff'],
    'POTASIO': ['#4B0082', '#6A0DAD', '#8A2BE2', '#9370DB', '#D8BFD8'],
    'TEXTURA': ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e'],
    'ELEVACION': ['#006837', '#1a9850', '#66bd63', '#a6d96a', '#d9ef8b', '#ffffbf', '#fee08b', '#fdae61', '#f46d43', '#d73027'],
    'PENDIENTE': ['#4daf4a', '#a6d96a', '#ffffbf', '#fdae61', '#f46d43', '#d73027']
}

# URLs de imágenes para sidebar - VERIFICADAS (2025)
IMAGENES_CULTIVOS = {
    'MAÍZ': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
    'SOYA': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
    'TRIGO': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
    'GIRASOL': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
}

# Estilos CSS (solo el string completo)
CSS_STYLES = """
<style>
/* === FONDO GENERAL OSCURO ELEGANTE === */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #ffffff !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ... (todo el CSS aquí) ... */
</style>
"""

# Hero Banner HTML
HERO_BANNER = """
<div class="hero-banner">
    <div class="hero-content">
        <h1 class="hero-title">ANALIZADOR MULTI-CULTIVO SATELITAL</h1>
        <p class="hero-subtitle">Potenciado con NASA POWER, GEE y tecnología avanzada para una agricultura de precisión</p>
    </div>
</div>
"""
