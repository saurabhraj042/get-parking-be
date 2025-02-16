from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
import os
import requests
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from config.database import SessionLocal
from models.report import ParkingReport
import openai

openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_version = "2023-03-15-preview"

router = APIRouter(prefix="/parking-spots", tags=["parking"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ParkingReportRequest(BaseModel):
    latitude: float = Field(..., description="Latitude of the parking spot")
    longitude: float = Field(..., description="Longitude of the parking spot")
    description: str = Field(..., description="Details about the parking spot")

class PredictParkingRequest(BaseModel):
    latitude: float
    longitude: float
    datetime: str  # e.g. "2025-02-15T12:00:00"
    location_history: Optional[list] = []
    user_reports: Optional[list] = []

@router.get("/")
async def get_parking_spots(latitude: float, longitude: float):
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing Google Places API key")

    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={latitude},{longitude}&radius=1500"
        f"&type=parking&key={api_key}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch data from Google Places")

    data = response.json().get("results", [])
    return {"parking_spots": data}

@router.post("/report-parking")
async def report_parking(
    data: ParkingReportRequest,
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Simple check if image is provided
    image_url = None
    if image:
        # In a real app, you might save the file to a storage service
        image_url = f"uploaded_images/{image.filename}"

    new_report = ParkingReport(
        latitude=data.latitude,
        longitude=data.longitude,
        description=data.description,
        image_url=image_url,
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {"message": "Report created successfully", "report_id": new_report.id}

@router.post("/predict-parking")
async def predict_parking_availability(request: PredictParkingRequest, db: Session = Depends(get_db)):
    # 1. Fetch traffic data from Google Maps API
    traffic_data = requests.get(
        "https://maps.googleapis.com/maps/api/distancematrix/json",
        params={
            "origins": f"{request.latitude},{request.longitude}",
            "destinations": f"{request.latitude},{request.longitude}",
            "key": os.environ.get("GOOGLE_MAPS_API_KEY"),
        },
    )
    if traffic_data.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get traffic data")

    # 2. Gather relevant parking reports from DB
    # Example: get last few user reports near the given location
    # (This is only an illustration; you'd implement proper distance filtering)
    reports_nearby = db.query(ParkingReport).all()

    # 3. Prepare prompt or structured data for Azure OpenAI
    prompt = f"""Predict parking availability. 
    Current time: {request.datetime}
    Location: {request.latitude}, {request.longitude}
    Traffic data: {traffic_data.json()}
    Location history: {request.location_history}
    User reports: {request.user_reports}
    Nearby DB reports: {[(r.latitude, r.longitude, r.description) for r in reports_nearby]}
    Provide a numeric availability score (0-100)."""

    try:
        response = openai.Completion.create(
            engine="YOUR_AZURE_OPENAI_DEPLOYMENT_ID",
            prompt=prompt,
            max_tokens=50,
            temperature=0.0,
        )
        predicted_availability = response.choices[0].text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"predicted_availability": predicted_availability}