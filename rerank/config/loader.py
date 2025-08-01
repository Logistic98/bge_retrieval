# -*- coding: utf-8 -*-

import os
import yaml

ENV = os.getenv("ENV", "dev")

with open(f"config/config.{ENV}.yml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}
