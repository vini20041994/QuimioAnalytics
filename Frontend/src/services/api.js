const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const API_PREFIX = '/api/v1'

function buildUrl(path, query = {}) {
  const base = `${API_BASE_URL}${API_PREFIX}${path}`
  const params = new URLSearchParams()

  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value))
    }
  })

  const queryString = params.toString()
  return queryString ? `${base}?${queryString}` : base
}

async function request(path, options = {}, query = {}) {
  const response = await fetch(buildUrl(path, query), options)
  if (!response.ok) {
    let message = 'Falha na comunicação com o backend.'
    let detail = ''
    try {
      const payload = await response.json()
      if (payload?.detail) {
        detail = String(payload.detail)
        message = detail
      }
    } catch {
      // keep default message
    }
    const error = new Error(message)
    error.status = response.status
    error.detail = detail
    throw error
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

export const api = {
  getDashboard() {
    return request('/dashboard')
  },

  getRankingFeatures(query = {}) {
    return request('/ranking/features', {}, query)
  },

  getRankingFeatureCandidates(featureId) {
    return request('/ranking/feature-candidates', {}, {
      feature_id: featureId,
    })
  },

  getRankingFeatureExternal(featureId, source) {
    return request('/ranking/feature-external', {}, {
      feature_id: featureId,
      source,
    })
  },

  startRankingFeatureExternalJob(featureId, source) {
    return request('/ranking/feature-external/jobs', { method: 'POST' }, {
      feature_id: featureId,
      source,
    })
  },

  getRankingFeatureExternalJobStatus(jobId) {
    return request(`/ranking/feature-external/jobs/${jobId}`)
  },

  getCompounds(query = {}) {
    return request('/compounds', {}, query)
  },

  getExportCsvUrl() {
    return buildUrl('/export/candidates.csv')
  },

  getExportXlsxUrl() {
    return buildUrl('/export/candidates.xlsx')
  },

  async uploadFiles({ identification, abundance, compounds }) {
    const formData = new FormData()
    formData.append('identification', identification)
    formData.append('abundance', abundance)
    formData.append('compounds', compounds)

    const response = await fetch(buildUrl('/upload'), {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      let message = 'Falha no upload.'
      let detail = ''
      try {
        const payload = await response.json()
        if (payload?.detail) {
          detail = String(payload.detail)
          message = detail
        }
      } catch {
        // keep fallback
      }
      const error = new Error(message)
      error.status = response.status
      error.detail = detail
      throw error
    }

    return response.json()
  },
}
