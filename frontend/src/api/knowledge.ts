import { apiClient, formatApiError } from './client';
import { Fact, ProductionRule, KnowledgeStats } from '../types';

export const knowledgeApi = {
  /**
   * Retrieves network domain facts with optional filtering.
   */
  getFacts: async (category?: string, sourceType?: string): Promise<Fact[]> => {
    try {
      const params: Record<string, string> = {};
      if (category && category !== 'ALL') params.category = category;
      if (sourceType && sourceType !== 'ALL') params.source_type = sourceType;
      const response = await apiClient.get<Fact[]>('/knowledge/facts', { params });
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Retrieves production rules with optional filtering.
   */
  getRules: async (category?: string, classification?: string): Promise<ProductionRule[]> => {
    try {
      const params: Record<string, string> = {};
      if (category && category !== 'ALL') params.category = category;
      if (classification && classification !== 'ALL') params.classification = classification;
      const response = await apiClient.get<ProductionRule[]>('/knowledge/rules', { params });
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },

  /**
   * Retrieves structural graph metrics and summary statistics.
   */
  getStats: async (): Promise<KnowledgeStats> => {
    try {
      const response = await apiClient.get<KnowledgeStats>('/knowledge/stats');
      return response.data;
    } catch (err) {
      throw formatApiError(err);
    }
  },
};

