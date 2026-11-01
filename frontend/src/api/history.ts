import { apiClient, formatApiError } from './client';
import { SessionListResponse, SessionDetailResponse } from '../types';

export const historyApi = {
  /**
   * Retrieves a paginated list of historical sessions.
   */
  listSessions: async (
    skip: number = 0,
    limit: number = 20,
    status?: string
  ): Promise<SessionListResponse> => {
    try {
      const params: Record<string, any> = { skip, limit };
      if (status && status !== 'ALL') {
        params.status = status;
      }
      const response = await apiClient.get<SessionListResponse>('/history', { params });
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Retrieves full audit details for a specific session.
   */
  getSessionDetail: async (sessionId: string): Promise<SessionDetailResponse> => {
    try {
      const response = await apiClient.get<SessionDetailResponse>(`/history/${sessionId}`);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Deletes a session and its associated answers, traces, and recommendations.
   */
  deleteSession: async (sessionId: string): Promise<{ message: string; deleted_id: string }> => {
    try {
      const response = await apiClient.delete<{ message: string; deleted_id: string }>(`/history/${sessionId}`);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },
};

