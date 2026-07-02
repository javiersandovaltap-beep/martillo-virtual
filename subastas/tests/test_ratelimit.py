"""
Tests for rate limiting (D09: django-ratelimit).

Covers:
- login_view: 5/m limit (5 attempts allowed, 6th blocked)
- registro: 3/h limit (3 attempts allowed, 4th blocked)
- Valid logins under limit still work
"""
import pytest
from django.test import Client
from django.urls import reverse


def get_client():
    return Client(HTTP_HOST='localhost')


# ============================================================================
# login_view rate limiting (5/m)
# ============================================================================

class TestLoginRateLimit:
    def test_5_attempts_allowed(self, db, vendedor):
        """5 failed login attempts should all return 200 (stays on form, not blocked)"""
        c = get_client()
        for _ in range(5):
            response = c.post(reverse('subastas:login'), {
                'username': 'wrong',
                'password': 'wrong',
            })
            assert response.status_code == 200  # Form re-rendered

    def test_6th_attempt_blocked(self, db, vendedor):
        """6th login attempt within 1 minute should be blocked (403)"""
        c = get_client()
        # Make 5 failed attempts
        for _ in range(5):
            c.post(reverse('subastas:login'), {'username': 'wrong', 'password': 'wrong'})
        # 6th should be blocked
        response = c.post(reverse('subastas:login'), {'username': 'wrong', 'password': 'wrong'})
        assert response.status_code == 403  # Ratelimited -> Django default 403

    def test_valid_login_under_limit_works(self, db, vendedor):
        """Valid login when under the rate limit should succeed"""
        c = get_client()
        # 4 failed attempts (under 5/m limit)
        for _ in range(4):
            c.post(reverse('subastas:login'), {'username': 'wrong', 'password': 'wrong'})
        # 5th: valid login (at limit, not over)
        response = c.post(reverse('subastas:login'), {
            'username': 'test_vendedor',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302  # Successful login redirect


# ============================================================================
# registro rate limiting (3/h)
# ============================================================================

class TestRegistroRateLimit:
    def test_3_attempts_allowed(self, db):
        """3 registration attempts should all be processed (not blocked)"""
        c = get_client()
        for i in range(3):
            response = c.post(reverse('subastas:registro'), {
                'username': f'user_{i}',
                'email': f'user_{i}@test.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            })
            # 302 = successful registration + redirect
            assert response.status_code == 302

    def test_4th_attempt_blocked(self, db):
        """4th registration attempt within 1 hour should be blocked"""
        c = get_client()
        # 3 successful registrations
        for i in range(3):
            c.post(reverse('subastas:registro'), {
                'username': f'user_{i}',
                'email': f'user_{i}@test.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            })
        # 4th should be blocked
        response = c.post(reverse('subastas:registro'), {
            'username': 'user_3',
            'email': 'user_3@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert response.status_code == 403  # Ratelimited
