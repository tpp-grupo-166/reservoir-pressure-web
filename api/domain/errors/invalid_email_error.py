"""Domain error for invalid email format."""


class InvalidEmailError(Exception):
    """Raised when email format is invalid."""

    def __init__(self):
        super().__init__("El formato del email no es válido")
