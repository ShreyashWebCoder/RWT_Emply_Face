# api.py
import os
import cv2
import dlib
import csv
import numpy as np
import face_recognition
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from io import BytesIO

# ==== CONFIG ====
PREDICTOR_PATH = "shape_predictor.dat"
IMAGES_PATH = "images"
ATTENDANCE_FILE = "attendance.csv"
EYE_AR_THRESH = 0.23
EYE_AR_CONSEC_FRAMES = 2
HEAD_TURN_THRESHOLD = 15
# ================

# ==== INIT ====
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)
(lStart, lEnd) = (42, 48)  # Right eye
(rStart, rEnd) = (36, 42)  # Left eye

def euclidean(p1, p2):
    return np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

def eye_aspect_ratio(eye):
    A = euclidean(eye[1], eye[5])
    B = euclidean(eye[2], eye[4])
    C = euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def get_nose_dx(shape):
    nose = shape.part(30)
    chin = shape.part(8)
    return abs(nose.x - chin.x)

def mark_attendance(name):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Date', 'Time'])

    with open(ATTENDANCE_FILE, 'r') as f:
        lines = f.readlines()
        if any(name in line and date in line for line in lines):
            return

    with open(ATTENDANCE_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, date, time])
        print(f"✅ Attendance marked for {name}")

def load_known_faces():
    known_encodings = []
    known_names = []
    for person in os.listdir(IMAGES_PATH):
        person_dir = os.path.join(IMAGES_PATH, person)
        for img_file in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_file)
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(person)
    return known_encodings, known_names

known_encodings, known_names = load_known_faces()

# @app.post("/verify-face")
# async def verify_face(file: UploadFile = File(...)):
    
#     print(f"Received file: {file.filename}")
    
#     contents = await file.read()
#     if not contents:
#             return JSONResponse(
#                 content={"name": "Empty image file"},
#                 status_code=400
#             )
            
#     np_img = np.frombuffer(contents, np.uint8)
#     frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = detector(gray, 0)

#     if frame is None:
#             return JSONResponse(
#                 content={"name": "Invalid image format"},
#                 status_code=400
#             )
            
#     for face in faces:
#         shape = predictor(gray, face)

#         leftEye = [shape.part(i) for i in range(lStart, lEnd)]
#         rightEye = [shape.part(i) for i in range(rStart, rEnd)]
#         ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0

#         blink_detected = False
#         head_turn_detected = False

#         if ear < EYE_AR_THRESH:
#             blink_detected = True

#         initial_dx = get_nose_dx(shape)
#         dx = get_nose_dx(shape)
#         if abs(dx - initial_dx) > HEAD_TURN_THRESHOLD:
#             head_turn_detected = True

#         if blink_detected and head_turn_detected:
#             face_locations = face_recognition.face_locations(frame)
#             face_encodings = face_recognition.face_encodings(frame, face_locations)

#             for encoding in face_encodings:
#                 matches = face_recognition.compare_faces(known_encodings, encoding)
#                 name = "Unknown"
#                 if True in matches:
#                     match_idx = matches.index(True)
#                     name = known_names[match_idx]
#                     mark_attendance(name)
#                     return JSONResponse(content={"name": name})
#             return JSONResponse(content={"name": "Unknown"})

#     return JSONResponse(content={"name": "No face or liveness failed"}, status_code=400)


@app.post("/verify-face")
async def verify_face(file: UploadFile = File(...)):
    try:
        # Read uploaded image
        contents = await file.read()
        if not contents:
            return JSONResponse(
                content={"name": "Empty image file"},
                status_code=400
            )

        # Convert to image array
        np_img = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if frame is None:
            return JSONResponse(
                content={"name": "Invalid image format"},
                status_code=400
            )

        # Image preprocessing (denoise and enhance contrast)
        frame = cv2.bilateralFilter(frame, 9, 75, 75)
        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)

        # Convert to required color formats
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Face detection
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            return JSONResponse(
                content={"name": "No face detected"},
                status_code=400
            )

        # Reject if multiple faces detected
        if len(face_locations) > 1:
            return JSONResponse(
                content={"name": "Multiple faces detected. Show only your face."},
                status_code=400
            )

        # Reject if face is too small
        (top, right, bottom, left) = face_locations[0]
        face_width = right - left
        face_height = bottom - top
        if face_width < 60 or face_height < 60:
            return JSONResponse(
                content={"name": "Face too small in frame. Come closer to the camera."},
                status_code=400
            )

        # Liveness detection using EAR
        faces = detector(gray, 0)
        if not faces:
            return JSONResponse(
                content={"name": "No face or liveness detection failed"},
                status_code=400
            )

        for face in faces:
            shape = predictor(gray, face)
            left_eye = [shape.part(i) for i in range(42, 48)]
            right_eye = [shape.part(i) for i in range(36, 42)]
            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

            # Check blink
            if ear < EYE_AR_THRESH:
                # Perform face recognition only if blink detected
                face_encodings = face_recognition.face_encodings(
                    rgb_frame, face_locations, num_jitters=2, model='large'
                )
                if not face_encodings:
                    return JSONResponse(
                        content={"name": "Face encoding failed"},
                        status_code=400
                    )

                encoding = face_encodings[0]
                face_distances = face_recognition.face_distance(known_encodings, encoding)
                best_match_index = np.argmin(face_distances)

                if face_distances[best_match_index] < 0.5:
                    name = known_names[best_match_index]
                    mark_attendance(name)
                    return JSONResponse(content={"name": name})
                else:
                    return JSONResponse(
                        content={"name": "Unknown face"},
                        status_code=400
                    )

        return JSONResponse(
            content={"name": "Please blink to verify liveness"},
            status_code=400
        )

    except Exception as e:
        print(f"Server error: {str(e)}")
        return JSONResponse(
            content={"name": "Internal server error"},
            status_code=500
        )

    try:
        # Read and validate image
        contents = await file.read()
        if not contents:
            return JSONResponse(
                content={"name": "Empty image file"},
                status_code=400
            )

        np_img = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse(
                content={"name": "Invalid image format"},
                status_code=400
            )

        # Convert to RGB (face_recognition uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find all face locations
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            return JSONResponse(
                content={"name": "No face detected"},
                status_code=400
            )

        # Liveness check - improved version
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)
        
        if not faces:
            return JSONResponse(
                content={"name": "No face or liveness failed"},
                status_code=400
            )

        for face in faces:
            shape = predictor(gray, face)
            
            # Improved liveness detection
            left_eye = [shape.part(i) for i in range(42, 48)]
            right_eye = [shape.part(i) for i in range(36, 42)]
            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
            
            # Check for blink
            if ear < EYE_AR_THRESH:
                # If blink detected, proceed with verification
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                for encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_encodings, encoding)
                    name = "Unknown"
                    
                    if True in matches:
                        match_idx = matches.index(True)
                        name = known_names[match_idx]
                        mark_attendance(name)
                        return JSONResponse(content={"name": name})
                
                return JSONResponse(
                    content={"name": "Unknown face"},
                    status_code=400
                )

        # If no blink detected
        return JSONResponse(
            content={"name": "Please blink to verify liveness"},
            status_code=400
        )

    except Exception as e:
        print(f"Server error: {str(e)}")
        return JSONResponse(
            content={"name": "Internal server error"},
            status_code=500
        )