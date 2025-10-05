import axios from "axios";
import { getSession, signOut } from "next-auth/react";
import { handleSignOut, updateSessionWithToken } from "./authHelpers";
import { API_URL, BASE_URL } from "../../config";

const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || BASE_URL, // Base URL for your API
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 5000, // Set timeout to 5 seconds
  // withCredentials: true, // Include cookies in requests
});

axiosInstance.interceptors.request.use(async (config) => {
  const session = await getSession();
  const sessionAccessToken = session?.user?.accessToken;

  if (sessionAccessToken) {
    config.headers["Authorization"] = `Bearer ${sessionAccessToken}`;
  }

  return config;
});

let isRefreshing = false; // To avoid multiple refresh calls
let failedQueue = []; // Queue for retrying failed requests

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if the error is 401 and the request has not been retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
        // If already refreshing, queue the request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers["Authorization"] = `Bearer ${token}`;
            return axiosInstance(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      isRefreshing = true;

      try {
        const session = await getSession();
        const sessionAccessToken = session?.user?.accessToken;

        if (session && session?.user && session?.user?.accessToken) {
          console.log(session);
          originalRequest.headers[
            "Authorization"
          ] = `Bearer ${sessionAccessToken}`;
          processQueue(null, sessionAccessToken);
          // console.log("sessionAccessToken", sessionAccessToken);
        } else {
          // Call the refresh token endpoint
          const refreshResponse = await axios.post(
            "/api/auth/refresh",
            {},
            { withCredentials: true }
          );
          // console.log("refreshResponse", refreshResponse);

          const { accessToken } = refreshResponse.data;
          processQueue(null, accessToken);
          originalRequest.headers["Authorization"] = `Bearer ${accessToken}`;
        }

        // updateSessionWithToken(accessToken);

        return await axiosInstance(originalRequest);
      } catch (refreshError) {
        console.log("An error occurred: ", refreshError);
        // alert("error");
        processQueue(refreshError, null);
        await handleSignOut(); // Log the user out if token refresh fails
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
