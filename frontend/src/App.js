import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Checkbox } from './components/ui/checkbox';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from './components/ui/sheet';
import { AlertCircle, Fish, CheckCircle, QrCode, Download, User, Shield, Settings, LogOut, Camera, History, FileText, Info, Menu } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 > Date.now()) {
          // Token is valid, get user info
          fetchCurrentUser();
        } else {
          // Token expired
          logout();
        }
      } catch (error) {
        logout();
      }
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (email, fullName, password, controllerCode = '') => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        full_name: fullName,
        password,
        controller_code: controllerCode || undefined
      });
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true, message: response.data.message };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setLoading(false);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Components
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    fullName: '',
    password: '',
    controllerCode: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    let result;
    if (isLogin) {
      result = await login(formData.email, formData.password);
    } else {
      result = await register(formData.email, formData.fullName, formData.password, formData.controllerCode);
    }

    if (!result.success) {
      setMessage(result.message);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50 flex items-center justify-center">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <Fish className="h-12 w-12 text-emerald-600 mx-auto mb-4" />
          <CardTitle className="text-2xl">Pozwolenia na Połów Ryb</CardTitle>
          <CardDescription>Jezioro Wieliszew</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={isLogin ? 'login' : 'register'} onValueChange={(val) => setIsLogin(val === 'login')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Logowanie</TabsTrigger>
              <TabsTrigger value="register">Rejestracja</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">Hasło</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-700">
                  {loading ? 'Logowanie...' : 'Zaloguj się'}
                </Button>
              </form>
            </TabsContent>
            
            <TabsContent value="register">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="fullName">Imię i nazwisko</Label>
                  <Input
                    id="fullName"
                    value={formData.fullName}
                    onChange={(e) => setFormData(prev => ({ ...prev, fullName: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">Hasło</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="controllerCode">Kod kontrolera (opcjonalnie)</Label>
                  <Input
                    id="controllerCode"
                    value={formData.controllerCode}
                    onChange={(e) => setFormData(prev => ({ ...prev, controllerCode: e.target.value }))}
                    placeholder="Wprowadź kod jeśli jesteś kontrolerem"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Pozostaw puste dla konta klienta
                  </p>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-700">
                  {loading ? 'Rejestracja...' : 'Zarejestruj się'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
          
          {message && (
            <div className={`mt-4 p-3 rounded-lg text-sm ${
              message.includes('successful') ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
            }`}>
              {message}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const ClientDashboard = () => {
  const { user, token, logout } = useAuth();
  const [permitTypes, setPermitTypes] = useState([]);
  const [selectedPermits, setSelectedPermits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [purchaseResult, setPurchaseResult] = useState(null);
  const [myPermits, setMyPermits] = useState([]);
  const [activeTab, setActiveTab] = useState('pro-buy');
  const [ownerCode, setOwnerCode] = useState('');
  const [regulationsAccepted, setRegulationsAccepted] = useState(false);
  const [dataProcessingAccepted, setDataProcessingAccepted] = useState(false);
  const [showRegulations, setShowRegulations] = useState(false);
  const [showDataAgreement, setShowDataAgreement] = useState(false);
  const [regulationsData, setRegulationsData] = useState(null);
  const [myCatches, setMyCatches] = useState([]);
  const [uploadingCatch, setUploadingCatch] = useState(false);
  const [catchImage, setCatchImage] = useState(null);
  const [hasActivePermits, setHasActivePermits] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Pro System State
  const [proWaters, setProWaters] = useState([]);
  const [proTariffs, setProTariffs] = useState([]);
  const [selectedProWater, setSelectedProWater] = useState(null);
  const [selectedProTariff, setSelectedProTariff] = useState(null);
  const [myProTickets, setMyProTickets] = useState([]);
  const [proRegulationsAccepted, setProRegulationsAccepted] = useState(false);
  const [proDataProcessingAccepted, setProDataProcessingAccepted] = useState(false);
  const [purchasingProTicket, setPurchasingProTicket] = useState(false);

  useEffect(() => {
    fetchPermitTypes();
    fetchRegulations();
    if (activeTab === 'history') {
      fetchMyPermits();
    }
    if (activeTab === 'catches') {
      fetchMyCatches();
    }
    if (activeTab === 'pro-buy') {
      fetchProWaters();
    }
    if (activeTab === 'pro-history') {
      fetchMyProTickets();
    }
  }, [activeTab]);

  const fetchMyCatches = async () => {
    try {
      const response = await axios.get(`${API}/fishing/my-catches`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyCatches(response.data.catches);
    } catch (error) {
      console.error('Error fetching catches:', error);
    }
  };

  const handleCatchUpload = async (e) => {
    e.preventDefault();
    
    if (!catchImage) {
      alert('Proszę wybrać zdjęcie ryby');
      return;
    }

    setUploadingCatch(true);

    try {
      const formData = new FormData();
      formData.append('image', catchImage);
      formData.append('notes', 'Połów z aplikacji mobilnej');

      const response = await axios.post(`${API}/fishing/upload-catch`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        alert('Zdjęcie połowu zostało przesłane!');
        setCatchImage(null);
        fetchMyCatches(); // Refresh list
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Błąd podczas przesyłania zdjęcia');
    } finally {
      setUploadingCatch(false);
    }
  };

  const fetchRegulations = async () => {
    try {
      const response = await axios.get(`${API}/regulations`);
      setRegulationsData(response.data);
    } catch (error) {
      console.error('Error fetching regulations:', error);
    }
  };

  const fetchPermitTypes = async () => {
    try {
      const response = await axios.get(`${API}/permits/types`);
      setPermitTypes(response.data.permit_types);
    } catch (error) {
      console.error('Error fetching permit types:', error);
    }
  };

  const fetchMyPermits = async () => {
    try {
      const response = await axios.get(`${API}/permits/my-permits`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyPermits(response.data.permits);
      
      // Check if user has any active permits
      const activePermits = response.data.permits.filter(permit => {
        const expiryDate = new Date(permit.expiry_date);
        const now = new Date();
        return permit.status === 'active' && expiryDate > now;
      });
      
      setHasActivePermits(activePermits.length > 0);
    } catch (error) {
      console.error('Error fetching my permits:', error);
    }
  };

  // Pro System Functions
  const fetchProWaters = async () => {
    try {
      const response = await axios.get(`${API}/pro/waters`);
      if (response.data.success) {
        setProWaters(response.data.waters);
        // Automatically select first water (Jezioro Wieliszew)
        if (response.data.waters.length > 0) {
          const firstWater = response.data.waters[0];
          setSelectedProWater(firstWater);
          fetchProTariffs(firstWater.id);
        }
      }
    } catch (error) {
      console.error('Error fetching Pro waters:', error);
    }
  };

  const fetchProTariffs = async (waterId) => {
    try {
      const response = await axios.get(`${API}/pro/waters/${waterId}/tariffs`);
      if (response.data.success) {
        setProTariffs(response.data.tariffs);
      }
    } catch (error) {
      console.error('Error fetching Pro tariffs:', error);
    }
  };

  const fetchMyProTickets = async () => {
    try {
      const response = await axios.get(`${API}/pro/tickets/my-tickets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setMyProTickets(response.data.tickets);
      }
    } catch (error) {
      console.error('Error fetching Pro tickets:', error);
    }
  };

  const handleProTariffSelection = (tariff) => {
    setSelectedProTariff(tariff);
  };

  const purchaseProTicket = async () => {
    if (!selectedProWater || !selectedProTariff) {
      alert('Proszę wybrać łowisko i taryfę');
      return;
    }

    if (!proRegulationsAccepted || !proDataProcessingAccepted) {
      alert('Proszę zaakceptować regulamin i zgodę na przetwarzanie danych');
      return;
    }

    setPurchasingProTicket(true);

    try {
      const response = await axios.post(`${API}/pro/tickets/purchase`, {
        water_id: selectedProWater.id,
        tariff_id: selectedProTariff.id,
        regulations_accepted: proRegulationsAccepted,
        data_processing_accepted: proDataProcessingAccepted
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        if (response.data.requires_payment) {
          // Redirect to P24 payment
          window.location.href = response.data.payment_url;
        } else {
          // Mock payment success - show success message and refresh tickets
          alert(response.data.message);
          setActiveTab('pro-history');
          fetchMyProTickets();
          
          // Reset form
          setSelectedProTariff(null);
          setProRegulationsAccepted(false);
          setProDataProcessingAccepted(false);
        }
      }
    } catch (error) {
      console.error('Error purchasing Pro ticket:', error);
      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert('Błąd podczas zakupu biletu Pro');
      }
    } finally {
      setPurchasingProTicket(false);
    }
  };

  const handlePermitSelection = (permitType, checked) => {
    console.log('Permit selection:', permitType, checked); // Debug log
    if (checked) {
      setSelectedPermits(prev => [...prev, permitType]);
    } else {
      setSelectedPermits(prev => prev.filter(p => p !== permitType));
    }
  };

  const calculateTotal = () => {
    const isOwner = ownerCode.trim() === 'WLASCICIELWIELISZEW';
    
    return selectedPermits.reduce((total, permitType) => {
      const permit = permitTypes.find(p => p.type === permitType);
      if (!permit) return total;
      
      // Apply owner discount for yearly permit
      if (isOwner && permitType === 'yearly') {
        return total + 50; // Special owner price
      }
      
      return total + permit.price;
    }, 0);
  };

  const handlePurchase = async (e) => {
    e.preventDefault();
    
    if (selectedPermits.length === 0) {
      alert('Proszę wybrać co najmniej jeden rodzaj pozwolenia');
      return;
    }

    setLoading(true);
    
    if (!regulationsAccepted) {
      alert('Musisz zaakceptować regulamin łowiska');
      return;
    }

    if (!dataProcessingAccepted) {
      alert('Musisz zaakceptować zgodę na przetwarzanie danych');
      return;
    }

    try {
      const response = await axios.post(`${API}/permits/purchase`, {
        permit_types: selectedPermits,
        owner_code: ownerCode.trim() || undefined,
        regulations_accepted: regulationsAccepted,
        data_processing_accepted: dataProcessingAccepted
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        if (response.data.requires_payment && response.data.payment_url) {
          // Redirect to payment
          window.location.href = response.data.payment_url;
        } else {
          // Mock payment success or immediate success
          setPurchaseResult(response.data);
          setActiveTab('success');
          setSelectedPermits([]);
          setOwnerCode('');
          setRegulationsAccepted(false);
          setDataProcessingAccepted(false);
          // Refresh permits to unlock catches tab
          fetchMyPermits();
        }
      }
    } catch (error) {
      console.error('Purchase error:', error);
      alert('Błąd podczas zakupu. Spróbuj ponownie.');
    } finally {
      setLoading(false);
    }
  };

  if (activeTab === 'success' && purchaseResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Zakup Pomyślny!</h1>
                <p className="text-gray-600">Twoje pozwolenia zostały aktywowane</p>
              </div>
              <Button onClick={() => setActiveTab('buy')} variant="outline">
                Kup kolejne
              </Button>
            </div>

            <Card className="mb-6 border-emerald-200 shadow-lg">
              <CardHeader className="bg-emerald-50">
                <CardTitle className="flex items-center gap-2 text-emerald-800">
                  <CheckCircle className="h-5 w-5" />
                  Zamówienie #{purchaseResult.order_id}
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
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg relative">
                          {/* Hamburger Menu w prawym górnym rogu QR sekcji */}
                          <div className="absolute top-2 right-2 md:hidden">
                            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                              <SheetTrigger asChild>
                                <Button variant="outline" size="sm" className="w-8 h-8 p-0">
                                  <Menu className="h-4 w-4" />
                                </Button>
                              </SheetTrigger>
                              <SheetContent side="left" className="w-72">
                                <SheetHeader>
                                  <SheetTitle className="flex items-center gap-2">
                                    <Fish className="h-5 w-5 text-emerald-600" />
                                    Jezioro Wieliszew
                                  </SheetTitle>
                                  <SheetDescription>
                                    Panel wędkarza - {user?.full_name}
                                  </SheetDescription>
                                </SheetHeader>
                                
                                <div className="mt-8 space-y-2">
                                  <Button
                                    variant={activeTab === 'pro-buy' ? 'default' : 'ghost'}
                                    className="w-full justify-start text-left"
                                    onClick={() => {
                                      setActiveTab('pro-buy');
                                      setMobileMenuOpen(false);
                                    }}
                                  >
                                    <Shield className="h-4 w-4 mr-3" />
                                    Bilety
                                  </Button>
                                  
                                  <Button
                                    variant={activeTab === 'pro-history' ? 'default' : 'ghost'}
                                    className="w-full justify-start text-left"
                                    onClick={() => {
                                      setActiveTab('pro-history');
                                      setMobileMenuOpen(false);
                                    }}
                                  >
                                    <QrCode className="h-4 w-4 mr-3" />
                                    Moje Bilety
                                  </Button>
                                  
                                  <Button
                                    variant={activeTab === 'catches' ? 'default' : 'ghost'}
                                    className="w-full justify-start text-left"
                                    onClick={() => {
                                      setActiveTab('catches');
                                      setMobileMenuOpen(false);
                                    }}
                                  >
                                    <Camera className="h-4 w-4 mr-3" />
                                    Moje połowy
                                  </Button>
                                  
                                  <div className="border-t pt-4 mt-6">
                                    <Button
                                      variant="ghost"
                                      className="w-full justify-start text-left text-red-600"
                                      onClick={() => {
                                        logout();
                                        setMobileMenuOpen(false);
                                      }}
                                    >
                                      <LogOut className="h-4 w-4 mr-3" />
                                      Wyloguj się
                                    </Button>
                                  </div>
                                </div>
                              </SheetContent>
                            </Sheet>
                          </div>
                          
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
              </CardContent>
            </Card>
            
            <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-emerald-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Camera className="h-5 w-5 text-blue-600" />
                    <span className="font-medium text-blue-800">🎉 Nowe funkcje odblokowane!</span>
                  </div>
                  <div className="text-sm text-blue-700 mb-3">
                    <p className="mb-2">Odkryj nowe możliwości w menu aplikacji:</p>
                    <div className="space-y-1">
                      <div>🎣 Zawody wędkarskie catch & release</div>
                      <div>🏆 Miesięczne rankingi z nagrodami</div>
                      <div>📸 Upload zdjęć ryb (ETAP 1)</div>
                    </div>
                    <p className="text-xs text-blue-600 mt-2 md:hidden">
                      💡 Sprawdź menu ☰ w lewym górnym rogu
                    </p>
                  </div>
                  <Button 
                    onClick={() => {
                      setActiveTab('catches');
                      // On mobile, highlight hamburger menu to show new options
                      if (window.innerWidth <= 768) {
                        setTimeout(() => {
                          const hamburgerButton = document.querySelector('button[data-state]');
                          if (hamburgerButton) {
                            hamburgerButton.classList.add('hamburger-tutorial-highlight');
                            // Remove highlight after 6 seconds
                            setTimeout(() => {
                              hamburgerButton.classList.remove('hamburger-tutorial-highlight');
                            }, 6000);
                          }
                        }, 500);
                      }
                    }}
                    className="bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white"
                    size="sm"
                  >
                    <Menu className="h-4 w-4 mr-2" />
                    Przejdź do menu
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50">
      <div className="container mx-auto px-4 py-2 md:py-8">
        <div className="max-w-6xl mx-auto">
          {/* Mobile Header with Hamburger Menu */}
          <div className="flex justify-between items-center mb-6 md:mb-8">
            <div className="flex items-center gap-4">
              {(hasActivePermits || myPermits.length > 0 || myProTickets.length > 0) && (
                <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                  <SheetTrigger asChild>
                    <Button variant="outline" size="sm" className="md:hidden">
                      <Menu className="h-5 w-5" />
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="left" className="w-72">
                    <SheetHeader>
                      <SheetTitle className="flex items-center gap-2">
                        <Fish className="h-5 w-5 text-emerald-600" />
                        Jezioro Wieliszew
                      </SheetTitle>
                      <SheetDescription>
                        Panel wędkarza - {user?.full_name}
                      </SheetDescription>
                    </SheetHeader>
                    
                    <div className="mt-8 space-y-2">
                      <Button
                        variant={activeTab === 'pro-buy' ? 'default' : 'ghost'}
                        className="w-full justify-start text-left"
                        onClick={() => {
                          setActiveTab('pro-buy');
                          setMobileMenuOpen(false);
                        }}
                      >
                        <Shield className="h-4 w-4 mr-3" />
                        Bilety
                      </Button>
                      
                      <Button
                        variant={activeTab === 'pro-history' ? 'default' : 'ghost'}
                        className="w-full justify-start text-left"
                        onClick={() => {
                          setActiveTab('pro-history');
                          setMobileMenuOpen(false);
                        }}
                      >
                        <QrCode className="h-4 w-4 mr-3" />
                        Moje Bilety
                      </Button>
                      
                      <Button
                        variant={activeTab === 'catches' ? 'default' : 'ghost'}
                        className="w-full justify-start text-left"
                        onClick={() => {
                          setActiveTab('catches');
                          setMobileMenuOpen(false);
                        }}
                      >
                        <Camera className="h-4 w-4 mr-3" />
                        Moje połowy
                      </Button>
                      
                      <div className="border-t pt-4 mt-6">
                        <Button
                          variant="ghost"
                          className="w-full justify-start text-left text-red-600"
                          onClick={() => {
                            logout();
                            setMobileMenuOpen(false);
                          }}
                        >
                          <LogOut className="h-4 w-4 mr-3" />
                          Wyloguj się
                        </Button>
                      </div>
                    </div>
                  </SheetContent>
                </Sheet>
              )}
              
              <div>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Panel Wędkarza</h1>
                <p className="text-gray-600 text-sm md:text-base">Witaj, {user?.full_name}</p>
              </div>
            </div>
            
            {/* Desktop logout button */}
            <Button onClick={logout} variant="outline" className="hidden md:flex items-center gap-2">
              <LogOut className="h-4 w-4" />
              Wyloguj
            </Button>
            
            {/* Mobile logout button (when no permits) */}
            {!hasActivePermits && (
              <Button onClick={logout} variant="outline" size="sm" className="md:hidden">
                <LogOut className="h-4 w-4" />
              </Button>
            )}
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            {/* Desktop Tabs */}
            <TabsList className="grid w-full grid-cols-3 mb-8">
              <TabsTrigger value="pro-buy" className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Bilety
              </TabsTrigger>
              <TabsTrigger value="pro-history" className="flex items-center gap-2">
                <QrCode className="h-4 w-4" />
                Moje Bilety
              </TabsTrigger>
              {(hasActivePermits || myPermits.length > 0 || myProTickets.length > 0) && (
                <TabsTrigger value="catches" className="flex items-center gap-2">
                  <Camera className="h-4 w-4" />
                  Moje połowy
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="buy">
              <div className="grid lg:grid-cols-2 gap-8">
                <Card className="shadow-lg border-emerald-200">
                  <CardHeader className="bg-emerald-50">
                    <CardTitle className="text-emerald-800">Wybierz pozwolenia</CardTitle>
                    <CardDescription>Dostępne typy pozwoleń na połów ryb</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      {permitTypes.map((permit) => (
                        <div 
                          key={permit.type} 
                          className={`border rounded-lg p-4 transition-colors cursor-pointer touch-manipulation ${
                            selectedPermits.includes(permit.type) 
                              ? 'bg-emerald-50 border-emerald-300' 
                              : 'hover:bg-gray-50 border-gray-200'
                          }`}
                          onClick={() => handlePermitSelection(permit.type, !selectedPermits.includes(permit.type))}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-4">
                              {/* Mobile-friendly checkbox */}
                              <div className="flex items-center mt-1">
                                <div className={`
                                  w-6 h-6 rounded border-2 flex items-center justify-center cursor-pointer touch-manipulation
                                  ${selectedPermits.includes(permit.type) 
                                    ? 'bg-emerald-600 border-emerald-600' 
                                    : 'border-gray-300 bg-white'
                                  }
                                `}>
                                  {selectedPermits.includes(permit.type) && (
                                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                  )}
                                </div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                  {permit.name}
                                </h3>
                                <p className="text-sm text-gray-600 mb-1">{permit.description}</p>
                                <p className="text-xs text-gray-500">
                                  Ważność: {permit.validity_days} {permit.validity_days === 1 ? 'dzień' : permit.validity_days < 5 ? 'dni' : 'dni'}
                                </p>
                              </div>
                            </div>
                            <div className="text-right ml-4">
                              <p className="text-2xl font-bold text-emerald-600">{permit.price} PLN</p>
                              {selectedPermits.includes(permit.type) && (
                                <p className="text-xs text-emerald-600 font-medium mt-1">✓ Wybrane</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {selectedPermits.length > 0 && (
                      <div className="mt-6 space-y-4">
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <Label htmlFor="owner-code" className="text-sm font-medium text-blue-800">
                            Kod współwłaściciela (opcjonalnie)
                          </Label>
                          <Input
                            id="owner-code"
                            value={ownerCode}
                            onChange={(e) => setOwnerCode(e.target.value)}
                            placeholder="Wprowadź kod dla zniżki właścicielskiej"
                            className="mt-1"
                          />
                          <p className="text-xs text-blue-600 mt-1">
                            Współwłaściciele jeziora: roczne pozwolenie za 50 PLN
                          </p>
                        </div>
                        
                        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                          <div className="flex justify-between items-center">
                            <span className="font-medium text-emerald-800">Łączna kwota:</span>
                            <span className="text-2xl font-bold text-emerald-600">{calculateTotal()} PLN</span>
                          </div>
                          {ownerCode.trim() === 'WLASCICIELWIELISZEW' && selectedPermits.includes('yearly') && (
                            <p className="text-sm text-emerald-700 mt-2">
                              ✅ Zastosowano zniżkę współwłaściciela dla pozwolenia rocznego (300 PLN → 50 PLN)
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="shadow-lg border-blue-200">
                  <CardHeader className="bg-blue-50">
                    <CardTitle className="text-blue-800">Podsumowanie</CardTitle>
                    <CardDescription>Potwierdź zakup pozwoleń</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <form onSubmit={handlePurchase} className="space-y-4">
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h3 className="font-medium mb-2">Dane klienta:</h3>
                        <p className="text-sm text-gray-600">
                          <strong>Nazwa:</strong> {user?.full_name}<br />
                          <strong>Email:</strong> {user?.email}
                        </p>
                      </div>

                      {selectedPermits.length > 0 && (
                        <div className="space-y-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <h3 className="font-medium text-yellow-800 flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            Wymagane akceptacje
                          </h3>
                          
                          <div className="space-y-3">
                            <div className="flex items-start space-x-3">
                              <Checkbox
                                id="regulations"
                                checked={regulationsAccepted}
                                onCheckedChange={setRegulationsAccepted}
                                className="mt-1"
                              />
                              <div className="flex-1">
                                <Label htmlFor="regulations" className="text-sm cursor-pointer">
                                  Akceptuję regulamin łowiska *
                                </Label>
                                <div className="mt-1">
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <Button variant="link" className="h-auto p-0 text-blue-600 text-xs">
                                        Przeczytaj regulamin łowiska
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                                      <DialogHeader>
                                        <DialogTitle>Regulamin Łowiska Jezioro Wieliszew</DialogTitle>
                                      </DialogHeader>
                                      <div className="mt-4 text-sm whitespace-pre-line">
                                        {regulationsData?.fishing_regulations?.content}
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-start space-x-3">
                              <Checkbox
                                id="data-processing"
                                checked={dataProcessingAccepted}
                                onCheckedChange={setDataProcessingAccepted}
                                className="mt-1"
                              />
                              <div className="flex-1">
                                <Label htmlFor="data-processing" className="text-sm cursor-pointer">
                                  Wyrażam zgodę na przetwarzanie danych osobowych *
                                </Label>
                                <div className="mt-1">
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <Button variant="link" className="h-auto p-0 text-blue-600 text-xs">
                                        Przeczytaj informację o danych osobowych
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                                      <DialogHeader>
                                        <DialogTitle>Przetwarzanie Danych Osobowych</DialogTitle>
                                      </DialogHeader>
                                      <div className="mt-4 text-sm whitespace-pre-line">
                                        {regulationsData?.data_processing_agreement?.content}
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      <Button 
                        type="submit" 
                        disabled={loading || selectedPermits.length === 0 || !regulationsAccepted || !dataProcessingAccepted}
                        className="w-full bg-emerald-600 hover:bg-emerald-700 text-lg py-3"
                      >
                        {loading ? 'Przetwarzanie...' : `Kup pozwolenia (${calculateTotal()} PLN)`}
                      </Button>
                      
                      {selectedPermits.length > 0 && (!regulationsAccepted || !dataProcessingAccepted) && (
                        <p className="text-xs text-gray-500 text-center">
                          Musisz zaakceptować regulamin i zgodę na dane, aby kontynuować
                        </p>
                      )}
                    </form>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="history">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Moje pozwolenia</CardTitle>
                  <CardDescription>Historia zakupionych pozwoleń</CardDescription>
                </CardHeader>
                <CardContent>
                  {myPermits.length === 0 ? (
                    <div className="text-center py-8">
                      <Fish className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 mb-4">
                        Nie masz jeszcze żadnych pozwoleń. <br />
                        Kup pozwolenie, aby uzyskać dostęp do zawodów wędkarskich!
                      </p>
                      <Button 
                        onClick={() => setActiveTab('buy')} 
                        className="mt-4 bg-emerald-600 hover:bg-emerald-700"
                      >
                        <Fish className="h-4 w-4 mr-2" />
                        Kup pierwsze pozwolenie
                      </Button>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {myPermits.map((permit, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <h3 className="font-semibold">{permit.description}</h3>
                              <p className="text-sm text-gray-600">
                                Ważne do: {new Date(permit.expiry_date).toLocaleDateString('pl-PL')}
                              </p>
                              <Badge 
                                className={
                                  permit.status === 'active' 
                                    ? 'bg-emerald-100 text-emerald-800 mt-2' 
                                    : 'bg-gray-100 text-gray-800 mt-2'
                                }
                              >
                                {permit.status === 'active' ? 'AKTYWNY' : permit.status.toUpperCase()}
                              </Badge>
                            </div>
                            <div className="text-right">
                              <p className="font-bold text-emerald-600">{permit.price} PLN</p>
                              {permit.qr_code && (
                                <img 
                                  src={permit.qr_code} 
                                  alt="QR Code" 
                                  className="w-16 h-16 border rounded mt-2"
                                />
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="catches">
              <div className="grid lg:grid-cols-2 gap-8">
                {/* Upload nowego połowu */}
                <Card className="shadow-lg border-blue-200">
                  <CardHeader className="bg-blue-50">
                    <CardTitle className="text-blue-800 flex items-center gap-2">
                      <Camera className="h-5 w-5" />
                      Prześlij połów (ETAP 1)
                    </CardTitle>
                    <CardDescription>Wgraj zdjęcie swojej ryby - start systemu catch & release!</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <form onSubmit={handleCatchUpload} className="space-y-4">
                      <div>
                        <Label htmlFor="catch-image">Zdjęcie ryby</Label>
                        <Input
                          id="catch-image"
                          type="file"
                          accept="image/*"
                          onChange={(e) => setCatchImage(e.target.files[0])}
                          className="mt-1"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Zrób zdjęcie ryby z miarką dla najlepszego efektu
                        </p>
                      </div>

                      {catchImage && (
                        <div className="mt-4">
                          <p className="text-sm font-medium text-gray-700 mb-2">Podgląd:</p>
                          <img 
                            src={URL.createObjectURL(catchImage)} 
                            alt="Preview" 
                            className="max-w-full h-48 object-cover rounded border"
                          />
                        </div>
                      )}

                      <Button 
                        type="submit" 
                        disabled={uploadingCatch || !catchImage}
                        className="w-full bg-blue-600 hover:bg-blue-700"
                      >
                        {uploadingCatch ? 'Przesyłanie...' : 'Prześlij połów'}
                      </Button>
                    </form>

                    <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <h4 className="font-medium text-yellow-800 mb-2">🎣 ETAP 1 - Podstawowy upload</h4>
                      <ul className="text-sm text-yellow-700 space-y-1">
                        <li>• Prześlij zdjęcie ryby</li>
                        <li>• Czeka na weryfikację admina</li>
                        <li>• Kolejne etapy: AI, punkty, rankingi</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>

                {/* Lista moich połowów */}
                <Card className="shadow-lg border-emerald-200">
                  <CardHeader className="bg-emerald-50">
                    <CardTitle className="text-emerald-800">Moje połowy</CardTitle>
                    <CardDescription>Historia przesłanych zdjęć połowów</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    {myCatches.length === 0 ? (
                      <div className="text-center py-8">
                        <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500">Brak przesłanych połowów</p>
                        <p className="text-sm text-gray-400 mt-2">
                          Prześlij swoje pierwsze zdjęcie ryby!
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {myCatches.map((catchItem, index) => (
                          <div key={index} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <p className="font-medium">
                                  Połów #{catchItem.id.slice(-6)}
                                </p>
                                <p className="text-sm text-gray-600">
                                  {new Date(catchItem.created_at).toLocaleDateString('pl-PL')}
                                </p>
                              </div>
                              <Badge 
                                className={
                                  catchItem.status === 'approved' 
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : catchItem.status === 'rejected'
                                    ? 'bg-red-100 text-red-800' 
                                    : 'bg-yellow-100 text-yellow-800'
                                }
                              >
                                {catchItem.status === 'approved' ? 'Zatwierdzony' : 
                                 catchItem.status === 'rejected' ? 'Odrzucony' : 'Oczekuje'}
                              </Badge>
                            </div>
                            
                            {catchItem.points > 0 && (
                              <p className="text-sm font-medium text-emerald-600">
                                Punkty: {catchItem.points}
                              </p>
                            )}
                            
                            {catchItem.species && (
                              <p className="text-sm text-gray-600">
                                Gatunek: {catchItem.species}
                                {catchItem.length_cm && ` (${catchItem.length_cm} cm)`}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Pro System - Buy Pro Tickets */}
            <TabsContent value="pro-buy">
              <div className="grid lg:grid-cols-2 gap-8">
                <Card className="shadow-lg border-blue-200">
                  <CardHeader className="bg-blue-50">
                    <CardTitle className="text-blue-800 flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Bilety Wędkarskie - System Zaawansowany
                    </CardTitle>
                    <CardDescription>Kup bilet z ShortCode i QR tokenem</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    {proWaters.length === 0 ? (
                      <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="text-gray-500 mt-4">Ładowanie łowisk Pro...</p>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Water Selection */}
                        <div>
                          <Label className="text-base font-medium">Łowisko</Label>
                          <div className="mt-2 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                            <div className="flex items-center gap-2">
                              <Fish className="h-5 w-5 text-emerald-600" />
                              <div>
                                <p className="font-medium text-emerald-800">{selectedProWater?.name}</p>
                                <p className="text-sm text-emerald-600">{selectedProWater?.location}</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Tariff Selection */}
                        <div>
                          <Label className="text-base font-medium">Wybierz taryfę</Label>
                          <div className="mt-3 space-y-3">
                            {proTariffs.map((tariff) => (
                              <div
                                key={tariff.id}
                                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                                  selectedProTariff?.id === tariff.id
                                    ? 'border-blue-500 bg-blue-50 shadow-md'
                                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                                }`}
                                onClick={() => handleProTariffSelection(tariff)}
                              >
                                <div className="flex justify-between items-center">
                                  <div>
                                    <h3 className="font-semibold text-blue-800">{tariff.name}</h3>
                                    <p className="text-sm text-gray-600 mt-1">{tariff.description}</p>
                                    <p className="text-xs text-gray-500 mt-1">
                                      Ważność: {tariff.validity_days} {tariff.validity_days === 1 ? 'dzień' : 'dni'}
                                    </p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-2xl font-bold text-blue-600">{tariff.price_pln} PLN</p>
                                    {selectedProTariff?.id === tariff.id && (
                                      <CheckCircle className="h-5 w-5 text-blue-600 mt-1 ml-auto" />
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Agreements */}
                        <div className="space-y-4">
                          <div className="flex items-start space-x-3">
                            <Checkbox
                              id="pro-regulations"
                              checked={proRegulationsAccepted}
                              onCheckedChange={setProRegulationsAccepted}
                              className="mt-1"
                            />
                            <Label htmlFor="pro-regulations" className="text-sm leading-relaxed">
                              Akceptuję <strong>regulamin systemu biletów</strong> i zasady zaawansowanego systemu biletów
                            </Label>
                          </div>
                          
                          <div className="flex items-start space-x-3">
                            <Checkbox
                              id="pro-rodo"
                              checked={proDataProcessingAccepted}
                              onCheckedChange={setProDataProcessingAccepted}
                              className="mt-1"
                            />
                            <Label htmlFor="pro-rodo" className="text-sm leading-relaxed">
                              Wyrażam zgodę na <strong>przetwarzanie danych osobowych</strong> w systemie biletów
                            </Label>
                          </div>
                        </div>

                        {/* Purchase Button */}
                        <Button 
                          onClick={purchaseProTicket}
                          disabled={!selectedProTariff || !proRegulationsAccepted || !proDataProcessingAccepted || purchasingProTicket}
                          className="w-full bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white py-3"
                          size="lg"
                        >
                          {purchasingProTicket ? (
                            <div className="flex items-center gap-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              Przetwarzanie...
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              <Shield className="h-5 w-5" />
                              Kup bilet {selectedProTariff ? `- ${selectedProTariff.price_pln} PLN` : ''}
                            </div>
                          )}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Pro System Features */}
                <Card className="shadow-lg border-emerald-200">
                  <CardHeader className="bg-emerald-50">
                    <CardTitle className="text-emerald-800">Zalety Pro Systemu</CardTitle>
                    <CardDescription>Dlaczego warto wybrać Pro?</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <QrCode className="h-6 w-6 text-emerald-600 mt-1" />
                        <div>
                          <h4 className="font-medium text-emerald-800">ShortCode + QR Token</h4>
                          <p className="text-sm text-gray-600">Bezpieczna weryfikacja przez kod 8-znakowy lub QR</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <Shield className="h-6 w-6 text-emerald-600 mt-1" />
                        <div>
                          <h4 className="font-medium text-emerald-800">JWT Security</h4>
                          <p className="text-sm text-gray-600">Zaawansowane zabezpieczenia z tokenami JWT</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <CheckCircle className="h-6 w-6 text-emerald-600 mt-1" />
                        <div>
                          <h4 className="font-medium text-emerald-800">Offline Mode</h4>
                          <p className="text-sm text-gray-600">Weryfikacja przez kontrolerów bez internetu</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <Fish className="h-6 w-6 text-emerald-600 mt-1" />
                        <div>
                          <h4 className="font-medium text-emerald-800">Multi-venue</h4>
                          <p className="text-sm text-gray-600">Wsparcie dla wielu łowisk i taryf</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-medium text-blue-800 mb-2">🚀 Pro System - ETAP 2</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Backend API w pełni funkcjonalny</li>
                        <li>• ShortCode generation z checksumą</li>
                        <li>• JWT tokens z nbf/exp/ver</li>
                        <li>• Mock payment w trybie dev</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Pro System - My Pro Tickets */}
            <TabsContent value="pro-history">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <QrCode className="h-5 w-5" />
                    Moje Bilety
                  </CardTitle>
                  <CardDescription>Historia zakupionych biletów z ShortCode i QR tokenami</CardDescription>
                </CardHeader>
                <CardContent>
                  {myProTickets.length === 0 ? (
                    <div className="text-center py-8">
                      <Shield className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 mb-4">
                        Nie masz jeszcze żadnych biletów Pro. <br />
                        Kup pierwszy bilet Pro aby uzyskać dostęp do zaawansowanych funkcji!
                      </p>
                      <Button 
                        onClick={() => setActiveTab('pro-buy')} 
                        className="mt-4 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700"
                      >
                        <Shield className="h-4 w-4 mr-2" />
                        Kup pierwszy bilet Pro
                      </Button>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {myProTickets.map((ticket, index) => (
                        <div key={index} className="border rounded-lg p-6 bg-gradient-to-r from-blue-50 to-emerald-50">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h3 className="font-semibold text-lg">{ticket.tariff?.name}</h3>
                              <p className="text-sm text-gray-600">{ticket.water?.name} - {ticket.water?.location}</p>
                              <p className="text-sm text-gray-600 mt-1">
                                Ważny do: {new Date(ticket.valid_until).toLocaleDateString('pl-PL')} {new Date(ticket.valid_until).toLocaleTimeString('pl-PL', {hour: '2-digit', minute: '2-digit'})}
                              </p>
                            </div>
                            <Badge 
                              className={
                                ticket.status === 'valid' 
                                  ? 'bg-emerald-100 text-emerald-800' 
                                  : ticket.status === 'expired'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }
                            >
                              {ticket.status === 'valid' ? 'AKTYWNY' : 
                               ticket.status === 'expired' ? 'WYGASŁ' : 
                               ticket.status.toUpperCase()}
                            </Badge>
                          </div>

                          {/* ShortCode */}
                          <div className="mb-4 p-3 bg-white border rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <Shield className="h-4 w-4 text-blue-600" />
                              <span className="text-sm font-medium">ShortCode do weryfikacji</span>
                            </div>
                            <div className="text-center">
                              <p className="text-2xl font-mono font-bold text-blue-600 tracking-wider">
                                {ticket.short_code}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                Podaj ten kod kontrolerowi
                              </p>
                            </div>
                          </div>

                          {/* QR Code */}
                          {ticket.qr_token && (
                            <div className="p-3 bg-white border rounded-lg">
                              <div className="flex items-center gap-2 mb-2">
                                <QrCode className="h-4 w-4 text-emerald-600" />
                                <span className="text-sm font-medium">QR Token do skanowania</span>
                              </div>
                              <div className="text-center">
                                <div className="inline-block p-2 bg-white border rounded">
                                  <div className="text-xs font-mono break-all text-gray-600 max-w-xs">
                                    {ticket.qr_token.substring(0, 50)}...
                                  </div>
                                </div>
                                <p className="text-xs text-gray-500 mt-2">
                                  Pokaż ten token podczas skanowania QR
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

const ControllerDashboard = () => {
  const { user, token, logout } = useAuth();
  const [verificationResult, setVerificationResult] = useState(null);
  const [qrData, setQrData] = useState('');
  const [orderId, setOrderId] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('scan');
  const [verificationHistory, setVerificationHistory] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [verificationMethod, setVerificationMethod] = useState('qr'); // 'qr' or 'order'

  useEffect(() => {
    if (activeTab === 'history') {
      fetchVerificationHistory();
    }
  }, [activeTab]);

  const fetchVerificationHistory = async () => {
    try {
      const response = await axios.get(`${API}/controller/verification-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVerificationHistory(response.data.logs);
    } catch (error) {
      console.error('Error fetching verification history:', error);
    }
  };

  const handleVerification = async (e) => {
    e.preventDefault();
    
    if (verificationMethod === 'qr' && !qrData.trim()) {
      alert('Proszę wprowadzić dane z kodu QR');
      return;
    }
    
    if (verificationMethod === 'order' && !orderId.trim()) {
      alert('Proszę wprowadzić numer zamówienia');
      return;
    }

    setLoading(true);
    
    try {
      let response;
      
      if (verificationMethod === 'qr') {
        response = await axios.post(`${API}/permits/verify`, {
          qr_data: qrData
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        response = await axios.post(`${API}/permits/verify-by-order`, {
          order_id: orderId
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

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

  const startQRScan = async () => {
    try {
      setScanning(true);
      
      const qrContainer = document.getElementById('qr-scanner-container');
      qrContainer.innerHTML = '';
      
      // Create scanner element
      const scannerDiv = document.createElement('div');
      scannerDiv.id = 'qr-reader';
      scannerDiv.style.width = '100%';
      scannerDiv.style.maxWidth = '400px';
      scannerDiv.style.margin = '0 auto';
      qrContainer.appendChild(scannerDiv);

      // Configuration for html5-qrcode
      const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
        disableFlip: false,
        supportedScanTypes: ['QR_CODE']
      };

      const html5QrCodeScanner = new Html5QrcodeScanner(
        'qr-reader',
        config,
        false // verbose logging
      );

      // Success callback
      const onScanSuccess = (decodedText, decodedResult) => {
        console.log('QR Code scanned:', decodedText);
        setQrData(decodedText);
        
        // Stop scanning
        html5QrCodeScanner.clear().then(() => {
          setScanning(false);
          qrContainer.innerHTML = '<p class="text-center text-green-600 font-semibold text-lg">✅ Kod QR zeskanowany pomyślnie!</p>';
          
          // Auto-verify after successful scan
          setTimeout(() => {
            const form = document.querySelector('form');
            if (form) {
              form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            }
          }, 1000);
        }).catch(err => {
          console.error('Error stopping scanner:', err);
        });
      };

      // Error callback
      const onScanFailure = (error) => {
        // Don't log every scanning error, just continue
      };

      // Start scanning
      html5QrCodeScanner.render(onScanSuccess, onScanFailure);
      
      // Add instructions
      const instructions = document.createElement('p');
      instructions.textContent = 'Skieruj kamerę na kod QR pozwolenia';
      instructions.className = 'text-center text-gray-600 text-sm mt-4';
      qrContainer.appendChild(instructions);
      
      // Add stop button
      const stopButton = document.createElement('button');
      stopButton.textContent = '❌ Zatrzymaj skanowanie';
      stopButton.className = 'mt-4 w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 font-medium';
      stopButton.onclick = () => {
        html5QrCodeScanner.clear().then(() => {
          setScanning(false);
          qrContainer.innerHTML = '';
        }).catch(err => {
          console.error('Error stopping scanner:', err);
          setScanning(false);
          qrContainer.innerHTML = '';
        });
      };
      qrContainer.appendChild(stopButton);

    } catch (error) {
      console.error('QR Scanner initialization error:', error);
      alert('Błąd podczas inicjalizacji skanera QR. Spróbuj weryfikacji przez numer zamówienia.');
      setScanning(false);
      
      const qrContainer = document.getElementById('qr-scanner-container');
      if (qrContainer) {
        qrContainer.innerHTML = '<p class="text-center text-red-600">Błąd skanera. Użyj weryfikacji przez numer zamówienia.</p>';
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-emerald-50 to-teal-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Panel Kontrolera</h1>
              <p className="text-gray-600">Witaj, {user?.full_name}</p>
            </div>
            <Button onClick={logout} variant="outline" className="flex items-center gap-2">
              <LogOut className="h-4 w-4" />
              Wyloguj
            </Button>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2 mb-8">
              <TabsTrigger value="scan" className="flex items-center gap-2">
                <QrCode className="h-4 w-4" />
                Weryfikacja
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                Historia kontroli
              </TabsTrigger>
            </TabsList>

            <TabsContent value="scan">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Weryfikacja pozwoleń</CardTitle>
                  <CardDescription>Wybierz metodę weryfikacji pozwolenia</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Method Selection */}
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <Button
                        variant={verificationMethod === 'qr' ? 'default' : 'outline'}
                        onClick={() => setVerificationMethod('qr')}
                        className="h-auto p-4 flex flex-col items-center"
                      >
                        <QrCode className="h-6 w-6 mb-2" />
                        <span className="text-sm">Kod QR</span>
                      </Button>
                      <Button
                        variant={verificationMethod === 'order' ? 'default' : 'outline'}
                        onClick={() => setVerificationMethod('order')}
                        className="h-auto p-4 flex flex-col items-center"
                      >
                        <FileText className="h-6 w-6 mb-2" />
                        <span className="text-sm">Nr zamówienia</span>
                      </Button>
                    </div>

                    {verificationMethod === 'qr' && (
                      <div className="space-y-4">
                        <div>
                          <Button 
                            onClick={startQRScan} 
                            disabled={scanning}
                            className="w-full bg-blue-600 hover:bg-blue-700 mb-4"
                          >
                            <Camera className="h-4 w-4 mr-2" />
                            {scanning ? 'Skanowanie...' : 'Skanuj kod QR kamerą'}
                          </Button>
                          
                          <div id="qr-scanner-container" className="text-center">
                            {/* QR Scanner will be inserted here */}
                          </div>
                        </div>

                        <div className="text-center text-gray-500">lub</div>

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
                            <p className="text-xs text-gray-500 mt-1">
                              Wpisz lub zeskanuj zawartość kodu QR
                            </p>
                          </div>

                          <Button 
                            type="submit" 
                            disabled={loading || !qrData.trim()}
                            className="w-full bg-blue-600 hover:bg-blue-700"
                          >
                            {loading ? 'Weryfikowanie...' : 'Weryfikuj przez QR'}
                          </Button>
                        </form>
                      </div>
                    )}

                    {verificationMethod === 'order' && (
                      <form onSubmit={handleVerification} className="space-y-4">
                        <div>
                          <Label htmlFor="order-id">Numer zamówienia</Label>
                          <Input
                            id="order-id"
                            value={orderId}
                            onChange={(e) => setOrderId(e.target.value)}
                            placeholder="FP1758229546"
                            className="mt-1"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Numer zamówienia znajdziesz na stronie sukcesu po zakupie pozwolenia
                          </p>
                        </div>

                        <Button 
                          type="submit" 
                          disabled={loading || !orderId.trim()}
                          className="w-full bg-emerald-600 hover:bg-emerald-700"
                        >
                          {loading ? 'Weryfikowanie...' : 'Weryfikuj przez zamówienie'}
                        </Button>
                      </form>
                    )}

                    {verificationResult && (
                      <div className={`p-4 rounded-lg ${
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

                        {verificationResult.valid && (
                          <div className="mt-3 text-sm text-emerald-700">
                            <p><strong>Posiadacz:</strong> {verificationResult.customer?.full_name}</p>
                            <p><strong>Email:</strong> {verificationResult.customer?.email}</p>
                            {verificationResult.order_id && (
                              <p><strong>Nr zamówienia:</strong> {verificationResult.order_id}</p>
                            )}
                            
                            {verificationResult.permits && (
                              <div className="mt-2">
                                <p><strong>Aktywne pozwolenia ({verificationResult.permits.length}):</strong></p>
                                {verificationResult.permits.map((permit, index) => (
                                  <div key={index} className="ml-2 mt-1 text-xs">
                                    • {permit.description} - ważne do {new Date(permit.expiry_date).toLocaleDateString('pl-PL')} 
                                    ({permit.days_remaining} dni pozostało)
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {verificationResult.permit && (
                              <div className="mt-2">
                                <p><strong>Typ:</strong> {verificationResult.permit.description}</p>
                                <p><strong>Ważne do:</strong> {new Date(verificationResult.expiry_date).toLocaleDateString('pl-PL')}</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    <Button 
                      onClick={() => {
                        setVerificationResult(null);
                        setQrData('');
                        setOrderId('');
                        // Clear scanner if active
                        const qrContainer = document.getElementById('qr-scanner-container');
                        if (qrContainer) {
                          qrContainer.innerHTML = '';
                        }
                        setScanning(false);
                      }}
                      variant="outline"
                      className="w-full"
                    >
                      Wyczyść i rozpocznij nowo
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Historia kontroli</CardTitle>
                  <CardDescription>Ostatnie weryfikacje pozwoleń</CardDescription>
                </CardHeader>
                <CardContent>
                  {verificationHistory.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">
                      Brak historii weryfikacji
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {verificationHistory.map((log, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium">{log.permit_holder}</p>
                              <p className="text-sm text-gray-600">
                                {new Date(log.timestamp).toLocaleString('pl-PL')}
                              </p>
                              <p className="text-xs text-gray-500">{log.location}</p>
                            </div>
                            <Badge 
                              className={
                                log.verification_result 
                                  ? 'bg-emerald-100 text-emerald-800' 
                                  : 'bg-red-100 text-red-800'
                              }
                            >
                              {log.verification_result ? 'WAŻNY' : 'NIEWAŻNY'}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    // Admin stats would be implemented here
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-emerald-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Panel Administratora</h1>
              <p className="text-gray-600">Witaj, {user?.full_name}</p>
            </div>
            <Button onClick={logout} variant="outline" className="flex items-center gap-2">
              <LogOut className="h-4 w-4" />
              Wyloguj
            </Button>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Użytkownicy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">0</div>
                <p className="text-sm text-gray-600">Zarejestrowani użytkownicy</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Fish className="h-5 w-5" />
                  Pozwolenia
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">0</div>
                <p className="text-sm text-gray-600">Sprzedane pozwolenia</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Kontrole
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">0</div>
                <p className="text-sm text-gray-600">Przeprowadzone kontrole</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Panel administratora</CardTitle>
              <CardDescription>Zarządzanie systemem pozwoleń</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-center text-gray-500 py-8">
                Panel administratora w budowie...
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const PaymentSuccess = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [paymentStatus, setPaymentStatus] = useState(null);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const orderId = urlParams.get('orderId');
    
    if (orderId) {
      checkPaymentStatus(orderId);
    } else {
      setLoading(false);
    }
  }, []);

  const checkPaymentStatus = async (orderId) => {
    try {
      const response = await axios.get(`${API}/payment/status/${orderId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPaymentStatus(response.data);
    } catch (error) {
      console.error('Payment status check failed:', error);
      setPaymentStatus({ status: 'error' });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <Fish className="h-12 w-12 text-emerald-600 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Sprawdzanie statusu płatności...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <Card className="shadow-lg">
            <CardHeader className="text-center">
              <Fish className="h-12 w-12 text-emerald-600 mx-auto mb-4" />
              <CardTitle className="text-2xl">
                {paymentStatus?.payment_status === 'completed' ? 'Płatność pomyślna!' : 'Status płatności'}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              {paymentStatus?.payment_status === 'completed' ? (
                <div>
                  <CheckCircle className="h-16 w-16 text-emerald-600 mx-auto mb-4" />
                  <p className="text-lg text-emerald-800 mb-4">
                    Twoje pozwolenia zostały aktywowane!
                  </p>
                  <p className="text-gray-600 mb-6">
                    Zamówienie: {paymentStatus.order_id}<br />
                    Kwota: {paymentStatus.amount} PLN
                  </p>
                  <Button 
                    onClick={() => window.location.href = '/'}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    Przejdź do panelu klienta
                  </Button>
                </div>
              ) : (
                <div>
                  <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
                  <p className="text-lg text-red-800 mb-4">
                    Problem z płatnością
                  </p>
                  <p className="text-gray-600 mb-6">
                    Status: {paymentStatus?.payment_status || 'Nieznany'}<br />
                    Zamówienie: {paymentStatus?.order_id || 'Brak'}
                  </p>
                  <Button 
                    onClick={() => window.location.href = '/'}
                    variant="outline"
                  >
                    Powrót do panelu
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const { user, loading, isAuthenticated } = useAuth();

  // Check if this is a payment return page
  if (window.location.pathname === '/payment-success') {
    return <PaymentSuccess />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <Fish className="h-12 w-12 text-emerald-600 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Ładowanie...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  // Route based on user role
  switch (user?.role) {
    case 'client':
      return <ClientDashboard />;
    case 'controller':
      return <ControllerDashboard />;
    case 'admin':
      return <AdminDashboard />;
    default:
      return <LoginForm />;
  }
};

const AppWithAuth = () => {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
};

export default AppWithAuth;