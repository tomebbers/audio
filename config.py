import os


class Config:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS = 4096

    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}

    # Interaural attenuation thresholds (dB)
    IA_SUPRAURAL = 40
    IA_INSERT = 55

    # Air-bone gap significance threshold (dB)
    ABG_THRESHOLD = 15

    # Bone conduction "elevated" threshold (dB HL)
    BC_ELEVATED_THRESHOLD = 20

    # Standard audiometric frequencies (Hz)
    STANDARD_FREQUENCIES = [250, 500, 1000, 2000, 4000, 8000]
    ALL_FREQUENCIES = [125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000]

    # Fletcher Index frequencies
    FH_FREQUENCIES = [500, 1000, 2000]
    FHI_FREQUENCIES = [1000, 2000, 4000]
