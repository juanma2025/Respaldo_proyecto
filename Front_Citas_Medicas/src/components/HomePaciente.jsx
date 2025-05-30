import axios from 'axios';
import React, { useEffect, useState } from 'react';

// Sidebar component
const Sidebar = ({ userName, avatarUrl }) => (
  <aside className="h-full w-64 bg-white border-r flex flex-col justify-between py-6 px-4">
    <div>
      <h1 className="text-2xl font-bold mb-8 flex items-center gap-2 text-indigo-700">
        <span className="text-3xl">🩺</span> Cita Salud
      </h1>
      <nav className="flex flex-col gap-2">
        <a href="#" className="flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-50 text-indigo-700 font-semibold">
          <span>📅</span> Mis Citas
        </a>
        <a href="#" className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-indigo-50">
          <span>💧</span> Historial Médico
        </a>
        <a href="#" className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-indigo-50">
          <span>🩺</span> Servicios
        </a>
        <a href="#" className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-indigo-50">
          <span>⚙️</span> Configuración
        </a>
      </nav>
    </div>
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-indigo-50">
      <img src={avatarUrl} alt="avatar" className="w-10 h-10 rounded-full" />
      <div>
        <div className="font-semibold">{userName}</div>
        <div className="text-xs text-gray-500">View profile</div>
      </div>
      <span className="ml-auto text-green-500 text-xs">●</span>
    </div>
  </aside>
);

// Header component
const Header = () => (
  <header className="h-16 flex items-center justify-between px-8 border-b bg-white">
    <nav className="flex gap-8">
      <a href="#" className="text-indigo-700 font-semibold border-b-2 border-indigo-700 pb-2">Home</a>
      <a href="#" className="text-gray-600 hover:text-indigo-700">Appointments</a>
      <a href="#" className="text-gray-600 hover:text-indigo-700">Settings</a>
    </nav>
    <div className="flex items-center gap-4">
      <button className="text-gray-500 hover:text-indigo-700">
        <svg width="22" height="22" fill="none" stroke="currentColor"><circle cx="10" cy="10" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
      </button>
      <img src="https://randomuser.me/api/portraits/women/44.jpg" alt="avatar" className="w-9 h-9 rounded-full" />
    </div>
  </header>
);

