from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import campaigns, contacts, domains, stats, webhooks

app = FastAPI(title="Inboxed", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(campaigns.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(domains.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")


@app.get("/health")
def health():
    return {"ok": True}
