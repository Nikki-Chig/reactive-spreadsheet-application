# reactive_spreadsheet/src/models.py

from pydantic import BaseModel
from typing import Optional, Dict


class CellUpdate(BaseModel):
    type: str  # e.g., "update_cell"
    payload: Dict[str, Optional[str]]  # e.g., {"row": 1, "col": 1, "value": "A1"}


class InitialData(BaseModel):
    type: str  # e.g., "initial_data"
    payload: Dict[str, str]  # e.g., {"1-1": "A1", "1-2": "B1", ...}
