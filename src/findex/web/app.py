# src/findex/web/app.py
from contextlib import asynccontextmanager
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, Request, Query, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from findex.search_engine import SearchEngine
from findex.web.config import settings

logger = logging.getLogger("findex.web")

ml_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading index from %s", settings.index_path)
    if settings.index_path.exists():
        try:
            ml_state["engine"] = SearchEngine(settings.index_path)
            ml_state["loaded"] = True
            logger.info("Index loaded successfully.")
        except Exception as e:
            logger.error("Failed to load index: %s", e)
            ml_state["loaded"] = False
    else:
        logger.warning("Index file not found at startup: %s", settings.index_path)
        ml_state["loaded"] = False
    yield
    ml_state.clear()


app = FastAPI(title="Findex Web API", lifespan=lifespan)

templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


class SearchResultItem(BaseModel):
    doc_id: str
    doc_path: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    k: int
    results: List[SearchResultItem]


class StatsResponse(BaseModel):
    total_documents: int
    vocabulary_size: int
    is_loaded: bool


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Request %s failed: %s", request_id, exc)
        return HTMLResponse(status_code=500, content=f"Internal Server Error. Request ID: {request_id}")


def get_engine() -> SearchEngine:
    if not ml_state.get("loaded", False):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Index not loaded")
    return ml_state["engine"]


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    if not ml_state.get("loaded", False):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Index not loaded")
    return {"status": "ok"}


@app.get("/stats", response_model=StatsResponse)
def get_stats(engine: SearchEngine = Depends(get_engine)):
    return StatsResponse(
        total_documents=len(engine.index.doc_titles),
        vocabulary_size=len(engine.index.index),
        is_loaded=True,
    )


@app.get("/search", response_model=SearchResponse)
def search_endpoint(
    q: str = Query(..., min_length=1),
    k: int = Query(10, ge=1, le=100),
    scorer: str = Query("bm25"),
    page: int = Query(1, ge=1),
    engine: SearchEngine = Depends(get_engine),
):
    results = engine.search(q, scorer=scorer)
    total = len(results)
    start = (page - 1) * k
    end = start + k
    page_results = results[start:end]

    items = [
        SearchResultItem(
            doc_id=str(res.doc_path),
            doc_path=str(res.doc_path),
            score=float(res.score),
            snippet=getattr(res, "snippet", ""),
        )
        for res in page_results
    ]
    return SearchResponse(query=q, total=total, page=page, k=k, results=items)


@app.get("/docs/{doc_id}")
def get_document(doc_id: str, engine: SearchEngine = Depends(get_engine)):
    if doc_id not in engine.index.doc_titles:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"doc_id": doc_id, "content": "Document text placeholder"}


@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})