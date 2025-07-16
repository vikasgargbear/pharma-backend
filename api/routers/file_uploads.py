"""
File Uploads Router - All file management endpoints
Supabase Storage compatible with local fallback
Supports documents, images, and pharmaceutical compliance files
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid
import mimetypes
from pathlib import Path

from ..database import get_db
from .. import models, schemas, crud
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..core.config import settings, get_supabase_client

# Create router
router = APIRouter(prefix="/files", tags=["file_uploads"])

# Create CRUD instances
file_upload_crud = create_crud(models.FileUpload)

# ================= FILE UPLOAD UTILITIES =================

def validate_file(file: UploadFile) -> bool:
    """Validate file type and size"""
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )
    
    # Check file size (if we can determine it)
    if hasattr(file, 'size') and file.size:
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        if file.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file.size} exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
            )
    
    return True

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename with timestamp and UUID"""
    file_extension = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}{file_extension}"

def save_file_locally(file: UploadFile, filename: str) -> str:
    """Save file to local storage"""
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_PATH)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Full file path
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return str(file_path)

def save_file_supabase(file: UploadFile, filename: str) -> str:
    """Save file to Supabase storage"""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Reset file pointer
        file.file.seek(0)
        
        # Upload to Supabase storage
        response = supabase.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
            filename, file.file.read()
        )
        
        if response.get('error'):
            raise HTTPException(status_code=500, detail=f"Upload failed: {response['error']}")
        
        # Get public URL
        public_url = supabase.storage.from_(settings.SUPABASE_STORAGE_BUCKET).get_public_url(filename)
        return public_url
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase upload failed: {str(e)}")

# ================= FILE UPLOAD ENDPOINTS =================

@router.post("/upload", response_model=schemas.FileUpload)
@handle_database_error
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query(..., description="File category (document, image, certificate, etc.)"),
    description: Optional[str] = Query(None, description="File description"),
    entity_type: Optional[str] = Query(None, description="Related entity type"),
    entity_id: Optional[int] = Query(None, description="Related entity ID"),
    db: Session = Depends(get_db)
):
    """Upload a file"""
    # Validate file
    validate_file(file)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Determine storage method
    if settings.is_supabase:
        file_url = save_file_supabase(file, unique_filename)
        storage_type = "supabase"
    else:
        file_path = save_file_locally(file, unique_filename)
        file_url = f"/files/download/{unique_filename}"
        storage_type = "local"
    
    # Get file metadata
    file_size = len(file.file.read()) if hasattr(file.file, 'read') else 0
    file.file.seek(0)  # Reset file pointer
    
    mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    # Create database record
    file_data = {
        "filename": file.filename,
        "unique_filename": unique_filename,
        "file_path": file_url,
        "file_size": file_size,
        "mime_type": mime_type,
        "category": category,
        "description": description,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "storage_type": storage_type,
        "uploaded_at": datetime.utcnow(),
        "is_active": True
    }
    
    uploaded_file = file_upload_crud.create(db, schemas.FileUploadCreate(**file_data))
    
    return uploaded_file

@router.post("/upload-multiple")
@handle_database_error
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    category: str = Query(..., description="File category"),
    description: Optional[str] = Query(None, description="Files description"),
    entity_type: Optional[str] = Query(None, description="Related entity type"),
    entity_id: Optional[int] = Query(None, description="Related entity ID"),
    db: Session = Depends(get_db)
):
    """Upload multiple files"""
    uploaded_files = []
    
    for file in files:
        try:
            # Validate file
            validate_file(file)
            
            # Generate unique filename
            unique_filename = generate_unique_filename(file.filename)
            
            # Determine storage method
            if settings.is_supabase:
                file_url = save_file_supabase(file, unique_filename)
                storage_type = "supabase"
            else:
                file_path = save_file_locally(file, unique_filename)
                file_url = f"/files/download/{unique_filename}"
                storage_type = "local"
            
            # Get file metadata
            file_size = len(file.file.read()) if hasattr(file.file, 'read') else 0
            file.file.seek(0)  # Reset file pointer
            
            mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            
            # Create database record
            file_data = {
                "filename": file.filename,
                "unique_filename": unique_filename,
                "file_path": file_url,
                "file_size": file_size,
                "mime_type": mime_type,
                "category": category,
                "description": description,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "storage_type": storage_type,
                "uploaded_at": datetime.utcnow(),
                "is_active": True
            }
            
            uploaded_file = file_upload_crud.create(db, schemas.FileUploadCreate(**file_data))
            uploaded_files.append(uploaded_file)
            
        except Exception as e:
            # Log error but continue with other files
            print(f"Error uploading {file.filename}: {str(e)}")
            continue
    
    return {
        "uploaded_count": len(uploaded_files),
        "total_files": len(files),
        "uploaded_files": uploaded_files
    }

