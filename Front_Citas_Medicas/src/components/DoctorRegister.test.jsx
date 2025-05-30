import { render, screen, fireEvent } from '@testing-library/react';
import CrearMedico from './DoctorRegister';
import { describe, vi } from 'vitest';

describe("DoctorRegister Component", () => {
    beforeEach(() => {
    vi.clearAllMocks();
    });

    test("renders the form with all fields and submit button", () => {
    render(<CrearMedico />);
    expect(screen.getByPlaceholderText("Nombre completo")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Especialidad")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Cédula profesional")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Correo electrónico")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Registrarme" })).toBeInTheDocument();
    });

    test("shows error if terms are not accepted", async () => {
    render(<CrearMedico />);
    fireEvent.change(screen.getByPlaceholderText("Nombre completo"), { 
        target: { value: "Dr. Juan" },
    });

    fireEvent.change(screen.getByPlaceholderText("Especialidad"), { 
        target: { value: "Cardiología" } 
    });

    fireEvent.change(screen.getByPlaceholderText("Cédula profesional"), { 
        target: { value: "123456" } 
    });

    fireEvent.change(screen.getByPlaceholderText("Correo electrónico"), { 
        target: { value: "juanmatabanchoy@mail.com" } 
    });

    fireEvent.click(screen.getByRole("button", { name: "Registrarme" }));

    expect(await screen.findByText(/Debes aceptar los términos/i)).toBeInTheDocument();
    });
});