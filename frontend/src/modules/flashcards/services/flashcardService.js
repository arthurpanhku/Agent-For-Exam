import { api } from '../../../services/api'

const base = (subjectId) => `/api/subjects/${subjectId}/flashcards`

export const flashcardService = {
  list: (subjectId) => api.get(base(subjectId)),
  due: (subjectId) => api.get(`${base(subjectId)}/due`),
  stats: (subjectId) => api.get(`${base(subjectId)}/stats`),
  generate: (subjectId, n = 15) => api.post(`${base(subjectId)}/generate`, { n }),
  review: (subjectId, cardId, quality) =>
    api.post(`${base(subjectId)}/${cardId}/review`, { quality }),
  deleteCard: (subjectId, cardId) => api.delete(`${base(subjectId)}/${cardId}`),
  deleteAll: (subjectId) => api.delete(base(subjectId)),
}