# ================= FILE MANAGEMENT ENDPOINTS =================

@router.get("/", response_model=List[schemas.FileUpload])
@handle_database_error
def get_files(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get uploaded files with filtering"""
    query = db.query(models.FileUpload).filter(models.FileUpload.is_active == True)
    
    if category:
        query = query.filter(models.FileUpload.category == category)
    if entity_type:
        query = query.filter(models.FileUpload.entity_type == entity_type)
    if entity_id:
        query = query.filter(models.FileUpload.entity_id == entity_id)
    
    return query.order_by(models.FileUpload.uploaded_at.desc()).offset(skip).limit(limit).all()

@router.get("/{file_id}", response_model=schemas.FileUpload)
@handle_database_error
def get_file(file_id: int, db: Session = Depends(get_db)):
    """Get file by ID"""
    file = file_upload_crud.get(db, file_id)
    if not file or not file.is_active:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.get("/download/{unique_filename}")
@handle_database_error
def download_file(unique_filename: str, db: Session = Depends(get_db)):
    """Download file by unique filename"""
    # Get file record
    file_record = db.query(models.FileUpload).filter(
        models.FileUpload.unique_filename == unique_filename,
        models.FileUpload.is_active == True
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # For Supabase storage, redirect to public URL
    if file_record.storage_type == "supabase":
        return {"download_url": file_record.file_path}
    
    # For local storage, serve file
    file_path = Path(settings.UPLOAD_PATH) / unique_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        filename=file_record.filename,
        media_type=file_record.mime_type
    )

@router.delete("/{file_id}")
@handle_database_error
def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Delete a file"""
    file_record = file_upload_crud.get(db, file_id)
    if not file_record or not file_record.is_active:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Soft delete - mark as inactive
    file_record.is_active = False
    file_record.deleted_at = datetime.utcnow()
    db.commit()
    
    # TODO: Actually delete file from storage (optional)
    # For now, we keep files for audit purposes
    
    return {"message": "File deleted successfully"}

# ================= FILE ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_file_analytics(db: Session = Depends(get_db)):
    """Get file upload analytics"""
    # Total files
    total_files = db.query(models.FileUpload).filter(models.FileUpload.is_active == True).count()
    
    # Files by category
    category_counts = db.query(
        models.FileUpload.category,
        db.func.count(models.FileUpload.id)
    ).filter(models.FileUpload.is_active == True).group_by(models.FileUpload.category).all()
    
    # Files by storage type
    storage_counts = db.query(
        models.FileUpload.storage_type,
        db.func.count(models.FileUpload.id)
    ).filter(models.FileUpload.is_active == True).group_by(models.FileUpload.storage_type).all()
    
    # Total storage used
    total_size = db.query(db.func.sum(models.FileUpload.file_size)).filter(
        models.FileUpload.is_active == True
    ).scalar() or 0
    
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "category_distribution": dict(category_counts),
        "storage_distribution": dict(storage_counts)
    }

