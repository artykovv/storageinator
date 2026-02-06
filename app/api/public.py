from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from app.services.file_service import file_service

router = APIRouter(prefix="/public/files", tags=["Public"])


@router.get("/{file_id}", response_class=RedirectResponse)
async def get_public_file_access(file_id: str):
    """
    Access a public file.
    Redirects to S3 presigned URL.
    No authentication required.
    """
    # Check if file exists and is public
    print(f"DEBUG: Requesting public file {file_id}")
    file_doc = await file_service.get_public_file(file_id)
    if not file_doc:
        print(f"DEBUG: File not found or not public: {file_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or not public",
        )
    
    # Generate presigned download URL (inline for preview)
    # We use service method which handles S3 interaction
    try:
        download_response = await file_service.get_preview_url(file_id)
        return RedirectResponse(url=download_response.presigned_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
