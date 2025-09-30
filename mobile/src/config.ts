const API = (process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export const API_HTTP = API;                         // http://localhost:8000
export const API_GRAPHQL = process.env.EXPO_PUBLIC_GRAPHQL_URL ?? `${API}/graphql/`;
export const API_AUTH = process.env.EXPO_PUBLIC_AUTH_URL ?? `${API}/api/auth/login/`;
export const API_WS = (API.startsWith("https") ? API.replace(/^https/, "wss")
                                              : API.replace(/^http/, "ws")) + "/ws/";

// Debug logging
console.log("🔧 API Configuration:", { API_HTTP, API_GRAPHQL, API_AUTH, API_WS });
