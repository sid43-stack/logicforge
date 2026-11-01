import { apiClient, formatApiError } from './client';
import {
  StartSessionResponse,
  AnswerResponse,
  Question,
  DiagnosticResult,
  ExplanationResponse,
} from '../types';

export const diagnosticsApi = {
  /**
   * Starts a new diagnostic session.
   */
  startSession: async (initialFacts?: Record<string, any>): Promise<StartSessionResponse> => {
    try {
      const payload = initialFacts ? { initial_facts: initialFacts } : {};
      const response = await apiClient.post<StartSessionResponse>('/diagnostics/start', payload);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Submits an answer to the current active question.
   */
  submitAnswer: async (
    sessionId: string,
    questionId: string,
    answer: 'YES' | 'NO' | 'UNKNOWN'
  ): Promise<AnswerResponse> => {
    try {
      const response = await apiClient.post<AnswerResponse>(`/diagnostics/${sessionId}/answer`, {
        question_id: questionId,
        answer,
      });
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Gets the active question with its dynamic WHY explanation for an in-progress session.
   */
  getCurrentQuestion: async (sessionId: string): Promise<Question> => {
    try {
      const response = await apiClient.get<Question>(`/diagnostics/${sessionId}/question`);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Retrieves the confirmed diagnosis and remediation plan for a completed session.
   */
  getResult: async (sessionId: string): Promise<DiagnosticResult> => {
    try {
      const response = await apiClient.get<DiagnosticResult>(`/diagnostics/${sessionId}/result`);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Retrieves the comprehensive HOW explanation and DAG inference tree.
   */
  getExplanation: async (sessionId: string): Promise<ExplanationResponse> => {
    try {
      const response = await apiClient.get<ExplanationResponse>(`/diagnostics/${sessionId}/explanation`);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Resets an existing diagnostic session to scratch.
   */
  restartSession: async (sessionId: string): Promise<StartSessionResponse> => {
    try {
      const response = await apiClient.post<StartSessionResponse>(`/diagnostics/${sessionId}/restart`);
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },
};

