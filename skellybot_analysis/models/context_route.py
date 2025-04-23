from pydantic import BaseModel

from skellybot_analysis.utilities.sanitize_filename import sanitize_name


class ContextRoute(BaseModel):
    server_id: int
    server_name: str
    category_id: int|None=None
    category_name: str|None=None
    channel_id: int|None=None
    channel_name: str|None=None
    @property
    def hash_id(self):
        return hash(tuple(self.ids.split("/")))

    @property
    def safe_context_route(self) -> str:
        """
        Return a context route  guaranteed to be safe for use in a filename.
        i.e. no forbidden characters and guaranteed to be unique, while still providing
        a human-readable context route.
        """
        cr = f"{sanitize_name(self.server_name)}-{self.server_id}/".lower().strip()
        if self.category_id:
            cr += f"{sanitize_name(self.category_name)}-{self.category_id}/".lower().strip()
        if self.channel_id:
            cr += f"{sanitize_name(self.channel_name)}-{self.channel_id}/".lower().strip()
        return cr

    @property
    def names(self):
        route = f"/{self.server_name}"
        if self.category_name:
            route += f"/{self.category_name}"
        if self.channel_name:
            route += f"/{self.channel_name}"
        return route

    @property
    def ids(self):
        route = f"/{self.server_id}"
        if self.category_id:
            route += f"/{self.category_id}"
        if self.channel_id:
            route += f"/{self.channel_id}"
        return route

    @property
    def as_formatted_text(self):
        """
        Return a formatted string of the context route.
        """
        route = f"Server: {self.server_name} (id:{self.server_id})"
        if self.category_id and self.category_name:
            route += f"\nCategory: {self.category_name} (id:{self.category_id})"
        if self.channel_id and self.channel_name:
            route += f"\nChannel: {self.channel_name} (id:{self.channel_id})"
        return route

    def __hash__(self):
        """
        Return a hash of the context route, e.g so it can be used as a key in a dictionary.
        """
        return self.hash_id