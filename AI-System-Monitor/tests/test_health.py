import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitoring.health_checker import HealthChecker
from ai.recommendation_engine import AIRecommendationEngine

class TestHealthAndAI(unittest.TestCase):
    """Test health evaluation rules and AI recommendation generation."""

    def test_classify_metric(self):
        # 0-49 HEALTHY, 50-80 WARNING, >80 CRITICAL
        self.assertEqual(HealthChecker.classify_metric(25.0, 50.0, 80.0), "HEALTHY")
        self.assertEqual(HealthChecker.classify_metric(50.0, 50.0, 80.0), "WARNING")
        self.assertEqual(HealthChecker.classify_metric(75.5, 50.0, 80.0), "WARNING")
        self.assertEqual(HealthChecker.classify_metric(80.0, 50.0, 80.0), "CRITICAL")
        self.assertEqual(HealthChecker.classify_metric(95.0, 50.0, 80.0), "CRITICAL")

    def test_evaluate_health_nominal(self):
        result = HealthChecker.evaluate_health(
            cpu_percent=20.0,
            ram_percent=35.0,
            disk_percent=45.0,
            network_connected=True,
            network_status_text="Connected"
        )
        self.assertEqual(result["overall_status"], "HEALTHY")
        self.assertEqual(result["counts"]["healthy"], 4)
        self.assertEqual(result["counts"]["warning"], 0)
        self.assertEqual(result["counts"]["critical"], 0)

    def test_evaluate_health_warning(self):
        result = HealthChecker.evaluate_health(
            cpu_percent=65.0,  # Warning
            ram_percent=30.0,
            disk_percent=40.0,
            network_connected=True,
            network_status_text="Connected"
        )
        self.assertEqual(result["overall_status"], "WARNING")
        self.assertIn("CPU", result["flagged_resources"])

    def test_evaluate_health_critical(self):
        result = HealthChecker.evaluate_health(
            cpu_percent=30.0,
            ram_percent=92.0,  # Critical
            disk_percent=40.0,
            network_connected=True,
            network_status_text="Connected"
        )
        self.assertEqual(result["overall_status"], "CRITICAL")
        self.assertIn("RAM", result["flagged_resources"])

    def test_ai_single_resource_recommendation(self):
        engine = AIRecommendationEngine()
        health = {
            "overall_status": "CRITICAL",
            "cpu_status": "CRITICAL",
            "ram_status": "HEALTHY",
            "disk_status": "HEALTHY",
            "network_status": "HEALTHY",
            "flagged_resources": ["CPU"]
        }
        rec, changed, is_rec = engine.analyze(
            {"cpu_percent": 91.0, "ram_percent": 30.0, "disk_percent": 40.0, "network_status": "Connected"},
            health
        )
        self.assertEqual(rec["status"], "CRITICAL")
        self.assertIn("91.0%", rec["problem"])
        self.assertTrue(len(rec["recommended_action"]) > 0)
        self.assertTrue(len(rec["preventive_action"]) > 0)

    def test_ai_multi_resource_correlation(self):
        engine = AIRecommendationEngine()
        health = {
            "overall_status": "CRITICAL",
            "cpu_status": "CRITICAL",
            "ram_status": "CRITICAL",
            "disk_status": "HEALTHY",
            "network_status": "HEALTHY",
            "flagged_resources": ["CPU", "RAM"]
        }
        rec, changed, is_rec = engine.analyze(
            {"cpu_percent": 90.0, "ram_percent": 92.0, "disk_percent": 40.0, "network_status": "Connected"},
            health
        )
        self.assertEqual(rec["status"], "CRITICAL")
        # Multi-resource correlation should mention both CPU and Memory in problem
        self.assertTrue("CPU" in rec["problem"] and "Memory" in rec["problem"])

    def test_ai_recovery_detection(self):
        engine = AIRecommendationEngine()
        # Step 1: Trigger critical
        health_crit = {
            "overall_status": "CRITICAL",
            "cpu_status": "CRITICAL",
            "ram_status": "HEALTHY",
            "disk_status": "HEALTHY",
            "network_status": "HEALTHY",
            "flagged_resources": ["CPU"]
        }
        engine.analyze({"cpu_percent": 90.0, "ram_percent": 40.0, "disk_percent": 40.0}, health_crit)

        # Step 2: System normalizes
        health_ok = {
            "overall_status": "HEALTHY",
            "cpu_status": "HEALTHY",
            "ram_status": "HEALTHY",
            "disk_status": "HEALTHY",
            "network_status": "HEALTHY",
            "flagged_resources": []
        }
        rec, changed, is_rec = engine.analyze({"cpu_percent": 35.0, "ram_percent": 40.0, "disk_percent": 40.0}, health_ok)

        self.assertTrue(is_rec)
        self.assertEqual(rec["status"], "HEALTHY")
        self.assertIn("normalized", rec["problem"].lower())

if __name__ == '__main__':
    unittest.main()
