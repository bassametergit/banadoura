from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import cv2
import os
import random
import numpy as np
import zipfile
import io
import base64



def take1_random_screenshots(video_path, num_screenshots, output_dir):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Capture 5 random shots from the beginning
    for i in range(num_screenshots // 2):
        # Generate a random frame number from the beginning
        random_frame_number = random.randint(0, frame_count // 2)
        # Set the frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_number)
        # Read the frame
        ret, frame = cap.read()
        if ret:
            # Save the frame as a JPEG image
            output_path = os.path.join(output_dir, f"frame_{i}.jpg")
            cv2.imwrite(output_path, frame)
    
    # Capture 5 random shots from the end
    for i in range(num_screenshots // 2, num_screenshots):
        # Generate a random frame number from the end
        random_frame_number = random.randint(frame_count // 2, frame_count)
        # Set the frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_number)
        # Read the frame
        ret, frame = cap.read()
        if ret:
            # Save the frame as a JPEG image
            output_path = os.path.join(output_dir, f"frame_{i}.jpg")
            cv2.imwrite(output_path, frame)
    
    cap.release()

async def generate_frames(video_path: str, num_frames: int, minutes:int) -> AsyncGenerator[bytes, None]:
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate the frame numbers for the first and last 5 minutes
    ten_minutes_frames = int(cap.get(cv2.CAP_PROP_FPS) * 60 * minutes*2)
    first_5_minutes_frames = min(frame_count, ten_minutes_frames)
    last_5_minutes_frames = max(0, frame_count - ten_minutes_frames)

    # Get frames from the first 5 minutes
    for _ in range(num_frames // 2):
        random_frame_number = random.randint(0, first_5_minutes_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_number)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_encoded = base64.b64encode(buffer).decode('utf-8')
            yield frame_encoded

    # Get frames from the last 5 minutes
    for _ in range(num_frames // 2):
        random_frame_number = random.randint(last_5_minutes_frames, frame_count - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_number)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_encoded = base64.b64encode(buffer).decode('utf-8')
            yield frame_encoded
    
    cap.release()

# Create an instance of FastAPI
app = FastAPI(title="Video Shots for Banadoura")



# Define a route to call your function
@app.get("/screenshots")
async def take_screenshots(video_path: str, num_frames: int, minutes:int, zip_filename: str):
    """
    Endpoint to take random screenshots from a video and stream them as a zip file.
    """
    # Create an in-memory zip file
    zip_buffer = io.BytesIO()
    i=1
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        async for frame_data in generate_frames(video_path, num_frames, minutes):
            zip_file.writestr(f"frame_{i}.jpg", base64.b64decode(frame_data))
            i=i+1

    # Seek to the beginning of the buffer
    zip_buffer.seek(0)

    # Set headers for response
    headers = {
        "Content-Disposition": f"attachment; filename={zip_filename}",
        "Content-Type": "application/zip",
    }

    # Return the zip file as a StreamingResponse
    return StreamingResponse(io.BytesIO(zip_buffer.read()), headers=headers)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0",
        port=8000
    )