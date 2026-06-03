import json
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator


class PipelineError(Exception):
    """Base pipeline error"""

    pass


class ConfigError(PipelineError):
    pass


class StepExecutionError(PipelineError):
    pass


class InputError(PipelineError):
    pass


class PrepareDataStep(BaseModel):
    type: Literal["prepare_data"]
    enabled: bool
    redo: bool
    input_glob: str
    output_dir: Path
    threads: int | Literal[1] = 1

    @field_validator("output_dir")
    @classmethod
    def input_must_exist(cls, v: Path):
        return v


class ConversionFinalReportToVcfStep(BaseModel):
    type: Literal["conversion_final_report_to_vcf"]
    enabled: bool = True
    redo: bool = True
    input: list[str]
    output_dir: Path
    threads: int | Literal[1] = 1

    @field_validator("input", mode="before")
    @classmethod
    def input_validator(cls, v: str):
        cash = json.loads(Path(f".cache/{v}/_all.json").read_text())
        output = cash.get("output", [])
        if len(output) == 0:
            raise InputError("input пустой")
        return output

    @field_validator("output_dir")
    @classmethod
    def input_must_exist(cls, v: Path):
        return v


class Config(BaseModel):
    pipeline_steps: list[
        Annotated[
            Union[PrepareDataStep, ConversionFinalReportToVcfStep],
            Field(discriminator="type"),
        ]
    ]


class StepsFunctionReturn(BaseModel):
    file_pool: list[str]
    desc: str
