from pathlib import Path
from typing import Annotated, Callable, Literal, Union

from pydantic import BaseModel, Field


class PipelineError(Exception):
    """Base pipeline error"""

    pass


class ConfigError(PipelineError):
    pass


class StepExecutionError(PipelineError):
    pass


class InputError(PipelineError):
    pass


# 1. initial_prepare_data ----
class PrepareDataStepInput(BaseModel):
    main: str


class PrepareDataStepParams(BaseModel):
    threads: int


class PrepareDataStep(BaseModel):
    name: str
    engine: Literal["initial_prepare_data"]
    enabled: bool
    redo: bool
    input: PrepareDataStepInput
    output_dir: Path
    params: PrepareDataStepParams


# 1. convert_recombination_map ----
class MAPconverterInput(BaseModel):
    main: str


class MAPconverterParams(BaseModel):
    threads: int


class MAPconverterStep(BaseModel):
    name: str
    engine: Literal["convert_recombination_map"]
    enabled: bool
    redo: bool
    input: MAPconverterInput
    output_dir: Path
    params: MAPconverterParams


# 1. vcf_converter ----
class VCFconverterInput(BaseModel):
    main: str


class VCFconverterParams(BaseModel):
    threads: int


class VCFconverterStep(BaseModel):
    name: str
    engine: Literal["vcf_converter"]
    enabled: bool
    redo: bool
    input: VCFconverterInput
    output_dir: Path
    params: VCFconverterParams


# 1. Config ----
class Config(BaseModel):
    pipeline_steps: list[
        Annotated[
            Union[PrepareDataStep, VCFconverterStep, MAPconverterStep],
            Field(discriminator="engine"),
        ]
    ]


class StepsFunctionReturn(BaseModel):
    """

    file_pool:
    В случае нескольких input = [{"main": path, "ref": path}, ...]
    В случае одного input = [{"main": path}, {"main": path}, ...]
    """

    file_pool: list[dict[str, list[str]]]

    desc: str
    func: Callable