const AgendarCita = ({ apiUrl = import.meta.env.VITE_API_URL }) => {
  const [especialidades, setEspecialidades] = useState([]);
  const [medicos, setMedicos] = useState([]);
  const [selectedEspecialidad, setSelectedEspecialidad] = useState('');
  const [selectedMedico, setSelectedMedico] = useState('');
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [motivo, setMotivo] = useState('');
  const [duracion, setDuracion] = useState(30);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Verificar autenticación al cargar el componente
  useEffect(() => {
    const checkAuthentication = () => {
      const token = localStorage.getItem('auth_token');
      const tokenExists = !!token;
      
      console.log('Verificando autenticación:', {
        token: token ? 'Presente' : 'Ausente',
        tokenLength: token ? token.length : 0
      });
      
      setIsAuthenticated(tokenExists);
      setCheckingAuth(false);
    };

    checkAuthentication();
    
    // Escuchar cambios en localStorage (cuando se hace login en otra pestaña)
    window.addEventListener('storage', checkAuthentication);
    
    return () => {
      window.removeEventListener('storage', checkAuthentication);
    };
  }, []);

  // Función para configurar axios con el token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No hay token de autenticación');
    }
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // Cargar especialidades
  useEffect(() => {
    const fetchEspecialidades = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // URL corregida según tus urlpatterns
        const response = await axios.get(`${apiUrl}auth/specialties/`, {
          headers: getAuthHeaders()
        });
        
        console.log('Especialidades response:', response.data);
        setEspecialidades(response.data);
      } catch (err) {
        console.error('Error fetching especialidades:', err);
        
        if (err.response?.status === 401) {
          setError('Sesión expirada. Por favor, inicia sesión nuevamente.');
          setIsAuthenticated(false);
          localStorage.removeItem('auth_token');
        } else {
          setError('Error al cargar las especialidades: ' + (err.response?.data?.detail || err.message));
        }
      } finally {
        setIsLoading(false);
      }
    };

    // Solo hacer la petición si está autenticado
    if (isAuthenticated) {
      fetchEspecialidades();
    } else {
      setError('Debes iniciar sesión para ver las especialidades');
    }
  }, [apiUrl, isAuthenticated]);

  // Cargar médicos según especialidad
  useEffect(() => {
    const fetchMedicos = async () => {
      if (selectedEspecialidad) {
        try {
          setIsLoading(true);
          setError('');
          
          // URL corregida según tus urlpatterns
          const response = await axios.get(
            `${apiUrl}auth/doctors/?specialty=${selectedEspecialidad}`,
            {
              headers: getAuthHeaders()
            }
          );
          
          console.log('Médicos response:', response.data);
          setMedicos(response.data);
          setSelectedMedico('');
        } catch (err) {
          console.error('Error fetching médicos:', err);
          
          if (err.response?.status === 401) {
            setError('Sesión expirada. Por favor, inicia sesión nuevamente.');
            setIsAuthenticated(false);
            localStorage.removeItem('auth_token');
          } else {
            setError('Error al cargar los médicos: ' + (err.response?.data?.detail || err.message));
          }
        } finally {
          setIsLoading(false);
        }
      } else {
        setMedicos([]);
        setSelectedMedico('');
      }
    };
    
    fetchMedicos();
  }, [selectedEspecialidad, apiUrl]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setIsLoading(true);

    try {
      const citaData = {
        doctor_id: parseInt(selectedMedico), // Asegurar que sea número
        appointment_date: fecha,
        appointment_time: hora,
        reason: motivo,
        duration: duracion // Opcional si tu backend lo maneja
      };

      console.log('Enviando datos de cita:', citaData);

      const response = await axios.post(
        `${apiUrl}appointments/create/`,
        citaData,
        {
          headers: getAuthHeaders()
        }
      );

      console.log('Respuesta del servidor:', response.data);
      
      setMensaje(response.data.mensaje || response.data.message || "Cita agendada correctamente.");
      setError('');
      
      // Limpiar formulario
      setSelectedEspecialidad('');
      setSelectedMedico('');
      setFecha('');
      setHora('');
      setMotivo('');
      setMedicos([]);
      
    } catch (err) {
      console.error('Error al agendar cita:', err);
      
      if (err.response?.status === 401) {
        setError('Sesión expirada. Por favor, inicia sesión nuevamente.');
        setIsAuthenticated(false);
        localStorage.removeItem('auth_token');
      } else {
        const msg = 
          err.response?.data?.detail ||
          err.response?.data?.non_field_errors?.[0] ||
          err.response?.data?.mensaje ||
          err.response?.data?.message ||
          err.message ||
          'Error al agendar la cita';
        setError(msg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Función para manejar el re-login
  const handleRelogin = () => {
    // Opción 1: Redirigir a la página de login (si tienes React Router)
    // window.location.href = '/login';
    
    // Opción 2: Recargar la página actual (si el login está en la misma app)
    window.location.reload();
    
    // Opción 3: Si tienes un modal de login, lo puedes abrir aquí
    // setShowLoginModal(true);
  };

  // Mostrar loading mientras verifica autenticación
  if (checkingAuth) {
    return (
      <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-4rem)]">
        <div className="max-w-md w-full p-6 bg-white shadow-lg rounded-xl mt-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-700 mx-auto mb-4"></div>
            <p className="text-gray-600">Verificando autenticación...</p>
          </div>
        </div>
      </div>
    );
  }

  // Verificar si el usuario está autenticado
  if (!isAuthenticated) {
    return (
      <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-4rem)]">
        <div className="max-w-md w-full p-6 bg-white shadow-lg rounded-xl mt-10">
          <h1 className="text-2xl font-bold text-center text-indigo-700 mb-4">Acceso Restringido</h1>
          <div className="text-center">
            <p className="text-gray-600 mb-4">Debes iniciar sesión para agendar una cita.</p>
            
            {/* Debug info - quitar en producción */}
            <div className="mb-4 p-2 bg-gray-100 rounded text-xs text-left">
              <p><strong>Debug Info:</strong></p>
              <p>Token presente: {localStorage.getItem('auth_token') ? 'Sí' : 'No'}</p>
              <p>Token length: {localStorage.getItem('auth_token')?.length || 0}</p>
              <p>Usuario: {localStorage.getItem('user_full_name') || 'No definido'}</p>
            </div>
            
            <div className="space-y-3">
              <button 
                onClick={handleRelogin}
                className="w-full bg-indigo-700 text-white px-6 py-2 rounded-lg hover:bg-indigo-800"
              >
                Iniciar Sesión
              </button>
              
              <button 
                onClick={() => window.location.reload()}
                className="w-full bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
              >
                Recargar Página
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-4rem)]">
      <div className="max-w-md w-full p-6 bg-white shadow-lg rounded-xl mt-10">
        <h1 className="text-2xl font-bold text-center text-indigo-700 mb-2">Agendar Cita</h1>
        
        {/* Debug info - quitar en producción */}
        <div className="mb-4 p-2 bg-gray-100 rounded text-xs">
          <p><strong>Estado actual:</strong></p>
          <p>Autenticado: {isAuthenticated ? 'Sí' : 'No'}</p>
          <p>Token presente: {localStorage.getItem('auth_token') ? 'Sí' : 'No'}</p>
          <p>Usuario: {localStorage.getItem('user_full_name') || 'No definido'}</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-900 font-medium mb-2">Especialidad</label>
            <select
              value={selectedEspecialidad}
              onChange={(e) => setSelectedEspecialidad(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg p-2"
              disabled={isLoading}
            >
              <option value="">Seleccione una especialidad</option>
              {especialidades.map((esp, index) => (
                <option key={esp.id || esp.value || index} value={esp.id || esp.value}>
                  {esp.name || esp.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-gray-900 font-medium mb-2">Médico</label>
            <select
              value={selectedMedico}
              onChange={(e) => setSelectedMedico(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg p-2"
              disabled={!selectedEspecialidad || isLoading}
            >
              <option value="">Seleccione un médico</option>
              {medicos.map((medico, index) => (
                <option key={medico.id || index} value={medico.id}>
                  {medico.user?.full_name || 
                   `${medico.user?.first_name} ${medico.user?.last_name}` ||
                   medico.full_name ||
                   `${medico.first_name} ${medico.last_name}` ||
                   'Médico sin nombre'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-gray-900 font-medium mb-2">Fecha</label>
            <input
              type="date"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              required
              className="w-full border border-gray-300 rounded-lg p-2"
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-gray-900 font-medium mb-2">Hora</label>
            <input
              type="time"
              value={hora}
              onChange={(e) => setHora(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg p-2"
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-gray-900 font-medium mb-2">Motivo</label>
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg p-2 h-20 resize-none"
              disabled={isLoading}
              placeholder="Describe el motivo de tu consulta..."
            />
          </div>

          <button
            type="submit"
            className="w-full bg-indigo-700 text-white font-medium py-2 rounded-lg hover:bg-indigo-800 transition disabled:opacity-50"
            disabled={isLoading || !selectedEspecialidad || !selectedMedico}
          >
            {isLoading ? 'Procesando...' : 'Confirmar Cita'}
          </button>
        </form>

        {mensaje && (
          <div className="mt-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            {mensaje}
          </div>
        )}
        
        {error && (
          <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

const HomePaciente = () => {
  const userName = localStorage.getItem('user_full_name') || 'Usuario';
  const avatarUrl = localStorage.getItem('user_avatar') || 'https://randomuser.me/api/portraits/men/32.jpg';

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar userName={userName} avatarUrl={avatarUrl} />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 flex flex-col items-center justify-center bg-gray-50">
          <AgendarCita />
        </main>
      </div>
    </div>
  );
};

export default HomePaciente;