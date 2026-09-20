import os
import tempfile
import unittest

os.environ["CIVICVOICE_AUTH_DEMO_MODE"] = "true"
import app as civic_app


class CivicVoiceApiTests(unittest.TestCase):
    def setUp(self):
        self.database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database.close()
        civic_app.app.config.update(TESTING=True, DATABASE=self.database.name, SECRET_KEY="test-secret")
        with civic_app.app.app_context():
            civic_app.init_db()
        self.client = civic_app.app.test_client()

    def tearDown(self):
        os.unlink(self.database.name)

    def sign_in(self, identifier="citizen@example.com"):
        self.client.post("/api/auth/request-code", json={"identifier": identifier})
        return self.client.post("/api/auth/verify", json={"identifier": identifier, "code": "123456"})

    def test_analyze_and_authenticated_report_lifecycle(self):
        analysis = self.client.post("/api/analyze", json={"text": "A large pothole is dangerous near the gate"})
        self.assertEqual(analysis.status_code, 200)
        self.assertEqual(analysis.json["analysis"]["category"], "Pothole / Road Damage")
        self.assertEqual(self.client.post("/api/reports", json={"text": "pothole"}).status_code, 401)
        self.assertEqual(self.sign_in().status_code, 200)
        created = self.client.post("/api/reports", json={"text": "A large pothole is dangerous", "latitude": 16.5, "longitude": 80.6, "location_text": "College gate"})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["report"]["status"], "Reported")
        self.assertEqual(len(self.client.get("/api/reports?mine=1").json["reports"]), 1)

    def test_admin_can_update_status(self):
        self.sign_in("citizen@example.com")
        created = self.client.post("/api/reports", json={"text": "streetlight not working"}).json["report"]
        self.client.post("/api/auth/logout")
        self.sign_in("admin@civicvoice.local")
        updated = self.client.patch(f"/api/admin/reports/{created['id']}/status", json={"status": "Resolved"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["status"], "Resolved")


if __name__ == "__main__":
    unittest.main()
