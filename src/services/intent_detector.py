# src/services/intent_detector.py - VERSION CON DOS NIVELES DE RESPUESTA
from src.config.settings import CONTACT_KEYWORDS

def extract_contact_intent(message):
    """Detecta intención con DOS niveles: INMEDIATO vs SUGERENCIA"""
    if not message:
        return "NINGUNA"
        
    message_lower = message.lower()
    
    # NIVEL 1: Frases de ALTO PESO (llevan DIRECTO al formulario)
    high_weight_phrases = [
        'quiero dejar mis datos', 'dejar mis datos', 'quiero contacto',
        'hablar con ejecutivo', 'que me contacten', 'quiero que me llamen',
        'quiero una demo', 'necesito un asesor', 'quiero cotizar',
        'quiero comprar', 'quiero contratar', 'dejar datos', 'formulario',
        'quiero hablar con alguien', 'me pueden llamar', 'escribanme'
    ]
    
    # Si encuentra frase de ALTO PESO → ACTIVA FORMULARIO DIRECTAMENTE
    for phrase in high_weight_phrases:
        if phrase in message_lower:
            return "DIRECTO"  # Lleva al formulario
    
    # NIVEL 2: Palabras de interés medio (sugiere contacto)
    medium_interest_words = [
        # Contacto directo
    'contacto', 'contactar', 'contactarme', 'contactenos', 'contactémonos', 
    'comuniquese', 'comuníquese', 'comuniquémonos', 'comunicarse',
    
    # Llamadas
    'llamar', 'llámenme', 'llamenme', 'llámame', 'llamame', 'telefonear', 
    'llamada', 'llámeme', 'llameme', 'hablar por teléfono', 'telefono',
    
    # Escritura/email
    'escribir', 'escribanme', 'escríbanme', 'escribame', 'escríbame',
    'email', 'correo', 'mail', 'e-mail', 'escribirme', 'envíen mail',
    
    # Datos personales
    'dejar mis datos', 'mis datos', 'tomar mis datos', 'registrar mis datos',
    'datos de contacto', 'información de contacto', 'datos personales',
    'compartir mis datos', 'proporcionar datos', 'dar mis datos',
    
    # Solicitud de contacto
    'quiero que me contacten', 'deseo que me contacten', 'necesito que me contacten',
    'que me contacten', 'me pueden contactar', 'pueden contactarme',
    'agenden contacto', 'solicito contacto', 'requiero contacto',
    
    # Ejecutivos/asesores
    'ejecutivo', 'ejecutiva', 'asesor', 'asesora', 'vendedor', 'vendedora',
    'especialista', 'consultor', 'consultora', 'agente', 'representante',
    'hablar con un ejecutivo', 'hablar con ejecutivo', 'hablar con asesor',
    'un asesor me contacte', 'un ejecutivo me llame', 'persona encargada',
    
    # Reuniones
    'reunión', 'reunion', 'reunirme', 'agendar reunión', 'agendar reunion',
    'coordinar reunión', 'coordinar reunion', 'programar reunión',
    'cita', 'agendar cita', 'coordinar cita', 'meeting', 'videollamada',
    'llamada programada', 'encuentro', 'demostración', 'demo',
    
    # Cotizaciones y precios
    'cotización', 'cotizacion', 'cotizar', 'presupuesto', 'presupuestar',
    'precio', 'precios', 'costo', 'costos', 'valor', 'tarifa', 'tarifas',
    'cuánto cuesta', 'cuanto cuesta', 'precio de', 'costo de', 'valor de',
    'cotización personalizada', 'presupuesto personalizado',
    
    # Compra/venta
    'comprar', 'adquirir', 'contratar', 'suscripción', 'suscripcion',
    'licencia', 'licencias', 'producto', 'servicio', 'solución',
    'quiero comprar', 'deseo comprar', 'necesito comprar', 'me interesa comprar',
    'adquirir el producto', 'contratar el servicio', 'tomar la licencia',
    
    # Interés general
    'me interesa', 'estoy interesado', 'estoy interesada', 'interesado',
    'interesada', 'tengo interés', 'tengo interes', 'me llama la atención',
    'quiero saber más', 'deseo información', 'necesito información',
    'más información', 'mas informacion', 'info', 'información adicional',
    
    # Consultas específicas
    'planes', 'ofertas', 'promociones', 'descuentos', 'beneficios',
    'características', 'funcionalidades', 'especificaciones',
    'implementación', 'instalación', 'configuración', 'soporte',
    
    # Empresa/organización
    'empresa', 'organización', 'organizacion', 'negocio', 'pyme',
    'empresarial', 'corporativo', 'corporativa', 'institucional',
    
    # Tiempo/urgencia
    'cuanto antes', 'lo antes posible', 'urgente', 'inmediato',
    'pronto', 'rápido', 'rapido', 'ahora', 'hoy',
    
    # Variantes con typos comunes
    'kontacto', 'kontactar', 'kontactarme', 'kontactenos',
    'llamenme', 'escribanme', 'llameme', 'asesor', 'reunion',
    'cotizacion', 'presupuesto', 'interes', 'informacion',
    
    # Frases completas comunes
    'me gustaría que me contacten', 'quisiera que me llamen',
    'necesito hablar con alguien', 'busco asesoramiento',
    'quiero dejar mis datos para', 'deseo que me cotizen',
    'me pueden asesorar', 'necesito una cotización',
    'estoy buscando precios', 'quiero información sobre precios',
    'me interesa el producto', 'deseo adquirir el servicio',
    
    # Variantes con mayúsculas (por si acaso)
    'CONTACTO', 'LLAMENME', 'ESCRIBANME', 'COTIZACIÓN', 'PRESUPUESTO'
]
    
    # Si encuentra interés medio → SUGIERE contacto
    if any(word in message_lower for word in medium_interest_words):
        return "SUGERENCIA"  # Sugiere dejar datos
    
    # NIVEL 3: Palabras básicas del config (respaldo)
    if any(keyword in message_lower for keyword in CONTACT_KEYWORDS):
        return "SUGERENCIA"  # Sugiere también
    
    # Sin intención detectada
    return "NINGUNA"
