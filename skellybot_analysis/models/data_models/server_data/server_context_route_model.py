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


    def as_path(self, title:str):

        path = f"{self.server_name}"
        if self.category_name:
            path += f"/{self.category_name}"
        if self.channel_name:
            path += f"/{self.channel_name}"
        if self.thread_name:
            path += f"/{title}-{self.thread_id}"
        return path