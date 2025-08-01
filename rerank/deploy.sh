#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

### ===== 配置区（按需修改）=====
ENV_NAME="prod"                                           # 对应 config/config.$ENV_NAME.yml
IMAGE="rerank_image"                                      # 镜像名
TAG="latest"                                              # 镜像标签
CONTAINER="rerank"                                        # 容器名
HOST_PORT=8089                                            # 宿主机端口
APP_PORT=8089                                             # 容器端口
RESTART_POLICY="always"                                   # 重启策略
USE_BUILDKIT=true                                         # BuildKit 加速
MODEL_DIR="$(dirname "$(pwd)")/models/bge-reranker-v2-m3" # 权重模型目录
DEVICE="cpu"                                              # 仅允许: cpu | cuda
GPU_IDS="0"                                               # 仅当 DEVICE=cuda 时生效，仅支持单卡运行
### =================================

# ---------- 参数校验 ----------
case "${DEVICE}" in cpu|cuda) ;; *)
  echo "错误: DEVICE=${DEVICE}，仅支持 cpu|cuda"; exit 2
esac

# ---------- 处理 GPU 参数 ----------
GPU_ARGS=()
GPU_ENV=()
if [[ "${DEVICE}" == "cuda" ]]; then
  if [[ -n "${GPU_IDS}" ]]; then
    GPU_COUNT="$(awk -F',' '{print NF}' <<<"${GPU_IDS}")"
    if [[ "${GPU_COUNT}" -ne 1 ]]; then
      echo "错误: 仅支持单卡运行，当前指定了 ${GPU_COUNT} 张卡: ${GPU_IDS}"
      exit 2
    fi
    GPU_ARGS=(--gpus device="${GPU_IDS}")
  else
    echo "错误: DEVICE=cuda 时必须显式指定一张 GPU_ID，例如 GPU_IDS=0"
    exit 2
  fi
fi

# ---------- 读取配置 ----------
CONFIG_FILE="config/config.${ENV_NAME}.yml"
[[ -f "${CONFIG_FILE}" ]] || { echo "错误: 未找到 ${CONFIG_FILE}"; exit 2; }

# ---------- 打印配置 ----------
FULL_IMAGE="${IMAGE}:${TAG}"
echo "环境: ${ENV_NAME}"
echo "DEVICE: ${DEVICE}    GPU_IDS: ${GPU_IDS:-全部}"
echo "镜像: ${FULL_IMAGE}"
echo "容器: ${CONTAINER}"
echo "端口映射: ${HOST_PORT}:${APP_PORT}"
echo "模型权重目录: ${MODEL_DIR}"
echo "BuildKit: ${USE_BUILDKIT}"

# ---------- BuildKit ----------
if [[ "${USE_BUILDKIT}" == "true" ]]; then
  docker buildx version >/dev/null 2>&1 || { echo "错误: 未检测到 buildx 插件"; exit 2; }
  export DOCKER_BUILDKIT=1
fi

# ---------- 清理旧实例 ----------
CID="$(docker ps -aq -f name="^${CONTAINER}$" || true)"
[[ -n "${CID}" ]] && { echo "移除旧容器"; docker rm -f "${CONTAINER}" >/dev/null; }

IID="$(docker images -q "${FULL_IMAGE}" || true)"
[[ -n "${IID}" ]] && { echo "移除旧镜像"; docker rmi -f "${FULL_IMAGE}" >/dev/null; }

# ---------- 构建镜像 ----------
echo "构建镜像..."
docker build -t "${FULL_IMAGE}" .

# ---------- 运行容器 ----------
echo "运行容器..."

DOCKER_RUN_ARGS=(
  --name "${CONTAINER}"
  -e ENV="${ENV_NAME}"
  -e DEVICE="${DEVICE}"
  -v "${MODEL_DIR}:/models/bge-reranker-v2-m3"
  -p "${HOST_PORT}:${APP_PORT}"
  --restart "${RESTART_POLICY}"
)

if [[ "${DEVICE}" == "cuda" ]]; then
  DOCKER_RUN_ARGS+=("${GPU_ARGS[@]}")
fi

docker run -d "${DOCKER_RUN_ARGS[@]}" "${FULL_IMAGE}"

echo "部署完成，查看日志："
docker logs -f "${CONTAINER}"