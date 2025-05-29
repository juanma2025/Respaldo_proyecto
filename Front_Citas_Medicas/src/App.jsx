import React from "react";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RegistrarPaciente from './components/PatientRegister';
import RegistrarMedico from './components/DoctorRegister';
import IniciarSesion from './components/Login'


function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-800 via-slate-900 to-gray-950 p-6 flex flex-col items-center justify-center">
        <h1 className="text-4xl md:text-5xl text-white font-bold text-center mt-9 mb-4 drop-shadow-lg">Plataforma Citas Médica</h1>

        <nav className="flex flex-col md:flex-row justify-center gap-4 mt-6">
          
            <button
            onClick={() => (window.location.href = "auth/login/")}
            className="flex items-center gap-2 bg-cyan-700 text-white px-6 py-3 rounded-xl hover:bg-cyan-600 transition-all duration-300 shadow-lg hover:scale-105"
          >
            Iniciar Sesión 
          </button>

          <button
            onClick={() => (window.location.href = "auth/register/patient/")}
            className="flex items-center gap-2 bg-cyan-700 text-white px-6 py-3 rounded-xl hover:bg-cyan-600 transition-all duration-300 shadow-lg hover:scale-105"
          >
            Registrar Paciente
          </button>

          <button
            onClick={() => (window.location.href = "auth/register/doctor/")}
            className="flex items-center gap-2 bg-indigo-700 text-white px-6 py-3 rounded-xl hover:bg-indigo-600 transition-all duration-300 shadow-lg hover:scale-105"
          >
            Registrar Médico
          </button>


        </nav>
        <div className="mt-8 w-full max-w-3xl">
          <Routes>
          <Route path="auth/register/patient/" element={<RegistrarPaciente />} />
          <Route path="auth/register/doctor/" element={<RegistrarMedico />} />
          <Route path="auth/login/" element={<IniciarSesion />} />

        </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

