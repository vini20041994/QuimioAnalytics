import { useState, useEffect } from 'react'
import { Search, Download, Filter, TrendingUp, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import './Top5Ranking.css'

const EXTERNAL_SOURCES = [
  { value: 'pubchem', label: 'PubChem' },
  { value: 'chebi', label: 'ChEBI' },
  { value: 'chemspider', label: 'ChemSpider' },
  { value: 'classyfire', label: 'ClassyFire' },
]

function Top5Ranking() {
  const [searchTerm, setSearchTerm] = useState('')
  const [rankingData, setRankingData] = useState([])
  const [selectedFeature, setSelectedFeature] = useState(null)
  const [selectedSourceByFeature, setSelectedSourceByFeature] = useState({})
  const [externalRowsByQuery, setExternalRowsByQuery] = useState({})
  const [externalFallbackByQuery, setExternalFallbackByQuery] = useState({})
  const [externalLoadingByQuery, setExternalLoadingByQuery] = useState({})
  const [externalErrorByQuery, setExternalErrorByQuery] = useState({})
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const getQueryKey = (featureId, source) => `${featureId}::${source}`

  const formatNumber = (value, digits = 2) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return '-'
    }
    return Number(value).toFixed(digits)
  }

  const fetchExternalRows = async (featureId, source) => {
    const queryKey = getQueryKey(featureId, source)
    setSelectedSourceByFeature((prev) => ({ ...prev, [featureId]: source }))

    if (externalRowsByQuery[queryKey]) {
      return
    }

    setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: true }))
    setExternalErrorByQuery((prev) => ({ ...prev, [queryKey]: '' }))
    setExternalFallbackByQuery((prev) => ({ ...prev, [queryKey]: null }))

    try {
      const payload = await api.getRankingFeatureExternal(featureId, source)
      const rows = Array.isArray(payload?.items) ? payload.items : []
      setExternalRowsByQuery((prev) => ({ ...prev, [queryKey]: rows }))
      if (payload?.fallback?.triggered) {
        setExternalFallbackByQuery((prev) => ({ ...prev, [queryKey]: payload.fallback }))
      }
    } catch (err) {
      setExternalErrorByQuery((prev) => ({
        ...prev,
        [queryKey]: err.message || 'Falha ao consultar a base externa para esta feature.',
      }))
    } finally {
      setExternalLoadingByQuery((prev) => ({ ...prev, [queryKey]: false }))
    }
  }
  
  useEffect(() => {
    let active = true

    const loadRanking = async () => {
      try {
        const payload = await api.getRankingFeatures()
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
    feature.candidates.some(c => c.name.toLowerCase().includes(searchTerm.toLowerCase()))
  )

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
        {filteredData.map((feature) => (
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
                onClick={() => setSelectedFeature(selectedFeature === feature.feature_id ? null : feature.feature_id)}
                className="btn btn-ghost"
              >
                {selectedFeature === feature.feature_id ? 'Ocultar' : 'Ver Detalhes'}
              </button>
            </div>
            
            {selectedFeature === feature.feature_id ? (
              <div className="feature-expanded-content">
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
                      {feature.candidates.map((candidate, index) => (
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
                    const rows = externalRowsByQuery[queryKey] || []
                    const fallbackInfo = externalFallbackByQuery[queryKey]

                    if (isQueryLoading) {
                      return <p className="text-muted">Consultando a base externa selecionada...</p>
                    }

                    if (queryError) {
                      return <p className="text-muted">{queryError}</p>
                    }

                    if (rows.length === 0) {
                      return <p className="text-muted">Nenhum registro encontrado nessa base para esta feature.</p>
                    }

                    return (
                      <>
                        {fallbackInfo?.triggered && (
                          <p className="text-muted">
                            Não havia registros locais. O sistema executou o ETL sob demanda para a fonte selecionada e recarregou os resultados.
                          </p>
                        )}
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
                      </>
                    )
                  })()}
                </section>
              </div>
            ) : (
              <p className="text-muted">{feature.candidates.length} candidatos ranqueados. Clique em "Ver Detalhes" para abrir.</p>
            )}
          </article>
        ))}
      </div>

      {filteredData.length === 0 && (
        <div className="empty-state">
          <p>Nenhuma feature encontrada.</p>
        </div>
      )}
    </div>
  )
}

export default Top5Ranking