"""Domain error for email already in use."""


class EmailAlreadyExistsError(Exception):
    """Raised when email is already registered."""

    def __init__(self):
        super().__init__("El email ya está en uso")
