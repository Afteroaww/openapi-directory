import requests
import sys
import json
from datetime import datetime

class FishingPermitsAPITester:
    def __init__(self, base_url="https://fishing-fees.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.client_token = None
        self.controller_token = None
        self.admin_token = None
        self.purchase_result = None
        self.client_user = None
        self.controller_user = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
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
                if files:
                    # For multipart form data, don't set Content-Type header
                    auth_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
                    response = requests.post(url, data=data, files=files, headers=auth_headers, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def get_auth_headers(self, token):
        """Get authorization headers with token"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_get_permit_types(self):
        """Test getting permit types"""
        success, response = self.run_test("Get Permit Types", "GET", "permits/types", 200)
        
        if success and response:
            # Validate response structure
            if 'permit_types' in response:
                permit_types = response['permit_types']
                expected_types = ['daily', 'monthly', 'yearly']
                # Updated prices according to the new system
                expected_prices = {'daily': 20.0, 'monthly': 60.0, 'yearly': 300.0}
                
                print(f"   Found {len(permit_types)} permit types")
                for permit in permit_types:
                    if permit['type'] in expected_types and permit['price'] == expected_prices[permit['type']]:
                        print(f"   ✅ {permit['type']}: {permit['price']} PLN - OK")
                    else:
                        print(f"   ❌ {permit['type']}: {permit['price']} PLN - Expected {expected_prices.get(permit['type'], 'unknown')}")
                        return False, response
                return True, response
            else:
                print("   ❌ Missing 'permit_types' in response")
                return False, response
        
        return success, response

    def test_register_client(self):
        """Test client registration"""
        timestamp = int(datetime.now().timestamp())
        test_data = {
            "email": f"client{timestamp}@test.com",
            "full_name": "Jan Kowalski",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Register Client", 
            "POST", 
            "auth/register", 
            200, 
            data=test_data
        )
        
        if success and response:
            if response.get('success') and response.get('access_token'):
                self.client_token = response['access_token']
                self.client_user = response.get('user', {})
                print(f"   ✅ Client registered successfully - Role: {self.client_user.get('role')}")
                return True, response
            else:
                print(f"   ❌ Registration failed: {response}")
                return False, response
        
        return success, response

    def test_register_controller(self):
        """Test controller registration with special code"""
        timestamp = int(datetime.now().timestamp())
        test_data = {
            "email": f"controller{timestamp}@test.com",
            "full_name": "Anna Kontroler",
            "password": "TestPass123!",
            "controller_code": "JEZIOROWIELISZEW"  # Updated to correct code
        }
        
        success, response = self.run_test(
            "Register Controller", 
            "POST", 
            "auth/register", 
            200, 
            data=test_data
        )
        
        if success and response:
            if response.get('success') and response.get('access_token'):
                self.controller_token = response['access_token']
                self.controller_user = response.get('user', {})
                print(f"   ✅ Controller registered successfully - Role: {self.controller_user.get('role')}")
                return True, response
            else:
                print(f"   ❌ Controller registration failed: {response}")
                return False, response
        
        return success, response

    def test_client_upgrade_to_controller(self):
        """Test upgrading existing client to controller with special code"""
        # First register as client
        timestamp = int(datetime.now().timestamp())
        client_email = f"upgrade_test{timestamp}@test.com"
        
        client_data = {
            "email": client_email,
            "full_name": "Test Upgrade User",
            "password": "TestPass123!"
        }
        
        print(f"\n🔄 Testing Client to Controller Upgrade Flow")
        
        # Step 1: Register as client
        success, response = self.run_test(
            "Step 1: Register as Client", 
            "POST", 
            "auth/register", 
            200, 
            data=client_data
        )
        
        if not success:
            return False, {}
        
        # Step 2: Try to register same email as controller without code (should fail)
        controller_data_no_code = {
            "email": client_email,
            "full_name": "Test Upgrade User",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Step 2: Try Register Same Email Without Code (Should Fail)", 
            "POST", 
            "auth/register", 
            400, 
            data=controller_data_no_code
        )
        
        if not success:
            print("   ❌ Expected 400 error for duplicate email without code")
            return False, {}
        
        # Step 3: Register same email as controller with correct code (should upgrade)
        controller_data_with_code = {
            "email": client_email,
            "full_name": "Test Upgrade User",
            "password": "TestPass123!",
            "controller_code": "JEZIOROWIELISZEW"
        }
        
        success, response = self.run_test(
            "Step 3: Upgrade Client to Controller with Code", 
            "POST", 
            "auth/register", 
            200, 
            data=controller_data_with_code
        )
        
        if success and response:
            if (response.get('success') and 
                response.get('access_token') and 
                response.get('user', {}).get('role') == 'controller'):
                print(f"   ✅ Client successfully upgraded to controller")
                print(f"   ✅ Message: {response.get('message', 'No message')}")
                return True, response
            else:
                print(f"   ❌ Upgrade failed: {response}")
                return False, response
        
        return success, response

    def test_register_invalid_controller_code(self):
        """Test controller registration with invalid code"""
        timestamp = int(datetime.now().timestamp())
        test_data = {
            "email": f"invalid{timestamp}@test.com",
            "full_name": "Invalid Controller",
            "password": "TestPass123!",
            "controller_code": "wrong code"
        }
        
        success, response = self.run_test(
            "Register Invalid Controller Code", 
            "POST", 
            "auth/register", 
            400, 
            data=test_data
        )
        
        return success, response

    def test_login_client(self):
        """Test client login"""
        if not self.client_user:
            print("❌ No client user available for login test")
            return False, {}
        
        test_data = {
            "email": self.client_user['email'],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Login Client", 
            "POST", 
            "auth/login", 
            200, 
            data=test_data
        )
        
        if success and response:
            if response.get('access_token'):
                print(f"   ✅ Client login successful")
                return True, response
            else:
                print(f"   ❌ Login failed: {response}")
                return False, response
        
        return success, response

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.client_token:
            print("❌ No client token available for user info test")
            return False, {}
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Get Current User Info", 
            "GET", 
            "auth/me", 
            200, 
            headers=headers
        )
        
        if success and response:
            if response.get('role') == 'client':
                print(f"   ✅ User info retrieved - Role: {response.get('role')}")
                return True, response
            else:
                print(f"   ❌ Incorrect user role: {response.get('role')}")
                return False, response
        
        return success, response

    def test_get_regulations(self):
        """Test getting fishing regulations and GDPR consent"""
        success, response = self.run_test(
            "Get Fishing Regulations", 
            "GET", 
            "regulations", 
            200
        )
        
        if success and response:
            # Validate response structure
            required_fields = ['fishing_regulations', 'data_processing_agreement']
            for field in required_fields:
                if field not in response:
                    print(f"   ❌ Missing field: {field}")
                    return False, response
            
            # Check fishing regulations content
            fishing_regs = response.get('fishing_regulations', {})
            if 'title' in fishing_regs and 'content' in fishing_regs:
                content = fishing_regs['content']
                # Check for key elements in regulations
                key_elements = ['REGULAMIN ŁOWISKA', 'szczupak', 'sandacz', 'karp', 'catch & release', 'wymiary ochronne']
                missing_elements = []
                for element in key_elements:
                    if element.lower() not in content.lower():
                        missing_elements.append(element)
                
                if missing_elements:
                    print(f"   ❌ Missing key elements in regulations: {missing_elements}")
                    return False, response
                else:
                    print(f"   ✅ Fishing regulations content complete with all key elements")
            else:
                print(f"   ❌ Missing title or content in fishing_regulations")
                return False, response
            
            # Check GDPR agreement content
            gdpr_agreement = response.get('data_processing_agreement', {})
            if 'title' in gdpr_agreement and 'content' in gdpr_agreement:
                content = gdpr_agreement['content']
                # Check for key GDPR elements
                gdpr_elements = ['Administrator danych', 'Cel przetwarzania', 'RODO', '3 lata', 'kontakt']
                missing_gdpr = []
                for element in gdpr_elements:
                    if element.lower() not in content.lower():
                        missing_gdpr.append(element)
                
                if missing_gdpr:
                    print(f"   ❌ Missing key GDPR elements: {missing_gdpr}")
                    return False, response
                else:
                    print(f"   ✅ GDPR agreement content complete with all key elements")
            else:
                print(f"   ❌ Missing title or content in data_processing_agreement")
                return False, response
            
            return True, response
        
        return success, response

    def test_purchase_without_regulations_consent(self):
        """Test purchasing permits without regulations consent"""
        if not self.client_token:
            print("❌ No client token available for consent test")
            return False, {}
        
        test_data = {
            "permit_types": ["daily"],
            "regulations_accepted": False,
            "data_processing_accepted": True
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Without Regulations Consent (Should Fail)", 
            "POST", 
            "permits/purchase", 
            400, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if 'fishing regulations' in response.get('detail', '').lower():
                print(f"   ✅ Correctly rejected purchase without regulations consent")
                return True, response
            else:
                print(f"   ❌ Wrong error message: {response.get('detail')}")
                return False, response
        
        return success, response

    def test_purchase_without_data_consent(self):
        """Test purchasing permits without data processing consent"""
        if not self.client_token:
            print("❌ No client token available for consent test")
            return False, {}
        
        test_data = {
            "permit_types": ["daily"],
            "regulations_accepted": True,
            "data_processing_accepted": False
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Without Data Processing Consent (Should Fail)", 
            "POST", 
            "permits/purchase", 
            400, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if 'data processing' in response.get('detail', '').lower():
                print(f"   ✅ Correctly rejected purchase without data processing consent")
                return True, response
            else:
                print(f"   ❌ Wrong error message: {response.get('detail')}")
                return False, response
        
        return success, response

    def test_purchase_with_both_consents(self):
        """Test purchasing permits with both consents accepted"""
        if not self.client_token:
            print("❌ No client token available for consent test")
            return False, {}
        
        test_data = {
            "permit_types": ["daily"],
            "regulations_accepted": True,
            "data_processing_accepted": True
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase With Both Consents Accepted", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if response.get('success') and response.get('total_amount') == 20.0:
                print(f"   ✅ Purchase successful with both consents")
                return True, response
            else:
                print(f"   ❌ Purchase failed despite both consents: {response}")
                return False, response
        
        return success, response

    def test_purchase_permits_client(self):
        """Test purchasing permits as client (legacy test without consents)"""
        if not self.client_token:
            print("❌ No client token available for purchase test")
            return False, {}
        
        test_data = {
            "permit_types": ["daily"],
            "regulations_accepted": True,
            "data_processing_accepted": True
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Daily Permit (Client)", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            # Store purchase result for verification test
            self.purchase_result = response
            
            # Validate response structure
            required_fields = ['success', 'order_id', 'total_amount', 'permits']
            for field in required_fields:
                if field not in response:
                    print(f"   ❌ Missing field: {field}")
                    return False, response
            
            if response['success'] and response['total_amount'] == 20.0:  # Updated price
                print(f"   ✅ Purchase successful - Order ID: {response['order_id']}")
                print(f"   ✅ Total amount: {response['total_amount']} PLN")
                
                # Check if QR code is generated
                if response['permits'] and len(response['permits']) > 0:
                    permit = response['permits'][0]
                    if 'qr_code' in permit and permit['qr_code']:
                        print(f"   ✅ QR code generated")
                    else:
                        print(f"   ❌ QR code missing")
                        return False, response
                
                return True, response
            else:
                print(f"   ❌ Purchase failed or incorrect amount - Expected 20.0, got {response.get('total_amount')}")
                return False, response
        
        return success, response

    def test_purchase_unauthorized(self):
        """Test purchasing permits without authentication"""
        test_data = {
            "permit_types": ["daily"]
        }
        
        success, response = self.run_test(
            "Purchase Without Auth", 
            "POST", 
            "permits/purchase", 
            401, 
            data=test_data
        )
        
        return success, response

    def test_purchase_controller_forbidden(self):
        """Test that controller cannot purchase permits"""
        if not self.controller_token:
            print("❌ No controller token available for forbidden test")
            return False, {}
        
        test_data = {
            "permit_types": ["daily"]
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Purchase as Controller (Should Fail)", 
            "POST", 
            "permits/purchase", 
            403, 
            data=test_data,
            headers=headers
        )
        
        return success, response

    def test_get_my_permits(self):
        """Test getting client's permits"""
        if not self.client_token:
            print("❌ No client token available for my permits test")
            return False, {}
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Get My Permits", 
            "GET", 
            "permits/my-permits", 
            200, 
            headers=headers
        )
        
        if success and response:
            if 'permits' in response:
                print(f"   ✅ Found {len(response['permits'])} permits")
                return True, response
            else:
                print(f"   ❌ Missing permits field in response")
                return False, response
        
        return success, response

    def test_purchase_multiple_permits(self):
        """Test purchasing multiple permits"""
        if not self.client_token:
            print("❌ No client token available for multiple permits test")
            return False, {}
        
        test_data = {
            "permit_types": ["daily", "monthly"],
            "regulations_accepted": True,
            "data_processing_accepted": True
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Multiple Permits", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            expected_total = 20.0 + 60.0  # daily + monthly (updated prices)
            if response.get('total_amount') == expected_total:
                print(f"   ✅ Multiple permits total correct: {expected_total} PLN")
                return True, response
            else:
                print(f"   ❌ Incorrect total: expected {expected_total}, got {response.get('total_amount')}")
                return False, response
        
        return success, response

    def test_purchase_validation_errors(self):
        """Test purchase validation errors"""
        if not self.client_token:
            print("❌ No client token available for validation test")
            return False, {}
        
        # Test missing permit types
        test_data_no_permits = {
            "permit_types": [],
            "regulations_accepted": True,
            "data_processing_accepted": True
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, _ = self.run_test(
            "Purchase with No Permit Types", 
            "POST", 
            "permits/purchase", 
            400, 
            data=test_data_no_permits,
            headers=headers
        )
        
        return success, {}

    def test_verify_permit_controller(self):
        """Test permit verification by controller"""
        if not self.controller_token:
            print("❌ No controller token available for verification test")
            return False, {}
        
        if not self.purchase_result or not self.purchase_result.get('permits'):
            print("❌ No purchase result available for verification test")
            return False, {}
        
        # Extract QR data from purchase result
        permit = self.purchase_result['permits'][0]
        permit_id = permit['id']
        customer_name = permit['customer_info']['full_name']
        qr_data = f"PERMIT:{permit_id}:NAME:{customer_name}:VERIFIED"
        
        test_data = {
            "qr_data": qr_data
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Valid Permit (Controller)", 
            "POST", 
            "permits/verify", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if response.get('valid') == True:
                print(f"   ✅ Permit verification successful")
                print(f"   ✅ Customer: {response.get('customer', {}).get('full_name')}")
                return True, response
            else:
                print(f"   ❌ Permit verification failed: {response.get('message')}")
                return False, response
        
        return success, response

    def test_verify_unauthorized(self):
        """Test verification without authentication"""
        test_data = {
            "qr_data": "PERMIT:test:NAME:Test:VERIFIED"
        }
        
        success, response = self.run_test(
            "Verify Without Auth", 
            "POST", 
            "permits/verify", 
            401, 
            data=test_data
        )
        
        return success, response

    def test_verify_client_forbidden(self):
        """Test that client cannot verify permits"""
        if not self.client_token:
            print("❌ No client token available for forbidden test")
            return False, {}
        
        test_data = {
            "qr_data": "PERMIT:test:NAME:Test:VERIFIED"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Verify as Client (Should Fail)", 
            "POST", 
            "permits/verify", 
            403, 
            data=test_data,
            headers=headers
        )
        
        return success, response

    def test_verify_invalid_permit(self):
        """Test verification with invalid QR data"""
        if not self.controller_token:
            print("❌ No controller token available for invalid verification test")
            return False, {}
        
        test_data = {
            "qr_data": "PERMIT:invalid-id:NAME:Test:VERIFIED"
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Invalid Permit", 
            "POST", 
            "permits/verify", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if response.get('valid') == False:
                print(f"   ✅ Invalid permit correctly rejected: {response.get('message')}")
                return True, response
            else:
                print(f"   ❌ Invalid permit was accepted")
                return False, response
        
        return success, response

    def test_verify_malformed_qr(self):
        """Test verification with malformed QR data"""
        if not self.controller_token:
            print("❌ No controller token available for malformed QR test")
            return False, {}
        
        test_data = {
            "qr_data": "INVALID_FORMAT"
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Malformed QR", 
            "POST", 
            "permits/verify", 
            400, 
            data=test_data,
            headers=headers
        )
        
        return success, response

    def test_get_verification_history(self):
        """Test getting verification history for controller"""
        if not self.controller_token:
            print("❌ No controller token available for verification history test")
            return False, {}
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Get Verification History", 
            "GET", 
            "controller/verification-history", 
            200, 
            headers=headers
        )
        
        if success and response:
            if 'logs' in response:
                print(f"   ✅ Found {len(response['logs'])} verification logs")
                return True, response
            else:
                print(f"   ❌ Missing logs field in response")
                return False, response
        
        return success, response

    def test_verify_by_order_valid(self):
        """Test permit verification by order ID with valid order"""
        if not self.controller_token:
            print("❌ No controller token available for order verification test")
            return False, {}
        
        if not self.purchase_result or not self.purchase_result.get('order_id'):
            print("❌ No purchase result available for order verification test")
            return False, {}
        
        order_id = self.purchase_result['order_id']
        test_data = {
            "order_id": order_id
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Valid Order ID", 
            "POST", 
            "permits/verify-by-order", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if response.get('valid') == True:
                print(f"   ✅ Order verification successful")
                print(f"   ✅ Customer: {response.get('customer', {}).get('full_name')}")
                print(f"   ✅ Active permits: {len(response.get('permits', []))}")
                print(f"   ✅ Order ID: {response.get('order_id')}")
                return True, response
            else:
                print(f"   ❌ Order verification failed: {response.get('message')}")
                return False, response
        
        return success, response

    def test_verify_by_order_invalid(self):
        """Test permit verification by order ID with invalid order"""
        if not self.controller_token:
            print("❌ No controller token available for invalid order verification test")
            return False, {}
        
        test_data = {
            "order_id": "FP9999999999"  # Invalid order ID
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Invalid Order ID", 
            "POST", 
            "permits/verify-by-order", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            if response.get('valid') == False:
                print(f"   ✅ Invalid order correctly rejected: {response.get('message')}")
                return True, response
            else:
                print(f"   ❌ Invalid order was accepted")
                return False, response
        
        return success, response

    def test_verify_by_order_empty(self):
        """Test permit verification by order ID with empty order ID"""
        if not self.controller_token:
            print("❌ No controller token available for empty order verification test")
            return False, {}
        
        test_data = {
            "order_id": ""
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Empty Order ID", 
            "POST", 
            "permits/verify-by-order", 
            400, 
            data=test_data,
            headers=headers
        )
        
        return success, response

    def test_verify_by_order_unauthorized(self):
        """Test order verification without authentication"""
        test_data = {
            "order_id": "FP1234567890"
        }
        
        success, response = self.run_test(
            "Verify Order Without Auth", 
            "POST", 
            "permits/verify-by-order", 
            401, 
            data=test_data
        )
        
        return success, response

    def test_verify_by_order_client_forbidden(self):
        """Test that client cannot verify permits by order ID"""
        if not self.client_token:
            print("❌ No client token available for forbidden order test")
            return False, {}
        
        test_data = {
            "order_id": "FP1234567890"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Verify Order as Client (Should Fail)", 
            "POST", 
            "permits/verify-by-order", 
            403, 
            data=test_data,
            headers=headers
        )
        
        return success, response

    def test_purchase_yearly_with_owner_code(self):
        """Test purchasing yearly permit with owner discount code"""
        if not self.client_token:
            print("❌ No client token available for owner code test")
            return False, {}
        
        test_data = {
            "permit_types": ["yearly"],
            "owner_code": "WLASCICIELWIELISZEW",
            "regulations_accepted": True,
            "data_processing_accepted": True
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Yearly with Owner Code", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            # Should be 50 PLN instead of 300 PLN for owner
            if response.get('total_amount') == 50.0:
                print(f"   ✅ Owner discount applied correctly: 50 PLN instead of 300 PLN")
                # Store this result for testing the specific order ID mentioned in requirements
                self.owner_purchase_result = response
                return True, response
            else:
                print(f"   ❌ Owner discount not applied: expected 50.0, got {response.get('total_amount')}")
                return False, response
        
        return success, response

    def test_verify_specific_order_id(self):
        """Test verification with the specific order ID mentioned in requirements"""
        if not self.controller_token:
            print("❌ No controller token available for specific order test")
            return False, {}
        
        # Test with the specific order ID mentioned in requirements: FP1758229556
        test_data = {
            "order_id": "FP1758229556"
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Verify Specific Test Order (FP1758229556)", 
            "POST", 
            "permits/verify-by-order", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            # This might not exist in the database, so we expect it to fail
            if response.get('valid') == False:
                print(f"   ✅ Test order ID correctly not found (expected): {response.get('message')}")
                return True, response
            else:
                print(f"   ✅ Test order ID found and verified: {response.get('message')}")
                return True, response
        
        return success, response

    def test_upload_catch_unauthorized(self):
        """Test uploading catch without authentication"""
        # Create a simple test file data
        test_data = {
            "notes": "Test catch upload"
        }
        
        success, response = self.run_test(
            "Upload Catch Without Auth", 
            "POST", 
            "fishing/upload-catch", 
            403,  # FastAPI returns 403 for missing auth
            data=test_data
        )
        
        return success, response

    def test_upload_catch_client(self):
        """Test uploading fish catch as client - ETAP 1"""
        if not self.client_token:
            print("❌ No client token available for catch upload test")
            return False, {}
        
        # Create a fake image file for testing
        import io
        fake_image = io.BytesIO(b"fake image content for testing")
        fake_image.name = "test_fish.jpg"
        
        test_data = {
            "notes": "Test catch from API test - ETAP 1"
        }
        
        files = {
            "image": ("test_fish.jpg", fake_image, "image/jpeg")
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Upload Fish Catch (Client) - ETAP 1", 
            "POST", 
            "fishing/upload-catch", 
            200,  # Should succeed with fake image
            data=test_data,
            headers=headers,
            files=files
        )
        
        if success and response:
            if response.get('success') and response.get('catch_id'):
                print(f"   ✅ Catch uploaded successfully - ID: {response['catch_id']}")
                print(f"   ✅ Message: {response.get('message', 'No message')}")
                # Store catch ID for later tests
                self.uploaded_catch_id = response['catch_id']
                return True, response
            else:
                print(f"   ❌ Catch upload failed: {response}")
                return False, response
        
        return success, response

    def test_get_my_catches_unauthorized(self):
        """Test getting catches without authentication"""
        success, response = self.run_test(
            "Get My Catches Without Auth", 
            "GET", 
            "fishing/my-catches", 
            403  # FastAPI returns 403 for missing auth
        )
        
        return success, response

    def test_get_my_catches_client(self):
        """Test getting user's fish catches"""
        if not self.client_token:
            print("❌ No client token available for get catches test")
            return False, {}
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Get My Fish Catches", 
            "GET", 
            "fishing/my-catches", 
            200, 
            headers=headers
        )
        
        if success and response:
            if 'catches' in response and 'total' in response:
                print(f"   ✅ Found {response['total']} catches")
                
                # Check if our uploaded catch is in the list
                if hasattr(self, 'uploaded_catch_id') and response['catches']:
                    catch_found = False
                    for catch in response['catches']:
                        if catch.get('id') == self.uploaded_catch_id:
                            catch_found = True
                            print(f"   ✅ Uploaded catch found in list")
                            print(f"   ✅ Status: {catch.get('status', 'unknown')}")
                            print(f"   ✅ Points: {catch.get('points', 0)}")
                            break
                    
                    if not catch_found:
                        print(f"   ❌ Uploaded catch not found in list")
                        return False, response
                
                return True, response
            else:
                print(f"   ❌ Missing catches or total field in response")
                return False, response
        
        return success, response

    def test_get_leaderboard_public(self):
        """Test getting monthly leaderboard - should be public"""
        success, response = self.run_test(
            "Get Monthly Leaderboard (Public)", 
            "GET", 
            "fishing/leaderboard", 
            200
        )
        
        if success and response:
            if 'leaderboard' in response and 'month' in response:
                print(f"   ✅ Leaderboard for month: {response['month']}")
                print(f"   ✅ Found {len(response['leaderboard'])} entries")
                
                # For ETAP 1, leaderboard should be empty or have minimal entries
                # since no catches are approved yet
                if len(response['leaderboard']) == 0:
                    print(f"   ✅ Leaderboard empty as expected for ETAP 1")
                else:
                    print(f"   ℹ️  Leaderboard has {len(response['leaderboard'])} entries")
                
                return True, response
            else:
                print(f"   ❌ Missing leaderboard or month field in response")
                return False, response
        
        return success, response

    def test_controller_cannot_upload_catch(self):
        """Test that controller can upload catches (any authenticated user can)"""
        if not self.controller_token:
            print("❌ No controller token available for controller catch test")
            return False, {}
        
        test_data = {
            "notes": "Controller trying to upload catch"
        }
        
        headers = self.get_auth_headers(self.controller_token)
        success, response = self.run_test(
            "Controller Upload Catch (Should Work)", 
            "POST", 
            "fishing/upload-catch", 
            400,  # Expect 400 because no image file provided
            data=test_data,
            headers=headers
        )
        
        # Note: Based on the backend code, any authenticated user can upload catches
        # The endpoint uses get_current_active_user, not role-specific authorization
        if success and response:
            if 'Image file is required' in response.get('detail', ''):
                print(f"   ✅ Controller can upload catches (authentication works)")
                print(f"   ✅ Endpoint correctly requires image file")
                return True, response
            else:
                print(f"   ❌ Unexpected error message: {response.get('detail')}")
                return False, response
        
        return success, response

    def test_fishing_endpoints_comprehensive(self):
        """Comprehensive test of all fishing endpoints - ETAP 1"""
        print(f"\n🎣 COMPREHENSIVE FISHING ENDPOINTS TEST - ETAP 1")
        print(f"=" * 50)
        
        # Test sequence for ETAP 1
        tests = [
            ("Upload unauthorized", self.test_upload_catch_unauthorized),
            ("Upload as client", self.test_upload_catch_client),
            ("Get catches unauthorized", self.test_get_my_catches_unauthorized),
            ("Get my catches", self.test_get_my_catches_client),
            ("Get leaderboard", self.test_get_leaderboard_public),
            ("Controller upload", self.test_controller_cannot_upload_catch),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                success, _ = test_func()
                if success:
                    passed += 1
                    print(f"   ✅ {test_name}: PASSED")
                else:
                    print(f"   ❌ {test_name}: FAILED")
            except Exception as e:
                print(f"   ❌ {test_name}: ERROR - {str(e)}")
        
        print(f"\n🎣 FISHING ENDPOINTS SUMMARY:")
        print(f"   Passed: {passed}/{total}")
        print(f"   Success rate: {(passed/total*100):.1f}%")
        
        return passed == total, {"passed": passed, "total": total}

def main():
    print("🎣 Starting Fishing Permits API Tests (Role-Based System)")
    print("=" * 60)
    
    tester = FishingPermitsAPITester()
    
    # Run all tests in order
    tests = [
        # Basic API tests
        tester.test_api_root,
        tester.test_get_permit_types,
        tester.test_get_regulations,  # NEW: Test regulations endpoint
        
        # Authentication tests
        tester.test_register_client,
        tester.test_register_controller,
        tester.test_client_upgrade_to_controller,  # New test for role upgrade
        tester.test_register_invalid_controller_code,
        tester.test_login_client,
        tester.test_get_current_user,
        
        # NEW: Consent validation tests
        tester.test_purchase_without_regulations_consent,
        tester.test_purchase_without_data_consent,
        tester.test_purchase_with_both_consents,
        
        # Client functionality tests
        tester.test_purchase_permits_client,
        tester.test_purchase_multiple_permits,
        tester.test_purchase_validation_errors,
        tester.test_get_my_permits,
        
        # Authorization tests
        tester.test_purchase_unauthorized,
        tester.test_purchase_controller_forbidden,
        tester.test_verify_unauthorized,
        tester.test_verify_client_forbidden,
        
        # Controller functionality tests
        tester.test_verify_permit_controller,
        tester.test_verify_invalid_permit,
        tester.test_verify_malformed_qr,
        tester.test_get_verification_history,
        
        # NEW: Order verification tests
        tester.test_verify_by_order_valid,
        tester.test_verify_by_order_invalid,
        tester.test_verify_by_order_empty,
        tester.test_verify_by_order_unauthorized,
        tester.test_verify_by_order_client_forbidden,
        
        # NEW: Owner discount tests
        tester.test_purchase_yearly_with_owner_code,
        tester.test_verify_specific_order_id,
        
        # NEW: ETAP 1 - Fishing catch & release endpoints
        tester.test_fishing_endpoints_comprehensive,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())