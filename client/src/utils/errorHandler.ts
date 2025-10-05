import { toast } from 'react-hot-toast';
import { AxiosError } from 'axios';

interface ApiErrorResponse {
  message?: string;
  error?: string;
  errors?: {
    [key: string]: string[] | string;
  };
  detail?: string;
}

export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export const handleApiError = (error: unknown, defaultMessage = 'An error occurred'): string => {
  console.error('API Error:', error);
  
  // Handle Axios errors
  if (typeof error === 'object' && error !== null && 'isAxiosError' in error) {
    const axiosError = error as AxiosError<ApiErrorResponse>;
    
    // Handle network errors
    if (axiosError.code === 'ERR_NETWORK') {
      return 'Network error. Please check your connection and try again.';
    }
    
    // Handle HTTP errors with response data
    if (axiosError.response) {
      const { data, status } = axiosError.response;
      
      // Handle validation errors (422)
      if (status === 422 && data.errors) {
        const errorMessages = Object.entries(data.errors)
          .map(([field, messages]) => {
            const fieldName = field.split('.').pop(); // Get the last part of nested field names
            const messageList = Array.isArray(messages) ? messages.join(' ') : messages;
            return `${fieldName ? `${fieldName}: ` : ''}${messageList}`;
          })
          .join('\n');
        return errorMessages || 'Validation failed. Please check your input.';
      }
      
      // Handle other HTTP errors with a message
      if (data.message || data.error || data.detail) {
        return (data.message || data.error || data.detail) as string;
      }
    }
  }
  
  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }
  
  // Handle Error objects
  if (error instanceof Error) {
    return error.message || defaultMessage;
  }
  
  // Fallback to default message
  return defaultMessage;
};

export const showErrorToast = (error: unknown, defaultMessage = 'An error occurred') => {
  const message = handleApiError(error, defaultMessage);
  toast.error(message, { duration: 5000 });
  return message;
};

export const showSuccessToast = (message: string) => {
  toast.success(message, { duration: 3000 });
};

export const showLoadingToast = (message: string) => {
  return toast.loading(message, { duration: 3000 });
};

export const updateLoadingToast = (toastId: string, type: 'success' | 'error' | 'loading', message: string) => {
  if (type === 'success') {
    toast.success(message, { id: toastId });
  } else if (type === 'error') {
    toast.error(message, { id: toastId });
  } else {
    toast.loading(message, { id: toastId });
  }
};

export const dismissToast = (toastId: string) => {
  toast.dismiss(toastId);
};
