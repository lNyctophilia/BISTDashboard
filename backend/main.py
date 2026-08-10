from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import market, reports

app = FastAPI(
    title="Finance Portfolio API",
    description="API for fetching BIST stock data, KAP reports, and technical signals.",
    version="1.0.0"
)

# Enable CORS for Flutter Web PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Finance Portfolio API"}
