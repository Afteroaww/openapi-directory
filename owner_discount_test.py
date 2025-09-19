import requests
import sys
import json
from datetime import datetime

class OwnerDiscountTester:
    def __init__(self, base_url="https://permit-manager-3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.client_token = None
        self.client_user = None

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

    def setup_client(self):
        """Register and login a test client"""
        timestamp = int(datetime.now().timestamp())
        test_data = {
            "email": f"owner_test_client{timestamp}@test.com",
            "full_name": "Jan Współwłaściciel",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Setup: Register Test Client", 
            "POST", 
            "auth/register", 
            200, 
            data=test_data
        )
        
        if success and response:
            if response.get('success') and response.get('access_token'):
                self.client_token = response['access_token']
                self.client_user = response.get('user', {})
                print(f"   ✅ Test client setup successful")
                return True, response
            else:
                print(f"   ❌ Client setup failed: {response}")
                return False, response
        
        return success, response

    def test_purchase_yearly_without_owner_code(self):
        """Test 1: Purchase yearly permit without owner code - should be 300 PLN"""
        if not self.client_token:
            print("❌ No client token available")
            return False, {}
        
        test_data = {
            "permit_types": ["yearly"]
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Yearly Without Owner Code", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            expected_price = 300.0
            actual_price = response.get('total_amount')
            
            if actual_price == expected_price:
                print(f"   ✅ Correct price without owner code: {actual_price} PLN")
                
                # Check permit description doesn't contain "(Współwłaściciel)"
                permits = response.get('permits', [])
                if permits and len(permits) > 0:
                    description = permits[0].get('description', '')
                    if "(Współwłaściciel)" not in description:
                        print(f"   ✅ Description correct (no owner suffix): {description}")
                        return True, response
                    else:
                        print(f"   ❌ Description incorrectly contains owner suffix: {description}")
                        return False, response
                else:
                    print(f"   ❌ No permits in response")
                    return False, response
            else:
                print(f"   ❌ Incorrect price: expected {expected_price}, got {actual_price}")
                return False, response
        
        return success, response

    def test_purchase_yearly_with_owner_code(self):
        """Test 2: Purchase yearly permit with owner code - should be 50 PLN"""
        if not self.client_token:
            print("❌ No client token available")
            return False, {}
        
        test_data = {
            "permit_types": ["yearly"],
            "owner_code": "WLASCICIELWIELISZEW"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Yearly With Owner Code", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            expected_price = 50.0
            actual_price = response.get('total_amount')
            
            if actual_price == expected_price:
                print(f"   ✅ Correct discounted price: {actual_price} PLN (saved 250 PLN!)")
                
                # Check permit description contains "(Współwłaściciel)"
                permits = response.get('permits', [])
                if permits and len(permits) > 0:
                    description = permits[0].get('description', '')
                    if "(Współwłaściciel)" in description:
                        print(f"   ✅ Description correctly contains owner suffix: {description}")
                        return True, response
                    else:
                        print(f"   ❌ Description missing owner suffix: {description}")
                        return False, response
                else:
                    print(f"   ❌ No permits in response")
                    return False, response
            else:
                print(f"   ❌ Incorrect price: expected {expected_price}, got {actual_price}")
                return False, response
        
        return success, response

    def test_purchase_yearly_with_wrong_owner_code(self):
        """Test 3: Purchase yearly permit with wrong owner code - should be 300 PLN"""
        if not self.client_token:
            print("❌ No client token available")
            return False, {}
        
        test_data = {
            "permit_types": ["yearly"],
            "owner_code": "WRONGCODE123"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Yearly With Wrong Owner Code", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            expected_price = 300.0
            actual_price = response.get('total_amount')
            
            if actual_price == expected_price:
                print(f"   ✅ Correct price with wrong code: {actual_price} PLN (no discount applied)")
                
                # Check permit description doesn't contain "(Współwłaściciel)"
                permits = response.get('permits', [])
                if permits and len(permits) > 0:
                    description = permits[0].get('description', '')
                    if "(Współwłaściciel)" not in description:
                        print(f"   ✅ Description correct (no owner suffix): {description}")
                        return True, response
                    else:
                        print(f"   ❌ Description incorrectly contains owner suffix: {description}")
                        return False, response
                else:
                    print(f"   ❌ No permits in response")
                    return False, response
            else:
                print(f"   ❌ Incorrect price: expected {expected_price}, got {actual_price}")
                return False, response
        
        return success, response

    def test_purchase_daily_with_owner_code(self):
        """Test 4: Purchase daily permit with owner code - should be 20 PLN (no discount)"""
        if not self.client_token:
            print("❌ No client token available")
            return False, {}
        
        test_data = {
            "permit_types": ["daily"],
            "owner_code": "WLASCICIELWIELISZEW"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Daily With Owner Code (No Discount)", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            expected_price = 20.0
            actual_price = response.get('total_amount')
            
            if actual_price == expected_price:
                print(f"   ✅ Correct price (no discount for daily): {actual_price} PLN")
                
                # Check permit description doesn't contain "(Współwłaściciel)"
                permits = response.get('permits', [])
                if permits and len(permits) > 0:
                    description = permits[0].get('description', '')
                    if "(Współwłaściciel)" not in description:
                        print(f"   ✅ Description correct (no owner suffix for daily): {description}")
                        return True, response
                    else:
                        print(f"   ❌ Description incorrectly contains owner suffix: {description}")
                        return False, response
                else:
                    print(f"   ❌ No permits in response")
                    return False, response
            else:
                print(f"   ❌ Incorrect price: expected {expected_price}, got {actual_price}")
                return False, response
        
        return success, response

    def test_purchase_monthly_with_owner_code(self):
        """Test 5: Purchase monthly permit with owner code - should be 60 PLN (no discount)"""
        if not self.client_token:
            print("❌ No client token available")
            return False, {}
        
        test_data = {
            "permit_types": ["monthly"],
            "owner_code": "WLASCICIELWIELISZEW"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Monthly With Owner Code (No Discount)", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            expected_price = 60.0
            actual_price = response.get('total_amount')
            
            if actual_price == expected_price:
                print(f"   ✅ Correct price (no discount for monthly): {actual_price} PLN")
                
                # Check permit description doesn't contain "(Współwłaściciel)"
                permits = response.get('permits', [])
                if permits and len(permits) > 0:
                    description = permits[0].get('description', '')
                    if "(Współwłaściciel)" not in description:
                        print(f"   ✅ Description correct (no owner suffix for monthly): {description}")
                        return True, response
                    else:
                        print(f"   ❌ Description incorrectly contains owner suffix: {description}")
                        return False, response
                else:
                    print(f"   ❌ No permits in response")
                    return False, response
            else:
                print(f"   ❌ Incorrect price: expected {expected_price}, got {actual_price}")
                return False, response
        
        return success, response

    def test_purchase_mixed_permits_with_owner_code(self):
        """Test 6: Purchase mixed permits with owner code - only yearly should get discount"""
        if not self.client_token:
            print("❌ No client token available")
            return False, {}
        
        test_data = {
            "permit_types": ["daily", "monthly", "yearly"],
            "owner_code": "WLASCICIELWIELISZEW"
        }
        
        headers = self.get_auth_headers(self.client_token)
        success, response = self.run_test(
            "Purchase Mixed Permits With Owner Code", 
            "POST", 
            "permits/purchase", 
            200, 
            data=test_data,
            headers=headers
        )
        
        if success and response:
            # Expected: daily (20) + monthly (60) + yearly (50 with discount) = 130 PLN
            expected_price = 20.0 + 60.0 + 50.0
            actual_price = response.get('total_amount')
            
            if actual_price == expected_price:
                print(f"   ✅ Correct mixed price with owner discount: {actual_price} PLN")
                
                # Check permits - only yearly should have owner suffix
                permits = response.get('permits', [])
                if permits and len(permits) == 3:
                    yearly_permit = None
                    daily_permit = None
                    monthly_permit = None
                    
                    for permit in permits:
                        if permit.get('permit_type') == 'yearly':
                            yearly_permit = permit
                        elif permit.get('permit_type') == 'daily':
                            daily_permit = permit
                        elif permit.get('permit_type') == 'monthly':
                            monthly_permit = permit
                    
                    # Check yearly permit has discount and suffix
                    if yearly_permit:
                        if yearly_permit.get('price') == 50.0 and "(Współwłaściciel)" in yearly_permit.get('description', ''):
                            print(f"   ✅ Yearly permit correctly discounted: {yearly_permit.get('price')} PLN with owner suffix")
                        else:
                            print(f"   ❌ Yearly permit incorrect: price={yearly_permit.get('price')}, desc={yearly_permit.get('description')}")
                            return False, response
                    
                    # Check daily permit has no discount or suffix
                    if daily_permit:
                        if daily_permit.get('price') == 20.0 and "(Współwłaściciel)" not in daily_permit.get('description', ''):
                            print(f"   ✅ Daily permit correctly not discounted: {daily_permit.get('price')} PLN without owner suffix")
                        else:
                            print(f"   ❌ Daily permit incorrect: price={daily_permit.get('price')}, desc={daily_permit.get('description')}")
                            return False, response
                    
                    # Check monthly permit has no discount or suffix
                    if monthly_permit:
                        if monthly_permit.get('price') == 60.0 and "(Współwłaściciel)" not in monthly_permit.get('description', ''):
                            print(f"   ✅ Monthly permit correctly not discounted: {monthly_permit.get('price')} PLN without owner suffix")
                        else:
                            print(f"   ❌ Monthly permit incorrect: price={monthly_permit.get('price')}, desc={monthly_permit.get('description')}")
                            return False, response
                    
                    return True, response
                else:
                    print(f"   ❌ Expected 3 permits, got {len(permits) if permits else 0}")
                    return False, response
            else:
                print(f"   ❌ Incorrect total price: expected {expected_price}, got {actual_price}")
                return False, response
        
        return success, response

def main():
    print("🏠 Starting Owner Discount System Tests")
    print("=" * 60)
    print("Testing discount code: WLASCICIELWIELISZEW")
    print("Expected: Yearly permit 300 PLN → 50 PLN (250 PLN savings)")
    print("=" * 60)
    
    tester = OwnerDiscountTester()
    
    # Setup test client first
    success, _ = tester.setup_client()
    if not success:
        print("❌ Failed to setup test client. Aborting tests.")
        return 1
    
    # Run owner discount tests
    tests = [
        tester.test_purchase_yearly_without_owner_code,
        tester.test_purchase_yearly_with_owner_code,
        tester.test_purchase_yearly_with_wrong_owner_code,
        tester.test_purchase_daily_with_owner_code,
        tester.test_purchase_monthly_with_owner_code,
        tester.test_purchase_mixed_permits_with_owner_code,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 OWNER DISCOUNT SYSTEM TEST RESULTS")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All owner discount tests passed! System working correctly.")
        print("✅ Owner code 'WLASCICIELWIELISZEW' provides 250 PLN discount on yearly permits")
        return 0
    else:
        print("⚠️  Some owner discount tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())