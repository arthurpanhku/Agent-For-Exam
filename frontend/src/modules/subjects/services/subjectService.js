import { api } from '../../../services/api'

class SubjectService {
  async createSubject(name = null, description = null) {
    const response = await api.post('/api/subjects', {
      name: name || undefined,
      description: description || undefined
    })
    return response
  }

  async getSubjects() {
    const response = await api.get('/api/subjects')
    return response
  }

  async getSubject(subjectId) {
    const response = await api.get(`/api/subjects/${subjectId}`)
    return response
  }

  async getConversationsBySubject(subjectId, statusFilter = null) {
    const params = statusFilter ? { status_filter: statusFilter } : {}
    const response = await api.get(`/api/subjects/${subjectId}/conversations`, { params })
    return response
  }

  async createConversationForSubject(subjectId, title = null, options = {}) {
    const body = { title: title ?? undefined }
    if (options.conversation_type) body.conversation_type = options.conversation_type
    if (options.selected_exam_ids && options.selected_exam_ids.length) body.selected_exam_ids = options.selected_exam_ids
    const response = await api.post(`/api/subjects/${subjectId}/conversations`, body)
    return response
  }

  async updateSubject(subjectId, patch = {}) {
    const body = {}
    for (const key of ['name', 'description', 'dataset_description']) {
      if (Object.prototype.hasOwnProperty.call(patch, key)) {
        body[key] = patch[key]
      }
    }
    return api.patch(`/api/subjects/${subjectId}`, body)
  }

  async deleteSubject(subjectId) {
    await api.delete(`/api/subjects/${subjectId}`)
  }
}

export default new SubjectService()


