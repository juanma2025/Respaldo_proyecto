import React, { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = "http://localhost:8000/api/appointments"; // Cambia según tu backend

function formatDate(date) {
  return date.toISOString().split("T")[0];
}

function formatTime(time) {
  return time.length === 5 ? `${time}:00` : time;
}

export default function HomeDoctor() {
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const [unavailabilities, setUnavailabilities] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [selectedRange, setSelectedRange] = useState({
    start_date: "",
    end_date: "",
    start_time: "",
    end_time: "",
    reason: "",
  });
  const [conflicts, setConflicts] = useState([]);
  const [showConflict, setShowConflict] = useState(false);
  const [forceBlock, setForceBlock] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // Cargar indisponibilidades y citas del mes
  useEffect(() => {
    fetchUnavailabilities();
    fetchAppointments();
    // eslint-disable-next-line
  }, [calendarMonth]);

  const fetchUnavailabilities = async () => {
    try {
      const res = await axios.get(`${API_BASE}/unavailable/list/`, {
        withCredentials: true,
      });
      setUnavailabilities(res.data);
    } catch (err) {
      setUnavailabilities([]);
    }
  };

  const fetchAppointments = async () => {
    try {
      const year = calendarMonth.getFullYear();
      const month = String(calendarMonth.getMonth() + 1).padStart(2, "0");
      const res = await axios.get(
        `${API_BASE}/doctor/?date_from=${year}-${month}-01`,
        { withCredentials: true }
      );
      setAppointments(res.data);
    } catch (err) {
      setAppointments([]);
    }
  };

  // Navegación de mes
  const changeMonth = (delta) => {
    const newMonth = new Date(calendarMonth);
    newMonth.setMonth(newMonth.getMonth() + delta);
    setCalendarMonth(newMonth);
  };

  // Manejo de inputs
  const handleInput = (e) => {
    setSelectedRange({ ...selectedRange, [e.target.name]: e.target.value });
  };

  // Verificar conflictos antes de bloquear
  const checkConflicts = async () => {
    setLoading(true);
    setMessage("");
    setConflicts([]);
    setShowConflict(false);
    const body = {
      ...selectedRange,
      start_time: formatTime(selectedRange.start_time),
      end_time: formatTime(selectedRange.end_time),
    };
    try {
      const res = await axios.post(
        `${API_BASE}/unavailable/check-conflicts/`,
        body,
        { withCredentials: true }
      );
      if (res.data.has_conflicts) {
        setConflicts(res.data.conflicting_appointments);
        setShowConflict(true);
      } else {
        setShowConflict(false);
        setConflicts([]);
        setMessage("No hay conflictos. Puedes bloquear el rango.");
      }
    } catch (err) {
      setMessage("Error al verificar conflictos.");
    }
    setLoading(false);
  };

  // Bloquear rango de fechas
  const blockRange = async () => {
    setLoading(true);
    setMessage("");
    const body = {
      ...selectedRange,
      start_time: formatTime(selectedRange.start_time),
      end_time: formatTime(selectedRange.end_time),
      force_block: forceBlock,
    };
    try {
      const res = await axios.post(`${API_BASE}/unavailable/range/`, body, {
        withCredentials: true,
      });
      if (res.status === 201) {
        setMessage("Indisponibilidad marcada exitosamente.");
        setShowConflict(false);
        setForceBlock(false);
        fetchUnavailabilities();
        fetchAppointments();
      }
    } catch (err) {
      if (
        err.response &&
        err.response.status === 409 &&
        err.response.data.existing_appointments
      ) {
        setConflicts(err.response.data.existing_appointments);
        setShowConflict(true);
        setMessage(
          err.response.data.warning || err.response.data.message || ""
        );
      } else {
        setMessage(
          (err.response && err.response.data.error) ||
            "Error al bloquear el rango."
        );
      }
    }
    setLoading(false);
  };

  // Desbloquear horario
  const removeUnavailability = async (id) => {
    if (!window.confirm("¿Seguro que deseas desbloquear este horario?")) return;
    setLoading(true);
    try {
      await axios.delete(`${API_BASE}/unavailable/${id}/`, {
        withCredentials: true,
      });
      setMessage("Horario desbloqueado.");
      fetchUnavailabilities();
      fetchAppointments();
    } catch (err) {
      setMessage("Error al desbloquear el horario.");
    }
    setLoading(false);
  };

  // Renderizar calendario simple
  const renderCalendar = () => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const weeks = [];
    let day = 1 - firstDay;
    for (let w = 0; w < 6; w++) {
      const week = [];
      for (let d = 0; d < 7; d++, day++) {
        if (day < 1 || day > daysInMonth) {
          week.push(<td key={d}></td>);
        } else {
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const isUnavailable = unavailabilities.some(
            (u) => u.date === dateStr
          );
          const hasAppointment = appointments.some(
            (a) => a.appointment_date === dateStr
          );
          week.push(
            <td
              key={d}
              className={`p-2 rounded-lg text-center cursor-pointer ${
                isUnavailable
                  ? "bg-red-200 text-red-700"
                  : hasAppointment
                  ? "bg-blue-100"
                  : "hover:bg-gray-100"
              }`}
              title={
                isUnavailable
                  ? "Horario bloqueado"
                  : hasAppointment
                  ? "Citas programadas"
                  : ""
              }
            >
              {day}
            </td>
          );
        }
      }
      weeks.push(<tr key={w}>{week}</tr>);
    }
    return weeks;
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-white border-r p-4">
        <h1 className="text-2xl font-bold mb-6">AgendaMed</h1>
        <nav className="flex flex-col gap-2">
          <span className="font-semibold text-indigo-600">Gestión de Horarios</span>
          <span className="text-gray-600">Bloqueo de Agenda</span>
          <span className="text-gray-600">Historial de Citas</span>
        </nav>
        <div className="mt-10 flex items-center gap-2">
          <img
            src="https://randomuser.me/api/portraits/med/men/1.jpg"
            alt="Doctor"
            className="w-10 h-10 rounded-full"
          />
          <div>
            <div className="font-semibold">Doctor</div>
            <div className="text-xs text-gray-500">Ver perfil</div>
          </div>
        </div>
      </aside>
      {/* Main */}
      <main className="flex-1 p-6">
        <div className="flex items-center gap-4 mb-4">
          <button
            className="p-2 rounded hover:bg-gray-200"
            onClick={() => changeMonth(-1)}
          >
            &lt;
          </button>
          <span className="font-semibold">
            {calendarMonth.toLocaleString("default", { month: "long", year: "numeric" })}
          </span>
          <button
            className="p-2 rounded hover:bg-gray-200"
            onClick={() => changeMonth(1)}
          >
            &gt;
          </button>
        </div>
        {/* Calendario */}
        <table className="w-full mb-6">
          <thead>
            <tr className="text-indigo-600">
              <th>Lun</th>
              <th>Mar</th>
              <th>Mié</th>
              <th>Jue</th>
              <th>Vie</th>
              <th>Sáb</th>
              <th>Dom</th>
            </tr>
          </thead>
          <tbody>{renderCalendar()}</tbody>
        </table>
        {/* Formulario de bloqueo */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h2 className="font-semibold mb-2">Bloquear rango de fechas y horas</h2>
          <div className="flex flex-wrap gap-2">
            <input
              type="date"
              name="start_date"
              value={selectedRange.start_date}
              onChange={handleInput}
              className="border rounded p-2"
              min={formatDate(new Date())}
            />
            <input
              type="date"
              name="end_date"
              value={selectedRange.end_date}
              onChange={handleInput}
              className="border rounded p-2"
              min={selectedRange.start_date || formatDate(new Date())}
            />
            <input
              type="time"
              name="start_time"
              value={selectedRange.start_time}
              onChange={handleInput}
              className="border rounded p-2"
            />
            <input
              type="time"
              name="end_time"
              value={selectedRange.end_time}
              onChange={handleInput}
              className="border rounded p-2"
            />
            <input
              type="text"
              name="reason"
              value={selectedRange.reason}
              onChange={handleInput}
              className="border rounded p-2 flex-1"
              placeholder="Motivo (opcional)"
            />
            <button
              className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600"
              onClick={checkConflicts}
              disabled={loading}
            >
              Verificar Conflictos
            </button>
            <button
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              onClick={blockRange}
              disabled={loading}
            >
              Bloquear
            </button>
            {showConflict && (
              <label className="flex items-center gap-1 ml-2">
                <input
                  type="checkbox"
                  checked={forceBlock}
                  onChange={() => setForceBlock(!forceBlock)}
                />
                Forzar bloqueo
              </label>
            )}
          </div>
          {loading && <div className="text-gray-500 mt-2">Cargando...</div>}
          {message && <div className="mt-2 text-indigo-600">{message}</div>}
          {showConflict && conflicts.length > 0 && (
            <div className="mt-4 bg-yellow-100 border-l-4 border-yellow-500 p-3 rounded">
              <div className="font-semibold text-yellow-700 mb-2">
                Conflicto con citas programadas:
              </div>
              <ul className="text-sm">
                {conflicts.map((c, i) => (
                  <li key={i}>
                    {c.date} {c.time} - Paciente: {c.patient_name || c.patient} - Motivo: {c.reason}
                  </li>
                ))}
              </ul>
              <div className="text-xs text-gray-600 mt-2">
                Marca "Forzar bloqueo" para continuar y bloquear el horario.
              </div>
            </div>
          )}
        </div>
        {/* Lista de horarios bloqueados */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h2 className="font-semibold mb-2">Horarios bloqueados</h2>
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Motivo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {unavailabilities.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-gray-400">
                    No hay horarios bloqueados.
                  </td>
                </tr>
              )}
              {unavailabilities.map((u) => (
                <tr key={u.id}>
                  <td>{u.date}</td>
                  <td>{u.start_time}</td>
                  <td>{u.end_time}</td>
                  <td>{u.reason}</td>
                  <td>
                    <button
                      className="text-red-500 hover:underline"
                      onClick={() => removeUnavailability(u.id)}
                    >
                      Desbloquear
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Lista de citas del mes */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-2">Citas programadas</h2>
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Paciente</th>
                <th>Motivo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {appointments.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-gray-400">
                    No hay citas programadas.
                  </td>
                </tr>
              )}
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td>{a.appointment_date}</td>
                  <td>{a.appointment_time}</td>
                  <td>{a.patient_info?.user?.full_name || a.patient_info?.user?.username}</td>
                  <td>{a.reason}</td>
                  <td>{a.status_display}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}