"""
Resumes routes
- Upload master resume (PDF / DOCX)
- Parse + cache text via AI
- List / delete resumes
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.resume import Resume
from app.schemas.common import ResumeOut
from app.core.dependencies import get_current_user
from app.services.storage import upload_file_to_s3
from app.services.resume_parser import parse_resume_text, extract_style_snapshot

router = APIRouter()

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@router.post("/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    is_master: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a resume (PDF or DOCX). Parses text and stores in S3."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are accepted")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5 MB limit
        raise HTTPException(status_code=400, detail="File size must be under 5 MB")

    # Upload to S3
    s3_key = f"resumes/{current_user.id}/{file.filename}"
    await upload_file_to_s3(contents, s3_key, file.content_type)

    # Parse text for AI matching
    parsed_text = await parse_resume_text(contents, file.content_type)
    style_snapshot = await extract_style_snapshot(parsed_text)

    # If master, demote previous masters
    if is_master:
        result = await db.execute(
            select(Resume).where(Resume.user_id == current_user.id, Resume.is_master == True)
        )
        for old in result.scalars().all():
            old.is_master = False

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        s3_key=s3_key,
        parsed_text=parsed_text,
        style_snapshot=style_snapshot,
        is_master=is_master,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("/", response_model=list[ResumeOut])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id, Resume.is_active == True)
    )
    return result.scalars().all()


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume.is_active = False
    await db.commit()
