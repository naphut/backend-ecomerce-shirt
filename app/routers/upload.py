from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
import shutil
import os
from uuid import uuid4
from pathlib import Path
from app.dependencies import get_current_admin_user

router = APIRouter()

# បង្កើត folder សម្រាប់រក្សាទុករូបភាព
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ប្រភេទឯកសារដែលអនុញ្ញាត
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'
}

# ទំហំឯកសារអតិបរមា 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

@router.post("/")
async def upload_image(
    file: UploadFile = File(...),
    admin = Depends(get_current_admin_user)
):
    """
    Upload an image file
    Returns the URL of the uploaded image
    """
    try:
        # ពិនិត្យទំហំឯកសារ
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE//1024//1024}MB"
            )
        
        # ពិនិត្យ MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{file.content_type}' not allowed"
            )
        
        # ពិនិត្យ extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File extension '{ext}' not allowed"
            )
        
        # បង្កើតឈ្មោះឯកសារថ្មីដោយប្រើ UUID
        filename = f"{uuid4()}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # រក្សាទុកឯកសារ
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # បង្កើត URL សម្រាប់ចូលមើលរូបភាព
        url = f"/static/uploads/{filename}"
        
        return {
            "url": url,
            "filename": filename,
            "size": file_size,
            "mime_type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")