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


"""
    - name: prepare_data
    engine: manage_project_files
    enabled: true
    redo: false
    input:
      main: "tests/data/raw/*.zip"
    output_dir: "tests/data/unpacked/"
    params:
      threads: 2
"""


class PrepareDataStepInput(BaseModel):
    main: str


class PrepareDataStepParams(BaseModel):
    threads: int


class PrepareDataStep(BaseModel):
    name: str
    engine: Literal["manage_project_files"]
    enabled: bool
    redo: bool
    input: PrepareDataStepInput
    output_dir: Path
    params: PrepareDataStepParams


class VCFconverterInput(BaseModel):
    main: str


class VCFconverterParams(BaseModel):
    threads: int


class VCFconverterStep(BaseModel):
    name: str
    engine: Literal["vcf-converter"]
    enabled: bool
    redo: bool
    input: VCFconverterInput
    output_dir: Path
    params: VCFconverterParams


class Config(BaseModel):
    pipeline_steps: list[
        Annotated[
            Union[PrepareDataStep, VCFconverterStep],
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
