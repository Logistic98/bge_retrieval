# -*- coding: utf-8 -*-

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.request import RerankRequest
from utils.response import success, fail, ResponseCode, ResponseMessage
from service.rerank_service import compute_rerank
from config.loader import cfg

router = APIRouter()


@router.post("/v1/rerank")
async def rerank_api(request: Request, body: RerankRequest):
    try:
        models_cfg = (cfg.get("rerank") or {}).get("models") or {}
        model_name = body.model or next(iter(models_cfg.keys()), None)
        if not model_name or model_name not in models_cfg:
            return JSONResponse(
                content=fail(
                    message=f"model 必须在以下范围内：{list(models_cfg.keys())}。",
                    code=ResponseCode.PARAM_FAIL,
                ),
                status_code=ResponseCode.PARAM_FAIL,
            )

        if not body.query or not body.documents:
            return JSONResponse(
                content=fail(
                    message=ResponseMessage.PARAM_FAIL,
                    code=ResponseCode.PARAM_FAIL,
                    data={"errors": [{"loc": ["body", "query/documents"], "msg": "query/documents 不能为空"}]},
                ),
                status_code=ResponseCode.PARAM_FAIL,
            )

        data = compute_rerank(body.query, body.documents, model_name, body.top_n)
        return JSONResponse(content=success(data))

    except Exception as e:
        return JSONResponse(
            content=fail(message=f"{e}", code=ResponseCode.BUSINESS_FAIL),
            status_code=ResponseCode.BUSINESS_FAIL,
        )
