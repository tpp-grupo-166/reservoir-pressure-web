"""Domain error for invalid password."""


class InvalidPasswordError(Exception):
    """Raised when password does not meet requirements."""

    def __init__(self):
        super().__init__("La contraseña debe tener al menos 8 caracteres e incluir letras y números")
