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
