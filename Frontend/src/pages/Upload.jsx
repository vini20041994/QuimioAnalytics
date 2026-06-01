import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle, Clock, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import './Upload.css'

const ETL_STAGES = [
  { id: 'upload',    label: 'Enviando arquivos',               pct: 8   },
  { id: 'extract',   label: 'Extract — lendo planilhas',       pct: 28  },
  { id: 'transform', label: 'Transform — normalizando dados',  pct: 50  },
  { id: 'load',      label: 'Load — gravando no banco',        pct: 68  },
  { id: 'ranking',   label: 'Ranking biológico dos candidatos', pct: 96  },
  { id: 'done',      label: 'Processamento concluído',          pct: 100 },
]

// pct_per_tick para cada faixa de progresso (intervalo de 250ms)
const INTERVAL_MS = 250
const STAGE_SPEEDS = [
  { start: 0,  end: 8,  speed: 8  / (1500  / INTERVAL_MS) },
  { start: 8,  end: 28, speed: 20 / (8000  / INTERVAL_MS) },
  { start: 28, end: 50, speed: 22 / (12000 / INTERVAL_MS) },
  { start: 50, end: 68, speed: 18 / (15000 / INTERVAL_MS) },
  { start: 68, end: 96, speed: 28 / (90000 / INTERVAL_MS) },
]

const PROCESS_STATUS = {
  idle: 'Aguardando as planilhas obrigatórias para iniciar o processamento.',
  validating: 'Validando arquivos enviados.',
  uploading: 'Enviando planilhas para o sistema.',
  processing: 'ETL interno e ranking em execução.',
  success: 'Processamento concluído com sucesso.',
  warning: 'Processamento concluído com alertas.',
  error: 'Processamento finalizado com falha.',
}

const OUTCOME_LABELS = {
  success_total: 'Sucesso total',
  success_partial: 'Sucesso parcial',
  failed: 'Falha',
}

function getActiveStageIndex(pct) {
  for (let i = 0; i < ETL_STAGES.length; i++) {
    if (pct < ETL_STAGES[i].pct) return i
  }
  return ETL_STAGES.length - 1
}

