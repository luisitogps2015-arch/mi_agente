import random

def revisar_bandeja():
    # Simulamos correos recibidos
    bandeja = [
        {"remitente": "Cliente A", "asunto": "Urgente: Problema en servidor", "urgente": True},
        {"remitente": "Jefe", "asunto": "Reporte mensual", "urgente": False},
        {"remitente": "Proveedor", "asunto": "Factura pendiente", "urgente": True}
    ]
    return bandeja

def generar_status(correos):
    pendientes = [c for c in correos if c['urgente']]
    reporte = f"--- STATUS DE PROYECTO ---\n"
    reporte += f"Total correos procesados: {len(correos)}\n"
    reporte += f"🔥 Urgencias detectadas: {len(pendientes)}\n"
    for p in pendientes:
        reporte += f"-> {p['remitente']}: {p['asunto']}\n"
    reporte += "\nEstado general: REQUIERE ACCIÓN INMEDIATA."
    return reporte
