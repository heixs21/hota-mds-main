from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class AdminAuthApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="admin",
            password="admin123456",
            is_staff=True,
            first_name="和泰",
            last_name="管理员",
        )
        user_model.objects.create_user(
            username="viewer",
            password="viewer123456",
            is_staff=False,
        )
        self.client = APIClient()

    def test_admin_login_returns_token_for_staff_user(self):
        response = self.client.post(
            "/api/admin/auth/login",
            {"username": "admin", "password": "admin123456"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertIn("access_token", response.data["data"])
        self.assertEqual(response.data["data"]["token_type"], "Bearer")
        self.assertIn("expires_in", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["username"], "admin")

    def test_admin_login_rejects_non_staff_user(self):
        response = self.client.post(
            "/api/admin/auth/login",
            {"username": "viewer", "password": "viewer123456"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "FORBIDDEN")

    def test_admin_me_requires_valid_bearer_token(self):
        response = self.client.get("/api/admin/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "UNAUTHORIZED")

    def test_admin_logout_clears_session_and_logs_action(self):
        login_response = self.client.post(
            "/api/admin/auth/login",
            {"username": "admin", "password": "admin123456"},
            format="json",
        )
        token = login_response.data["data"]["access_token"]

        response = self.client.post(
            "/api/admin/auth/logout/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    def test_admin_logout_rejects_without_token(self):
        response = self.client.post("/api/admin/auth/logout/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "UNAUTHORIZED")

    def test_admin_me_returns_current_admin(self):
        login_response = self.client.post(
            "/api/admin/auth/login",
            {"username": "admin", "password": "admin123456"},
            format="json",
        )
        token = login_response.data["data"]["access_token"]

        response = self.client.get(
            "/api/admin/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["displayName"], "和泰 管理员")
