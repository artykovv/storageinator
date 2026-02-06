# Storageinator

Backend-сервис для хранения файлов на S3-совместимом хранилище с управлением пользователями, иерархией директорий и гибкой системой прав доступа.

## 🚀 Features

- **Authentication**: JWT-based auth with access/refresh tokens
- **Directory Management**: Hierarchical directory structure
- **File Management**: Upload/download via presigned URLs (no files stored on backend)
- **Access Control**: Read/write/delete permissions with inheritance
- **Vue SPA**: Modern frontend with dark theme

## 🛠 Tech Stack

### Backend
- Python 3.12
- FastAPI
- MongoDB (Motor async driver)
- AWS S3 (MinIO for local development)
- JWT authentication

### Frontend
- Vue 3 + Vite
- Pinia (state management)
- Vue Router
- Axios

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose

### Run with Docker Compose

```bash
# 1. Clone the repository
git clone <repo-url>
cd storageinator

# 2. Create .env file from example
cp .env.example .env

# 3. (Optional) Edit .env to change settings
#    IMPORTANT: Change JWT_SECRET_KEY in production!

# 4. Start all services
docker compose up -d

# 5. Open in browser
#    Frontend: http://localhost:3000
#    API Docs: http://localhost:8000/docs
#    MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
```

### Stop Services

```bash
docker compose down

# To also remove volumes (data):
docker compose down -v
```

## 🔧 Configuration

Edit `.env` file to configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me...` | **CHANGE IN PRODUCTION!** |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | MinIO secret key |
| `MAX_FILE_SIZE_MB` | `100` | Max file upload size |
| `ALLOWED_MIME_TYPES` | `image/*,pdf...` | Allowed file types |

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Directories
- `POST /api/directories` - Create directory
- `GET /api/directories` - Get directory tree
- `GET /api/directories/{id}` - Get directory
- `DELETE /api/directories/{id}` - Delete directory

### Files
- `POST /api/files/upload-url` - Get presigned upload URL
- `POST /api/files/{id}/confirm` - Confirm upload
- `GET /api/files/{id}/download-url` - Get presigned download URL
- `DELETE /api/files/{id}` - Delete file
- `GET /api/files/directory/{id}` - List files in directory

### Permissions
- `POST /api/directories/{id}/permissions` - Grant permissions
- `DELETE /api/directories/{id}/permissions/{user_id}` - Revoke
- `GET /api/directories/{id}/permissions` - List permissions

## 🔐 Permission System

| Permission | Actions |
|------------|---------|
| `read` | View and download files |
| `write` | Upload and modify files |
| `delete` | Delete files |

Permissions are inherited from parent directories. Explicitly set permissions override inheritance.

## 📁 Project Structure

```
storageinator/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Config, security
│   ├── db/            # MongoDB, S3 clients
│   ├── models/        # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── api/       # Axios client
│   │   ├── components/
│   │   ├── router/
│   │   ├── stores/    # Pinia stores
│   │   └── views/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── pyproject.toml
```

## 🧑‍💻 Development Setup

For local development without Docker:

```bash
# Backend
poetry install
docker compose up -d mongodb minio
poetry run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## 📄 License

MIT
