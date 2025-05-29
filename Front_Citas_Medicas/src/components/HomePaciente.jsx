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

  // Cargar especialidades
  useEffect(() => {
    const fetchEspecialidades = async () => {
      try {
        setIsLoading(true);
        // Usar la ruta correcta según tus URLs de AppCitasMedicas
        const response = await axios.get(`${apiUrl}auth/specialties/`);
        console.log('Especialidades response:', response.data); // Para debug
        setEspecialidades(response.data);
      } catch (err) {
        console.error('Error fetching especialidades:', err); // Para debug
        setError('Error al cargar las especialidades: ' + (err.response?.data?.detail || err.message));
      } finally {
        setIsLoading(false);
      }
    };
    fetchEspecialidades();
  }, [apiUrl]);

  // Cargar médicos según especialidad
  useEffect(() => {
    const fetchMedicos = async () => {
      if (selectedEspecialidad) {
        try {
          setIsLoading(true);
          // Usar la ruta correcta según tus URLs de AppCitasMedicas
          const response = await axios.get(
            `${apiUrl}auth/doctors/?specialty=${selectedEspecialidad}`
          );
          console.log('Médicos response:', response.data); // Para debug
          setMedicos(response.data);
          setSelectedMedico('');
        } catch (err) {
          console.error('Error fetching médicos:', err); // Para debug
          setError('Error al cargar los médicos: ' + (err.response?.data?.detail || err.message));
        } finally {
          setIsLoading(false);
        }
      }
    };
    fetchMedicos();
  }, [selectedEspecialidad, apiUrl]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setIsLoading(true);

    const token = localStorage.getItem('auth_token');
    if (!token) {
      setError('Debes iniciar sesión para agendar una cita');
      setIsLoading(false);
      return;
    }

    const citaData = {
      doctor_id: selectedMedico,
      appointment_date: fecha,
      appointment_time: hora,
      reason: motivo,
    };

    try {
      const response = await axios.post(
        `${apiUrl}appointments/create/`,
        citaData,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setMensaje(response.data.mensaje || "Cita agendada correctamente.");
      setError('');
      setSelectedMedico('');
      setFecha('');
      setHora('');
      setMotivo('');
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.mensaje ||
        'Error al agendar la cita';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-4rem)]">
      <div className="max-w-md w-full p-6 bg-white shadow-lg rounded-xl mt-10">
        <h1 className="text-2xl font-bold text-center text-indigo-700 mb-2">Agendar Cita</h1>
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
                <option key={esp.value || index} value={esp.value}>
                  {esp.label}
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
                   `${medico.first_name} ${medico.last_name}`}
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
            <input
              type="text"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg p-2"
              disabled={isLoading}
              placeholder="Motivo de la cita"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-indigo-700 text-white font-medium py-2 rounded-lg hover:bg-indigo-800 transition disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Procesando...' : 'Confirmar'}
          </button>
        </form>

        {mensaje && <p role="alert" className="text-green-600 mt-4">{mensaje}</p>}
        {error && <p role="alert" className="text-red-600 mt-4">{error}</p>}
      </div>
    </div>
  );
};

const HomePaciente = () => {
  // Obtén el nombre y avatar del usuario desde localStorage, contexto o props
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