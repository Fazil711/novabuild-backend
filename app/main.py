from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import plan, build, projects, iterate 

app = FastAPI(title="NovaBuild Backend")

# Loosen this once you know your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(build.router, prefix="/api", tags=["build"])
app.include_router(projects.router, prefix="/api", tags=["projects"])  
app.include_router(iterate.router, prefix="/api", tags=["iterate"])

@app.get("/health")
def health():
    return {"status": "ok"}