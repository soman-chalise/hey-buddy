"""Dataclasses for API request/response models."""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

# --- General Responses --- #
@dataclass
class BasicResponse:
    message: str

@dataclass
class BooleanResponse:
    result: bool

@dataclass
class TextResponse:
    text: str

# --- Element Related Responses --- #
@dataclass
class ElementResponse:
    role: str
    label: Optional[str] = None
    id: Optional[str] = None

@dataclass
class ElementsResponse:
    elements: List[ElementResponse]

@dataclass
class ClickResponse:
    method: str
    details: str
    coordinates: Optional[Tuple[float, float]] = None

@dataclass
class AttributesResponse:
    role: str
    properties: Dict[str, Optional[Any]] # Corresponds to HashMap<String, Option<serde_json::Value>>
    label: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    id: Optional[str] = None

@dataclass
class BoundsResponse:
    x: float
    y: float
    width: float
    height: float

# --- Base Request Structures --- #
@dataclass
class ChainedRequest:
    selector_chain: List[str]

# --- Specific Action Requests --- #
@dataclass
class TypeTextRequest(ChainedRequest):
    text: str

@dataclass
class GetTextRequest(ChainedRequest):
    max_depth: Optional[int] = None

@dataclass
class PressKeyRequest(ChainedRequest):
    key: str

# --- App/URL Requests --- #
@dataclass
class OpenApplicationRequest:
    app_name: str

@dataclass
class OpenUrlRequest:
    url: str
    browser: Optional[str] = None

# --- Expectation Requests --- #
@dataclass
class ExpectRequest(ChainedRequest):
    timeout_ms: Optional[int] = None

@dataclass
class ExpectTextRequest(ChainedRequest): # Inherit directly from ChainedRequest
    expected_text: str             # Non-default field
    timeout_ms: Optional[int] = None # Default field
    max_depth: Optional[int] = None  # Default field 