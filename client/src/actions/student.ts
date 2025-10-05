import {
  handleApiError,
  showErrorToast,
  showSuccessToast,
  showLoadingToast,
  updateLoadingToast,
} from "@/utils/errorHandler";
import { apiDelete, apiGet, apiPatch, apiPost } from "./fetchApi";


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
    school?: number;
  }
  

export interface ClassData {
  id: number;
  name: string;
  display_name?: string;
}

export interface StudentData {
  id?: number;
  user: number | UserData; // Can be ID or full user object
  reg_no?: string;
  student_id?: string;
  session_admitted?: string;
  admission_date?: string;
  date_of_birth?: string;
  student_class: string | ClassData; // Can be ID or class object
  school?: number;
  created_at?: string;
  updated_at?: string;
}

export interface StudentFormData {
  user: {
    first_name: string;
    last_name: string;
    email: string;
    phone?: string;
    image?: File | string | null;
  };
  reg_no?: string;
  student_id?: string;
  student_class: string | number;
  admission_date?: string;
  date_of_birth?: string;
  session_admitted?: string;
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

const prepareStudentData = (data: any): FormData => {
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

  // Handle student data
  Object.entries(data).forEach(([key, value]) => {
    if (key !== "user" && value !== undefined && value !== null) {
      formData.append(key, String(value));
    }
  });

  return formData;
};

export const fetchStudents = async (
  queryParams = ""
): Promise<ApiResponse<StudentData[] | any>> => {
  const loadingToast = showLoadingToast("Loading students...");

  try {
    const response = await apiGet(
      `/students/${queryParams ? `?${queryParams}` : ""}`,
      {
        headers: {
          "Content-Type": "application/json",
        },
        withCredentials: true,
      }
    );

    updateLoadingToast(loadingToast, "success", "Students loaded successfully");
    
    return {
      success: true,
      data: response.data,
      count: response.data.length,
      next: response.data.next,
      previous: response.data.previous,
    };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to fetch students");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

export const getStudent = async (id: number): Promise<ApiResponse<StudentData>> => {
  const loadingToast = showLoadingToast("Loading student details...");

  try {
    const response = await apiGet(`/students/${id}/`, {
      withCredentials: true,
      headers: {
        "Content-Type": "application/json",
      },
    });

    updateLoadingToast(loadingToast, "success", "Student details loaded");
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to load student details");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

export const createStudent = async (
  data: Partial<StudentData>
): Promise<ApiResponse<StudentData>> => {
  const loadingToast = showLoadingToast("Creating student...");
  const formData = prepareStudentData(data);

  try {
    const response = await apiPost(`/students/`, formData, {
      withCredentials: true,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    showSuccessToast("Student created successfully");
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to create student");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

export const updateStudent = async (
  id: number,
  data: Partial<StudentData>
): Promise<ApiResponse<StudentData>> => {
  const loadingToast = showLoadingToast("Updating student...");
  const formData = prepareStudentData(data);

  try {
    const response = await apiPatch(`/students/${id}/`, formData, {
      withCredentials: true,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    showSuccessToast("Student updated successfully");
    return { success: true, data: response.data };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to update student");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};

export const deleteStudent = async (id: number): Promise<ApiResponse<null>> => {
  const loadingToast = showLoadingToast("Deleting student...");

  try {
    await apiDelete(`/students/${id}/`, {
      withCredentials: true,
    });

    showSuccessToast("Student deleted successfully");
    return { success: true };
  } catch (error) {
    const errorMessage = handleApiError(error, "Failed to delete student");
    updateLoadingToast(loadingToast, "error", errorMessage);
    return { success: false, error: errorMessage };
  }
};
