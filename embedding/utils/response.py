# -*- coding: utf-8 -*-

class ResponseCode:
    SUCCESS = 200
    PARAM_FAIL = 400
    AUTH_FAIL = 403
    BUSINESS_FAIL = 500


class ResponseMessage:
    SUCCESS = "接口请求成功"
    PARAM_FAIL = "参数校验失败"
    AUTH_FAIL = "接口鉴权失败"
    BUSINESS_FAIL = "业务处理失败"


def success(data=None, message=ResponseMessage.SUCCESS):
    return {
        "code": ResponseCode.SUCCESS,
        "message": message,
        "data": data,
    }


def fail(message=ResponseMessage.BUSINESS_FAIL, code=ResponseCode.BUSINESS_FAIL, data=None):
    return {
        "code": code,
        "message": message,
        "data": data,
    }
