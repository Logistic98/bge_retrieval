# -*- coding: utf-8 -*-

import os
import math
import uuid
from functools import lru_cache
from typing import Dict, Any, List, Tuple

from FlagEmbedding import FlagReranker

from config.loader import cfg
from utils.log import get_logger

_RERANK = (cfg.get("rerank") or {})
_MODELS: Dict[str, str] = _RERANK.get("models") or {}

# 仅允许：cpu | cuda，优先读取环境变量，其次 YML，最后默认 cpu
_DEVICE: str = str(os.getenv("DEVICE") or _RERANK.get("device", "cpu")).strip().lower()
_ALLOWED = {"cpu", "cuda"}
if _DEVICE not in _ALLOWED:
    raise ValueError(f"rerank.device 仅支持 {_ALLOWED}，当前：{_DEVICE}")

# 仅 cuda 支持 fp16
_USE_FP16 = _DEVICE == "cuda"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@lru_cache(maxsize=1)
def _load_engines() -> Dict[str, FlagReranker]:
    logger = get_logger()
    engines: Dict[str, FlagReranker] = {}

    if logger:
        import asyncio
        asyncio.create_task(
            logger.info(
                {
                    "rerank_init": {
                        "device": _DEVICE,
                        "use_fp16": _USE_FP16,
                        "models": list(_MODELS.keys()),
                    }
                }
            )
        )

    for name, path in _MODELS.items():
        try:
            engines[name] = FlagReranker(
                model_name_or_path=path,
                use_fp16=_USE_FP16,
                local_files_only=True,
                device=_DEVICE,
            )
            if logger:
                import asyncio
                asyncio.create_task(
                    logger.info(
                        {
                            "model_ready": {
                                "name": name,
                                "path": path,
                                "device": _DEVICE,
                                "fp16": _USE_FP16,
                            }
                        }
                    )
                )
        except Exception as e:
            if logger:
                import asyncio
                asyncio.create_task(
                    logger.error(
                        {
                            "model_init_failed": {
                                "name": name,
                                "path": path,
                                "err": str(e),
                            }
                        }
                    )
                )
            raise
    return engines


def compute_rerank(
    query: str,
    documents: List[str],
    model_name: str,
    top_n: int | None = None,
) -> Dict[str, Any]:
    engines = _load_engines()
    if model_name not in engines:
        raise RuntimeError(f"模型未初始化：{model_name}")
    rk = engines[model_name]

    pairs = [[query, doc] for doc in documents]
    scores = rk.compute_score(pairs)
    if isinstance(scores, float):
        scores = [scores]

    actual_top = len(documents) if top_n is None else max(0, min(top_n, len(documents)))
    combined: List[Tuple[int, float]] = list(
        zip(range(len(documents)), [float(s) for s in scores])
    )
    combined.sort(key=lambda x: x[1], reverse=True)
    selected = combined[:actual_top]

    return {
        "id": str(uuid.uuid4()),
        "results": [
            {
                "index": idx,
                "relevance_score": _sigmoid(score),
                "text": documents[idx],
            }
            for idx, score in selected
        ],
    }
