import { Route, BrowserRouter as Router, Routes, useNavigate } from 'react-router-dom';
import RegistrarMedico from './components/DoctorRegister';
import IniciarSesion from './components/Login';
import RegistrarPaciente from './components/PatientRegister';
import HomePaciente from './components/HomePaciente';
import HomeDoctor from './components/HomeDoctor';


function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-800 via-slate-900 to-gray-950 p-6 flex flex-col items-center justify-center">
      <h1 className="text-4xl md:text-5xl text-white font-bold text-center mt-9 mb-4 drop-shadow-lg">Plataforma Citas Médica</h1>
      <nav className="flex flex-col md:flex-row justify-center gap-4 mt-6">
        <button
          onClick={() => navigate("/auth/login/")}
          className="flex items-center gap-2 bg-cyan-700 text-white px-6 py-3 rounded-xl hover:bg-cyan-600 transition-all duration-300 shadow-lg hover:scale-105"
        >
          Iniciar Sesión 
        </button>
        <button
          onClick={() => navigate("/auth/register/patient/")}
          className="flex items-center gap-2 bg-cyan-700 text-white px-6 py-3 rounded-xl hover:bg-cyan-600 transition-all duration-300 shadow-lg hover:scale-105"
        >
          Registrar Paciente
        </button>
        <button
          onClick={() => navigate("/auth/register/doctor/")}
          className="flex items-center gap-2 bg-indigo-700 text-white px-6 py-3 rounded-xl hover:bg-indigo-600 transition-all duration-300 shadow-lg hover:scale-105"
        >
          Registrar Médico
        </button>
      </nav>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth/login/" element={<IniciarSesion />} />
        <Route path="/auth/register/patient/" element={<RegistrarPaciente />} />
        <Route path="/auth/register/doctor/" element={<RegistrarMedico />} />
        <Route path="/appointments/create/" element={<HomePaciente />} />
        <Route path="/appointments/doctor/" element={<HomeDoctor />} />
      </Routes>
    </Router>
  );
}

export default App;

