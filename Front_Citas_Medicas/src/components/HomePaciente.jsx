import axios from 'axios';
import React, { useEffect, useState } from 'react';

const AgendarCita = ({ apiUrl = import.meta.env.VITE_API_URL }) => {
  const [especialidades, setEspecialidades] = useState([]);
  const [medicos, setMedicos] = useState([]);
  const [selectedEspecialidad, setSelectedEspecialidad] = useState('');
  const [selectedMedico, setSelectedMedico] = useState('');
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Cargar especialidades
  useEffect(() => {
    const fetchEspecialidades = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get(`${apiUrl}especialidades/`);
        setEspecialidades(response.data);
      } catch (err) {
        setError('Error al cargar las especialidades');
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
          const response = await axios.get(
            `${apiUrl}medicos/?especialidad=${selectedEspecialidad}`
          );
          setMedicos(response.data);
          setSelectedMedico('');
        } catch (err) {
          setError('Error al cargar los médicos');
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
      doctor: selectedMedico,
      appointment_date: fecha,
      appointment_time: hora,
    };

    try {
      const response = await axios.post(
        `${apiUrl}agendar_cita/`,
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
    <div className="max-w-md mx-auto mt-10 p-6 bg-white shadow-lg rounded-xl">
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
            {especialidades.map((esp) => (
              <option key={esp.id} value={esp.id}>
                {esp.nombre}
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
            {medicos.map((medico) => (
              <option key={medico.id} value={medico.id}>
                {medico.user?.full_name || medico.user?.first_name + " " + medico.user?.last_name}
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
  );
};

export default AgendarCita;