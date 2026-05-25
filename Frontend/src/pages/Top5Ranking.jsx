import { useState, useEffect } from 'react'
import { Search, Download, Filter, TrendingUp, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import './Top5Ranking.css'

function Top5Ranking() {
  const [searchTerm, setSearchTerm] = useState('')
  const [rankingData, setRankingData] = useState([])
  const [selectedFeature, setSelectedFeature] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  
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
        setError(err.message || 'Falha ao carregar ranking.')
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

  // ESTA É A VARIÁVEL QUE ESTAVA FALTANDO:
  const filteredData = rankingData.filter(feature =>
    feature.feature_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    feature.candidates.some(c => c.name.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const getProbClass = (prob) => {
    if (prob >= 0.8) return 'prob-high'
    if (prob >= 0.6) return 'prob-medium'
    return 'prob-low'
  }

  return (
    <div className="ranking-container">
      <header className="ranking-header">
        <div className="header-text">
          <h1 className="page-title">Top 5 Ranking</h1>
          <p className="page-subtitle">Candidatos ranqueados por probabilidade analítica</p>
        </div>
        <button className="btn btn-primary" onClick={() => window.open(api.getExportCsvUrl(), '_blank')}>
          <Download size={18} />
          <span>Exportar CSV</span>
        </button>
      </header>

      {isLoading && <p className="text-muted">Carregando ranking do backend...</p>}
      {error && <p className="text-muted">{error}</p>}
      
      <section className="filter-section">
        <div className="search-wrapper">
          <Search className="search-icon" size={20} />
          <input
            type="text"
            placeholder="Buscar por Feature ID ou nome..."
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
            
            <div className="table-container">
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Composto</th>
                    <th>Fórmula</th>
                    <th>Probabilidade</th>
                    <th>Erro (ppm)</th>
                    <th>Fonte</th>
                  </tr>
                </thead>
                <tbody>
                  {feature.candidates.map((candidate) => (
                    <tr key={candidate.rank}>
                      <td>
                        <div className="rank-cell">
                          <TrendingUp size={14} className={candidate.rank === 1 ? 'icon-top' : 'icon-muted'} />
                          <span className="rank-number">#{candidate.rank}</span>
                        </div>
                      </td>
                      <td className="compound-name">{candidate.name}</td>
                      <td className="compound-formula">{candidate.formula}</td>
                      <td>
                        <span className={`prob-text ${getProbClass(candidate.probability)}`}>
                          {(Number(candidate.probability || 0) * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="text-muted">{Number(candidate.mass_error_ppm || 0).toFixed(1)}</td>
                      <td>
                        <span className={`badge-source ${candidate.source.toLowerCase()}`}>
                          {candidate.source}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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