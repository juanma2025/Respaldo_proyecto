// src/components/Login.jsx
import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [mensaje, setMensaje] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje("");
    setLoading(true);
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}auth/login/`,
        form
      );
      setMensaje("Login exitoso");
      // Aquí puedes guardar el token o datos del usuario si tu backend los retorna
      // Por ejemplo: localStorage.setItem('token', response.data.token);
      // Redirige a la página principal o dashboard
      // navigate('/dashboard');
    } catch (error) {
      if (error.response?.data?.detail) {
        setMensaje(error.response.data.detail);
      } else {
        setMensaje("Correo o contraseña incorrectos");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="w-full max-w-md p-8 rounded-xl shadow-lg bg-white">
        <h2 className="text-3xl font-bold mb-2 text-center text-indigo-700">
          Iniciar Sesión
        </h2>
        <p className="text-center text-gray-700 mb-8">
          Accede a tus citas médicas
        </p>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              {/* Icono de correo */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 12l-4-4-4 4m8 0v6a2 2 0 01-2 2H6a2 2 0 01-2-2v-6m16-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v4"
                />
              </svg>
            </span>
            <input
              type="email"
              name="email"
              placeholder="Tu correo electrónico"
              className="w-full pl-10 pr-3 py-3 rounded-md bg-gray-100 text-gray-700 focus:outline-none"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              {/* Icono de candado */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 11c1.104 0 2-.896 2-2V7a2 2 0 10-4 0v2c0 1.104.896 2 2 2zm6 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2v-6a2 2 0 012-2h8a2 2 0 012 2z"
                />
              </svg>
            </span>
            <input
              type="password"
              name="password"
              placeholder="Ingresa tu contraseña"
              className="w-full pl-10 pr-3 py-3 rounded-md bg-gray-100 text-gray-700 focus:outline-none"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>
          <div className="flex justify-end">
            <a
              href="#"
                className="text-indigo-500 text-sm hover:underline"
            >
                ¿Olvidaste tu contraseña?
            </a>
            </div>
            <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-700 text-white py-3 rounded-md font-semibold text-lg hover:bg-indigo-800 transition"
            >
            {loading ? "Ingresando..." : "Iniciar Sesión"}
            </button>
        </form>
        <div className="mt-6 text-center text-sm text-gray-700">
            ¿Necesitas crear una cuenta?
            <span
            onClick={() => navigate("/register/patient")}
            className="text-indigo-700 ml-1 hover:underline cursor-pointer"
            >
            Crear cuenta
            </span>
        </div>
        {mensaje && (
            <p
            className={`mt-4 text-center ${
                mensaje === "Login exitoso"
                ? "text-green-600"
                : "text-red-500"
            }`}
            >
            {mensaje}
            </p>
        )}
        </div>
    </div>
    );
}