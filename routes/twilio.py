from fastapi import APIRouter, Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests

router = APIRouter(prefix="/twilio", tags=["twilio"])

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    user_message = form_data.get("Body", "").strip().lower()

    if "location:" in user_message and "report:" not in user_message:
        # Existing logic for finding parking spots
        _, coords = user_message.split("location:")
        coords = coords.strip().split(",")
        if len(coords) != 2:
            raise HTTPException(status_code=400, detail="Invalid location format")

        lat, lng = coords
        try:
            response = requests.get(
                "http://localhost:8000/parking-spots",
                params={"latitude": lat.strip(), "longitude": lng.strip()},
            )
            response.raise_for_status()
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch parking data")

        data = response.json().get("parking_spots", [])
        spots_info = "\n".join([f"{spot['name']}" for spot in data[:5]]) or "No spots found."
        message_body = f"Nearby Parking Spots:\n{spots_info}"

        resp = MessagingResponse()
        msg = resp.message(message_body)
        msg.body(message_body + "\n\nReply 'help' for more options.")
        return str(resp)

    elif "report:" in user_message and "location:" in user_message:
        # New logic for reporting free parking
        # Example format: "report: free parking. location: 40.7128,-74.0060"
        parts = user_message.split("report:")[1].strip().split("location:")
        description_part = parts[0].strip()
        coords = parts[1].strip().split(",")

        if len(coords) != 2:
            raise HTTPException(status_code=400, detail="Invalid location format")

        lat, lng = coords
        try:
            report_data = {
                "latitude": float(lat),
                "longitude": float(lng),
                "description": description_part or "No description provided"
            }
            # Call existing /parking-spots/report-parking endpoint
            post_response = requests.post(
                "http://localhost:8000/parking-spots/report-parking",
                json=report_data
            )
            post_response.raise_for_status()
            message_body = "Thank you! Your free parking report has been recorded."
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to submit parking report")

        resp = MessagingResponse()
        resp.message(message_body)
        return str(resp)

    else:
        resp = MessagingResponse()
        resp.message("Welcome to ParkingBot!\n"
                     "To see nearby parking, send: 'location: LAT,LNG'\n"
                     "To report free parking, send: 'report: Some description. location: LAT,LNG'")
        return str(resp)