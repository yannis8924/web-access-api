# Web Access API (Railway-ready)

这是一个可直接部署到 Railway/Render 的最小可用 API，用于给 Custom GPT 提供网页分析与小红书内容拆解能力。

## 1. 包含接口
- `POST /analyze`：通用网页分析
- `POST /xhs-note`：小红书专用拆解
- `GET /health`：健康检查

## 2. 本地运行（有 Docker 更简单）
```bash
cp .env.example .env
# 修改 API_KEY 和 BASE_URL

docker build -t web-access-api .
docker run -p 8000:8000 --env-file .env web-access-api
```

本地打开：
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## 3. 测试接口
### analyze
```bash
curl -X POST 'http://localhost:8000/analyze' \
  -H 'Authorization: Bearer replace-with-a-long-secret' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com",
    "focus": "structure",
    "screenshot": true,
    "use_browser": true
  }'
```

### xhs-note
```bash
curl -X POST 'http://localhost:8000/xhs-note' \
  -H 'Authorization: Bearer replace-with-a-long-secret' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://www.xiaohongshu.com/discovery/item/xxxxxxxx",
    "focus": "selling_points",
    "screenshot": true,
    "use_browser": true
  }'
```

## 4. Railway 部署（最傻瓜版）
1. 把整个目录上传到 GitHub 仓库。
2. 打开 Railway，新建 Project。
3. 选择 `Deploy from GitHub repo`。
4. 选中这个仓库。
5. 在 Variables 里设置：
   - `API_KEY`：你自己设置一个长字符串
   - `BASE_URL`：部署成功后你的真实域名，例如 `https://xxx.up.railway.app`
6. 点击部署。
7. 部署成功后访问：`https://你的域名/health`，看到 `ok: true` 就说明成功。

## 5. 在 GPT 里怎么接
1. 打开 ChatGPT → Explore GPTs → Create。
2. 在 Configure 里填写 Name / Description / Instructions。
3. 进入 Actions → Create new action。
4. Authentication 选择 API Key（Bearer）。
5. 把 `openapi.yaml` 内容粘进去，把 `servers.url` 改成你的真实域名。
6. 保存后在 Preview 里测试。

## 6. 重要说明
- 小红书页面可能受登录、地区、风控、动态加载影响，结果可能不稳定。
- 这是一个最小可用版本，优先解决“先跑通”。
- 真正上线后，可以继续补更稳的站点模板和截图存储方式（例如 S3/R2）。
