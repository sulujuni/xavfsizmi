import cv2
import numpy as np

def extract_qr_url(image_bytes: bytes) -> str:
    """
    Extracts URL from a QR code image using OpenCV.
    No system libraries needed — works anywhere.
    """
    try:
        # Convert bytes to numpy array then to OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return ""

        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)

        return data if data else ""
    except Exception:
        return ""
