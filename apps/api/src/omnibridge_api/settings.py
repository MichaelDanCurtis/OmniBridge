from pydantic import BaseModel


class ApiSettings(BaseModel):
    app_name: str = "OmniBridge API"


settings = ApiSettings()
