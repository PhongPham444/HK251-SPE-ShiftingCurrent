# src/patient.py
from typing import Dict, Optional

class Patient:
    def __init__(self, id: int, arrival_time: float):
        self.id = id
        self.arrival_time = arrival_time
        # standardized timestamps: for each node X store:
        # X_arrival (time patient entered node queue),
        # X_service_start, X_service_end
        self.timestamps: Dict[str, float] = {}

    def record_arrival(self, node: str, t: float):
        self.timestamps[f"{node}_arrival"] = t

    def record_service_start(self, node: str, t: float):
        self.timestamps[f"{node}_service_start"] = t

    def record_service_end(self, node: str, t: float):
        self.timestamps[f"{node}_service_end"] = t

    def get(self, key: str):
        return self.timestamps.get(key, None)

    def exit_time(self) -> Optional[float]:
        # Define exit as pharmacy_service_end if exists, else doctor_service_end, else None
        if self.get('pharmacy_service_end') is not None:
            return self.get('pharmacy_service_end')
        return self.get('doctor_service_end')
