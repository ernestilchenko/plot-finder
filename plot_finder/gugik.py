from pydantic import BaseModel


class GugikEntry(BaseModel):
    organ: str
    nazwa: str
    wms: str | None = None
    wfs: str | None = None
