import { useEffect, useMemo, useState } from 'react'
import { Search, Database, ExternalLink, Beaker, Tag } from 'lucide-react'
import { api } from '../services/api'
import './ChemicalRef.css'

function ChemicalRef() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSource, setSelectedSource] = useState('all')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [compounds, setCompounds] = useState([])
  
  useEffect(() => {
    let active = true

    const loadCompounds = async () => {
      try {
        const payload = await api.getCompounds()
        if (!active) return
        setCompounds(Array.isArray(payload?.items) ? payload.items : [])
        setError('')
      } catch (err) {
        if (!active) return
        setError(err.message || 'Falha ao carregar referências químicas.')
      } finally {
        if (active) {
          setIsLoading(false)
        }
      }
    }

    loadCompounds()
    return () => {
      active = false
    }
  }, [])

  const sources = useMemo(() => [
    { value: 'all', label: 'Todas as Fontes', count: compounds.length },
    { value: 'interna', label: 'Interna', count: compounds.filter(c => (c.sources || []).includes('Interna')).length },
    { value: 'pubchem', label: 'PubChem', count: compounds.filter(c => (c.sources || []).includes('PubChem')).length },
    { value: 'chebi', label: 'ChEBI', count: compounds.filter(c => (c.sources || []).includes('ChEBI')).length },
    { value: 'chemspider', label: 'ChemSpider', count: compounds.filter(c => (c.sources || []).includes('ChemSpider')).length },
    { value: 'classyfire', label: 'ClassyFire', count: compounds.filter(c => (c.sources || []).includes('ClassyFire')).length },
  ], [compounds])

  const filteredCompounds = compounds.filter(compound => {
    const matchesSearch = 
      compound.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      compound.formula.toLowerCase().includes(searchTerm.toLowerCase()) ||
      compound.inchikey.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesSource = 
      selectedSource === 'all' || 
      compound.sources.some(s => s.toLowerCase() === selectedSource)
    
    return matchesSearch && matchesSource
  })

  const prettyKey = (rawKey) => rawKey
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\s+/g, ' ')
    .trim()

  const groupedExternalRefs = (compound) => {
    const refs = Array.isArray(compound.external_references) ? compound.external_references : []
    return refs.reduce((acc, ref) => {
      const source = ref?.source || 'Externa'
      if (!acc[source]) acc[source] = []
      acc[source].push(ref)
      return acc
    }, {})
  }

  return (
    <div className="page-container">
      <header className="page-header">
        <h1 className="page-title">Referências Químicas</h1>
        <p className="page-description">Base integrada de compostos químicos para consulta operacional.</p>
      </header>

      {isLoading && <p className="text-muted">Carregando compostos...</p>}
      {error && <p className="text-muted">{error}</p>}
      
      {/* Estatísticas / Filtros */}
      <div className="stats-grid">
        {sources.map((source) => (
          <button
            key={source.value}
            onClick={() => setSelectedSource(source.value)}
            className={`stat-card ${selectedSource === source.value ? 'active' : ''}`}
          >
            <div className="stat-content">
              <div className="stat-info">
                <span className="stat-label">{source.label}</span>
                <span className="stat-value">{source.count}</span>
              </div>
              <Database className="stat-icon" size={32} />
            </div>
          </button>
        ))}
      </div>
      
      {/* Barra de Busca */}
      <div className="search-container">
        <div className="search-wrapper">
          <Search className="search-icon" size={20} />
          <input
            type="text"
            placeholder="Buscar por nome, fórmula ou InChIKey..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field search-input"
          />
        </div>
      </div>
      
      {/* Lista de Compostos */}
      <div className="compounds-list">
        {filteredCompounds.map((compound) => (
          <div key={compound.id} className="compound-card">
            <div className="compound-main">
              <div className="compound-info">
                <div className="compound-header">
                  <Beaker className="icon-beaker" size={24} />
                  <h3 className="compound-name">{compound.name}</h3>
                </div>
                
                <div className="compound-details">
                  <div className="detail-group">
                    <label>Fórmula Molecular</label>
                    <span className="formula">{compound.formula}</span>
                  </div>
                  <div className="detail-group">
                    <label>Peso Molecular</label>
                    <span>{compound.molecular_weight} g/mol</span>
                  </div>
                  <div className="detail-group full-width">
                    <label>InChIKey</label>
                    <span className="inchikey">{compound.inchikey}</span>
                  </div>
                  {compound.description && (
                    <div className="detail-group full-width">
                      <label>ClassyFire — Descrição</label>
                      <span className="classyfire-desc">{compound.description}</span>
                    </div>
                  )}
                </div>
                
                <div className="tag-section">
                  <label>Classes Químicas</label>
                  <div className="tag-list">
                    {compound.classes.map((cls, idx) => (
                      <span key={idx} className="badge-class">
                        <Tag size={12} />
                        <span>{cls}</span>
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="external-links">
                  <label>Identificadores Externos</label>
                  <div className="link-buttons">
                    {(() => {
                      const classyfireRef = Array.isArray(compound.external_references)
                        ? compound.external_references.find(ref => String(ref?.source || '').toLowerCase() === 'classyfire')
                        : null
                      const classyfireId = classyfireRef?.external_id || ''

                      return (
                        classyfireId && (
                          <a
                            href={`http://classyfire.wishartlab.com/entities/${classyfireId}`}
                            target="_blank"
                            rel="noreferrer"
                            className="ext-link classyfire"
                          >
                            ClassyFire: {classyfireId} <ExternalLink size={14} />
                          </a>
                        )
                      )
                    })()}
                    {compound.pubchem_cid && (
                      <a 
                        href={`https://pubchem.ncbi.nlm.nih.gov/compound/${compound.pubchem_cid}`} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="ext-link pubchem"
                      >
                        PubChem: {compound.pubchem_cid} <ExternalLink size={14} />
                      </a>
                    )}
                    {compound.chebi_id && (
                      <a 
                        href={`https://www.ebi.ac.uk/chebi/searchId.do?chebiId=${compound.chebi_id}`} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="ext-link chebi"
                      >
                        ChEBI: {compound.chebi_id} <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                </div>

                {Array.isArray(compound.external_references) && compound.external_references.length > 0 && (
                  <div className="external-data-panel">
                    <label>Informações Externas Organizadas</label>
                    <div className="external-groups-grid">
                      {Object.entries(groupedExternalRefs(compound)).map(([sourceName, refs]) => (
                        <article key={sourceName} className="external-source-card">
                          <header className="external-source-header">
                            <span className="external-source-name">{sourceName}</span>
                            <span className="external-source-count">{refs.length} registro(s)</span>
                          </header>

                          <div className="external-source-body">
                            {refs.map((ref, idx) => {
                              const details = ref?.details && typeof ref.details === 'object' ? ref.details : {}
                              const detailEntries = Object.entries(details).filter(([, value]) => String(value || '').trim() !== '')

                              return (
                                <div key={`${sourceName}-${idx}`} className="external-record">
                                  <div className="external-record-main">
                                    {ref.external_id && (
                                      <span className="external-record-chip">ID: {ref.external_id}</span>
                                    )}
                                    {ref.standardized_name && (
                                      <span className="external-record-name">{ref.standardized_name}</span>
                                    )}
                                  </div>

                                  {(ref.chemical_class || ref.chemical_subclass) && (
                                    <div className="external-record-taxonomy">
                                      {ref.chemical_class && <span>Classe: {ref.chemical_class}</span>}
                                      {ref.chemical_subclass && <span>Subclasse: {ref.chemical_subclass}</span>}
                                    </div>
                                  )}

                                  {ref.description && (
                                    <p className="external-record-description">{ref.description}</p>
                                  )}

                                  {detailEntries.length > 0 && (
                                    <div className="external-details-grid">
                                      {detailEntries.slice(0, 12).map(([key, value]) => (
                                        <div key={key} className="external-detail-item">
                                          <span className="external-detail-key">{prettyKey(key)}</span>
                                          <span className="external-detail-value">{String(value)}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </article>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="compound-sources">
                <label>Fontes</label>
                <div className="source-badges">
                  {compound.sources.map((source, idx) => (
                    <span key={idx} className={`source-badge ${source.toLowerCase()}`}>
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredCompounds.length === 0 && (
        <div className="empty-state">
          <Database size={48} />
          <p>Nenhum composto encontrado com os critérios de busca.</p>
        </div>
      )}
    </div>
  )
}

export default ChemicalRef;