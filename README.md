# Embedding & Rerank 服务

本项目封装了文本嵌入（Embedding）与重排序（Rerank）两个独立服务，分别基于 BGE-M3 与 BGE-Reranker-V2-M3 模型构建，提供统一风格的 FastAPI 接口，支持设备配置（CPU/CUDA）、令牌鉴权、容器化部署，适用于向量检索增强场景。

---

## 📁 目录结构

```ini
.
├── embedding/              # Embedding 服务代码
│   ├── config/             # 配置文件（dev/prod）
│   ├── controller/         # 路由接口
│   ├── service/            # 嵌入处理逻辑
│   ├── utils/              # 公共工具类
│   ├── deploy.sh           # Docker 部署脚本
│   ├── Dockerfile          # Docker 镜像构建文件
│   ├── pyproject.toml      # Python 依赖管理
│   └── server.py           # 服务启动入口
│
├── rerank/                 # Rerank 服务代码
│   ├── config/             # 配置文件（dev/prod）
│   ├── controller/         # 路由接口
│   ├── service/            # 重排序逻辑
│   ├── utils/              # 公共工具类
│   ├── deploy.sh           # Docker 部署脚本
│   ├── Dockerfile          # Docker 镜像构建文件
│   ├── pyproject.toml      # Python 依赖管理
│   └── server.py           # 服务启动入口
│
├── models/                 # 本地模型存储目录
│   └── download_models.py  # 下载模型脚本
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 本地启动

### Embedding 启动

```bash
$ cd embedding
$ uv run uvicorn server:app --host 0.0.0.0 --port 8088 --workers 1
```

### Rerank 启动

```bash
$ cd rerank
$ uv run uvicorn server:app --host 0.0.0.0 --port 8089 --workers 1
```

---

## 🐳 Docker 一键部署

### Embedding 部署

```bash
$ cd embedding
$ bash deploy.sh
```

### Rerank 部署

```bash
$ cd rerank
$ bash deploy.sh
```

---

## 🧪 接口测试

### Embedding 接口

```bash
$ curl -X POST "http://127.0.0.1:8088/v1/embeddings" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer sk-11111111111111111111111111111111" \
  --data '{
    "input": ["测试"],
    "model": "bge-m3"
  }'
  
{
    "code": 200,
    "message": "接口请求成功",
    "data": {
        "data": [
            {
                "sparse": {
                    "data": [
                        0.06353759765625,
                        0.361083984375
                    ],
                    "indices": [
                        6,
                        49125
                    ],
                    "indptr": [
                        0,
                        2
                    ],
                    "shape": [
                        1,
                        250002
                    ]
                },
                "dense": [
                    [
                        -0.027374267578125,
                        0.0117034912109375,
                        -0.03497314453125,
                        -0.01328277587890625,
												...
                        -0.0384521484375,
                        0.0263519287109375
                    ]
                ]
            }
        ],
        "model": "bge-m3",
        "object": "list",
        "usage": {
            "prompt_tokens": 2,
            "total_tokens": 2
        }
    }
}
```

### Rerank 接口

```bash
$ curl -X POST "http://127.0.0.1:8089/v1/rerank" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer sk-11111111111111111111111111111111" \
  --data '{
    "model": "bge-reranker-v2-m3",
    "query": "自然语言处理",
    "documents": [
      "深度学习基础教程",
      "天气预测算法解析",
      "Transformer模型原理"
    ]
  }'
  
{
    "code": 200,
    "message": "接口请求成功",
    "data": {
        "id": "41c197cb-59c7-4e0d-b98d-b516b7dd032d",
        "results": [
            {
                "index": 2,
                "relevance_score": 0.0008492456216931709,
                "text": "Transformer模型原理"
            },
            {
                "index": 0,
                "relevance_score": 0.0005680935199787149,
                "text": "深度学习基础教程"
            },
            {
                "index": 1,
                "relevance_score": 1.952588520864222e-05,
                "text": "天气预测算法解析"
            }
        ]
    }
}
```
