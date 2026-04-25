import os
import tomllib
from pathlib import Path


def _read_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    try:
        with open(pyproject, "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "0.0.0-dev"


_APP_VERSION = _read_version()


class Settings:
    # API Settings
    PROJECT_NAME: str = "Lidar Standalone API"
    VERSION: str = _APP_VERSION
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8005))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # LIDAR Settings
    LIDAR_MODE: str = os.getenv("LIDAR_MODE", "real")  # "real" or "sim"
    LIDAR_IP: str = os.getenv("LIDAR_IP", "192.168.100.123")
    LIDAR_LAUNCH: str = os.getenv("LIDAR_LAUNCH", "./launch/sick_multiscan.launch")
    LIDAR_PCD_PATH: str = os.getenv("LIDAR_PCD_PATH", "./test.pcd")

    # Directory Settings
    DEBUG_OUTPUT_DIR: str = "debug_data"


settings = Settings()
