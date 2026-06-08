import type { StaticProps } from '../types';

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

const MIN_PASSWORD_LENGTH = 8;

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidPasswordLength(password: string): boolean {
  return password.length >= MIN_PASSWORD_LENGTH;
}

export function isValidPasswordComplexity(password: string): boolean {
  const hasLetter = /[a-zA-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  return hasLetter && hasNumber;
}

export function validateRegistration(email: string, password: string): ValidationResult {
  const errors: ValidationError[] = [];

  if (!email || email.trim() === '') {
    errors.push({ field: 'email', message: 'El email es obligatorio' });
  } else if (!isValidEmail(email)) {
    errors.push({ field: 'email', message: 'El formato del email no es válido' });
  }

  if (!password || password.trim() === '') {
    errors.push({ field: 'password', message: 'La contraseña es obligatoria' });
  } else if (!isValidPasswordLength(password)) {
    errors.push({ field: 'password', message: `La contraseña debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres` });
  } else if (!isValidPasswordComplexity(password)) {
    errors.push({ field: 'password', message: 'La contraseña debe incluir letras y números' });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/** Rangos físicos de las propiedades del reservorio (paso 1 del wizard). */
export function validateStaticProps(p: StaticProps): ValidationError[] {
  const errors: ValidationError[] = [];
  const positive = (v: number) => Number.isFinite(v) && v > 0;

  if (!(Number.isFinite(p.porosidad) && p.porosidad > 0 && p.porosidad < 1)) {
    errors.push({ field: 'porosidad', message: 'La porosidad debe estar entre 0 y 1' });
  }
  if (!positive(p.permeabilidad_mD)) {
    errors.push({ field: 'permeabilidad_mD', message: 'La permeabilidad debe ser mayor a 0' });
  }
  if (!positive(p.espesor_neto_m)) {
    errors.push({ field: 'espesor_neto_m', message: 'El espesor neto debe ser mayor a 0' });
  }
  if (!positive(p.area_m2)) {
    errors.push({ field: 'area_m2', message: 'El área debe ser mayor a 0' });
  }
  if (!positive(p.presion_inicial_psi)) {
    errors.push({ field: 'presion_inicial_psi', message: 'La presión inicial debe ser mayor a 0' });
  }
  return errors;
}

export function validateLogin(email: string, password: string): ValidationResult {
  const errors: ValidationError[] = [];

  if (!email || email.trim() === '') {
    errors.push({ field: 'email', message: 'El email es obligatorio' });
  } else if (!isValidEmail(email)) {
    errors.push({ field: 'email', message: 'El formato del email no es válido' });
  }

  if (!password || password.trim() === '') {
    errors.push({ field: 'password', message: 'La contraseña es obligatoria' });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}
