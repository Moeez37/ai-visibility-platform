import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

DOMAIN_PATTERN = re.compile(r"^(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,}$")


def _check_domain(value: str) -> str:
    domain = value.strip().lower()
    if not DOMAIN_PATTERN.fullmatch(domain):
        raise ValueError("Use a bare domain such as example.com, without http:// or a path.")
    return domain


Domain = Annotated[str, AfterValidator(_check_domain)]
RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ProfileCreate(BaseModel):
    name: Annotated[RequiredText, StringConstraints(max_length=255)]
    domain: Domain
    industry: Annotated[RequiredText, StringConstraints(max_length=255)]
    description: RequiredText
    competitors: list[Domain] = Field(default_factory=list, max_length=20)


class QueryFilters(BaseModel):
    min_score: float | None = Field(default=None, ge=0, le=1)
    status: Literal["visible", "not_visible", "unknown"] | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
