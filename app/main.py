from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection
from app.db.s3 import s3_client
from app.api import auth, directories, files, permissions, public, users
from app.services.auth_service import auth_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await connect_to_mongodb()
    await s3_client.ensure_bucket_exists()
    
    # Create admin user if not exists
    await auth_service.create_admin_user(
        email=settings.admin_email,
        password=settings.admin_password,
    )
    
    print("Application started")
    
    yield
    
    # Shutdown
    await close_mongodb_connection()
    print("Application stopped")


app = FastAPI(
    title="Storageinator",
    description="File storage service with S3 backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(directories.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(permissions.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Storageinator API", "docs": "/docs"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
