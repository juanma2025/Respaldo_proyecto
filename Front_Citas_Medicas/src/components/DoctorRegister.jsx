import axios from "axios";
import { useState } from "react";
import { FaEnvelope, FaUser, FaIdCard, FaStethoscope } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

const CrearMedico = () => {
  const [formData, setFormData] = useState({
    full_name: "",
    specialty: "",
    professional_license: "",
    email: "",
  });

  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje(null);
    setError(null);

    if (!aceptaTerminos) {
      setError("Debes aceptar los términos y condiciones.");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}auth/register/doctor/`,
        formData
      );
      setMensaje("Registro exitoso. Revisa tu correo para tus credenciales.");
      setFormData({
        full_name: "",
        specialty: "",
        professional_license: "",
        email: "",
      });
      setAceptaTerminos(false);
    } catch (err) {
      if (err.response?.data) {
        const data = err.response.data;
        const firstError = Object.values(data)[0];
        setError(Array.isArray(firstError) ? firstError[0] : firstError);
      } else {
        setError("Ocurrió un error al intentar registrar.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white shadow-lg rounded-xl">
      <h2 className="text-2xl font-bold text-center text-indigo-600 mb-2">
        Registrar Médico
      </h2>
      <p className="text-center text-gray-700 mb-4">
        Completa el formulario para crear tu cuenta
      </p>

      {mensaje && (
        <p className="text-green-600 text-center mb-4">{mensaje}</p>
      )}
      {error && <p className="text-red-600 text-center mb-4">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField
          icon={<FaUser />}
          name="full_name"
          type="text"
          placeholder="Nombre completo"
          value={formData.full_name}
          onChange={handleChange}
        />
        <InputField
          icon={<FaStethoscope />}
          name="specialty"
          type="text"
          placeholder="Especialidad"
          value={formData.specialty}
          onChange={handleChange}
        />
        <InputField
          icon={<FaIdCard />}
          name="professional_license"
          type="text"
          placeholder="Cédula profesional"
          value={formData.professional_license}
          onChange={handleChange}
        />
        <InputField
          icon={<FaEnvelope />}
          name="email"
          type="email"
          placeholder="Correo electrónico"
          value={formData.email}
          onChange={handleChange}
        />

        <div className="flex items-center text-sm">
          <input
            type="checkbox"
            checked={aceptaTerminos}
            onChange={(e) => setAceptaTerminos(e.target.checked)}
            className="mr-2"
          />
          <span>
            Acepto los{" "}
            <a href="#" className="text-blue-600 underline">
              Términos y Condiciones
            </a>
          </span>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-700 hover:bg-indigo-800 text-white py-2 rounded-xl font-semibold transition"
        >
          {loading ? "Registrando..." : "Registrarme"}
        </button>

        <p className="text-center text-gray-700 mt-4">
          ¿Ya tienes una cuenta?{" "}
          <span
            onClick={() => navigate("/login-medico")}
            className="text-blue-600 underline cursor-pointer"
          >
            Iniciar sesión
          </span>
        </p>
      </form>
    </div>
  );
};

const InputField = ({ icon, ...props }) => (
  <div className="relative">
    <span className="absolute left-3 top-3 text-gray-400">{icon}</span>
    <input
      {...props}
      className="w-full pl-10 pr-4 py-2 border rounded-xl bg-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      required
    />
  </div>
);

export default CrearMedico;