import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

interface LoginResponse {
  token: string;
  userId: number;
  name: string;
  email: string;
  role: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = 'https://localhost:7272/api/Auth';
  private readonly tokenKey = 'library_token';

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.apiUrl}/login`, {
        email,
        password
      })
      .pipe(
        tap((response) => {
          localStorage.setItem(this.tokenKey, response.token);
        })
      );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isLoggedIn(): boolean {
    const token = this.getToken();

    if (!token) {
      return false;
    }

    try {
      const payload = this.decodeToken(token);

      if (!payload.exp) {
        return true;
      }

      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  getRole(): string {
    const token = this.getToken();

    if (!token) {
      return '';
    }

    try {
      const payload = this.decodeToken(token);

      return (
        payload.role ||
        payload[
          'http://schemas.microsoft.com/ws/2008/06/identity/claims/role'
        ] ||
        ''
      );
    } catch {
      return '';
    }
  }

  isAdmin(): boolean {
    return this.getRole().toLowerCase() === 'admin';
  }

  private decodeToken(token: string): any {
    const payload = token.split('.')[1];

    const normalized = payload
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const decoded = decodeURIComponent(
      atob(normalized)
        .split('')
        .map(
          (character) =>
            '%' +
            ('00' + character.charCodeAt(0).toString(16)).slice(-2)
        )
        .join('')
    );

    return JSON.parse(decoded);
  }
}