@router.get("/analytics/recent")
@handle_database_error
def get_recent_uploads(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get recent upload analytics"""
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    recent_files = db.query(models.FileUpload).filter(
        models.FileUpload.uploaded_at >= start_date,
        models.FileUpload.is_active == True
    ).all()
    
    # Daily upload counts
    daily_counts = {}
    for file in recent_files:
        day_key = file.uploaded_at.date().isoformat()
        if day_key not in daily_counts:
            daily_counts[day_key] = 0
        daily_counts[day_key] += 1
    
    return {
        "period_days": days,
        "total_uploads": len(recent_files),
        "daily_uploads": daily_counts,
        "avg_uploads_per_day": len(recent_files) / days if days > 0 else 0
    }

# ================= ENTITY-SPECIFIC FILE ENDPOINTS =================

@router.get("/entity/{entity_type}/{entity_id}", response_model=List[schemas.FileUpload])
@handle_database_error
def get_entity_files(
    entity_type: str,
    entity_id: int,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get files for a specific entity"""
    query = db.query(models.FileUpload).filter(
        models.FileUpload.entity_type == entity_type,
        models.FileUpload.entity_id == entity_id,
        models.FileUpload.is_active == True
    )
    
    if category:
        query = query.filter(models.FileUpload.category == category)
    
    return query.order_by(models.FileUpload.uploaded_at.desc()).all()

@router.get("/customer/{customer_id}/documents", response_model=List[schemas.FileUpload])
@handle_database_error
def get_customer_documents(customer_id: int, db: Session = Depends(get_db)):
    """Get all documents for a customer"""
    return db.query(models.FileUpload).filter(
        models.FileUpload.entity_type == "customer",
        models.FileUpload.entity_id == customer_id,
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()

@router.get("/product/{product_id}/images", response_model=List[schemas.FileUpload])
@handle_database_error
def get_product_images(product_id: int, db: Session = Depends(get_db)):
    """Get all images for a product"""
    return db.query(models.FileUpload).filter(
        models.FileUpload.entity_type == "product",
        models.FileUpload.entity_id == product_id,
        models.FileUpload.category == "image",
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()

# ================= COMPLIANCE DOCUMENT ENDPOINTS =================

@router.get("/compliance/certificates", response_model=List[schemas.FileUpload])
@handle_database_error
def get_compliance_certificates(db: Session = Depends(get_db)):
    """Get all compliance certificates"""
    return db.query(models.FileUpload).filter(
        models.FileUpload.category == "certificate",
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()

@router.get("/compliance/licenses", response_model=List[schemas.FileUpload])
@handle_database_error
def get_license_documents(db: Session = Depends(get_db)):
    """Get all license documents"""
    return db.query(models.FileUpload).filter(
        models.FileUpload.category == "license",
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()

@router.post("/compliance/upload-certificate")
@handle_database_error
async def upload_compliance_certificate(
    file: UploadFile = File(...),
    certificate_type: str = Query(..., description="Type of certificate"),
    expiry_date: Optional[str] = Query(None, description="Certificate expiry date"),
    db: Session = Depends(get_db)
):
    """Upload a compliance certificate"""
    # Validate file
    validate_file(file)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Save file
    if settings.is_supabase:
        file_url = save_file_supabase(file, unique_filename)
        storage_type = "supabase"
    else:
        file_path = save_file_locally(file, unique_filename)
        file_url = f"/files/download/{unique_filename}"
        storage_type = "local"
    
    # Get file metadata
    file_size = len(file.file.read()) if hasattr(file.file, 'read') else 0
    file.file.seek(0)
    
    mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    # Create database record
    file_data = {
        "filename": file.filename,
        "unique_filename": unique_filename,
        "file_path": file_url,
        "file_size": file_size,
        "mime_type": mime_type,
        "category": "certificate",
        "description": f"{certificate_type} certificate",
        "entity_type": "compliance",
        "storage_type": storage_type,
        "uploaded_at": datetime.utcnow(),
        "is_active": True
    }
    
    uploaded_file = file_upload_crud.create(db, schemas.FileUploadCreate(**file_data))
    
    return uploaded_file 