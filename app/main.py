import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pyinstrument import Profiler
 
from app.core.config import Config
from app.core.logging import setup_logging
from app.core.database import engine, check_database_connection
from app.models.models import Base
from app.routes.auth import router as auth_router
from app.routes import election, location, meta, member, candidate, notification, result, nomination
from app.tasks.scheduler import start_scheduler
 
from app.tasks.scheduler import scheduler
from app.tasks.election_tasks import run_status_update
from app.services.result_scheduler import start_result_scheduler
from app.tasks.election_tasks import run_status_update
 
 
# ================= LOGGING =================
setup_logging(Config.LOG_LEVEL)
logger = logging.getLogger(__name__)
 
 
# ================= APP =================
app = FastAPI(
    title=Config.APP_NAME,
    version="1.0.0",
)
 
 
# ================= CORS FIX =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",
                   "http://18.205.17.63:3001"
                   ],  # 🔐 change to ["http://18.205.17.63:3001"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
# ================= PROFILING MIDDLEWARE =================
# Enabled ONLY in development
if Config.APP_ENV == "development":
 
    @app.middleware("http")
    async def profile_requests(request: Request, call_next):
        profiler = Profiler()
        profiler.start()
 
        response = await call_next(request)
 
        profiler.stop()
 
        # Show profiling in browser when ?profile=1
        if request.query_params.get("profile") == "1":
            return HTMLResponse(profiler.output_html())
 
        return response
 
 
# ================= STARTUP EVENT (MERGED) =================
@app.on_event("startup")
async def on_startup():
    logger.info("Starting Political Voting System")
 
    # 1️⃣ Check DB connection
    await check_database_connection()
 
    # 2️⃣ Create tables ONLY IF NOT EXISTS
    logger.info("Creating database tables (if not exist)")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
 
    logger.info("Database tables are ready")
 
    # 3️⃣ Start schedulers
    start_scheduler()
   
    logger.info("Schedulers started successfully")
 
 
 
@app.on_event("startup")
async def startup():
 
    # STATUS JOB
    scheduler.add_job(
        run_status_update,
        "interval",
        minutes=1,
        id="status_job",
        replace_existing=True,
    )
 
    # RESULT JOB
    start_result_scheduler()
 
    if not scheduler.running:
        scheduler.start()
 
 
 
# ================= ROUTERS =================
app.include_router(auth_router)
app.include_router(election.router)
app.include_router(location.router)
app.include_router(meta.router)
app.include_router(member.router)
app.include_router(candidate.router)
app.include_router(notification.router)
app.include_router(result.router)
app.include_router(nomination.router)
 
 
# ================= ROOT =================
@app.get("/")
async def root():
    return {"status": "API Running"}
 