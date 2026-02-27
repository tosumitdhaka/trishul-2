from pydantic import BaseModel, ConfigDict


class TrishulBaseModel(BaseModel):
    """Shared Pydantic config for all Trishul models."""

    model_config = ConfigDict(
        populate_by_name=True,      # allow both alias and field name
        use_enum_values=True,       # serialize enums as their values
        str_strip_whitespace=True,  # strip leading/trailing whitespace
    )
