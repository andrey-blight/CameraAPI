from pydantic import BaseModel


class AlertModel(BaseModel):
    cam_id: str
    resp_type: str
