import os

import yaml
from dotenv import load_dotenv

from src.config.schema import Config

load_dotenv()

with open(os.getenv("CONFIG", "config.yaml")) as f:
    raw = yaml.safe_load(f)

config = Config.model_validate(raw)
