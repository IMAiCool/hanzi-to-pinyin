# 汉字转带声调拼音

一个基于 Flask、jieba 和 pypinyin 的汉字拼音转换工具，支持上下文分词、多音字读音展示、逐字复制和汉字释义查询。
基于bs4+requests获取获取单字释义，数据来源于https://www.zdic.net

## 功能

- 根据词语上下文生成带声调拼音
- 单字输入时展示全部候选读音
- 单字存在多个读音时提示“该字为多音字，找到 N 个读音”
- 提供完整拼音和逐字拼音结果
- 每个字符支持复制“字(音)”“拼音”“字+音”三种格式
- 支持按当前读音查询汉字释义
- 当前读音无对应释义时显示“未找到该读音释义”
- 支持最多 5000 个字符输入
- 提供健康检查接口，便于 Docker 部署监控

## 项目结构

```text
.
├── main.py                 # Flask 应用及接口
├── hanzi_to_pinyin.py      # 分词与拼音转换
├── get_definition.py       # 汉字释义请求与解析
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 镜像配置
├── templates/
│   └── index.html          # 页面模板
├── static/
│   ├── app.js              # 页面交互
│   ├── style.css           # 页面样式
│   └── favicon.png         # 网站图标
└── tests/
    └── test_app.py         # 接口测试
```

## 本地运行

要求 Python 3.10 或更高版本。

### Windows PowerShell

```powershell
cd D:\Project\flask-hanzi-pinyin
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

访问：<http://127.0.0.1:5000>

## Docker 部署

Dockerfile 默认通过阿里云 PyPI 镜像安装依赖。

```bash
docker build --no-cache -t flask-hanzi-pinyin .
docker run -d \
  --name flask-hanzi-pinyin \
  --restart unless-stopped \
  -p 5000:5000 \
  flask-hanzi-pinyin
```

访问：<http://服务器IP:5000>

查看日志：

```bash
docker logs -f flask-hanzi-pinyin
```

健康检查：

```bash
curl http://127.0.0.1:5000/health
```

返回：

```json
{"status":"ok"}
```

## API

### 拼音转换

```http
POST /pinyin
Content-Type: application/json
```

请求示例：

```json
{"text":"银行行长"}
```

返回示例：

```json
{
  "text": "银行行长",
  "result": [
    {"index": 1, "char": "银", "pinyin": "yín"},
    {"index": 2, "char": "行", "pinyin": "háng"},
    {"index": 3, "char": "行", "pinyin": "háng"},
    {"index": 4, "char": "长", "pinyin": "zhǎng"}
  ]
}
```

### 汉字释义

```http
POST /definition
Content-Type: application/json
```

请求示例：

```json
{"text":"行"}
```

释义来自外部汉典页面，因此容器必须能够访问互联网。外部请求失败时接口返回 `502`，未解析到释义时返回 `404`。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

## 常见部署问题

### 容器提示找不到本地模块

请从项目根目录构建镜像，并确认 `main.py`、`hanzi_to_pinyin.py` 和 `get_definition.py` 均已复制到 `/app`：

```bash
docker run --rm flask-hanzi-pinyin ls -la /app
```

### 页面与本地版本不一致

重新构建镜像并使用 `Ctrl + F5` 强制刷新浏览器。如果使用 Nginx 或 CDN，还需要清除静态资源缓存。

### 释义查询失败

在容器中检查汉典网站的网络连通性：

```bash
docker exec flask-hanzi-pinyin python -c "import requests; print(requests.get('https://www.zdic.net/hans/行', timeout=10).status_code)"
```
