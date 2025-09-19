#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "ETAP 2: IMPLEMENTACJA API PRO SYSTEM - implementacja endpointów API dla nowego systemu Tickets z wykorzystaniem zdefiniowanych modeli Pro (Waters, Tariffs, Tickets, Payments, Inspections, Inspectors) oraz funkcji ShortCode i JWT"

backend:
  - task: "ETAP 2: Pro Waters API"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Need to implement GET /api/pro/waters and GET /api/pro/waters/{water_id}/tariffs endpoints"
        - working: "NA"
          agent: "main"
          comment: "✅ IMPLEMENTED: Added GET /api/pro/waters and GET /api/pro/waters/{water_id}/tariffs endpoints. Returns active waters and their tariffs with price conversion from grosze to PLN."
        - working: true
          agent: "testing"
          comment: "✅ PRO WATERS API VERIFIED: GET /api/pro/waters returns 1 water (Jezioro Wieliszew) with correct location and description. GET /api/pro/waters/{water_id}/tariffs returns 3 Pro tariffs: Pro Dzienny (20 PLN/2000 grosze/24h), Pro Miesięczny (60 PLN/6000 grosze/720h), Pro Roczny (300 PLN/30000 grosze/8760h). Price conversion from grosze to PLN working correctly. All expected data from ETAP 1 properly accessible via Pro API."
          
  - task: "ETAP 2: Pro Purchase API"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 1
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Need to implement POST /api/pro/tickets/purchase and GET /api/pro/tickets/my-tickets endpoints with ShortCode and JWT QR generation"
        - working: "NA"
          agent: "main"
          comment: "✅ IMPLEMENTED: Added POST /api/pro/tickets/purchase (creates Payment + P24 redirect) and GET /api/pro/tickets/my-tickets endpoints. Integrated with existing Przelewy24 flow, generates ShortCode and JWT QR tokens."
        - working: "NA"
          agent: "main"
          comment: "🔧 FIXED P24 FALLBACK: Added P24 configuration check and mock payment fallback similar to legacy system. Fixed critical error 'invalid literal for int() with base 10: YOUR_MERCHANT_ID' by implementing proper P24 validation before attempting int conversion."
        - working: false
          agent: "testing"
          comment: "❌ PRO PURCHASE API CRITICAL ISSUE: POST /api/pro/tickets/purchase fails with 500 error 'invalid literal for int() with base 10: YOUR_MERCHANT_ID'. Pro system lacks fallback mechanism for unconfigured P24 (unlike legacy system). GET /api/pro/tickets/my-tickets works correctly (returns empty list as expected). Authorization working correctly (403 for unauthorized, 400 for missing consents, 404 for invalid water/tariff)."
        - working: true
          agent: "testing"
          comment: "✅ PRO PURCHASE API FIXED! POST /api/pro/tickets/purchase now works without P24 errors. Mock payment fallback successfully implemented - creates Pro ticket automatically in dev mode with ShortCode (e.g., FJQE4MEN) and JWT token. GET /api/pro/tickets/my-tickets returns created tickets correctly. All authorization checks working: 403 for unauthorized, 400 for missing consents, 404 for invalid water/tariff. Message confirms dev mode: 'Pro bilet zakupiony pomyślnie! Pro Dzienny - Jezioro Wieliszew (Tryb deweloperski - brak P24)'. Critical P24 fallback mechanism now matches legacy system behavior."
          
  - task: "ETAP 2: Pro Verification API"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Need to implement POST /api/pro/tickets/verify-qr, POST /api/pro/tickets/verify-shortcode and GET /api/pro/inspections/history endpoints"
        - working: "NA"
          agent: "main"
          comment: "✅ IMPLEMENTED: Added POST /api/pro/tickets/verify-qr (JWT verification), POST /api/pro/tickets/verify-shortcode (ShortCode validation), GET /api/pro/inspections/history endpoints. Full verification system with inspection logging."
        - working: true
          agent: "testing"
          comment: "✅ PRO VERIFICATION API VERIFIED: All endpoints properly implemented with controller role authorization. POST /api/pro/tickets/verify-qr correctly rejects invalid JWT tokens with proper error messages. POST /api/pro/tickets/verify-shortcode validates ShortCode format and rejects invalid codes. GET /api/pro/inspections/history returns empty list (expected for ETAP 2). Authorization working: 403 for non-controllers, proper error handling. Minor: Response format uses 'success: false' instead of 'valid: false' but functionality correct."

  - task: "ETAP 2: Pro Payment Integration"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Need to integrate Pro system with existing Przelewy24 payment flow and webhook handling"
        - working: "NA"
          agent: "main"
          comment: "✅ IMPLEMENTED: Added POST /api/pro/payment/webhook for Pro payments. Integrated with existing P24 flow, creates Ticket with ShortCode and JWT after successful payment via create_ticket_from_payment() helper function."
        - working: true
          agent: "testing"
          comment: "✅ PRO PAYMENT INTEGRATION VERIFIED: POST /api/pro/payment/webhook endpoint implemented and responding correctly. Webhook properly handles invalid signatures and missing payments with appropriate error responses. Integration with P24 flow structure in place. Minor: Webhook returns 'Payment not found' for test data (expected behavior)."

  - task: "ETAP 1: Pro Models Implementation"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "All Pro models defined: Water, Tariff, Payment, Ticket, Inspector, Inspection. Database indexes created. Default water and tariffs initialization implemented."
        - working: true
          agent: "testing"
          comment: "✅ ETAP 1 VERIFIED: All Pro models successfully implemented. Waters collection: 1 document (Jezioro Wieliszew). Tariffs collection: 3 documents (Pro Dzienny 20PLN, Pro Miesięczny 60PLN, Pro Roczny 300PLN). Default water and tariffs properly initialized. Backend startup successful with Pro system message. Legacy FishingPermit system working in parallel (26 permits, 22 orders). API tests: 36/39 passed (92.3% success rate). Minor: Some Pro collections (payments, tickets, inspections, inspectors) not yet created as expected for ETAP 1 - they will be created when first used."
          
  - task: "Database Indexes for Pro System"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Created indexes for all Pro collections: waters, tariffs, payments, tickets, inspections, inspectors. Indexes are created on startup."
        - working: true
          agent: "testing"
          comment: "✅ DATABASE INDEXES VERIFIED: Core indexes successfully created - users.email (unique), fishing_permits.customer_id+status, waters and tariffs collections ready. Index creation function working properly. Minor: Some Pro collection indexes not yet visible as collections don't exist until first document inserted (expected for ETAP 1). ensure_admin_user(), ensure_default_water_and_tariffs(), create_database_indexes() all executing successfully on startup."

frontend:
  - task: "Legacy System Compatibility"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Frontend should still work with existing FishingPermit system while Pro system is being developed in parallel."
        - working: true
          agent: "testing"
          comment: "✅ LEGACY COMPATIBILITY VERIFIED: Backend API tests confirm legacy FishingPermit system fully operational. All legacy endpoints working: /api/permits/types, /api/permits/purchase, /api/permits/my-permits, /api/permits/verify, /api/permits/verify-by-order. Legacy collections active: fishing_permits (26 docs), permit_orders (22 docs), verification_logs (20 docs). Frontend can continue using existing endpoints while Pro system develops."
        - working: true
          agent: "testing"
          comment: "✅ COMPREHENSIVE FRONTEND TESTING COMPLETED: All major functionality verified after ETAP 1 implementation. Homepage loads correctly with proper branding (Pozwolenia na Połów Ryb, Jezioro Wieliszew). User registration/login working for both clients and controllers. Dashboard displays all permit types (20 PLN dzienny, 60 PLN miesięczny, 300 PLN roczny). Custom checkboxes and permit selection functional. Owner code WLASCICIELWIELISZEW discount system working. Regulations and RODO acceptance modals operational. Purchase process generates QR codes successfully. EcoFishing Challenge unlocked with photo upload (ETAP 1). My Permits section displays QR codes. Controller panel with QR/Order verification methods working. Mobile responsiveness confirmed. API connectivity stable. Legacy system maintains full compatibility while Pro models run in parallel."

  - task: "Hamburger Menu Fix in QR Code Section"
    implemented: true
    working: "NA"
    file: "App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Fixed hamburger menu accessibility in QR code section. Changed condition from hasActivePermits to hasActivePermits || myPermits.length > 0. Added additional hamburger menu button in top-right corner of QR section (.bg-gray-50 .absolute button). Should improve UX by making menu more accessible than just bottom button."

  - task: "Frontend User Registration and Authentication"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "✅ USER AUTHENTICATION VERIFIED: Registration form working for both regular users and controllers. Login/logout functionality operational. User session persistence confirmed. Controller code JEZIOROWIELISZEW properly creates controller accounts with Panel Kontrolera access."

  - task: "Permit System and Purchase Flow"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "✅ PERMIT SYSTEM FULLY FUNCTIONAL: All permit types loaded correctly (dzienny 20 PLN, miesięczny 60 PLN, roczny 300 PLN). Custom checkbox selection working. Owner code WLASCICIELWIELISZEW applies discount for yearly permits. Regulations and RODO acceptance required before purchase. Purchase process generates QR codes and order IDs. Success page displays properly with permit details."

  - task: "Controller Verification System"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "✅ CONTROLLER SYSTEM OPERATIONAL: Controller registration with JEZIOROWIELISZEW code creates proper controller accounts. Panel Kontrolera provides both QR scanning and Order ID verification methods. QR scanner interface available with camera access. Manual QR data input functional. Order ID verification form working. Historia kontroli tab accessible for verification history."

  - task: "EcoFishing Challenge - Photo Upload (ETAP 1)"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "✅ ECOFISHING CHALLENGE ETAP 1 VERIFIED: Photo upload functionality unlocked after permit purchase. 'Moje połowy' tab becomes available. File input for fish photos present. Upload button functional. ETAP 1 description properly displayed (Podstawowy upload, czeka na weryfikację admina, kolejne etapy: AI, punkty, rankingi). Feature unlock notification working with menu navigation."

  - task: "Mobile Responsiveness and UI"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "✅ MOBILE RESPONSIVENESS CONFIRMED: Application adapts to mobile viewport (390x844). Touch-friendly form inputs. Hamburger menu available for users with active permits. Mobile layout maintains functionality. Desktop view shows proper tab grid layout. Responsive design working across different screen sizes."

  - task: "ETAP 2: Frontend Regression Testing"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Need to test frontend after ETAP 2 Pro API implementation to ensure legacy system compatibility and no conflicts with new Pro endpoints"
        - working: true
          agent: "testing"
          comment: "✅ ETAP 2 FRONTEND REGRESSION TESTING COMPLETED: Comprehensive testing confirms legacy system works perfectly after Pro API implementation. Homepage loads correctly with proper branding. User/controller registration and authentication fully functional. Legacy permit system (20/60/300 PLN) working without issues. Complete purchase flow with QR code generation successful. Owner code WLASCICIELWIELISZEW discount system operational. Regulations/RODO acceptance working. Controller verification panel (QR/Order ID) functional. EcoFishing Challenge (ETAP 1) unlocks properly after permit purchase with photo upload capability. Mobile responsiveness maintained with hamburger menu. CRITICAL: Frontend makes 0 Pro API calls (as expected) - only uses legacy endpoints. No conflicts between legacy and Pro API systems. No console errors detected. API connectivity stable. CONCLUSION: Legacy system maintains 100% compatibility after ETAP 2 Pro API backend changes. Frontend ready for future Pro system integration."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Hamburger Menu Fix in QR Code Section"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "ETAP 1 wydaje się być ukończony. Wszystkie modele Pro są zdefiniowane, indeksy utworzone, inicjalizacja danych zaimplementowana. Teraz potrzeba przetestować czy backend startuje poprawnie i czy wszystkie kolekcje są tworzone prawidłowo."
    - agent: "testing" 
      message: "✅ ETAP 1 TESTING COMPLETE: Backend uruchamia się poprawnie bez błędów. Wszystkie wymagane kolekcje MongoDB utworzone (waters: 1, tariffs: 3, plus legacy collections). Indeksy bazy danych prawidłowo utworzone. Domyślne dane (Jezioro Wieliszew i 3 taryfy Pro) zainicjalizowane. Stary system FishingPermit działa równolegle (26 permits, 22 orders). Podstawowe endpointy API odpowiadają poprawnie (92.3% success rate). Funkcje startup: ensure_admin_user(), ensure_default_water_and_tariffs(), create_database_indexes() działają bez błędów. ETAP 1 zakończony pomyślnie - modele i baza danych prawidłowo skonfigurowane."
    - agent: "main"
      message: "Backend ETAP 1 zakończony pomyślnie. Teraz testuję frontend żeby upewnić się, że kompatybilność wsteczna działa poprawnie i użytkownicy mogą nadal korzystać z aplikacji podczas gdy nowe modele Pro są gotowe w tle."
    - agent: "testing"
      message: "🎣 FRONTEND TESTING ETAP 1 ZAKOŃCZONY POMYŚLNIE! Przeprowadziłem kompleksowe testowanie wszystkich funkcjonalności aplikacji wędkarskiej po implementacji ETAP 1. Wszystkie główne funkcje działają poprawnie: rejestracja/logowanie użytkowników i kontrolerów, system pozwoleń (20/60/300 PLN), kod właściciela WLASCICIELWIELISZEW, akceptacja regulaminu/RODO, proces zakupu z QR kodami, panel kontrolera z weryfikacją, EcoFishing Challenge z uploadem zdjęć (ETAP 1), responsywność mobile. Legacy system FishingPermit działa równolegle z nowymi modelami Pro. API connectivity stabilne. Aplikacja gotowa do użytku przez wędkarzy i kontrolerów. Brak krytycznych błędów - wszystkie testy przeszły pomyślnie!"
    - agent: "main"
      message: "🚀 ETAP 2: IMPLEMENTACJA API PRO SYSTEM - Dodałem wszystkie kluczowe endpointy Pro API: Waters API (lista łowisk, taryfy), Purchase API (zakup biletów z ShortCode i JWT), Verification API (weryfikacja QR i ShortCode z logowaniem kontroli), Payment Integration (webhook P24 dla Pro). Backend uruchamia się poprawnie. Gotowy do testowania API Pro systemu."
    - agent: "testing"
      message: "🏆 ETAP 2 PRO API TESTING COMPLETED: Przeprowadziłem kompleksowe testowanie wszystkich nowych endpointów Pro API. WYNIKI: ✅ Pro Waters API (100% working) - zwraca Jezioro Wieliszew i 3 taryfy Pro (20/60/300 PLN). ✅ Pro Verification API (100% working) - weryfikacja JWT/ShortCode z autoryzacją kontrolerów. ✅ Pro Payment Integration (100% working) - webhook P24 zaimplementowany. ❌ CRITICAL ISSUE: Pro Purchase API fails - brak fallback mechanizmu dla niekonfigurowanego P24 (błąd: invalid literal for int() 'YOUR_MERCHANT_ID'). Legacy system ma fallback, Pro system nie. Ogólny wynik: 84.2% success rate (48/57 testów). Główny problem: Pro ticket purchase wymaga naprawy P24 fallback."
    - agent: "testing"
      message: "🎯 ETAP 2 PRO PURCHASE API RETESTING COMPLETED: Po naprawie fallback mechanizmu przez main agenta, przeprowadziłem ponowne testowanie Pro Purchase API. WYNIKI: ✅ POST /api/pro/tickets/purchase działa bez błędów P24! Mock payment fallback tworzy Pro ticket automatycznie w trybie dev z ShortCode (np. FJQE4MEN) i JWT token. ✅ GET /api/pro/tickets/my-tickets zwraca utworzone bilety Pro poprawnie. ✅ Wszystkie sprawdzenia autoryzacji działają (403/400/404). ✅ Komunikat potwierdza tryb dev: 'Pro bilet zakupiony pomyślnie! Pro Dzienny - Jezioro Wieliszew (Tryb deweloperski - brak P24)'. KRYTYCZNY PROBLEM ROZWIĄZANY - Pro Purchase API teraz działa identycznie jak legacy system z fallback mechanizmem."
    - agent: "main"
      message: "📋 PLAN: Robię oba - najpierw testuję frontend z nowym Pro API z ETAP 2, a potem przejdę do ETAP 3. Frontend powinien nadal działać z legacy systemem, ale warto sprawdzić czy nie ma konfliktów z nowymi endpointami Pro API."
    - agent: "testing"
      message: "🎯 ETAP 2 FRONTEND REGRESSION TESTING COMPLETED: Przeprowadziłem kompleksowe testowanie regresji frontend po implementacji ETAP 2 Pro API. WYNIKI: ✅ Homepage ładuje się poprawnie z właściwym brandingiem (Pozwolenia na Połów Ryb, Jezioro Wieliszew). ✅ Rejestracja użytkowników i kontrolerów działa bez problemów. ✅ System pozwoleń legacy (20/60/300 PLN) w pełni funkcjonalny. ✅ Kompletny flow zakupu pozwoleń z QR kodami działa poprawnie. ✅ Kod właściciela WLASCICIELWIELISZEW i akceptacja regulaminu/RODO działają. ✅ Panel kontrolera z weryfikacją QR/Order ID funkcjonalny. ✅ EcoFishing Challenge (ETAP 1) z uploadem zdjęć odblokowany po zakupie. ✅ Mobile responsiveness zachowana z hamburger menu. ✅ KLUCZOWE: Brak wywołań Pro API w frontend (0 calls) - frontend używa tylko legacy endpointów jak oczekiwano. ✅ Brak konfliktów między legacy i Pro API. ✅ Brak błędów w konsoli. PODSUMOWANIE: Legacy system działa w 100% bez zmian po dodaniu Pro API endpointów. Frontend gotowy do przyszłej integracji z Pro systemem."
    - agent: "main"
      message: "🔧 HAMBURGER MENU FIX: Naprawiłem dostępność hamburger menu w sekcji QR kodu. Zmieniłem warunek z hasActivePermits na hasActivePermits || myPermits.length > 0. Dodałem dodatkowy przycisk hamburger menu w prawym górnym rogu sekcji QR (.bg-gray-50 .absolute button). Powinno to poprawić UX - użytkownik ma łatwiejszy dostęp do menu niż tylko przycisk na dole."
    - agent: "testing"
      message: "🎯 ROZPOCZYNAM TESTOWANIE HAMBURGER MENU FIX: Testuję naprawkę hamburger menu w sekcji QR kodu. Plan testów: 1) Rejestracja/logowanie użytkownika, 2) Zakup pozwolenia (dowolny typ), 3) Sprawdzenie sekcji QR - czy hamburger menu w prawym górnym rogu, 4) Test funkcjonalności hamburger menu, 5) Porównanie UX. Test na mobile viewport (390x844)."