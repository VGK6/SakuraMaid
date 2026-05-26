"""
环境感知模块 — 通过摄像头感知外界环境
OpenCV + Haar Cascade 人脸检测
"""
import cv2
import numpy as np
import threading, time

class CameraEnv:
    """摄像头环境感知"""

    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap = None
        self.face_cascade = None
        self._last_frame = None
        self._lock = threading.Lock()

    def _init_camera(self) -> bool:
        """初始化摄像头"""
        if self.cap is not None:
            return True
        try:
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)  # Windows用DSHOW加速
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_id)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # 低分辨率，省资源
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                self.cap.set(cv2.CAP_PROP_FPS, 5)
                print(f"✅ 摄像头已启动 (ID:{self.camera_id})")
                return True
        except:
            pass
        return False

    def _get_face_cascade(self):
        """获取人脸检测模型（懒加载）"""
        if self.face_cascade is None:
            try:
                model_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.face_cascade = cv2.CascadeClassifier(model_path)
                if self.face_cascade.empty():
                    self.face_cascade = None
                    return None
            except:
                return None
        return self.face_cascade

    def capture(self) -> np.ndarray:
        """捕获一帧画面"""
        if not self._init_camera():
            return None
        with self._lock:
            ret, frame = self.cap.read()
        if not ret or frame is None:
            return None
        return frame

    def detect_faces(self, frame: np.ndarray) -> int:
        """检测人脸数量"""
        cascade = self._get_face_cascade()
        if cascade is None:
            return 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return len(faces)

    def detect_motion(self, frame: np.ndarray) -> bool:
        """帧差法检测是否有运动"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self._last_frame is None:
            self._last_frame = gray
            return False
        
        diff = cv2.absdiff(self._last_frame, gray)
        self._last_frame = gray
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        motion_pixels = np.sum(thresh > 0) / thresh.size
        return motion_pixels > 0.01  # >1%像素变化认为有运动

    def get_brightness(self, frame: np.ndarray) -> int:
        """获取画面亮度（0~255）"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return int(np.mean(gray))

    def get_scene(self) -> dict:
        """
        获取当前场景状态
        返回: {face_count, has_motion, is_dark, brightness, camera_ok}
        """
        frame = self.capture()
        if frame is None:
            return {"camera_ok": False, "face_count": 0, "has_motion": False,
                    "is_dark": False, "brightness": 0}

        brightness = self.get_brightness(frame)
        face_count = self.detect_faces(frame)
        has_motion = self.detect_motion(frame)

        return {
            "camera_ok": True,
            "face_count": face_count,
            "has_motion": has_motion,
            "is_dark": brightness < 30,       # 亮度<30认为暗（深夜）
            "brightness": brightness,
        }

    def release(self):
        """释放摄像头"""
        with self._lock:
            if self.cap:
                self.cap.release()
                self.cap = None
        print("📷 摄像头已释放")

    def __del__(self):
        self.release()
