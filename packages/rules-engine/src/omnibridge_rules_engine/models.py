from pydantic import BaseModel


class ReadinessFinding(BaseModel):
    rule_id: str
    severity: str
    target_node_id: str
    message: str
