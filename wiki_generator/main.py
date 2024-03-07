from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from wiki_generator.app.views import (
    data_analysis,
    export_csv, 
    healthcheck, 
    docs,  
    search, 
    list_wiki_data, 
    retrieve_wiki_data
)
from wiki_generator.middleware import SwitchDatabaseMiddleware
from .config import settings


def get_app() -> Starlette:
    middleware = [
        Middleware(SwitchDatabaseMiddleware),
    ]
    routes = [
        Route("/healthcheck", endpoint=healthcheck, methods=["GET"]),
        Mount("/static", app=StaticFiles(directory='static'), name="static"),
        Route("/docs", endpoint=docs, methods=["GET"]),
        Mount(
            "/api",
            routes=[
                Route("/search", endpoint=search, methods=["POST"]),
                Route("/analyze", endpoint=data_analysis, methods=["POST"]),
                Route("/wiki_data", endpoint=list_wiki_data, methods=["GET"]),
                Route("/wiki_data/{pk}", endpoint=retrieve_wiki_data, methods=["GET"]),   
                Route("/report", endpoint=export_csv, methods=["GET"])
            ],
            middleware=middleware
        ),
    ]

    application = Starlette(
        debug=settings.DEBUG,
        routes=routes,
    )
    return application

limiter = Limiter(key_func=get_remote_address)

app = get_app()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)