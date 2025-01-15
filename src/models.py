# reactive_spreadsheet/src/models.py

from pydantic import BaseModel
from typing import Dict, Any

class CellPayload(BaseModel):
    row: int
    col: int
    value: str

class CellUpdate(BaseModel):
    type: str
    payload: CellPayload

class InitialData(BaseModel):
    type: str
    payload: Dict[str, str]  # Keys like "1-1", values as cell values

# Optionally, if you want to differentiate the get_initial_data message
class GetInitialData(BaseModel):
    type: str  # Should be "get_initial_data"
