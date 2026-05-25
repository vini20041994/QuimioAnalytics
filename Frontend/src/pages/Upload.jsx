import { useState } from 'react'
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { api } from '../services/api'
import './Upload.css'

function Upload() {
  const [files, setFiles] = useState({ identification: null, abundance: null })
  const [uploadStatus, setUploadStatus] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const handleFileChange = (type, event) => {
    const file = event.target.files[0]
    if (file) {
      setFiles(prev => ({ ...prev, [type]: file }))
      setUploadStatus(null)
    }
  }
  
  const handleUpload = async () => {
    if (!files.identification || !files.abundance) {
      setUploadStatus({ type: 'error', message: 'Por favor, selecione ambos os arquivos antes de enviar.' })
      return
    }

    setIsProcessing(true)

    try {
      const response = await api.uploadFiles({
        identification: files.identification,
        abundance: files.abundance,
      })

      setUploadStatus({
        type: 'success',
        message: response?.message || 'Arquivos carregados com sucesso! O ETL foi iniciado.',
        details: response?.details,
      })
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: err.message || 'Falha ao enviar arquivos para processamento.',
      })
    } finally {
      setIsProcessing(false)
    }
  }
  
  return (
    <div className="upload-page">
      <header className="page-header">
        <h1 className="page-title">Upload de Planilhas</h1>
        <p className="page-subtitle">Envie as planilhas de Identificação e Abundância para processamento ETL</p>
      </header>
      
      {/* Card de Instruções */}
      <div className="alert-card info">
        <AlertTriangle className="alert-icon" size={24} />
        <div className="alert-content">
          <h3>Instruções de Upload</h3>
          <ul className="instruction-list">
            <li>Selecione a planilha de <strong>Identificação</strong> (.xlsx ou .csv)</li>
            <li>Selecione a planilha de <strong>Abundância</strong> (.xlsx ou .csv)</li>
            <li>Aguarde a confirmação antes de sair da página</li>
          </ul>
        </div>
      </div>
      
      {/* Upload Area */}
      <div className="upload-grid">
        {/* Card Identificação */}
        <div className="upload-card">
          <FileSpreadsheet className="icon-main text-verde" size={48} />
          <h3>Planilha de Identificação</h3>
          <p>Contém dados de m/z, RT, fórmula molecular e candidatos</p>
          
          <label htmlFor="id-upload" className="btn btn-secondary">
            <UploadIcon size={18} />
            <span>{files.identification ? 'Alterar Arquivo' : 'Selecionar Arquivo'}</span>
          </label>
          <input id="id-upload" type="file" accept=".xlsx,.csv" className="hidden" 
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
          
          <label htmlFor="ab-upload" className="btn btn-primary">
            <UploadIcon size={18} />
            <span>{files.abundance ? 'Alterar Arquivo' : 'Selecionar Arquivo'}</span>
          </label>
          <input id="ab-upload" type="file" accept=".xlsx,.csv" className="hidden"
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
      </div>
      
      {/* Botões de Ação */}
      <div className="actions-bar">
        <button onClick={() => setFiles({identification:null, abundance:null})} className="btn btn-ghost" disabled={isProcessing}>
          Limpar Seleção
        </button>
        <button onClick={handleUpload} className="btn btn-primary large" 
                disabled={!files.identification || !files.abundance || isProcessing}>
          {isProcessing ? 'Processando...' : 'Iniciar ETL'}
        </button>
      </div>
      
      {/* Status e Histórico simplificados abaixo */}
      {uploadStatus && (
        <div className={`status-card ${uploadStatus.type}`}>
           <header className="status-header">
             {uploadStatus.type === 'success' ? <CheckCircle size={24}/> : <XCircle size={24}/>}
             <h3>{uploadStatus.type === 'success' ? 'Pipeline Iniciado' : 'Falha no Upload'}</h3>
           </header>
           <p>{uploadStatus.message}</p>
           {uploadStatus.details && (
             <div className="details-box">
               <div className="detail-row"><span>Batch ID:</span> <code className="text-verde">{uploadStatus.details.batch_name}</code></div>
               <div className="detail-row"><span>Total Processado:</span> <span>{uploadStatus.details.identification_rows + uploadStatus.details.abundance_rows} linhas</span></div>
             </div>
           )}
        </div>
      )}
    </div>
  )
}

export default Upload