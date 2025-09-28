const API = (process.env.EXPO_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export const API_HTTP = API;                         // http://riches-reach-alb-...
export const API_GRAPHQL = `${API}/graphql/`;
export const API_WS = (API.startsWith("https") ? API.replace(/^https/, "wss")
                                              : API.replace(/^http/, "ws")) + "/ws/";

// Debug logging
console.log("🔧 API Configuration:", { API_HTTP, API_GRAPHQL, API_WS });
