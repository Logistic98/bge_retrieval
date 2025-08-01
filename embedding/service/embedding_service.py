# -*- coding: utf-8 -*-

import os
from functools import lru_cache
from typing import List, Dict, Any

from FlagEmbedding import FlagModel

from config.loader import cfg
from utils.log import get_logger

_EMBED = (cfg.get("embedding") or {})
_MODELS: Dict[str, str] = _EMBED.get("models") or {}

# 仅允许：cpu | cuda，优先读取环境变量，其次 YML，最后默认 cpu
_DEVICE: str = str(os.getenv("DEVICE") or _EMBED.get("device", "cpu")).strip().lower()
_ALLOWED = {"cpu", "cuda"}
if _DEVICE not in _ALLOWED:
    raise ValueError(f"embedding.device 仅支持 {_ALLOWED}，当前：{_DEVICE}")

# 仅 cuda 支持 fp16
_USE_FP16 = _DEVICE == "cuda"


@lru_cache(maxsize=1)
def _load_engines() -> Dict[str, FlagModel]:
    logger = get_logger()
    engines: Dict[str, FlagModel] = {}

    if logger:
        import asyncio
        asyncio.create_task(logger.info({
            "embedding_init": {
                "device": _DEVICE,
                "use_fp16": _USE_FP16,
                "models": list(_MODELS.keys())
            }
        }))

    for name, path in _MODELS.items():
        try:
            engines[name] = FlagModel(
                model_name_or_path=path,
                use_fp16=_USE_FP16,
                device=_DEVICE,
                local_files_only=True
            )
            if logger:
                import asyncio
                asyncio.create_task(logger.info({
                    "model_ready": {"name": name, "path": path, "device": _DEVICE, "fp16": _USE_FP16}
                }))
        except Exception as e:
            if logger:
                import asyncio
                asyncio.create_task(logger.error({
                    "model_init_failed": {"name": name, "path": path, "err": str(e)}
                }))
            raise RuntimeError(f"模型加载失败: {name}, 错误信息: {e}")
    return engines


def embed_texts(texts: List[str], model_name: str) -> List[Dict[str, Any]]:
    engines = _load_engines()
    if model_name not in engines:
        raise RuntimeError(f"模型未初始化：{model_name}")
    ef = engines[model_name]

    dense = ef.encode(texts)

    return [{"dense": dense.tolist()}]


def token_count(texts: List[str], model_name: str) -> List[int]:
    engines = _load_engines()
    if model_name not in engines:
        raise RuntimeError(f"模型未初始化：{model_name}")
    tokenizer = engines[model_name].tokenizer
    enc = tokenizer.batch_encode_plus(
        texts, add_special_tokens=False, return_attention_mask=False, return_token_type_ids=False
    )
    return [len(ids) for ids in enc["input_ids"]]
