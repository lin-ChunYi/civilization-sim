# 单服务镜像：Python 后台 + 网页 + 数据持久化都在一个容器里。
# 构建： docker build -f observer/deploy/Dockerfile -t civ-observer .
# 运行： docker run -p 8765:8765 -e OBSERVER_TOKEN=换成你的令牌 \
#           -v $PWD/observer-data:/var/data civ-observer
FROM python:3.12-slim

WORKDIR /app
COPY observer/requirements.txt /app/observer/requirements.txt
RUN pip install --no-cache-dir -r /app/observer/requirements.txt

# 冻结的模拟引擎 + 观察台。exp01/ exp02/ 也一并带上，便于核对基线（都是只读的）。
COPY exp01 /app/exp01
COPY exp02 /app/exp02
COPY exp03 /app/exp03
COPY observer /app/observer

ENV OBSERVER_DATA_DIR=/var/data \
    PYTHONUNBUFFERED=1 \
    PORT=8765
VOLUME ["/var/data"]
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",8765)}/api/health').read()"
CMD ["sh", "-c", "python -m uvicorn observer.app:app --host 0.0.0.0 --port ${PORT}"]
