from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator


class PrepareDataStep(BaseModel):
    type: Literal["prepare_data"]
    enabled: bool
    redo: bool
    input_dir: Path
    output_dir: Path

    @field_validator("input_dir")
    @classmethod
    def input_must_exist(cls, v: Path):
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        return v


class AlignStep(BaseModel):
    type: Literal["align"]
    reference: str
    threads: int


class Config(BaseModel):
    pipeline_steps: list[
        Annotated[Union[PrepareDataStep, AlignStep], Field(discriminator="type")]
    ]
