from pydantic import BaseModel


class FieldMapping(BaseModel):
    source_field: str
    suggested_wms_field: str
    internal_field: str
    confidence: float
    reason: str


class MappingResponse(BaseModel):
    mappings: list[FieldMapping]