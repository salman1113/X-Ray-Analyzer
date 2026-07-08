from datetime import date

from pydantic import BaseModel


class PatientCreateSchema(BaseModel):
    name: str
    age: int
    gender: str  # "M" | "F" | "Other"
    contact: str | None = None
    date_of_birth: date | None = None
    medical_history: list[str] | None = []


class PatientUpdateSchema(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    contact: str | None = None
    medical_history: list[str] | None = None


class PatientOut(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    contact: str | None = None
    medical_history: list[str] = []
    created_by: str
