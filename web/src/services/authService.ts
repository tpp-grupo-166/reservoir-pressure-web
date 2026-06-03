import { getToken, setToken, removeToken } from '../utils/auth';

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  email: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

async function handleResponse(res: Response): Promise<never> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    detail = body.detail ?? detail;
  } catch {
    /* respuesta sin JSON */
  }
  throw new Error(detail);
}

export async function register(data: RegisterData): Promise<void> {
  const res = await fetch('/api/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) return handleResponse(res);
}

export async function login(data: LoginData): Promise<string> {
  const res = await fetch('/api/auth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) return handleResponse(res);
  
  const tokenData: LoginResponse = await res.json();
  setToken(tokenData.access_token);
  return tokenData.access_token;
}

export async function getCurrentUser(): Promise<User> {
  const token = getToken();
  if (!token) {
    throw new Error('No token found');
  }
  
  const res = await fetch('/api/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!res.ok) return handleResponse(res);
  
  return res.json();
}

export function logout(): void {
  removeToken();
}
