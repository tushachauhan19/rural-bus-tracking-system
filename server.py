from fastapi import FastAPI

app = FastAPI(
    title="Rural Bus Tracking System",
    description="Bus tracking system for rural and Tier-3 cities",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Rural Bus Tracking System API is running!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }