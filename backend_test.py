#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Special Education Landing Page
Tests all endpoints including auth, content management, settings, SEO, and uploads
"""

import requests
import sys
import json
import os
from datetime import datetime

class SpecialEducationAPITester:
    def __init__(self, base_url="https://neuro-diverse-care.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_credentials = {
            "email": "admin@educacaoespecial.com",
            "password": "Admin@2024Edu!"
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        return success

    def test_content_endpoint(self):
        """Test GET /api/content - should work without auth"""
        try:
            response = self.session.get(f"{self.api_url}/content", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                # Verify structure
                required_keys = ['sections', 'settings', 'seo']
                has_structure = all(key in data for key in required_keys)
                if not has_structure:
                    return self.log_test("GET /api/content", False, f"Missing required keys: {required_keys}")
                
                # Verify sections exist
                sections = data.get('sections', {})
                expected_sections = ['hero', 'social_proof', 'target_audience', 'how_it_works', 
                                   'differentials', 'testimonials', 'about', 'final_cta']
                missing_sections = [s for s in expected_sections if s not in sections]
                if missing_sections:
                    return self.log_test("GET /api/content", False, f"Missing sections: {missing_sections}")
                
                return self.log_test("GET /api/content", True)
            else:
                return self.log_test("GET /api/content", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("GET /api/content", False, str(e))

    def test_admin_login(self):
        """Test admin login and store session"""
        try:
            response = self.session.post(
                f"{self.api_url}/auth/login",
                json=self.admin_credentials,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                # Verify response structure
                required_fields = ['id', 'email', 'name', 'role']
                if not all(field in data for field in required_fields):
                    return self.log_test("POST /api/auth/login", False, "Missing user fields in response")
                
                # Verify cookies are set
                cookies = response.cookies
                if 'access_token' not in cookies:
                    return self.log_test("POST /api/auth/login", False, "No access_token cookie set")
                
                return self.log_test("POST /api/auth/login", True)
            else:
                return self.log_test("POST /api/auth/login", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            return self.log_test("POST /api/auth/login", False, str(e))

    def test_auth_me(self):
        """Test GET /api/auth/me - requires auth"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                if data.get('email') != self.admin_credentials['email']:
                    return self.log_test("GET /api/auth/me", False, "Email mismatch")
                return self.log_test("GET /api/auth/me", True)
            else:
                return self.log_test("GET /api/auth/me", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("GET /api/auth/me", False, str(e))

    def test_unauthorized_access(self):
        """Test that protected endpoints return 401 without auth"""
        # Create a new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({'Content-Type': 'application/json'})
        
        protected_endpoints = [
            ("PUT", "/content/section/hero", {"headline": "test"}),
            ("PUT", "/content/sections/toggle", {"section_id": "hero", "enabled": True}),
            ("PUT", "/content/sections/order", {"order": ["hero", "social_proof"]}),
            ("PUT", "/settings", {"whatsapp_number": "test"}),
            ("PUT", "/seo", {"title": "test"}),
            ("GET", "/auth/me", None)
        ]
        
        all_passed = True
        for method, endpoint, data in protected_endpoints:
            try:
                if method == "PUT":
                    response = unauth_session.put(f"{self.api_url}{endpoint}", json=data, timeout=10)
                else:
                    response = unauth_session.get(f"{self.api_url}{endpoint}", timeout=10)
                
                if response.status_code != 401:
                    self.log_test(f"Unauthorized {method} {endpoint}", False, f"Expected 401, got {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(f"Unauthorized {method} {endpoint}", False, str(e))
                all_passed = False
        
        if all_passed:
            return self.log_test("Unauthorized access protection", True)
        return False

    def test_hero_section_update(self):
        """Test updating hero section"""
        try:
            test_data = {
                "headline": "Test Headline Updated",
                "subheadline": "Test subheadline updated",
                "cta_text": "Test CTA Updated",
                "image_url": ""
            }
            
            response = self.session.put(
                f"{self.api_url}/content/section/hero",
                json=test_data,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                # Verify the update by fetching content
                content_response = self.session.get(f"{self.api_url}/content", timeout=10)
                if content_response.status_code == 200:
                    content = content_response.json()
                    hero = content.get('sections', {}).get('hero', {})
                    if hero.get('headline') == test_data['headline']:
                        return self.log_test("PUT /api/content/section/hero", True)
                    else:
                        return self.log_test("PUT /api/content/section/hero", False, "Update not reflected")
                else:
                    return self.log_test("PUT /api/content/section/hero", False, "Could not verify update")
            else:
                return self.log_test("PUT /api/content/section/hero", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("PUT /api/content/section/hero", False, str(e))

    def test_section_toggle(self):
        """Test toggling section visibility"""
        try:
            # Toggle hero section off
            response = self.session.put(
                f"{self.api_url}/content/sections/toggle",
                json={"section_id": "hero", "enabled": False},
                timeout=10
            )
            success = response.status_code == 200
            if not success:
                return self.log_test("PUT /api/content/sections/toggle", False, f"Status: {response.status_code}")
            
            # Verify the toggle
            content_response = self.session.get(f"{self.api_url}/content", timeout=10)
            if content_response.status_code == 200:
                content = content_response.json()
                hero_enabled = content.get('sections', {}).get('hero', {}).get('enabled', True)
                if not hero_enabled:
                    # Toggle back on
                    self.session.put(
                        f"{self.api_url}/content/sections/toggle",
                        json={"section_id": "hero", "enabled": True},
                        timeout=10
                    )
                    return self.log_test("PUT /api/content/sections/toggle", True)
                else:
                    return self.log_test("PUT /api/content/sections/toggle", False, "Toggle not reflected")
            else:
                return self.log_test("PUT /api/content/sections/toggle", False, "Could not verify toggle")
        except Exception as e:
            return self.log_test("PUT /api/content/sections/toggle", False, str(e))

    def test_section_reorder(self):
        """Test reordering sections"""
        try:
            # Get current order first
            content_response = self.session.get(f"{self.api_url}/content", timeout=10)
            if content_response.status_code != 200:
                return self.log_test("PUT /api/content/sections/order", False, "Could not get current content")
            
            content = content_response.json()
            sections = content.get('sections', {})
            current_order = sorted(sections.keys(), key=lambda x: sections[x].get('order', 0))
            
            # Reverse the order for testing
            new_order = list(reversed(current_order))
            
            response = self.session.put(
                f"{self.api_url}/content/sections/order",
                json={"order": new_order},
                timeout=10
            )
            success = response.status_code == 200
            if success:
                # Restore original order
                self.session.put(
                    f"{self.api_url}/content/sections/order",
                    json={"order": current_order},
                    timeout=10
                )
                return self.log_test("PUT /api/content/sections/order", True)
            else:
                return self.log_test("PUT /api/content/sections/order", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("PUT /api/content/sections/order", False, str(e))

    def test_settings_update(self):
        """Test updating settings"""
        try:
            test_settings = {
                "whatsapp_number": "5511999999999",
                "whatsapp_message": "Test message updated",
                "response_time": "Respondo em ate 1h",
                "scarcity_text": "Test scarcity updated"
            }
            
            response = self.session.put(
                f"{self.api_url}/settings",
                json=test_settings,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                # Verify the update
                content_response = self.session.get(f"{self.api_url}/content", timeout=10)
                if content_response.status_code == 200:
                    content = content_response.json()
                    settings = content.get('settings', {})
                    if settings.get('whatsapp_message') == test_settings['whatsapp_message']:
                        return self.log_test("PUT /api/settings", True)
                    else:
                        return self.log_test("PUT /api/settings", False, "Update not reflected")
                else:
                    return self.log_test("PUT /api/settings", False, "Could not verify update")
            else:
                return self.log_test("PUT /api/settings", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("PUT /api/settings", False, str(e))

    def test_seo_update(self):
        """Test updating SEO settings"""
        try:
            test_seo = {
                "title": "Test SEO Title Updated",
                "description": "Test SEO description updated",
                "og_title": "Test OG Title Updated",
                "og_description": "Test OG description updated",
                "og_image_url": ""
            }
            
            response = self.session.put(
                f"{self.api_url}/seo",
                json=test_seo,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                # Verify the update
                content_response = self.session.get(f"{self.api_url}/content", timeout=10)
                if content_response.status_code == 200:
                    content = content_response.json()
                    seo = content.get('seo', {})
                    if seo.get('title') == test_seo['title']:
                        return self.log_test("PUT /api/seo", True)
                    else:
                        return self.log_test("PUT /api/seo", False, "Update not reflected")
                else:
                    return self.log_test("PUT /api/seo", False, "Could not verify update")
            else:
                return self.log_test("PUT /api/seo", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("PUT /api/seo", False, str(e))

    def test_logout(self):
        """Test logout functionality"""
        try:
            response = self.session.post(f"{self.api_url}/auth/logout", timeout=10)
            success = response.status_code == 200
            if success:
                # Verify that auth/me now returns 401
                me_response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
                if me_response.status_code == 401:
                    return self.log_test("POST /api/auth/logout", True)
                else:
                    return self.log_test("POST /api/auth/logout", False, "Still authenticated after logout")
            else:
                return self.log_test("POST /api/auth/logout", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("POST /api/auth/logout", False, str(e))

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Special Education Landing Page Backend API Tests")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 60)
        
        # Test public endpoints first
        self.test_content_endpoint()
        
        # Test authentication
        if not self.test_admin_login():
            print("❌ Login failed - stopping authenticated tests")
            return self.print_summary()
        
        self.test_auth_me()
        
        # Test protected endpoints
        self.test_hero_section_update()
        self.test_section_toggle()
        self.test_section_reorder()
        self.test_settings_update()
        self.test_seo_update()
        
        # Test unauthorized access
        self.test_unauthorized_access()
        
        # Test logout (this will invalidate session)
        self.test_logout()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run}")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = SpecialEducationAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())