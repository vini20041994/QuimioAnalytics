import { useEffect, useRef, useState } from 'react'
import { Search, Download, Filter, TrendingUp } from 'lucide-react'
import { api } from '../services/api'
import './Top5Ranking.css'

const EXTERNAL_SOURCES = [
  { value: 'pubchem', label: 'PubChem' },
  { value: 'chebi', label: 'ChEBI' },
  { value: 'chemspider', label: 'ChemSpider' },
  { value: 'classyfire', label: 'ClassyFire' },
]

const FEATURES_PER_PAGE = 10
const QUERY_POLL_INTERVAL_MS = 1200

const QUERY_STEP_LABELS = {
  queued: 'Consulta registrada. Aguardando início.',
  checking_local_cache: 'Verificando resultados já disponíveis no banco.',
  preparing_feature_candidates: 'Preparando candidatos da feature para consulta externa.',
  running_external_etl: 'Acionando a rotina externa para a base selecionada.',
  executing_external_etl: 'Consultando a base externa e aguardando resposta.',
  loading_external_report: 'Carregando o relatório retornado pela consulta externa.',
  reloading_results: 'Atualizando os resultados da feature com os dados externos.',
  completed: 'Consulta finalizada.',
  failed: 'A consulta externa falhou.',
}

const getStepMessage = (status) => {
  if (!status) {
    return ''
  }
  return QUERY_STEP_LABELS[status.step] || 'Processando consulta externa.'
}

const getStatusTone = (status) => {
  if (!status) {
    return 'idle'
  }
  if (status.state === 'failed') {
    return 'failed'
  }
  if (status.state === 'completed') {
    return 'completed'
  }
  return 'running'
}

