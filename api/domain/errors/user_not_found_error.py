"""Domain error for user not found."""


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    def __init__(self):
        super().__init__("Usuario no encontrado")
