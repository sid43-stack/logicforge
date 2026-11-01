import axios, { AxiosError } from 'axios';
import { ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const formatApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    if (axiosError.response?.data) {
      const data = axiosError.response.data;
      return {
        detail: typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || 'An unexpected server error occurred.'),
        error_code: data.error_code || `HTTP_${axiosError.response.status}`,
        status_code: axiosError.response.status,
      };
    }
    if (axiosError.request) {
      return {
        detail: 'Unable to connect to the NetSage backend service. Please ensure the backend server is running on http://localhost:8000.',
        error_code: 'NETWORK_ERROR',
        status_code: 0,
      };
    }
  }
  return {
    detail: (error as Error)?.message || 'An unknown error occurred.',
    error_code: 'UNKNOWN_ERROR',
    status_code: 500,
  };
};