function Top5Ranking() {
  const [searchTerm, setSearchTerm] = useState('')
  const [rankingData, setRankingData] = useState([])
  const [selectedFeature, setSelectedFeature] = useState(null)
  const [selectedSourceByFeature, setSelectedSourceByFeature] = useState({})
  const [externalRowsByQuery, setExternalRowsByQuery] = useState({})
  const [externalFallbackByQuery, setExternalFallbackByQuery] = useState({})
  const [externalLoadingByQuery, setExternalLoadingByQuery] = useState({})
  const [externalStatusByQuery, setExternalStatusByQuery] = useState({})
  const [externalErrorByQuery, setExternalErrorByQuery] = useState({})
  const [candidatesByFeature, setCandidatesByFeature] = useState({})
  const [featureCandidatesLoading, setFeatureCandidatesLoading] = useState({})
  const [featureCandidatesError, setFeatureCandidatesError] = useState({})
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const pollTimeoutsRef = useRef({})

  const getQueryKey = (featureId, source) => `${featureId}::${source}`

  const clearQueryPolling = (queryKey) => {
    const timeoutId = pollTimeoutsRef.current[queryKey]
    if (timeoutId) {
      window.clearTimeout(timeoutId)
      delete pollTimeoutsRef.current[queryKey]
    }
  }

  const scheduleQueryPolling = (queryKey, callback) => {
    clearQueryPolling(queryKey)
    pollTimeoutsRef.current[queryKey] = window.setTimeout(callback, QUERY_POLL_INTERVAL_MS)
  }

  const formatNumber = (value, digits = 2) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return '-'
    }
    return Number(value).toFixed(digits)
  }

  const finalizeQuerySuccess = (queryKey, payload) => {
    const rows = Array.isArray(payload?.items) ? payload.items : []
    setExternalRowsByQuery((prev) => ({ ...prev, [queryKey]: rows }))
    setExternalFallbackByQuery((prev) => ({ ...prev, [queryKey]: payload?.fallback || null }))
    setExternalStatusByQuery((prev) => ({ ...prev, [queryKey]: payload }))
    setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: false }))
  }

  const pollExternalQuery = async (featureId, source, jobId) => {
    const queryKey = getQueryKey(featureId, source)

    try {
      const statusPayload = await api.getRankingFeatureExternalJobStatus(jobId)
      setExternalStatusByQuery((prev) => ({ ...prev, [queryKey]: statusPayload }))

      if (statusPayload?.state === 'completed') {
        clearQueryPolling(queryKey)
        finalizeQuerySuccess(queryKey, statusPayload)
        return
      }

      if (statusPayload?.state === 'failed') {
        clearQueryPolling(queryKey)
        setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: false }))
        setExternalErrorByQuery((prev) => ({
          ...prev,
          [queryKey]: statusPayload?.error || 'Falha ao consultar a base externa para esta feature.',
        }))
        return
      }

      scheduleQueryPolling(queryKey, () => {
        void pollExternalQuery(featureId, source, jobId)
      })
    } catch (err) {
      clearQueryPolling(queryKey)
      setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: false }))
      setExternalErrorByQuery((prev) => ({
        ...prev,
        [queryKey]: err.message || 'Falha ao acompanhar o status da consulta externa.',
      }))
    }
  }

  const fetchExternalRows = async (featureId, source) => {
    const queryKey = getQueryKey(featureId, source)
    setSelectedSourceByFeature((prev) => ({ ...prev, [featureId]: source }))

    if (externalRowsByQuery[queryKey]) {
      return
    }

    clearQueryPolling(queryKey)
    setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: true }))
    setExternalErrorByQuery((prev) => ({ ...prev, [queryKey]: '' }))
    setExternalFallbackByQuery((prev) => ({ ...prev, [queryKey]: null }))
    setExternalStatusByQuery((prev) => ({ ...prev, [queryKey]: null }))

    try {
      const startPayload = await api.startRankingFeatureExternalJob(featureId, source)
      setExternalStatusByQuery((prev) => ({ ...prev, [queryKey]: startPayload }))

      if (startPayload?.state === 'completed') {
        finalizeQuerySuccess(queryKey, startPayload)
        return
      }

      if (startPayload?.state === 'failed') {
        setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: false }))
        setExternalErrorByQuery((prev) => ({
          ...prev,
          [queryKey]: startPayload?.error || 'Falha ao consultar a base externa para esta feature.',
        }))
        return
      }

      scheduleQueryPolling(queryKey, () => {
        void pollExternalQuery(featureId, source, startPayload.job_id)
      })
    } catch (err) {
      setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: false }))
      setExternalErrorByQuery((prev) => ({
        ...prev,
        [queryKey]: err.message || 'Falha ao consultar a base externa para esta feature.',
      }))
    }
  }

  const fetchFeatureCandidates = async (featureId) => {
    if (!featureId || candidatesByFeature[featureId]) {
      return
    }

    setFeatureCandidatesLoading((prev) => ({ ...prev, [featureId]: true }))
    setFeatureCandidatesError((prev) => ({ ...prev, [featureId]: '' }))

    try {
      const payload = await api.getRankingFeatureCandidates(featureId)
      const items = Array.isArray(payload?.items) ? payload.items : []
      setCandidatesByFeature((prev) => ({ ...prev, [featureId]: items }))
    } catch (err) {
      setFeatureCandidatesError((prev) => ({
        ...prev,
        [featureId]: err.message || 'Falha ao carregar os candidatos desta feature.',
      }))
    } finally {
      setFeatureCandidatesLoading((prev) => ({ ...prev, [featureId]: false }))
    }
  }

  useEffect(() => () => {
    Object.values(pollTimeoutsRef.current).forEach((timeoutId) => {
      window.clearTimeout(timeoutId)
    })
    pollTimeoutsRef.current = {}
  }, [])
  
  useEffect(() => {
    let active = true

    const loadRanking = async () => {
      try {
        const payload = await api.getRankingFeatures({ include_candidates: false })
        if (!active) return

        const items = Array.isArray(payload?.items) ? payload.items : []
        setRankingData(items)
        setError('')
      } catch (err) {
        if (!active) return
        setError(err.message || 'Falha ao carregar o ranking de candidatos.')
      } finally {
        if (active) {
          setIsLoading(false)
        }
      }
    }

    loadRanking()
    return () => {
      active = false
    }
  }, [])

  const filteredData = rankingData.filter(feature =>
    feature.feature_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    String(feature.top_candidate_name || '').toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totalPages = Math.max(1, Math.ceil(filteredData.length / FEATURES_PER_PAGE))
  const safeCurrentPage = Math.min(currentPage, totalPages)
  const pageStart = (safeCurrentPage - 1) * FEATURES_PER_PAGE
  const paginatedData = filteredData.slice(pageStart, pageStart + FEATURES_PER_PAGE)

  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm])

  useEffect(() => {
    if (safeCurrentPage !== currentPage) {
      setCurrentPage(safeCurrentPage)
    }
  }, [safeCurrentPage, currentPage])

  const handleExport = (format) => {
    const url = format === 'xlsx' ? api.getExportXlsxUrl() : api.getExportCsvUrl()
    window.open(url, '_blank')
  }

  return (
    <div className="ranking-container">
      <header className="ranking-header">
        <div className="header-text">
          <h1 className="page-title">Classificação de Compostos</h1>
          <p className="page-subtitle">Priorização analítica dos compostos candidatos por feature.</p>
        </div>
        <div className="export-actions">
          <button className="btn btn-secondary" onClick={() => handleExport('csv')}>
            <Download size={18} />
            <span>Exportar CSV</span>
          </button>
          <button className="btn btn-primary" onClick={() => handleExport('xlsx')}>
            <Download size={18} />
            <span>Exportar Excel</span>
          </button>
        </div>
      </header>

      {isLoading && <p className="text-muted">Carregando ranking de candidatos...</p>}
      {error && <p className="text-muted">{error}</p>}
      
      <section className="filter-section">
        <div className="search-wrapper">
          <Search className="search-icon" size={20} />
          <input
            type="text"
            placeholder="Buscar por Feature ID ou nome do composto..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field"
          />
        </div>
        <button className="btn btn-secondary">
          <Filter size={18} />
          <span>Filtros</span>
        </button>
      </section>
      
      <div className="features-list">
        {paginatedData.map((feature) => (
          <article key={feature.feature_id} className="feature-card">
            <div className="feature-card-header">
              <div className="feature-meta">
                <div className="feature-id-badge">{feature.feature_id}</div>
                <div className="feature-specs">
                  <p className="spec-mz">m/z: <span>{feature.mz.toFixed(4)}</span></p>
                  <p className="spec-rt">RT: {feature.rt.toFixed(2)} min</p>
                </div>
              </div>
              <button
                onClick={() => {
                  const next = selectedFeature === feature.feature_id ? null : feature.feature_id
                  setSelectedFeature(next)
                  if (next === feature.feature_id) {
                    void fetchFeatureCandidates(feature.feature_id)
                  }
                }}
                className="btn btn-ghost"
              >
                {selectedFeature === feature.feature_id ? 'Ocultar' : 'Ver Detalhes'}
              </button>
            </div>
            
            {selectedFeature === feature.feature_id ? (
              <div className="feature-expanded-content">
                {featureCandidatesLoading[feature.feature_id] && (
                  <p className="text-muted">Carregando candidatos desta feature...</p>
                )}

                {featureCandidatesError[feature.feature_id] && (
                  <p className="text-muted">{featureCandidatesError[feature.feature_id]}</p>
                )}

                {!featureCandidatesLoading[feature.feature_id] && !featureCandidatesError[feature.feature_id] && (
                <div className="table-container">
                  <table className="ranking-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Composto</th>
                        <th>Compound ID</th>
                        <th>Fórmula</th>
                        <th>Score</th>
                        <th>Fragmentation Score</th>
                        <th>Mass Error (ppm)</th>
                        <th>Isotope Similarity</th>
                        <th>Link</th>
                        <th>Description</th>
                        <th>Neutral mass (Da)</th>
                        <th>m/z</th>
                        <th>Retention time (min)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(candidatesByFeature[feature.feature_id] || []).map((candidate, index) => (
                        <tr key={`${feature.feature_id}-${candidate.rank}-${candidate.name}-${index}`}>
                          <td>
                            <div className="rank-cell">
                              <TrendingUp size={14} className={candidate.rank === 1 ? 'icon-top' : 'icon-muted'} />
                              <span className="rank-number">#{candidate.rank}</span>
                            </div>
                          </td>
                          <td className="compound-name">{candidate.name}</td>
                          <td className="compound-formula">{candidate.compound_id || '-'}</td>
                          <td className="compound-formula">{candidate.formula}</td>
                          <td className="text-muted">{formatNumber(candidate.score, 2)}</td>
                          <td className="text-muted">{formatNumber(candidate.fragmentation_score ?? candidate.fragmentation, 2)}</td>
                          <td className="text-muted">{formatNumber(candidate.mass_error_ppm, 3)}</td>
                          <td className="text-muted">{formatNumber(candidate.isotope_similarity, 2)}</td>
                          <td>
                            {candidate.link ? (
                              <a className="external-link-cell" href={candidate.link} target="_blank" rel="noreferrer">
                                Abrir
                              </a>
                            ) : '-'}
                          </td>
                          <td className="external-description-cell">{candidate.description || '-'}</td>
                          <td className="text-muted">{formatNumber(candidate.neutral_mass_da, 4)}</td>
                          <td className="text-muted">{formatNumber(candidate.mz, 4)}</td>
                          <td className="text-muted">{formatNumber(candidate.retention_time_min, 2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                )}

                <section className="external-query-panel">
                  <div className="external-query-header">
                    <h4>Consulta por Base Externa</h4>
                    <p>Selecione uma base para consultar os registros desta feature.</p>
                  </div>

                  <div className="external-source-actions">
                    {EXTERNAL_SOURCES.map((source) => (
                      <button
                        key={`${feature.feature_id}-${source.value}`}
                        onClick={() => fetchExternalRows(feature.feature_id, source.value)}
                        className={`btn btn-secondary source-query-btn ${selectedSourceByFeature[feature.feature_id] === source.value ? 'active' : ''}`}
                        type="button"
                      >
                        {source.label}
                      </button>
                    ))}
                  </div>

                  {selectedSourceByFeature[feature.feature_id] && (() => {
                    const source = selectedSourceByFeature[feature.feature_id]
                    const queryKey = getQueryKey(feature.feature_id, source)
                    const isQueryLoading = !!externalLoadingByQuery[queryKey]
                    const queryError = externalErrorByQuery[queryKey]
                    const queryStatus = externalStatusByQuery[queryKey]
                    const rows = externalRowsByQuery[queryKey] || []
                    const fallbackInfo = externalFallbackByQuery[queryKey]
                    const statusTone = getStatusTone(queryStatus)

                    return (
                      <>
                        {queryStatus && (
                          <div className={`external-status-card status-${statusTone}`}>
                            <div className="external-status-meta">
                              <div>
                                <strong>Status da consulta</strong>
                                <p>{getStepMessage(queryStatus)}</p>
                              </div>
                              <span className="external-status-progress">{Math.max(0, Math.min(Number(queryStatus.progress || 0), 100))}%</span>
                            </div>
                            <div className="external-status-bar" aria-hidden="true">
                              <div
                                className={`external-status-fill status-${statusTone}`}
                                style={{ width: `${Math.max(0, Math.min(Number(queryStatus.progress || 0), 100))}%` }}
                              />
                            </div>
                            <div className="external-status-caption">
                              <span>Feature: {feature.feature_id}</span>
                              <span>Base: {EXTERNAL_SOURCES.find((item) => item.value === source)?.label || source}</span>
                            </div>
                          </div>
                        )}

                        {isQueryLoading && <p className="text-muted">A consulta está em andamento. O status é atualizado automaticamente.</p>}

                        {queryError && <p className="text-muted">{queryError}</p>}

                        {fallbackInfo?.triggered && (
                          <p className="text-muted">
                            Não havia registros locais. O sistema executou o ETL sob demanda para a fonte selecionada e recarregou os resultados.
                          </p>
                        )}

                        {!isQueryLoading && !queryError && rows.length === 0 && (
                          <p className="text-muted">Nenhum registro encontrado nessa base para esta feature.</p>
                        )}

                        {rows.length > 0 && (
                        <div className="table-container external-table-container">
                          <table className="ranking-table external-ranking-table">
                          <thead>
                            <tr>
                              <th>Compound ID</th>
                              <th>Fórmula</th>
                              <th>Score</th>
                              <th>Fragmentation Score</th>
                              <th>Mass Error (ppm)</th>
                              <th>Isotope Similarity</th>
                              <th>Link</th>
                              <th>Descrição</th>
                              <th>Neutral mass (Da)</th>
                              <th>m/z</th>
                              <th>Retention time (min)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {rows.map((row, index) => (
                              <tr key={`${queryKey}-${row.compound_id || 'compound'}-${row.external_id || 'external'}-${index}`}>
                                <td className="compound-formula">{row.compound_id || '-'}</td>
                                <td className="compound-formula">{row.formula || '-'}</td>
                                <td className="text-muted">{formatNumber(row.score, 2)}</td>
                                <td className="text-muted">{formatNumber(row.fragmentation_score, 2)}</td>
                                <td className="text-muted">{formatNumber(row.mass_error_ppm, 3)}</td>
                                <td className="text-muted">{formatNumber(row.isotope_similarity, 2)}</td>
                                <td>
                                  {row.link ? (
                                    <a className="external-link-cell" href={row.link} target="_blank" rel="noreferrer">
                                      Abrir
                                    </a>
                                  ) : '-'}
                                </td>
                                <td className="external-description-cell">{row.description || '-'}</td>
                                <td className="text-muted">{formatNumber(row.neutral_mass_da, 4)}</td>
                                <td className="text-muted">{formatNumber(row.mz, 4)}</td>
                                <td className="text-muted">{formatNumber(row.retention_time_min, 2)}</td>
                              </tr>
                            ))}
                          </tbody>
                          </table>
                        </div>
                        )}
                      </>
                    )
                  })()}
                </section>
              </div>
            ) : (
              <p className="text-muted">{feature.candidate_count || 0} candidatos ranqueados. Clique em "Ver Detalhes" para abrir.</p>
            )}
          </article>
        ))}
      </div>

      {filteredData.length > 0 && (
        <nav className="pagination" aria-label="Paginação do ranking">
          <div className="pagination-summary">
            <span>
              Exibindo {pageStart + 1}-{Math.min(pageStart + FEATURES_PER_PAGE, filteredData.length)} de {filteredData.length} features
            </span>
            <span>
              Página {safeCurrentPage} de {totalPages}
            </span>
          </div>
          <div className="pagination-actions">
            <button
              className="btn btn-ghost"
              type="button"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={safeCurrentPage === 1}
            >
              Anterior
            </button>
            <button
              className="btn btn-ghost"
              type="button"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={safeCurrentPage === totalPages}
            >
              Próxima
            </button>
          </div>
        </nav>
      )}

      {filteredData.length === 0 && (
        <div className="empty-state">
          <p>Nenhuma feature encontrada.</p>
        </div>
      )}
    </div>
  )
}

export default Top5Ranking