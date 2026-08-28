from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, plan, build, projects, iterate, discovery, deploy, references

app = FastAPI(
    title="NovaBuild Backend",
    description="AI-powered application generator backend with User Management, Prompt Engine, Blueprint Engine, Discovery Q&A, Reference Ingestion, and One-Click Cloud Deployment.",
    version="1.2.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")
app.include_router(references.router, prefix="/api")
app.include_router(plan.router, prefix="/api")
app.include_router(build.router, prefix="/api")
app.include_router(projects.router, prefix="/api")  
app.include_router(deploy.router, prefix="/api")
app.include_router(iterate.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "service": "NovaBuild Backend", "version": "1.0.0"}