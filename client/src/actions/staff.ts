import {
  handleApiError,
  showErrorToast,
  showSuccessToast,
  showLoadingToast,
  updateLoadingToast,
} from "@/utils/errorHandler";
import { apiDelete, apiGet, apiPatch, apiPost } from "./fetchApi";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Types
export interface UserData {
  id?: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  gender?: "M" | "F";
  image?: File | string | null;
  is_active?: boolean;
  role?: string;
  password?: string;
  confirm_password?: string;
}

export interface StaffData {
  id?: number;
  user: number | UserData;
  department: string;
  is_teaching_staff: boolean;
  school?: number;
  created_at?: string;
  updated_at?: string;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: T[];
}

// Helper function to convert form data to the format expected by the API
const prepareStaffData = (data: any): FormData => {
  const formData = new FormData();

  // Handle user data
  if (data.user) {
    Object.entries(data.user).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (key === "image" && value instanceof File) {
          formData.append("user.image", value);
        } else if (key === "password" && value) {
          formData.append("user.password", value as string);
        } else if (key !== "confirm_password") {
          formData.append(`user.${key}`, String(value));
        }
      }
    });
  }

  // Handle staff data
  Object.entries(data).forEach(([key, value]) => {
    if (key !== "user" && value !== undefined && value !== null) {
      formData.append(key, String(value));
    }
  });

  return formData;
};

// Get staff list
export const fetchStaff = async (
  queryParams = ""
): Promise<ApiResponse<StaffData[]>> => {
  const loadingToast = showLoadingToast("Loading staff...");

  try {
    const response = await apiGet(
      `/staff/${queryParams ? `?${queryParams}` : ""}`,
      {
        headers: {
          "Content-Type": "application/json",
        },
        withCredentials: true,
      }
    );

    updateLoadingToast(loadingToast, "success", "Staff loaded successfully");
    console.log("Response from Django API:", response);

    return {
      success: response.success,
      data: response.data,
      count: response.data.length,
      next: response.data.next,
      previous: response.data.previous,
    };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to fetch staff");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

// Get single staff member
export const getStaff = async (id: number): Promise<ApiResponse<StaffData>> => {
  const loadingToast = showLoadingToast("Loading staff details...");

  try {
    const response = await apiGet(`/staff/${id}/`, {
      withCredentials: true,
      headers: {
        "Content-Type": "application/json",
      },
    });

    updateLoadingToast(loadingToast, "success", "Staff details loaded");
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to load staff details");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

// Create new staff
export const createStaff = async (
  data: Partial<StaffData>
): Promise<ApiResponse<StaffData>> => {
  const loadingToast = showLoadingToast("Creating staff member...");
  const formData = prepareStaffData(data);

  try {
    const response = await apiPost(`/staff/`, formData, {
      withCredentials: true,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    showSuccessToast("Staff member created successfully");
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to create staff member");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

// Update staff
export const updateStaff = async (
  id: number,
  data: Partial<StaffData>
): Promise<ApiResponse<StaffData>> => {
  const loadingToast = showLoadingToast("Updating staff member...");
  const formData = prepareStaffData(data);

  try {
    const response = await apiPatch(`/staff/${id}/`, formData, {
      withCredentials: true,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    showSuccessToast("Staff member updated successfully");
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to update staff member");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

// Delete staff
export const deleteStaff = async (id: number): Promise<ApiResponse<null>> => {
  const loadingToast = showLoadingToast("Deleting staff member...");

  try {
    await apiDelete(`/staff/${id}/`, {
      withCredentials: true,
    });

    showSuccessToast("Staff member deleted successfully");
    return { success: true };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to delete staff member");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

// Import staff from file
export const importStaff = async (
  file: File
): Promise<ApiResponse<{ imported: number; failed: number }>> => {
  const loadingToast = showLoadingToast("Importing staff data...");
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await apiPost(`/staff/import/`, formData, {
      withCredentials: true,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    const successMessage =
      `Successfully imported ${response.data.imported_count} staff members` +
      (response.data.failed_count
        ? ` (${response.data.failed_count} failed)`
        : "");

    showSuccessToast(successMessage);

    return {
      success: true,
      data: {
        imported: response.data.imported_count || 0,
        failed: response.data.failed_count || 0,
      },
    };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to import staff data");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

// Export staff data
export const exportStaff = async (queryParams = ""): Promise<Blob | null> => {
  const loadingToast = showLoadingToast("Preparing export...");

  try {
    const response = await apiGet(
      `/staff/export/${queryParams ? `?${queryParams}` : ""}`,
      {
        withCredentials: true,
      }
    );

    showSuccessToast("Export ready");
    return response.data;
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to export staff data");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return null;
  }
};
