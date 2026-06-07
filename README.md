## WisdomRetrieve

Enterprise RAG knowledge base QA system initialization.

### Local backend

Install and run inside the uv environment:

```powershell
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

The `/health` response reports app status plus MySQL and Redis connectivity.

### Configuration

Runtime configuration is loaded from `.env`. The local defaults are:

- MySQL: `root` / `040716`, database `wisdom_retrieve`
- Docker MySQL host port: `3307` by default, so it does not conflict with a local MySQL on `3306`
- Redis: `localhost:6379`
- ChromaDB path: `./chroma_db`
- PDF upload path: `./uploads`
- Qwen model: `qwen3.7-plus`
- QA cache TTL: `QA_CACHE_TTL_SECONDS=86400`

### Document API

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/document/upload -Form @{ file = Get-Item .\example.pdf }
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/document/index
Invoke-RestMethod http://127.0.0.1:8000/api/document/list
Invoke-RestMethod -Method Delete http://127.0.0.1:8000/api/document/1
```

### Chat API

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -ContentType 'application/json' -Body '{"session_id":"demo","question":"请根据知识库回答问题"}'
Invoke-RestMethod 'http://127.0.0.1:8000/api/chat/history?session_id=demo'
```

Repeated questions use Redis keys shaped like `qa:{question_hash}:kb:{version}:scope:{session}:top_k:{top_k}`.
The cached payload stores `answer`, `sources`, and hit `document_ids`; upload, delete, and index rebuild bump the knowledge base version.

### Monitor API

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/monitor/qa
```

### Docker Compose

```powershell
docker compose up --build
```

Services:

- `mysql`: MySQL 8.4, exposed on `3306`
- `redis`: Redis 7.4, exposed on `6379`
- `backend`: FastAPI, exposed on `8000`
- `frontend`: Vue/Vite static app through Nginx, exposed on `5173`
