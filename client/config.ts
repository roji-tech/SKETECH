const LIVE_API_URL = "https://crystone.onrender.com/api/v1";

const LOCAL_API_URL = "http://localhost:8000/api/v1";

export const API_URL =
  process.env.NODE_ENV === "production" ? LIVE_API_URL : LOCAL_API_URL;

const LIVE_BASE_URL = "https://crystone.onrender.com";

const LOCAL_BASE_URL = "http://localhost:8000";

export const BASE_URL =
  process.env.NODE_ENV === "production" ? LIVE_BASE_URL : LOCAL_BASE_URL;
