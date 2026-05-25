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
    let message = 'Falha na comunicacao com backend.'
    try {
      const payload = await response.json()
      if (payload?.detail) {
        message = payload.detail
      }
    } catch {
      // keep default message
    }
    throw new Error(message)
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

  getCompounds(query = {}) {
    return request('/compounds', {}, query)
  },

  getExportCsvUrl() {
    return buildUrl('/export/candidates.csv')
  },

  getExportXlsxUrl() {
    return buildUrl('/export/candidates.xlsx')
  },

  async uploadFiles({ identification, abundance }) {
    const formData = new FormData()
    formData.append('identification', identification)
    formData.append('abundance', abundance)

    const response = await fetch(buildUrl('/upload'), {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      let message = 'Falha no upload.'
      try {
        const payload = await response.json()
        if (payload?.detail) {
          message = payload.detail
        }
      } catch {
        // keep fallback
      }
      throw new Error(message)
    }

    return response.json()
  },
}
