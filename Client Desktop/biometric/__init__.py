"""
BioAccess-Secure Client Desktop - Biometric Module
Capture et traitement biométrique local intégrant MUSE
"""

from .face_capture_service import (
    LocalFaceCaptureService,
    BiometricCacheManager,
    FaceDetectionResult,
    get_capture_service,
    get_cache_manager,
    MUSE_AVAILABLE
)

from .biometric_api_client import (
    BioAccessAPIClient,
    BiometricAPI,
    APIResponse,
    get_api_client
)

__version__ = "2.0.0"

__all__ = [
    # Services
    'LocalFaceCaptureService',
    'BiometricCacheManager',
    'BioAccessAPIClient',
    
    # Namespace
    'BiometricAPI',
    
    # Data classes
    'FaceDetectionResult',
    'APIResponse',
    
    # Factory functions
    'get_capture_service',
    'get_cache_manager',
    'get_api_client',
    
    # Constants
    'MUSE_AVAILABLE',
]
