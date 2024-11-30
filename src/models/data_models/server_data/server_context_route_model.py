from pydantic import BaseModel


class ServerContextRoute(BaseModel):
    """
    A route to a specific context in the server data
    """
    server_name: str
    server_id: int

    category_name: str | None = None
    category_id: int | None = None

    channel_name: str | None = None
    channel_id: int | None = None

    thread_id: int | None = None
    thread_name: str | None = None

    message_id: int | None = None
