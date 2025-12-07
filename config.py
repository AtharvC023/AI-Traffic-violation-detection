import os
from dataclasses import dataclass

@dataclass
class Config:
    # Model settings
    MODEL_PATH: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.25
    
    # Processing settings
    MAX_FRAME_WIDTH: int = 640
    BATCH_SIZE: int = 4
    SKIP_FRAMES: int = 5  # Process every 5th frame
    
    # File limits
    MAX_VIDEO_SIZE_MB: int = 100
    MAX_IMAGE_SIZE_MB: int = 10
    
    # Database
    DB_PATH: str = "current_session.db"
    
    # Violation thresholds
    SPEED_THRESHOLD: float = 30.0
    TAILGATE_DISTANCE: float = 80.0
    HELMET_DARK_THRESHOLD: float = 0.3
    
    # Directories
    OUTPUT_DIR: str = "outputs/violations"
    SAMPLE_DIR: str = "data/samples"
    
    @classmethod
    def from_env(cls):
        """Load config from environment variables"""
        return cls(
            MODEL_PATH=os.getenv("MODEL_PATH", cls.MODEL_PATH),
            CONFIDENCE_THRESHOLD=float(os.getenv("CONFIDENCE_THRESHOLD", cls.CONFIDENCE_THRESHOLD)),
            MAX_VIDEO_SIZE_MB=int(os.getenv("MAX_VIDEO_SIZE_MB", cls.MAX_VIDEO_SIZE_MB)),
            DB_PATH=os.getenv("DB_PATH", cls.DB_PATH)
        )

# Global config instance
config = Config.from_env()