class ChatError(Exception):
    """Domain-level chat error that carries an HTTP status."""

    def __init__(self, detail: str, status_code: int):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

