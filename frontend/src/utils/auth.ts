const TOKEN_KEY = "wisdomretrieve_token";
const USER_KEY = "wisdomretrieve_user";

export function getAuthToken(): string {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function getAuthUser(): string {
  return localStorage.getItem(USER_KEY) || "";
}

export function setAuthSession(username: string, token: string): void {
  localStorage.setItem(USER_KEY, username.trim());
  localStorage.setItem(TOKEN_KEY, token.trim());
}

export function clearAuthSession(): void {
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getAuthToken());
}
