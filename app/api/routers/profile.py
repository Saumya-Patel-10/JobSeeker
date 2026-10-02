"""``/profile`` routes."""

from __future__ import annotations

import shutil

import yaml
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import ValidationError

from app.api.deps import get_config
from app.config.loader import AppConfig, reload_config
from app.config.paths import RESUMES_MASTER_DIR, user_config_path
from app.models.profile import Profile
from app.utils.errors import ConfigError

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=Profile)
async def get_profile(config: AppConfig = Depends(get_config)) -> Profile:
    return config.profile


@router.put("", response_model=Profile)
async def update_profile(payload: Profile) -> Profile:
    path = user_config_path("profile.yaml")
    path.write_text(yaml.safe_dump(payload.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
    try:
        cfg = reload_config()
    except (ConfigError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=f"Updated profile failed validation: {exc}") from exc
    return cfg.profile


@router.post("/master-resume/upload")
async def upload_master_resume(file: UploadFile) -> dict:
    """Upload a master resume PDF to data/resumes/master/master_resume.pdf."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    RESUMES_MASTER_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESUMES_MASTER_DIR / "master_resume.pdf"
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"saved_to": str(dest), "filename": file.filename, "size_bytes": dest.stat().st_size}


@router.get("/master-resume/info")
async def master_resume_info() -> dict:
    """Return metadata about the currently stored master resume PDF."""
    dest = RESUMES_MASTER_DIR / "master_resume.pdf"
    if not dest.exists():
        return {"exists": False, "filename": None, "size_bytes": None, "path": None}
    return {
        "exists": True,
        "filename": "master_resume.pdf",
        "size_bytes": dest.stat().st_size,
        "path": str(dest),
    }
