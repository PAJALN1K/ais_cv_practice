import cv2 as cv
import numpy as np
from pathlib import Path
from ultralytics import YOLO


class MotoDetector:
    def __init__(self):
        src_dir = Path(__file__).resolve().parent
        model_path = src_dir / "models" / "yolov8n.pt"
        
        self.model = YOLO(model_path)
        self.moto_class_id = 3

    def process_frame(self, frame, polygon_points):
        h, w = frame.shape[:2]
        abs_polygon = np.array(
            [[int(p[0] * w), int(p[1] * h)] for p in polygon_points], np.int32
        )

        results = self.model(frame, verbose=False)[0]
        m_count = 0
        v_count = 0

        overlay = frame.copy()
        cv.fillPoly(overlay, [abs_polygon], (255, 0, 0))
        cv.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        cv.polylines(frame, [abs_polygon], True, (255, 0, 0), 2)

        for box in results.boxes:
            if int(box.cls[0]) == self.moto_class_id:
                m_count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                contact_point = (int((x1 + x2) / 2), y2)

                is_violation = (
                    cv.pointPolygonTest(abs_polygon, contact_point, False) >= 0
                )
                color = (0, 0, 255) if is_violation else (0, 255, 0)
                if is_violation:
                    v_count += 1

                cv.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv.putText(
                    frame, "Moto", (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                )

        return frame, m_count, v_count
