"""Domain error for invalid credentials."""


class InvalidCredentialsError(Exception):
    """Raised when email or password is incorrect."""

    def __init__(self):
        super().__init__("Email o contraseña incorrectos")
