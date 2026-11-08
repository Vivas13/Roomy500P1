import time

DURACION_PENALIZACION = 20 

def ejecutar_penalizacion(jugador, resultado_validador, cartas_intentadas=None):
    """
    Marca el castigo en el objeto jugador y genera el paquete de red
    para sincronizar la "Exposición" de cartas en todas las pantallas.

    cartas_intentadas: lista de objetos Card que el jugador trató de bajar
                        (las que se mostrarán boca arriba a todos). Si no se
                        provee, se usa la mano completa como fallback (no
                        recomendado, pero mantiene compatibilidad).

    NO envía nada por red, NO toca la mano del jugador: eso lo hace
    quien llama a esta función (ui2.py), usando el paquete devuelto.
    """
    mensaje_error = resultado_validador.get("mensaje", "Jugada ilegal detectada.")

    cartas_expuestas = cartas_intentadas if cartas_intentadas is not None else jugador.playerHand
    # Texto para depuración / UIs que solo manejen strings
    mano_texto = [str(c) for c in cartas_expuestas]

    duracion = DURACION_PENALIZACION
    tiempo_fin = time.time() + duracion

    # 1. Marcamos el bloqueo temporal en el objeto local
    jugador.penalizado_hasta = tiempo_fin
    # Guardamos referencia a las cartas expuestas para la restitución automática
    jugador.cartas_expuestas = list(cartas_expuestas)

    # 2. Construimos el paquete de red ("Fallo Crítico") para todos los oponentes
    paquete_red = {
        "type": "REVELAR_FALLO",
        "infractor_id": jugador.playerId,
        "nombre": jugador.playerName,
        "cards": mano_texto,
        "cards_objs": list(cartas_expuestas),  # objetos Card reales (mismo proceso/pickle de red)
        "duration": duracion,
        "tiempo_fin": tiempo_fin,
        "mensaje": mensaje_error
    }

    print(f">>> [SISTEMA] Penalizacion generada para {jugador.playerName}. Duracion: {duracion}s")
    return paquete_red


def esta_penalizado(jugador):
    """
    Consulta si el jugador está bajo los efectos del castigo.
    """
    if not hasattr(jugador, 'penalizado_hasta'):
        return False
    return time.time() < jugador.penalizado_hasta


def tiempo_restante_penalizacion(jugador):
    """
    Devuelve los segundos restantes de penalización (0 si no está penalizado).
    Útil para mostrar un contador en la UI.
    """
    if not hasattr(jugador, 'penalizado_hasta'):
        return 0
    restante = jugador.penalizado_hasta - time.time()
    return max(0, restante)


def restituir_cartas(jugador):
    """
    Devuelve las cartas expuestas a la mano privada del jugador y limpia
    el estado de exposición. Debe llamarse cuando expiren los 5 segundos.

    Retorna True si hubo restitución efectiva, False si no había nada que
    restituir (ya se había limpiado antes, por ejemplo).
    """
    cartas = getattr(jugador, "cartas_expuestas", None)
    if not cartas:
        # Limpiar de todas formas el flag de penalización por si quedó colgado
        if hasattr(jugador, "penalizado_hasta"):
            jugador.penalizado_hasta = 0
        return False

    for carta in cartas:
        if carta not in jugador.playerHand:
            jugador.playerHand.append(carta)

    jugador.cartas_expuestas = []
    jugador.penalizado_hasta = 0
    return True
