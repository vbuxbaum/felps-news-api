from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from news.db import create_db_and_table, engine, populate_table, is_table_empty
from news.model import News
from sqlmodel import Session, select


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    return Session(engine)


def create_response(news: list, category_filter: str, current_page: int, total_pages: int):
    return {
        "total_pages": total_pages,
        "current_page": current_page,
        "category_filter": category_filter,
        "result": news,
    }


@app.on_event("startup")
def on_startup():
    create_db_and_table()
    with get_session() as session:
        if is_table_empty(session, News):
            populate_table(session)


@app.get("/")
async def home():
    return {"detail": "news-api, access /docs for documentation"}


@app.get("/health")
async def health():
    return {"status": "healthy as a horse"}


@app.get("/get_news")
async def evaluation(category: str | None = None, page: int = 1):
    with get_session() as session:
        if category:
            news = session.exec(select(News).where(News.category == category.lower())).all()
        else:
            news = session.exec(select(News)).all()

    total_pages = (len(news) // 12) if len(news) % 12 == 0 else (len(news) // 12) + 1

    if int(page) == total_pages:
        return create_response(
            news[12 * (int(page) - 1) :], category, page, total_pages
        )
    elif 0 < int(page) < total_pages:
        return create_response(
            news[12 * (int(page) - 1) : 12 * (int(page))], category, page, total_pages
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="page does not exist"
        )
