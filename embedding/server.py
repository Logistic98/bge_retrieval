# -*- coding: utf-8 -*-

from contextlib import asynccontextmanager
from typing import Any, Dict, Set

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.loader import cfg
from controller.embedding_controller import router
from utils.exception import register_exception_handlers
from utils.log import get_logger, build_log_config
from utils.response import fail, ResponseMessage, ResponseCode


def _uvicorn_options_from_cfg() -> Dict[str, Any]:
    app_cfg = (cfg.get("app") or {})
    host = app_cfg.get("host")
    port = int(app_cfg.get("port"))

    return {
        "host": host,
        "port": port,
        "workers": 1,
    }


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.logger = get_logger()
        yield

    app = FastAPI(lifespan=lifespan)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[],
        max_age=600,
    )

    # 接口鉴权
    _auth_cfg = (cfg.get("auth") or {})
    _auth_enabled: bool = bool(_auth_cfg.get("enabled", False))
    _auth_keys: Set[str] = {str(x).strip() for x in (_auth_cfg.get("keys") or []) if str(x).strip()}

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        if not _auth_enabled:
            return await call_next(request)

        if not _auth_keys:
            return JSONResponse(
                fail(message=ResponseMessage.AUTH_FAIL, code=ResponseCode.AUTH_FAIL),
                status_code=ResponseCode.AUTH_FAIL,
            )

        auth_header = request.headers.get("authorization") or ""
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                fail(message=ResponseMessage.AUTH_FAIL, code=ResponseCode.AUTH_FAIL),
                status_code=ResponseCode.AUTH_FAIL,
            )

        token = auth_header.split(" ", 1)[1].strip()
        if token not in _auth_keys:
            return JSONResponse(
                fail(message=ResponseMessage.AUTH_FAIL, code=ResponseCode.AUTH_FAIL),
                status_code=ResponseCode.AUTH_FAIL,
            )

        return await call_next(request)

    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    opts = _uvicorn_options_from_cfg()
    uvicorn.run(
        "server:app",
        host=opts["host"],
        port=opts["port"],
        workers=opts["workers"],
        log_config=build_log_config(cfg),
        access_log=True,
    )
