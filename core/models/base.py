from pydantic import BaseModel, ConfigDict


class TrishulBaseModel(BaseModel):
    """Shared Pydantic config for all Trishul models."""
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )
