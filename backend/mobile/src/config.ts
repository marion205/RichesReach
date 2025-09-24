import Constants from "expo-constants";

// Production server (AWS)
const PROD = "https://54.226.87.216";

// Local development servers
const IOS_SIM = "http://127.0.0.1:8000";
const ANDROID_EMU = "http://10.0.2.2:8000";
const LAN = "http://192.168.1.151:8000"; // Your Mac's IP from the terminal

// Use local production server (full backend with all resolvers)
export const API_BASE = IOS_SIM;

// Alternative: Use local server based on platform
// export const API_BASE = Constants.platform?.ios ? IOS_SIM : ANDROID_EMU;

console.log("🔗 API_BASE configured as:", API_BASE);
