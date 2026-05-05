import { api } from '../../../services/api'

const base = (subjectId) => `/api/subjects/${subjectId}/audio-overview`

export const audioOverviewService = {
  get: (subjectId) => api.get(base(subjectId)),
  generate: (subjectId) => api.post(base(subjectId)),
  delete: (subjectId) => api.delete(base(subjectId)),
}
