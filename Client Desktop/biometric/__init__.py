"""
Package biométrique - Reconnaissance faciale et vocale
"""

from .face import face_recognizer, FaceRecognizer
from .voice import voice_recorder, VoiceRecorder

__all__ = [
    'face_recognizer',
    'FaceRecognizer',
    'voice_recorder',
    'VoiceRecorder'
]
