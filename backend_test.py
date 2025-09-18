import requests
import sys
import json
from datetime import datetime

class FishingPermitsAPITester:
    def __init__(self, base_url="https://fishing-fees.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.purchase_result = None

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
                expected_prices = {'daily': 25.0, 'monthly': 150.0, 'yearly': 500.0}
                
                print(f"   Found {len(permit_types)} permit types")
                for permit in permit_types:
                    if permit['type'] in expected_types and permit['price'] == expected_prices[permit['type']]:
                        print(f"   ✅ {permit['type']}: {permit['price']} PLN - OK")
                    else:
                        print(f"   ❌ {permit['type']}: {permit['price']} PLN - Unexpected")
                        return False, response
                return True, response
            else:
                print("   ❌ Missing 'permit_types' in response")
                return False, response
        
        return success, response

    def test_purchase_permits(self):
        """Test purchasing permits"""
        test_data = {
            "customer": {
                "full_name": "Jan Kowalski",
                "email": "jan.kowalski@test.com",
                "phone": "+48123456789"
            },
            "permit_types": ["daily"]
        }
        
        success, response = self.run_test(
            "Purchase Daily Permit", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data
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
            
            if response['success'] and response['total_amount'] == 25.0:
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
                print(f"   ❌ Purchase failed or incorrect amount")
                return False, response
        
        return success, response

    def test_purchase_multiple_permits(self):
        """Test purchasing multiple permits"""
        test_data = {
            "customer": {
                "full_name": "Anna Nowak",
                "email": "anna.nowak@test.com"
            },
            "permit_types": ["daily", "monthly"]
        }
        
        success, response = self.run_test(
            "Purchase Multiple Permits", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data
        )
        
        if success and response:
            expected_total = 25.0 + 150.0  # daily + monthly
            if response.get('total_amount') == expected_total:
                print(f"   ✅ Multiple permits total correct: {expected_total} PLN")
                return True, response
            else:
                print(f"   ❌ Incorrect total: expected {expected_total}, got {response.get('total_amount')}")
                return False, response
        
        return success, response

    def test_purchase_validation_errors(self):
        """Test purchase validation errors"""
        # Test missing customer data
        test_data_no_customer = {
            "customer": {
                "full_name": "",
                "email": ""
            },
            "permit_types": ["daily"]
        }
        
        success, _ = self.run_test(
            "Purchase with Missing Customer Data", 
            "POST", 
            "permits/purchase", 
            400, 
            data=test_data_no_customer
        )
        
        # Test missing permit types
        test_data_no_permits = {
            "customer": {
                "full_name": "Test User",
                "email": "test@test.com"
            },
            "permit_types": []
        }
        
        success2, _ = self.run_test(
            "Purchase with No Permit Types", 
            "POST", 
            "permits/purchase", 
            400, 
            data=test_data_no_permits
        )
        
        return success and success2, {}

    def test_verify_permit(self):
        """Test permit verification"""
        if not self.purchase_result or not self.purchase_result.get('permits'):
            print("❌ No purchase result available for verification test")
            return False, {}
        
        # Extract QR data from purchase result
        permit = self.purchase_result['permits'][0]
        permit_id = permit['id']
        customer_name = permit['customer']['full_name']
        qr_data = f"PERMIT:{permit_id}:NAME:{customer_name}:VERIFIED"
        
        test_data = {
            "qr_data": qr_data
        }
        
        success, response = self.run_test(
            "Verify Valid Permit", 
            "POST", 
            "permits/verify", 
            200, 
            data=test_data
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

    def test_verify_invalid_permit(self):
        """Test verification with invalid QR data"""
        test_data = {
            "qr_data": "PERMIT:invalid-id:NAME:Test:VERIFIED"
        }
        
        success, response = self.run_test(
            "Verify Invalid Permit", 
            "POST", 
            "permits/verify", 
            200, 
            data=test_data
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
        test_data = {
            "qr_data": "INVALID_FORMAT"
        }
        
        success, response = self.run_test(
            "Verify Malformed QR", 
            "POST", 
            "permits/verify", 
            400, 
            data=test_data
        )
        
        return success, response

    def test_get_order_permits(self):
        """Test getting permits by order ID"""
        if not self.purchase_result:
            print("❌ No purchase result available for order test")
            return False, {}
        
        order_id = self.purchase_result['order_id']
        
        success, response = self.run_test(
            "Get Order Permits", 
            "GET", 
            f"permits/order/{order_id}", 
            200
        )
        
        if success and response:
            if 'permits' in response and len(response['permits']) > 0:
                print(f"   ✅ Found {len(response['permits'])} permits for order")
                return True, response
            else:
                print(f"   ❌ No permits found for order")
                return False, response
        
        return success, response

def main():
    print("🎣 Starting Fishing Permits API Tests")
    print("=" * 50)
    
    tester = FishingPermitsAPITester()
    
    # Run all tests
    tests = [
        tester.test_api_root,
        tester.test_get_permit_types,
        tester.test_purchase_permits,
        tester.test_purchase_multiple_permits,
        tester.test_purchase_validation_errors,
        tester.test_verify_permit,
        tester.test_verify_invalid_permit,
        tester.test_verify_malformed_qr,
        tester.test_get_order_permits
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
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