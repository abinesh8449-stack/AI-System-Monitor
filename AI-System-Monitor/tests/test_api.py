import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from config import Config
from database import init_db

class TestFlaskEndpoints(unittest.TestCase):
    """Test web routes, authentication, REST APIs, and export endpoints."""

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    def login_admin(self):
        """Helper to authenticate test client."""
        return self.client.post('/login', data={
            'username': Config.DEFAULT_ADMIN_USER,
            'password': Config.DEFAULT_ADMIN_PASS
        }, follow_redirects=True)

    def test_unauthenticated_redirect(self):
        res = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_login_failure(self):
        res = self.client.post('/login', data={
            'username': 'admin',
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Invalid credentials", res.data)

    def test_login_success(self):
        res = self.login_admin()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Overall System Health", res.data)

    def test_dashboard_authenticated(self):
        self.login_admin()
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CPU Utilization", res.data)
        self.assertIn(b"AI System Analysis", res.data)

    def test_history_page(self):
        self.login_admin()
        res = self.client.get('/history')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"System Telemetry History", res.data)

    def test_alerts_page(self):
        self.login_admin()
        res = self.client.get('/alerts')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Alert Incident Directory", res.data)

    def test_server_info_page(self):
        self.login_admin()
        res = self.client.get('/server-info')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Operating System Architecture", res.data)

    def test_reports_page(self):
        self.login_admin()
        res = self.client.get('/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Audit Report Generation Center", res.data)

    def test_api_metrics(self):
        self.login_admin()
        res = self.client.get('/api/metrics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("cpu", data)
        self.assertIn("ram", data)
        self.assertIn("disk", data)
        self.assertIn("health", data)
        self.assertIn("ai_recommendation", data)

    def test_api_health(self):
        self.login_admin()
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn(data["overall_status"], ["HEALTHY", "WARNING", "CRITICAL"])

    def test_api_summary(self):
        self.login_admin()
        res = self.client.get('/api/summary')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("alert_counts", data)

    def test_csv_download(self):
        self.login_admin()
        res = self.client.get('/reports/download/csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        self.assertIn(b"Timestamp,CPU Usage (%),RAM Usage (%)", res.data)

    def test_pdf_download(self):
        self.login_admin()
        res = self.client.get('/reports/download/pdf')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')
        # PDF files begin with %PDF
        self.assertTrue(res.data.startswith(b"%PDF"))

    def test_ai_simulation_and_remediation(self):
        self.login_admin()
        # 1. Start multi-resource critical simulation
        sim_res = self.client.post('/api/remediate/simulate', json={'type': 'multi'})
        self.assertEqual(sim_res.status_code, 200)
        sim_data = sim_res.get_json()
        self.assertEqual(sim_data["status"], "success")
        self.assertEqual(sim_data["ai_recommendation"]["status"], "CRITICAL")

        # 2. Verify /api/metrics reflects CRITICAL simulated state
        metrics_res = self.client.get('/api/metrics')
        metrics_data = metrics_res.get_json()
        self.assertEqual(metrics_data["health"]["overall_status"], "CRITICAL")
        self.assertTrue(metrics_data["remediation"]["simulation_active"])

        # 3. Execute AI Self-Healing to resolve the incident
        heal_res = self.client.post('/api/remediate/execute', json={'action_type': 'auto_heal'})
        self.assertEqual(heal_res.status_code, 200)
        heal_data = heal_res.get_json()
        self.assertEqual(heal_data["remediation_result"]["status"], "RESOLVED")
        self.assertFalse(heal_data["engine_status"]["simulation_active"])

    def test_toggle_auto_heal(self):
        self.login_admin()
        res = self.client.post('/api/remediate/toggle-auto', json={'enabled': True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["auto_heal_enabled"])

        res_off = self.client.post('/api/remediate/toggle-auto', json={'enabled': False})
        self.assertEqual(res_off.status_code, 200)
        self.assertFalse(res_off.get_json()["auto_heal_enabled"])

    def test_kill_process_quarantine(self):
        self.login_admin()
        # Fetch initial top processes
        m1 = self.client.get('/api/metrics').get_json()
        top_cpu = m1["top_processes"]["top_cpu_processes"]
        self.assertTrue(len(top_cpu) > 0)
        target_pid = top_cpu[0]["pid"]

        # Execute kill_process on target_pid
        kill_res = self.client.post('/api/remediate/execute', json={
            'action_type': 'kill_process',
            'pid': target_pid
        })
        self.assertEqual(kill_res.status_code, 200)
        self.assertEqual(kill_res.get_json()["remediation_result"]["status"], "RESOLVED")

        # Verify target_pid is removed from top_processes on subsequent poll
        m2 = self.client.get('/api/metrics').get_json()
        remaining_pids = [p["pid"] for p in m2["top_processes"]["top_cpu_processes"]]
        self.assertNotIn(target_pid, remaining_pids)

    def test_test_email_endpoint(self):
        self.login_admin()
        # When EMAIL_ENABLED is False (default in tests), expect 400 with diagnostic message
        res = self.client.post('/api/alerts/test-email', json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("disabled", data["message"].lower())

if __name__ == '__main__':
    unittest.main()


