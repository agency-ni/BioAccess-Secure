"""
Tests unitaires pour le module biométrique
Tests de capture, encodage et API
"""

import unittest
import numpy as np
import io
from pathlib import Path
import tempfile
import logging

# Configurer logging pour tests
logging.basicConfig(level=logging.DEBUG)

try:
    from biometric import (
        LocalFaceCaptureService,
        BiometricCacheManager,
        BioAccessAPIClient,
        BiometricAPI,
        FaceDetectionResult,
        APIResponse
    )
    BIOMETRIC_AVAILABLE = True
except ImportError:
    BIOMETRIC_AVAILABLE = False


class TestFaceDetectionResult(unittest.TestCase):
    """Tests pour FaceDetectionResult dataclass"""
    
    def test_success_result(self):
        """Test création résultat succès"""
        result = FaceDetectionResult(
            success=True,
            face_encoding=np.random.rand(128),
            quality_score=0.85
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.quality_score, 0.85)
        self.assertIsNone(result.error_message)
    
    def test_failure_result(self):
        """Test création résultat erreur"""
        result = FaceDetectionResult(
            success=False,
            error_message="Face not detected"
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.face_encoding)
        self.assertEqual(result.error_message, "Face not detected")


class TestBiometricCacheManager(unittest.TestCase):
    """Tests pour BiometricCacheManager"""
    
    def setUp(self):
        """Créer cache temporaire pour tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = BiometricCacheManager(cache_dir=self.temp_dir)
    
    def test_save_encoding(self):
        """Test sauvegarde encodage"""
        encoding = np.random.rand(128)
        filepath = self.cache.save_encoding(
            user_id="test_user",
            face_encoding=encoding,
            label="test"
        )
        
        self.assertIsNotNone(filepath)
        self.assertTrue(Path(filepath).exists())
    
    def test_load_encoding(self):
        """Test chargement encodage"""
        original = np.random.rand(128)
        self.cache.save_encoding("user123", original, "test")
        
        loaded = self.cache.load_encoding("user123")
        
        self.assertIsNotNone(loaded)
        np.testing.assert_array_almost_equal(original, loaded)
    
    def test_nonexistent_encoding(self):
        """Test chargement encodage inexistant"""
        loaded = self.cache.load_encoding("nonexistent")
        self.assertIsNone(loaded)
    
    def tearDown(self):
        """Nettoyer fichiers temporaires"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestAPIResponse(unittest.TestCase):
    """Tests pour APIResponse dataclass"""
    
    def test_success_response(self):
        """Test réponse succès"""
        response = APIResponse(
            success=True,
            status_code=200,
            data={"token": "abc123"}
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["token"], "abc123")
    
    def test_error_response(self):
        """Test réponse erreur"""
        response = APIResponse(
            success=False,
            status_code=401,
            error_message="Unauthorized"
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.error_message, "Unauthorized")


class TestBioAccessAPIClient(unittest.TestCase):
    """Tests pour BioAccessAPIClient (sans réseau réel)"""
    
    def setUp(self):
        """Initialiser client"""
        self.client = BioAccessAPIClient(
            api_base="http://localhost:5000/api/v1",
            timeout=5
        )
    
    def test_initialization(self):
        """Test initialisation client"""
        self.assertEqual(
            self.client.api_base,
            "http://localhost:5000/api/v1"
        )
        self.assertIsNone(self.client.auth_token)
    
    def test_set_auth_token(self):
        """Test définition token"""
        token = "test_token_123"
        self.client.set_auth_token(token, expires_in=3600)
        
        self.assertEqual(self.client.auth_token, token)
        self.assertTrue(self.client.is_token_valid())
    
    def test_token_expiration(self):
        """Test expiration token"""
        from datetime import timedelta, datetime
        
        self.client.set_auth_token("token", expires_in=1)
        self.assertTrue(self.client.is_token_valid())
        
        # Simuler expiration
        self.client.token_expires_at = datetime.now() - timedelta(seconds=1)
        self.assertFalse(self.client.is_token_valid())


class TestIntegration(unittest.TestCase):
    """Tests d'intégration"""
    
    @unittest.skipIf(not BIOMETRIC_AVAILABLE, "Biometric module not available")
    def test_module_import(self):
        """Test import du module"""
        self.assertTrue(BIOMETRIC_AVAILABLE)
    
    def test_cache_manager_singleton(self):
        """Test pattern singleton cache manager"""
        from biometric import get_cache_manager
        
        cache1 = get_cache_manager()
        cache2 = get_cache_manager()
        
        # Même instance
        self.assertIs(cache1, cache2)
    
    def test_api_client_singleton(self):
        """Test pattern singleton API client"""
        from biometric import get_api_client
        
        client1 = get_api_client()
        client2 = get_api_client()
        
        # Même instance
        self.assertIs(client1, client2)


class TestBiometricAPI(unittest.TestCase):
    """Tests pour namespace BiometricAPI"""
    
    def test_namespace_configuration(self):
        """Test configuration namespace"""
        # Ces appels ne doivent pas lever d'exception
        BiometricAPI.set_base_url("http://test:5000/api/v1")
        BiometricAPI.set_token("test_token")
        
        # Vérifier configuration appliquée
        from biometric import get_api_client
        client = get_api_client()
        self.assertEqual(client.auth_token, "test_token")


def run_tests(verbosity=2):
    """Lance tous les tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
