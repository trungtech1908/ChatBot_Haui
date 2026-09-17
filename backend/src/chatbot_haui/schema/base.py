from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Model trả về cho frontend: field snake_case trong Python, camelCase trong JSON."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
