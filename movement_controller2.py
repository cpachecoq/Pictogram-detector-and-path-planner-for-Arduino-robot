# Tiempo máximo permitido sin detección antes de detener el robot.
# Aproximadamente 1 segundo (30 FPS)
MAX_MISSING_FRAMES = 30

# Distancia en píxeles a la que se considera que el robot
# ha llegado al pictograma objetivo.
DISTANCE_STOP = 200


class MovementController:
    def __init__(self):
        self.state = "WAITING"
        self.missing_frames = 0

    def update(self, angle=None, distance=None, has_valid_detection=True, robot_safe=True):

        # 1. Robot fuera de la zona segura
        if not robot_safe:
            self.state = "UNSAFE"
            return {
                "state": self.state,
                "action": "STOP",
                "angle": None,
                "distance": None
            }

        # 2. Se perdió la detección
        if not has_valid_detection or angle is None or distance is None:
            self.missing_frames += 1

            if self.missing_frames >= MAX_MISSING_FRAMES:
                self.state = "LOST"
                return {
                    "state": self.state,
                    "action": "STOP",
                    "angle": None,
                    "distance": None
                }

            return {
                "state": self.state,
                "action": "HOLD",
                "angle": None,
                "distance": None
            }

        # Se recuperó la detección
        self.missing_frames = 0

        # 3. Llegó al objetivo
        if distance <= DISTANCE_STOP:
            self.state = "ARRIVED"
            return {
                "state": self.state,
                "action": "STOP",
                "angle": angle,
                "distance": distance
            }

        # 4. Navegación normal
        self.state = "NAVIGATING"
        return {
            "state": self.state,
            "action": "NAVIGATE",
            "angle": angle,
            "distance": distance
        }