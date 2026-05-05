import { api } from '../../../services/api'

export const analyticsService = {
  globalStats: () => api.get('/api/analytics/global'),
  subjectStats: (subjectId) => api.get(`/api/analytics/subjects/${subjectId}`),
}
