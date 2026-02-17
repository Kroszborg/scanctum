export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("scanctum_token");
}

export function setToken(token: string): void {
  localStorage.setItem("scanctum_token", token);
}

export function removeToken(): void {
  localStorage.removeItem("scanctum_token");
  localStorage.removeItem("scanctum_user");
}

export function getUser(): { id: string; email: string; full_name: string; role: string } | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("scanctum_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setUser(user: object): void {
  localStorage.setItem("scanctum_user", JSON.stringify(user));
}
