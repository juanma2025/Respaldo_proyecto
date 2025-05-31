import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import HomePaciente from './HomePaciente';

// Mock localStorage
beforeAll(() => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn((key) => {
      if (key === 'user_full_name') return 'Juan';
      if (key === 'user_avatar') return 'avatar.jpg';
      if (key === 'auth_token') return 'token';
      return null;
    }),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  });
});

describe('HomePaciente', () => {
  it('muestra los botones del sidebar', () => {
    render(<HomePaciente />);
    expect(screen.getByText('Mis Citas')).toBeInTheDocument();
    expect(screen.getByText('Agendar Citas')).toBeInTheDocument();
    expect(screen.getByText('Cancelar Citas')).toBeInTheDocument();
    expect(screen.getByText('Configuración')).toBeInTheDocument();
  });

  it('cambia de sección al hacer clic en los botones', () => {
    render(<HomePaciente />);
    fireEvent.click(screen.getByText('Agendar Citas'));
    expect(screen.getByText('Agendar Cita')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Cancelar Citas'));
    expect(screen.getByText('Cancelar Citas')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Configuración'));
    expect(screen.getByText('Configuración')).toBeInTheDocument();
  });
});