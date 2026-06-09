const TOKEN_KEY = "wisdomretrieve_token";
const USER_KEY = "wisdomretrieve_user";

// 后期接入后端鉴权时,移除该表并改用 verifyCredentials 调后端接口
const ACCOUNTS: Record<string, string> = {
  admin: "demo666"
};

export function verifyCredentials(username: string, password: string): boolean {
  const u = username.trim();
  const p = password;
  return Boolean(ACCOUNTS[u]) && ACCOUNTS[u] === p;
}

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
