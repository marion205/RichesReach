// Import from single source of truth
import { API_HTTP, API_GRAPHQL, API_AUTH, API_WS } from './api';

// Re-export for other modules
export { API_HTTP, API_GRAPHQL, API_AUTH, API_WS };

// Debug logging
console.log("🔧 API Configuration:", { API_HTTP, API_GRAPHQL, API_AUTH, API_WS });
