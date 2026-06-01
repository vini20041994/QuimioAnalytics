import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Database, Beaker, FileCheck, Activity } from 'lucide-react'
import { api } from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [stats, setStats] = useState({
    totalFeatures: 0,
    totalCandidates: 0,
    totalCompounds: 0,
    externalSources: 0
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [updates, setUpdates] = useState([])
  
  const [abundanceData, setAbundanceData] = useState([])
  
  const [sourceDistribution, setSourceDistribution] = useState([])
  
  useEffect(() => {
    let active = true

    const loadDashboard = async () => {
      try {
        const payload = await api.getDashboard()
        if (!active) return

        setStats(payload?.stats || {
          totalFeatures: 0,
          totalCandidates: 0,
          totalCompounds: 0,
          externalSources: 0,
        })

        setAbundanceData(Array.isArray(payload?.abundanceData) ? payload.abundanceData : [])

        setSourceDistribution(Array.isArray(payload?.sourceDistribution) ? payload.sourceDistribution : [])

        setUpdates(Array.isArray(payload?.updates) ? payload.updates : [])

        setError('')
      } catch (err) {
        if (!active) return
        setError(err.message || 'Falha ao carregar os indicadores operacionais.')
        setAbundanceData([])
        setSourceDistribution([])
        setUpdates([])
      } finally {
        if (active) {
          setIsLoading(false)
        }
      }
    }

    loadDashboard()
    return () => {
      active = false
    }
  }, [])
  
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="dashboard-title">Dashboard Analítico</h1>
        <p className="dashboard-subtitle">Painel operacional para acompanhamento de features, candidatos e enriquecimento externo.</p>
      </header>

      {isLoading && <p className="text-muted">Carregando indicadores operacionais...</p>}
      {error && <p className="text-muted">Falha ao carregar o painel: {error}</p>}
      
      {/* Cards de Estatísticas */}
      <div className="stats-grid">
        <div className="stat-card border-verde">
          <div className="stat-content">
            <div className="stat-text">
              <p className="stat-label">Total de Features</p>
              <p className="stat-value text-verde">{stats.totalFeatures}</p>
            </div>
            <Database className="stat-icon text-verde" size={40} />
          </div>
        </div>
        
        <div className="stat-card border-azul">
          <div className="stat-content">
            <div className="stat-text">
              <p className="stat-label">Candidatos</p>
              <p className="stat-value text-azul">{stats.totalCandidates}</p>
            </div>
            <Beaker className="stat-icon text-azul" size={40} />
          </div>
        </div>
        
        <div className="stat-card border-verde-medium">
          <div className="stat-content">
            <div className="stat-text">
              <p className="stat-label">Compostos Ref.</p>
              <p className="stat-value text-verde-medium">{stats.totalCompounds}</p>
            </div>
            <FileCheck className="stat-icon text-verde-medium" size={40} />
          </div>
        </div>
        
        <div className="stat-card border-azul-light">
          <div className="stat-content">
            <div className="stat-text">
              <p className="stat-label">Fontes Externas</p>
              <p className="stat-value text-azul-light">{stats.externalSources}</p>
            </div>
            <Activity className="stat-icon text-azul-light" size={40} />
          </div>
        </div>
      </div>
      
    {/* Seção de Gráficos Lado a Lado */}
      <div className="charts-grid">
        
        {/* Gráfico de Abundância */}
        <div className="chart-card">
          <h2 className="chart-title">Abundância Bruta por Réplica</h2>
          <div className="chart-wrapper">
            {abundanceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={abundanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#424242" vertical={false} />
                  <XAxis dataKey="sample" stroke="#737373" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#737373" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} 
                    contentStyle={{ 
                      backgroundColor: '#111111', 
                      border: '1px solid #424242',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                    itemStyle={{ color: '#04BDA2' }}
                  />
                  <Bar dataKey="abundance" fill="#04BDA2" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-muted">Sem dados brutos de abundância por réplica. Execute um novo upload para gerar este indicador.</p>
            )}
          </div>
        </div>

        {/* Gráfico de Distribuição de Fontes */}
        <div className="chart-card">
          <h2 className="chart-title">Distribuição por Fonte</h2>
          <div className="chart-wrapper">
            {sourceDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sourceDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={{ fill: '#ffffff', fontSize: 12 }}
                  >
                    {sourceDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#111111', 
                      border: '1px solid #424242',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-muted">Sem distribuição de fontes externas no momento.</p>
            )}
          </div>
        </div>

      </div> 
      
      {/* Tabela */}
      <div className="table-card">
        <h2 className="chart-title">Últimas Atualizações</h2>
        <div className="table-responsive">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Batch</th>
                <th>Tipo</th>
                <th>Data</th>
                <th>Registros</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {updates.length > 0 ? updates.map((row, index) => (
                <tr key={`${row.batch}-${index}`}>
                  <td className="font-medium">{row.batch}</td>
                  <td><span className="badge badge-verde">{row.type}</span></td>
                  <td className="text-muted">{row.date || '-'}</td>
                  <td>{Number(row.records || 0).toLocaleString('pt-BR')}</td>
                  <td><span className="badge badge-azul">{row.status || 'Completo'}</span></td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="text-muted">Sem atualizações recentes. Realize um upload para iniciar novo ciclo.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard