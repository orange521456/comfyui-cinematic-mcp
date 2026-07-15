# ComfyUI Docker — 支持 Blackwell RTX 5060 (sm_120)
# 使用 PyTorch 官方 CUDA 12.8 镜像（兼容 Blackwell 架构）
FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime

# 避免交互式安装卡住
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 使用阿里云镜像加速（避免默认源访问失败）
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list || true && \
    sed -i 's@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list || true

WORKDIR /app

# 安装系统依赖
# git: 部分自定义节点需要
# libgl1, libglib2.0-0: opencv 运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制 ComfyUI 依赖清单
COPY requirements.txt /tmp/comfyui-requirements.txt

# 安装 Python 依赖
# base 镜像已含 torch/torchvision/torchaudio（与 CUDA 12.8 匹配），跳过它们避免被覆盖
# 使用清华 pip 镜像加速
# 注意：用 \b 边界匹配，避免误删 torchsde（以 torch 开头但是独立包）
RUN grep -v -E '^(torch|torchvision|torchaudio)(\b|[<>=!~;])' /tmp/comfyui-requirements.txt > /tmp/req-no-torch.txt && \
    cat /tmp/req-no-torch.txt && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r /tmp/req-no-torch.txt

# ComfyUI 源代码由 docker-compose bind-mount 提供（host C:\Users\17386\ComfyUI → /app/ComfyUI）
WORKDIR /app/ComfyUI

# 暴露 ComfyUI 端口
EXPOSE 8188

# 输出目录使用单独挂载（避免与 host ComfyUI 冲突）
VOLUME ["/output", "/input"]

# 启动 ComfyUI，监听所有网卡，输出到 /output 挂载点
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--output-directory", "/output", "--input-directory", "/input"]
