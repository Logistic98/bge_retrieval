# -*- coding: utf-8 -*-

from typing import List
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.request import EmbeddingsRequest
from utils.response import success, fail, ResponseCode, ResponseMessage
from service.embedding_service import embed_texts, token_count
from config.loader import cfg

router = APIRouter()


@router.post("/v1/embeddings")
async def embeddings_api(request: Request, body: EmbeddingsRequest):
    try:
        models_cfg = (cfg.get("embedding") or {}).get("models") or {}
        model_name = body.model or next(iter(models_cfg.keys()), None)
        if not model_name or model_name not in models_cfg:
            return JSONResponse(
                content=fail(
                    message=f"model 必须在以下范围内：{list(models_cfg.keys())}。",
                    code=ResponseCode.PARAM_FAIL,
                ),
                status_code=ResponseCode.PARAM_FAIL,
            )

        inputs: List[str] = body.input or []
        if not inputs:
            return JSONResponse(
                content=fail(
                    message=ResponseMessage.PARAM_FAIL,
                    code=ResponseCode.PARAM_FAIL,
                    data={"errors": [{"loc": ["body", "input"], "msg": "input 不能为空"}]},
                ),
                status_code=ResponseCode.PARAM_FAIL,
            )

        data = embed_texts(inputs, model_name)
        count = sum(token_count(inputs, model_name))
        resp = {
            "data": data,
            "model": model_name,
            "object": "list",
            "usage": {"prompt_tokens": count, "total_tokens": count},
        }
        return JSONResponse(content=success(resp))
    except Exception as e:
        return JSONResponse(
            content=fail(message=f"{e}", code=ResponseCode.BUSINESS_FAIL),
            status_code=ResponseCode.BUSINESS_FAIL,
        )
