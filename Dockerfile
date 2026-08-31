FROM python:3.12-slim

# ==============================
# Python / pip 环境配置
# ==============================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

# ==============================
# 工作目录
# ==============================
WORKDIR /app

# ==============================
# 先复制 requirements
# 充分利用 Docker 缓存
# ==============================
COPY requirements.txt ./

# ==============================
# 安装 Python 依赖
# ==============================
RUN python -m pip install \
    --no-cache-dir \
    --timeout 120 \
    --retries 10 \
    -r requirements.txt

# ==============================
# 复制 Python 源代码
# ==============================
COPY main.py ./
COPY hanzi_to_pinyin.py ./
COPY get_definition.py ./

# ==============================
# 复制前端模板和静态资源
# ==============================
COPY templates ./templates
COPY static ./static

# ==============================
# Flask 服务端口
# ==============================
EXPOSE 5000

# ==============================
# 启动程序
# ==============================
CMD ["python", "main.py"]