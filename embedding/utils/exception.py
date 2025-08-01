# -*- coding: utf-8 -*-

from typing import Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.response import fail, ResponseCode, ResponseMessage
from utils.log import get_logger


async def _read_body_safely(request: Request) -> Optional[Any]:
    try:
        body = await request.body()
        if not body:
            return None
        try:
            import json
            return json.loads(body.decode("utf-8"))
        except Exception:
            return body.decode("utf-8", errors="ignore")
    except Exception:
        return None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        logger = get_logger()
        if logger:
            body = await _read_body_safely(request)
            await logger.error({
                "path": str(request.url),
                "type": "ValidationError",
                "errors": exc.errors(),
                "body": body,
            })
        return JSONResponse(
            fail(message=ResponseMessage.PARAM_FAIL,
                 code=ResponseCode.PARAM_FAIL,
                 data={"errors": exc.errors()}),
            status_code=ResponseCode.PARAM_FAIL,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        status = getattr(exc, "status_code", ResponseCode.BUSINESS_FAIL)
        message = str(getattr(exc, "detail", "")) or ResponseMessage.BUSINESS_FAIL
        logger = get_logger()
        if logger:
            body = await _read_body_safely(request)
            await logger.error({
                "path": str(request.url),
                "type": "HTTPException",
                "status": status,
                "detail": message,
                "body": body,
            })
        return JSONResponse(
            fail(message=message, code=status),
            status_code=status,
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger = get_logger()
        if logger:
            body = await _read_body_safely(request)
            await logger.error({
                "path": str(request.url),
                "type": "UnhandledException",
                "error": repr(exc),
                "body": body,
            })
        return JSONResponse(
            fail(message=ResponseMessage.BUSINESS_FAIL,
                 code=ResponseCode.BUSINESS_FAIL),
            status_code=ResponseCode.BUSINESS_FAIL,
        )