function Upload() {
  const [files, setFiles] = useState({ identification: null, abundance: null, compounds: null })
  const [uploadStatus, setUploadStatus] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressVisible, setProgressVisible] = useState(false)
  const [progressError, setProgressError] = useState(null)
  const [processPhase, setProcessPhase] = useState('idle')
  const timerRef = useRef(null)
  const statusMessageRef = useRef(null)
  const exitWarningMessage = 'O processamento está em execução. Se você sair agora, ele será cancelado.'

  useEffect(() => {
    if (!isProcessing) {
      clearInterval(timerRef.current)
      return
    }

    setProgress(0)
    setProgressError(null)
    setProgressVisible(true)
    setProcessPhase('processing')

    timerRef.current = setInterval(() => {
      setProgress(prev => {
        const stage = STAGE_SPEEDS.find(s => prev >= s.start && prev < s.end)
        if (!stage) return prev
        return Math.min(prev + stage.speed, stage.end)
      })
    }, INTERVAL_MS)

    return () => clearInterval(timerRef.current)
  }, [isProcessing])

  // Avisa o usuário antes de fechar/navegar fora enquanto o ETL está em execução
  useEffect(() => {
    if (!isProcessing) return

    const handleBeforeUnload = (e) => {
      e.preventDefault()
      e.returnValue = exitWarningMessage
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isProcessing, exitWarningMessage])

  // Intercepta clique em links internos para confirmar navegação durante ETL.
  useEffect(() => {
    if (!isProcessing) return

    const handleDocumentClick = (event) => {
      const anchor = event.target?.closest?.('a[href]')
      if (!anchor) return
      if (anchor.target === '_blank' || anchor.hasAttribute('download')) return

      const href = anchor.getAttribute('href')
      if (!href || href.startsWith('#')) return

      const destination = new URL(href, window.location.origin)
      const isInternal = destination.origin === window.location.origin
      const isDifferentPath = destination.pathname !== window.location.pathname || destination.search !== window.location.search

      if (!isInternal || !isDifferentPath) return

      const confirmed = window.confirm(exitWarningMessage)
      if (!confirmed) {
        event.preventDefault()
        event.stopPropagation()
      }
    }

    document.addEventListener('click', handleDocumentClick, true)
    return () => document.removeEventListener('click', handleDocumentClick, true)
  }, [isProcessing, exitWarningMessage])

  const requiredFileLabels = {
    identification: 'Identificação',
    abundance: 'Abundância',
    compounds: 'Compostos',
  }

  const missingFiles = Object.entries(requiredFileLabels)
    .filter(([key]) => !files[key])
    .map(([, label]) => label)

  const handleFileChange = (type, event) => {
    if (isProcessing) {
      return
    }

    const file = event.target.files[0]
    if (!file) return

    const validExtensions = ['.xlsx', '.xls']
    const isValid = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
    if (!isValid) {
      setUploadStatus({
        type: 'error',
        message: `Formato inválido para ${requiredFileLabels[type]}. Envie apenas .xlsx ou .xls.`,
      })
      setProcessPhase('error')
      event.target.value = ''
      return
    }

    setFiles(prev => ({ ...prev, [type]: file }))
    setUploadStatus(null)
    setProcessPhase('idle')
  }

  useEffect(() => {
    if (uploadStatus?.type === 'error' && statusMessageRef.current) {
      statusMessageRef.current.focus()
    }
  }, [uploadStatus])

  const getActionableError = (err) => {
    const status = Number(err?.status || 0)
    const detail = String(err?.detail || err?.message || '').trim()

    if (status === 0 && /failed to fetch|networkerror|network error/i.test(detail)) {
      return 'Não foi possível se comunicar com o backend. Verifique se os containers de backend/frontend estão ativos e tente novamente.'
    }

    if (status === 409) {
      return 'Já existe um processamento em execução. Aguarde a finalização atual e tente novamente em instantes.'
    }
    if (status === 400) {
      return 'Os arquivos enviados não são válidos. Revise o formato, selecione apenas .xlsx/.xls e tente novamente.'
    }
    if (status === 500 && detail.toLowerCase().includes('db_pass')) {
      return 'O sistema está sem configuração de banco (DB_PASS). Solicite o ajuste do ambiente antes de reenviar.'
    }
    if (status === 500 && /connection refused|operationalerror|could not connect|is the server running/i.test(detail)) {
      return 'Falha de conexão com o banco durante o ETL. Verifique se o PostgreSQL está ativo e se o backend está configurado com o host correto.'
    }
    if (status >= 500) {
      return 'Falha interna no processamento. Aguarde alguns minutos e tente novamente. Se persistir, acione o suporte técnico.'
    }

    return detail || 'Falha ao enviar os arquivos para processamento. Verifique os dados e tente novamente.'
  }

  const handleUpload = async () => {
    if (!files.identification || !files.abundance || !files.compounds) {
      setUploadStatus({ type: 'error', message: 'Selecione as três planilhas (Identificação, Abundância e Compostos) antes de enviar.' })
      setProcessPhase('error')
      return
    }

    setProcessPhase('validating')
    setIsProcessing(true)
    setUploadStatus(null)
    setProgressError(null)

    try {
      setProcessPhase('uploading')
      const response = await api.uploadFiles({
        identification: files.identification,
        abundance: files.abundance,
        compounds: files.compounds,
      })

      clearInterval(timerRef.current)
      setProgress(100)
      const outcome = response?.details?.outcome || 'success_total'
      const hasWarning = outcome === 'success_partial'
      const isFailedOutcome = outcome === 'failed'
      setUploadStatus({
        type: isFailedOutcome ? 'error' : (hasWarning ? 'warning' : 'success'),
        message: isFailedOutcome
          ? 'Upload finalizado com falha no processamento. Revise os detalhes e tente novamente.'
          : hasWarning
          ? 'Upload concluído com alertas nas bases externas. Revise os detalhes abaixo.'
          : (response?.message || 'Arquivos carregados com sucesso. ETL interno e ranking concluídos.'),
        details: response?.details,
      })
      setProcessPhase(isFailedOutcome ? 'error' : (hasWarning ? 'warning' : 'success'))
    } catch (err) {
      clearInterval(timerRef.current)
      const message = getActionableError(err)
      setProgressError(message)
      setUploadStatus({ type: 'error', message })
      setProcessPhase('error')
    } finally {
      setIsProcessing(false)
    }
  }

  const activeStageIndex = getActiveStageIndex(progress)

  return (
    <div className="upload-page">
      <header className="page-header">
        <h1 className="page-title">Upload de Planilhas</h1>
        <p className="page-subtitle">Envie Identificação, Abundância e Compostos para executar o ETL interno e o ranking com rastreabilidade.</p>
      </header>

      {/* Card de Instruções */}
      <div className="alert-card info">
        <AlertTriangle className="alert-icon" size={24} />
        <div className="alert-content">
          <h3>Instruções de Upload</h3>
          <ul className="instruction-list">
            <li>Selecione a planilha de <strong>Identificação</strong> (.xlsx ou .xls)</li>
            <li>Selecione a planilha de <strong>Abundância</strong> (.xlsx ou .xls)</li>
            <li>Selecione a planilha de <strong>Compostos</strong> (.xlsx ou .xls)</li>
            <li>Nesta etapa, o sistema executa apenas ETL interno e ranking</li>
            <li>As bases externas devem ser consultadas depois, pelo botão da fonte na tela de Ranking</li>
          </ul>
        </div>
      </div>

      {/* Aviso de execução em andamento */}
      {isProcessing && (
        <div className="alert-card warning-processing">
          <AlertTriangle className="alert-icon" size={24} />
          <div className="alert-content">
            <h3>Pipeline em execução — não saia desta página</h3>
            <p>Fechar a aba, recarregar ou navegar para outra página irá cancelar o processamento ETL imediatamente.</p>
          </div>
        </div>
      )}

      <div className="processing-status" role="status" aria-live="polite" aria-atomic="true">
        <strong>Status operacional:</strong> {PROCESS_STATUS[processPhase]}
      </div>

      {/* Upload Area */}
      <div className="upload-grid">
        {/* Card Identificação */}
        <div className="upload-card">
          <FileSpreadsheet className="icon-main text-verde" size={48} />
          <h3>Planilha de Identificação</h3>
          <p>Contém dados de m/z, RT, fórmula molecular e candidatos</p>

          <label htmlFor="id-upload" className={`btn btn-secondary${isProcessing ? ' disabled' : ''}`} aria-disabled={isProcessing}>
            <UploadIcon size={18} />
            <span>{files.identification ? 'Alterar Arquivo' : 'Selecionar Arquivo'}</span>
          </label>
          <input id="id-upload" type="file" accept=".xlsx,.xls" className="hidden"
            disabled={isProcessing}
            onChange={(e) => handleFileChange('identification', e)} />

          {files.identification && (
            <div className="file-info success">
              <CheckCircle size={16} />
              <div className="file-meta">
                <span className="file-name">{files.identification.name}</span>
                <span className="file-size">{(files.identification.size / 1024).toFixed(2)} KB</span>
              </div>
            </div>
          )}
        </div>

        {/* Card Abundância */}
        <div className="upload-card">
          <FileSpreadsheet className="icon-main text-azul" size={48} />
          <h3>Planilha de Abundância</h3>
          <p>Contém valores de abundância por amostra e replicata</p>

          <label htmlFor="ab-upload" className={`btn btn-primary${isProcessing ? ' disabled' : ''}`} aria-disabled={isProcessing}>
            <UploadIcon size={18} />
            <span>{files.abundance ? 'Alterar Arquivo' : 'Selecionar Arquivo'}</span>
          </label>
          <input id="ab-upload" type="file" accept=".xlsx,.xls" className="hidden"
            disabled={isProcessing}
            onChange={(e) => handleFileChange('abundance', e)} />

          {files.abundance && (
            <div className="file-info info">
              <CheckCircle size={16} />
              <div className="file-meta">
                <span className="file-name">{files.abundance.name}</span>
                <span className="file-size">{(files.abundance.size / 1024).toFixed(2)} KB</span>
              </div>
            </div>
          )}
        </div>

        {/* Card Compostos */}
        <div className="upload-card">
          <FileSpreadsheet className="icon-main text-verde" size={48} />
          <h3>Planilha de Compostos</h3>
          <p>Catálogo de compostos para consolidação do ETL interno</p>

          <label htmlFor="comp-upload" className={`btn btn-secondary${isProcessing ? ' disabled' : ''}`} aria-disabled={isProcessing}>
            <UploadIcon size={18} />
            <span>{files.compounds ? 'Alterar Arquivo' : 'Selecionar Arquivo'}</span>
          </label>
          <input id="comp-upload" type="file" accept=".xlsx,.xls" className="hidden"
            disabled={isProcessing}
            onChange={(e) => handleFileChange('compounds', e)} />

          {files.compounds && (
            <div className="file-info success">
              <CheckCircle size={16} />
              <div className="file-meta">
                <span className="file-name">{files.compounds.name}</span>
                <span className="file-size">{(files.compounds.size / 1024).toFixed(2)} KB</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Botões de Ação */}
      <div className="actions-bar">
        <button onClick={() => setFiles({ identification: null, abundance: null, compounds: null })} className="btn btn-ghost" disabled={isProcessing}>
          Limpar seleção
        </button>
        <button onClick={handleUpload} className="btn btn-primary large" disabled={isProcessing}>
          {isProcessing ? 'Processando...' : 'Iniciar processamento'}
        </button>
      </div>

      {missingFiles.length > 0 && !isProcessing && (
        <p className="text-muted">Faltam planilhas obrigatórias: {missingFiles.join(', ')}.</p>
      )}

      {/* Barra de Progresso do ETL */}
      {progressVisible && (
        <div className={`etl-progress-card${progressError ? ' has-error' : ''}`}>
          <div className="etl-progress-header">
            <h3>Progresso do Pipeline ETL</h3>
            <span className="etl-progress-pct">{Math.round(progress)}%</span>
          </div>

          <div className="etl-progress-track">
            <div
              className={`etl-progress-fill${progressError ? ' error' : progress >= 100 ? ' done' : ''}`}
              style={{ width: `${progress}%` }}
            />
          </div>

          {progressError && (
            <div className="etl-progress-error-msg">
              <XCircle size={16} />
              <span>{progressError}</span>
            </div>
          )}

          <ol className="etl-stages-list">
            {ETL_STAGES.map((stage, idx) => {
              const isDone = progress >= stage.pct
              const isActive = !progressError && idx === activeStageIndex && isProcessing
              const isErrored = !!progressError && idx === activeStageIndex

              return (
                <li
                  key={stage.id}
                  className={`etl-stage-item${isDone ? ' done' : ''}${isActive ? ' active' : ''}${isErrored ? ' errored' : ''}`}
                >
                  <span className="etl-stage-icon">
                    {isErrored
                      ? <XCircle size={15} />
                      : isDone
                        ? <CheckCircle size={15} />
                        : isActive
                          ? <Loader2 size={15} className="etl-spin" />
                          : <Clock size={15} />}
                  </span>
                  <span className="etl-stage-label">{stage.label}</span>
                  {isActive && <span className="etl-stage-badge">Em execução</span>}
                  {isErrored && <span className="etl-stage-badge error">Falhou</span>}
                </li>
              )
            })}
          </ol>
        </div>
      )}

      {/* Resultado final */}
      {uploadStatus && !isProcessing && (
        <div
          className={`status-card ${uploadStatus.type}`}
          role={uploadStatus.type === 'error' ? 'alert' : 'status'}
          tabIndex={uploadStatus.type === 'error' ? -1 : undefined}
          ref={statusMessageRef}
        >
          <header className="status-header">
            {uploadStatus.type === 'success' || uploadStatus.type === 'warning' ? <CheckCircle size={24} /> : <XCircle size={24} />}
            <h3>
              {uploadStatus.type === 'success' && 'Pipeline concluído'}
              {uploadStatus.type === 'warning' && 'Pipeline concluído com alertas'}
              {uploadStatus.type === 'error' && 'Falha no Upload'}
            </h3>
          </header>
          <p>{uploadStatus.message}</p>
          {uploadStatus.details && (
            <div className="details-box">
              <div className="detail-row"><span>Resultado:</span> <span>{OUTCOME_LABELS[uploadStatus.details.outcome] || uploadStatus.details.outcome || '-'}</span></div>
              <div className="detail-row"><span>Batch:</span> <code className="text-verde">{uploadStatus.details.batch_name || 'BIOLOGICAL_RANKING'}</code></div>
              <div className="detail-row"><span>Tempo:</span> <span>{uploadStatus.details.duration_seconds ? `${uploadStatus.details.duration_seconds}s` : 'n/d'}</span></div>
              <div className="detail-row"><span>ETL interno:</span> <span>{uploadStatus.details.etl_ok ? 'OK' : 'Falhou'}</span></div>
              <div className="detail-row"><span>Ranking:</span> <span>{uploadStatus.details.ranking_ok ? 'OK' : 'Falhou'}</span></div>
            </div>
          )}
          {Array.isArray(uploadStatus?.details?.external_sources) && uploadStatus.details.external_sources.length > 0 && (
            <div className="details-box source-status-box">
              <h4>Status por fonte externa</h4>
              {uploadStatus.details.external_sources.map((item, index) => (
                <div className="detail-row" key={`${item.source || 'fonte'}-${index}`}>
                  <span>{item.source || item.step || 'Fonte'}</span>
                  <span>{item.ok ? 'OK' : `Falhou${item.error ? `: ${item.error}` : ''}`}</span>
                </div>
              ))}
            </div>
          )}
          {uploadStatus?.details?.next_action && (
            <div className="postprocess-summary" role="status" aria-live="polite">
              <h4>Próximo passo recomendado</h4>
              <p>{uploadStatus.details.next_action}</p>
              <div className="postprocess-actions">
                <Link to="/dashboard" className="btn btn-primary">Ir para Dashboard</Link>
                <Link to="/reference" className="btn btn-secondary">Revisar referências</Link>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Upload
