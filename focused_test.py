#!/usr/bin/env python3
"""
Focused Backend Testing for Key Endpoints
Testing after mobile layout repairs
"""

import requests
import json
from datetime import datetime

class FocusedAPITester:
    def __init__(self, base_url="https://permit-manager-3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.client_token = None
        self.controller_token = None
        self.admin_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def get_auth_headers(self, token):
        """Get authorization headers with token"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def setup_users(self):
        """Setup test users for authentication"""
        print("🔧 SETTING UP TEST USERS")
        print("=" * 40)
        
        # Register client
        timestamp = int(datetime.now().timestamp())
        client_data = {
            "email": f"client{timestamp}@test.com",
            "full_name": "Jan Kowalski",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("Register Client", "POST", "auth/register", 200, data=client_data)
        if success and response.get('access_token'):
            self.client_token = response['access_token']
        
        # Register controller
        controller_data = {
            "email": f"controller{timestamp}@test.com",
            "full_name": "Anna Kontroler",
            "password": "TestPass123!",
            "controller_code": "JEZIOROWIELISZEW"
        }
        
        success, response = self.run_test("Register Controller", "POST", "auth/register", 200, data=controller_data)
        if success and response.get('access_token'):
            self.controller_token = response['access_token']
        
        # Login admin
        admin_data = {
            "email": "admin@jezioro-wieliszew.pl",
            "password": "admin"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, data=admin_data)
        if success and response.get('access_token'):
            self.admin_token = response['access_token']

    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 AUTHENTICATION ENDPOINTS")
        print("=" * 40)
        
        # Test login
        if self.client_token:
            headers = self.get_auth_headers(self.client_token)
            self.run_test("GET /api/auth/me", "GET", "auth/me", 200, headers=headers)
        
        # Test registration (already done in setup)
        print("✅ Registration endpoints tested in setup")

    def test_pro_system_endpoints(self):
        """Test Pro system endpoints"""
        print("\n🏆 PRO SYSTEM ENDPOINTS")
        print("=" * 40)
        
        # Test Pro waters
        success, response = self.run_test("GET /api/pro/waters", "GET", "pro/waters", 200)
        
        water_id = None
        tariff_id = None
        if success and response.get('waters'):
            water_id = response['waters'][0].get('id')
            
            # Test tariffs for first water
            if water_id:
                success, tariff_response = self.run_test(
                    f"GET /api/pro/waters/{water_id}/tariffs", 
                    "GET", 
                    f"pro/waters/{water_id}/tariffs", 
                    200
                )
                if success and tariff_response.get('tariffs'):
                    tariff_id = tariff_response['tariffs'][0].get('id')
        
        # Test Pro ticket purchase
        if self.client_token and water_id and tariff_id:
            purchase_data = {
                "water_id": water_id,
                "tariff_id": tariff_id,
                "regulations_accepted": True,
                "data_processing_accepted": True
            }
            headers = self.get_auth_headers(self.client_token)
            self.run_test("POST /api/pro/tickets/purchase", "POST", "pro/tickets/purchase", 200, 
                         data=purchase_data, headers=headers)
        
        # Test my Pro tickets
        if self.client_token:
            headers = self.get_auth_headers(self.client_token)
            self.run_test("GET /api/pro/tickets/my-tickets", "GET", "pro/tickets/my-tickets", 200, headers=headers)

    def test_admin_panel_endpoints(self):
        """Test admin panel endpoints"""
        print("\n🔐 ADMIN PANEL ENDPOINTS")
        print("=" * 40)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return
        
        headers = self.get_auth_headers(self.admin_token)
        
        # Test admin dashboard
        self.run_test("GET /api/admin/dashboard", "GET", "admin/dashboard", 200, headers=headers)
        
        # Test admin waters
        success, response = self.run_test("GET /api/admin/waters", "GET", "admin/waters", 200, headers=headers)
        
        water_id = None
        if success and response.get('waters'):
            water_id = response['waters'][0].get('id')
        
        # Test create water
        create_data = {
            "name": "Test Lake API",
            "location": "Test Location, Poland",
            "description": "Test lake created via API testing",
            "regulations": "Test regulations"
        }
        success, create_response = self.run_test("POST /api/admin/waters", "POST", "admin/waters", 200, 
                                                data=create_data, headers=headers)
        
        created_water_id = None
        if success and create_response.get('water'):
            created_water_id = create_response['water'].get('id')
        
        # Test update water
        if created_water_id:
            update_data = {
                "name": "Test Lake API Updated",
                "location": "Updated Location, Poland",
                "description": "Updated description",
                "regulations": "Updated regulations"
            }
            self.run_test(f"PUT /api/admin/waters/{created_water_id}", "PUT", 
                         f"admin/waters/{created_water_id}", 200, data=update_data, headers=headers)
        
        # Test delete water (should succeed for created water)
        if created_water_id:
            self.run_test(f"DELETE /api/admin/waters/{created_water_id}", "DELETE", 
                         f"admin/waters/{created_water_id}", 200, headers=headers)
        
        # Test delete water with tickets (should fail)
        if water_id:
            self.run_test(f"DELETE /api/admin/waters/{water_id} (Should Fail)", "DELETE", 
                         f"admin/waters/{water_id}", 400, headers=headers)

    def test_controller_endpoints(self):
        """Test controller verification endpoints"""
        print("\n🎯 CONTROLLER VERIFICATION ENDPOINTS")
        print("=" * 40)
        
        if not self.controller_token:
            print("❌ No controller token available")
            return
        
        headers = self.get_auth_headers(self.controller_token)
        
        # Test QR verification with invalid token
        qr_data = {"qr_token": "invalid-jwt-token"}
        self.run_test("POST /api/pro/tickets/verify-qr", "POST", "pro/tickets/verify-qr", 200, 
                     data=qr_data, headers=headers)
        
        # Test ShortCode verification with invalid code
        shortcode_data = {"short_code": "INVALID1"}
        self.run_test("POST /api/pro/tickets/verify-shortcode", "POST", "pro/tickets/verify-shortcode", 200, 
                     data=shortcode_data, headers=headers)

    def test_legacy_system_endpoints(self):
        """Test legacy system endpoints"""
        print("\n📋 LEGACY SYSTEM ENDPOINTS")
        print("=" * 40)
        
        # Test permit types
        self.run_test("GET /api/permits/types", "GET", "permits/types", 200)
        
        # Test permit purchase
        if self.client_token:
            purchase_data = {
                "permit_types": ["daily"],
                "regulations_accepted": True,
                "data_processing_accepted": True
            }
            headers = self.get_auth_headers(self.client_token)
            self.run_test("POST /api/permits/purchase", "POST", "permits/purchase", 200, 
                         data=purchase_data, headers=headers)

    def run_focused_tests(self):
        """Run focused tests on key endpoints"""
        print("🎯 FOCUSED BACKEND TESTING - KEY ENDPOINTS AFTER MOBILE LAYOUT REPAIRS")
        print("=" * 80)
        
        # Setup
        self.setup_users()
        
        # Test key endpoint categories
        self.test_authentication_endpoints()
        self.test_pro_system_endpoints()
        self.test_admin_panel_endpoints()
        self.test_controller_endpoints()
        self.test_legacy_system_endpoints()
        
        # Final results
        print(f"\n📊 FOCUSED TEST RESULTS")
        print("=" * 40)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL KEY ENDPOINTS WORKING!")
        else:
            print("⚠️  Some endpoints have issues - see details above")

if __name__ == "__main__":
    tester = FocusedAPITester()
    tester.run_focused_tests()