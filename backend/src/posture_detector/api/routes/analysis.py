import cv2
import numpy as np
import base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, Query
from posture_detector.api import schemas, dependencies
from posture_detector.session import PostureSession

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/frame", response_model=schemas.FrameAnalysisResponse)
async def process_frame(
    file: UploadFile = File(...),
    session: PostureSession = Depends(dependencies.get_active_session)
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    result = session.process_frame(frame)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to process frame")

    return schemas.FrameAnalysisResponse(
        posture_label=result.posture_label,
        neck_angle=result.neck_angle,
        back_angle=result.back_angle,
        show_warning=result.show_warning,
        warning_message=result.warning_message,
        show_break=result.show_break,
        break_message=result.break_message,
        show_fatigue=result.show_fatigue,
        fatigue_message=result.fatigue_message,
        calibration_message=result.calibration_message,
    )


@router.websocket("/ws")
async def websocket_analysis(
    websocket: WebSocket,
    token: str = Query(...)
):
    """Real-time posture analysis streaming over WebSockets."""
    await websocket.accept()

    user = dependencies.get_current_user_from_token(token)
    if user is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    session = dependencies.get_active_session_by_id(user.id)

    try:
        while True:
            # Can receive bytes (binary JPEG) or text (base64 string or json)
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                nparr = np.frombuffer(message["bytes"], np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif "text" in message and message["text"]:
                text_data = message["text"]
                if text_data.startswith("data:image"):
                    text_data = text_data.split(",")[1]
                img_bytes = base64.b64decode(text_data)
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                continue

            if frame is None:
                continue

            result = session.process_frame(frame)
            if result is None:
                continue

            payload = {
                "posture_label": result.posture_label,
                "neck_angle": round(result.neck_angle, 1) if result.neck_angle is not None else None,
                "back_angle": round(result.back_angle, 1) if result.back_angle is not None else None,
                "show_warning": result.show_warning,
                "warning_message": result.warning_message,
                "show_break": result.show_break,
                "break_message": result.break_message,
                "show_fatigue": result.show_fatigue,
                "fatigue_message": result.fatigue_message,
                "calibration_message": result.calibration_message,
            }

            await websocket.send_json(payload)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass
