import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Checkbox } from './components/ui/checkbox';
import { Badge } from './components/ui/badge';
import { AlertCircle, Fish, CheckCircle, QrCode, Download } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [permitTypes, setPermitTypes] = useState([]);
  const [selectedPermits, setSelectedPermits] = useState([]);
  const [customerData, setCustomerData] = useState({
    full_name: '',
    email: '',
    phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [purchaseResult, setPurchaseResult] = useState(null);
  const [currentView, setCurrentView] = useState('purchase'); // 'purchase', 'success', 'verify'
  const [verificationResult, setVerificationResult] = useState(null);
  const [qrData, setQrData] = useState('');

  useEffect(() => {
    fetchPermitTypes();
  }, []);

  const fetchPermitTypes = async () => {
    try {
      const response = await axios.get(`${API}/permits/types`);
      setPermitTypes(response.data.permit_types);
    } catch (error) {
      console.error('Error fetching permit types:', error);
    }
  };

  const handlePermitSelection = (permitType, checked) => {
    if (checked) {
      setSelectedPermits(prev => [...prev, permitType]);
    } else {
      setSelectedPermits(prev => prev.filter(p => p !== permitType));
    }
  };

  const calculateTotal = () => {
    return selectedPermits.reduce((total, permitType) => {
      const permit = permitTypes.find(p => p.type === permitType);
      return total + (permit ? permit.price : 0);
    }, 0);
  };

  const handlePurchase = async (e) => {
    e.preventDefault();
    
    if (selectedPermits.length === 0) {
      alert('Proszę wybrać co najmniej jeden rodzaj pozwolenia');
      return;
    }

    if (!customerData.full_name || !customerData.email) {
      alert('Proszę wypełnić wszystkie wymagane pola');
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/permits/purchase`, {
        customer: customerData,
        permit_types: selectedPermits
      });

      if (response.data.success) {
        setPurchaseResult(response.data);
        setCurrentView('success');
      }
    } catch (error) {
      console.error('Purchase error:', error);
      alert('Błąd podczas zakupu. Spróbuj ponownie.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerification = async (e) => {
    e.preventDefault();
    
    if (!qrData.trim()) {
      alert('Proszę wprowadzić dane z kodu QR');
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/permits/verify`, {
        qr_data: qrData
      });

      setVerificationResult(response.data);
    } catch (error) {
      console.error('Verification error:', error);
      setVerificationResult({
        valid: false,
        message: 'Błąd podczas weryfikacji'
      });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setSelectedPermits([]);
    setCustomerData({ full_name: '', email: '', phone: '' });
    setPurchaseResult(null);
    setCurrentView('purchase');
    setVerificationResult(null);
    setQrData('');
  };

  if (currentView === 'success' && purchaseResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <Fish className="h-12 w-12 text-emerald-600 mx-auto mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Zakup Pomyślny!</h1>
              <p className="text-gray-600">Twoje pozwolenia na połów ryb zostały aktywowane</p>
            </div>

            <Card className="mb-6 border-emerald-200 shadow-lg">
              <CardHeader className="bg-emerald-50">
                <CardTitle className="flex items-center gap-2 text-emerald-800">
                  <CheckCircle className="h-5 w-5" />
                  Szczegóły zamówienia #{purchaseResult.order_id}
                </CardTitle>
                <CardDescription>
                  Łączna kwota: {purchaseResult.total_amount} PLN
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid gap-6">
                  {purchaseResult.permits.map((permit, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-white">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="font-semibold text-lg text-gray-900">
                            {permit.description}
                          </h3>
                          <p className="text-gray-600">
                            Ważne do: {new Date(permit.expiry_date).toLocaleDateString('pl-PL')}
                          </p>
                          <Badge className="mt-2 bg-emerald-100 text-emerald-800">
                            AKTYWNY
                          </Badge>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-emerald-600">{permit.price} PLN</p>
                        </div>
                      </div>
                      
                      {permit.qr_code && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                          <div className="flex items-center gap-2 mb-2">
                            <QrCode className="h-4 w-4" />
                            <span className="text-sm font-medium">Kod QR do weryfikacji</span>
                          </div>
                          <div className="flex justify-center">
                            <img 
                              src={permit.qr_code} 
                              alt="QR Code" 
                              className="border rounded"
                            />
                          </div>
                          <p className="text-xs text-gray-500 text-center mt-2">
                            Pokaż ten kod podczas kontroli
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                <div className="flex gap-4 mt-6">
                  <Button 
                    onClick={() => setCurrentView('verify')}
                    variant="outline"
                    className="flex-1"
                  >
                    <QrCode className="h-4 w-4 mr-2" />
                    Weryfikuj pozwolenie
                  </Button>
                  <Button 
                    onClick={resetForm}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                  >
                    Kup kolejne pozwolenie
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'verify') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-emerald-50 to-teal-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <QrCode className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Weryfikacja Pozwolenia</h1>
              <p className="text-gray-600">Wprowadź dane z kodu QR aby zweryfikować pozwolenie</p>
            </div>

            <Card className="shadow-lg">
              <CardContent className="p-6">
                <form onSubmit={handleVerification}>
                  <div className="mb-4">
                    <Label htmlFor="qr-data">Dane z kodu QR</Label>
                    <Input
                      id="qr-data"
                      value={qrData}
                      onChange={(e) => setQrData(e.target.value)}
                      placeholder="PERMIT:xxxxx:NAME:xxxxx:VERIFIED"
                      className="mt-1"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      Wpisz lub zeskanuj zawartość kodu QR
                    </p>
                  </div>

                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? 'Weryfikowanie...' : 'Weryfikuj pozwolenie'}
                  </Button>
                </form>

                {verificationResult && (
                  <div className={`mt-6 p-4 rounded-lg ${
                    verificationResult.valid ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      {verificationResult.valid ? (
                        <CheckCircle className="h-5 w-5 text-emerald-600" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className={`font-medium ${
                        verificationResult.valid ? 'text-emerald-800' : 'text-red-800'
                      }`}>
                        {verificationResult.valid ? 'Pozwolenie WAŻNE' : 'Pozwolenie NIEWAŻNE'}
                      </span>
                    </div>
                    
                    <p className={
                      verificationResult.valid ? 'text-emerald-700' : 'text-red-700'
                    }>
                      {verificationResult.message}
                    </p>

                    {verificationResult.valid && verificationResult.permit && (
                      <div className="mt-3 text-sm text-emerald-700">
                        <p><strong>Posiadacz:</strong> {verificationResult.permit.customer.full_name}</p>
                        <p><strong>Typ:</strong> {verificationResult.permit.description}</p>
                        <p><strong>Ważne do:</strong> {new Date(verificationResult.expiry_date).toLocaleDateString('pl-PL')}</p>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-4 mt-6">
                  <Button 
                    onClick={() => setCurrentView('purchase')}
                    variant="outline"
                    className="flex-1"
                  >
                    Kup pozwolenie
                  </Button>
                  <Button 
                    onClick={() => {
                      setVerificationResult(null);
                      setQrData('');
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    Wyczyść
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <Fish className="h-16 w-16 text-emerald-600 mx-auto mb-4" />
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Pozwolenia na Połów Ryb</h1>
            <p className="text-xl text-gray-600">Kup swoje pozwolenie online i otrzymaj natychmiastowy dostęp</p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left side - Permit selection */}
            <Card className="shadow-lg border-emerald-200">
              <CardHeader className="bg-emerald-50">
                <CardTitle className="text-emerald-800">Wybierz rodzaj pozwolenia</CardTitle>
                <CardDescription>Dostępne typy pozwoleń na połów ryb</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  {permitTypes.map((permit) => (
                    <div key={permit.type} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <Checkbox
                            id={permit.type}
                            checked={selectedPermits.includes(permit.type)}
                            onCheckedChange={(checked) => handlePermitSelection(permit.type, checked)}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <Label htmlFor={permit.type} className="text-base font-medium cursor-pointer">
                              {permit.name}
                            </Label>
                            <p className="text-sm text-gray-600 mt-1">{permit.description}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              Ważność: {permit.validity_days} {permit.validity_days === 1 ? 'dzień' : permit.validity_days < 5 ? 'dni' : 'dni'}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-emerald-600 text-lg">{permit.price} PLN</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {selectedPermits.length > 0 && (
                  <div className="mt-6 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-emerald-800">Łączna kwota:</span>
                      <span className="text-2xl font-bold text-emerald-600">{calculateTotal()} PLN</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Right side - Customer form */}
            <Card className="shadow-lg border-blue-200">
              <CardHeader className="bg-blue-50">
                <CardTitle className="text-blue-800">Dane osobowe</CardTitle>
                <CardDescription>Wypełnij dane do wystawienia pozwolenia</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <form onSubmit={handlePurchase} className="space-y-4">
                  <div>
                    <Label htmlFor="full_name">Imię i nazwisko *</Label>
                    <Input
                      id="full_name"
                      value={customerData.full_name}
                      onChange={(e) => setCustomerData(prev => ({ ...prev, full_name: e.target.value }))}
                      placeholder="Jan Kowalski"
                      required
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="email">Adres email *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={customerData.email}
                      onChange={(e) => setCustomerData(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="jan.kowalski@example.com"
                      required
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="phone">Numer telefonu</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={customerData.phone}
                      onChange={(e) => setCustomerData(prev => ({ ...prev, phone: e.target.value }))}
                      placeholder="+48 123 456 789"
                      className="mt-1"
                    />
                  </div>

                  <Button 
                    type="submit" 
                    disabled={loading || selectedPermits.length === 0}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-lg py-3"
                  >
                    {loading ? 'Przetwarzanie...' : `Kup pozwolenie (${calculateTotal()} PLN)`}
                  </Button>
                </form>

                <div className="mt-6 text-center">
                  <Button 
                    onClick={() => setCurrentView('verify')}
                    variant="outline"
                    className="w-full"
                  >
                    <QrCode className="h-4 w-4 mr-2" />
                    Weryfikuj istniejące pozwolenie
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-8 text-center text-sm text-gray-500">
            <p>Pozwolenia są wydawane natychmiastowo po zakupie. Kod QR służy do weryfikacji podczas kontroli.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;