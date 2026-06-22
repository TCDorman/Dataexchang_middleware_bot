# models/endpoint_models.py

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ResponseField:
    name: str
    type: str = "unknown"
    nullable: bool = False
    description: str = ""
    sample_value: Any = None


@dataclass
class EndpointSchema:
    path: str
    method: str
    summary: str = ""
    response_fields: list[ResponseField] = field(default_factory=list)


@dataclass
class EndpointConfig:
    url: str
    method: str
    direction: Literal["inbound_to_wms", "outbound_from_wms"]
    auth_strategy: str = "none"
    polling_frequency: str = "on_demand"
    selected_fields: list[ResponseField] = field(default_factory=list)
    request_body_schema: dict | None = None
    requests_per_minute: int = 60