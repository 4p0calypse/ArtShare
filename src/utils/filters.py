from datetime import datetime

def format_date(value):
    """Formatea una fecha en formato legible en español"""
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    
    months = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    return f"{value.day} de {months[value.month]} de {value.year}"

def format_datetime(value):
    """Formatea una fecha y hora en formato legible en español"""
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    
    months = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    # Formatear la hora en formato 24h
    hora = value.strftime("%H:%M")
    
    # Si la fecha es hoy, solo mostrar la hora
    now = datetime.now()
    if value.date() == now.date():
        return f"Hoy a las {hora}"
    # Si la fecha es ayer, mostrar "Ayer"
    elif value.date() == now.date().replace(day=now.day - 1):
        return f"Ayer a las {hora}"
    # Para otras fechas, mostrar la fecha completa
    else:
        return f"{value.day} de {months[value.month]} de {value.year} a las {hora}" 