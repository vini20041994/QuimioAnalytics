import { Link, useLocation } from 'react-router-dom'
import { BarChart3, TrendingUp, Upload, Database } from 'lucide-react'
import './Navbar.css'

function Navbar() {
  const location = useLocation()
  
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { path: '/ranking', label: 'Top 5 Ranking', icon: TrendingUp },
    { path: '/upload', label: 'Upload', icon: Upload },
    { path: '/reference', label: 'Referências', icon: Database },
  ]
  
  return (
    <nav className="navbar">
      <div className="navbar-container">
        
        {/* Branding */}
        <div className="navbar-brand">
          <div className="brand-logo">
           <img src="./src/public/logo.png" alt="logo" />
          </div>
          <div className="brand-text">
              <h1 className="brand-title">
                Quimio<span className="text-verde-analytics">Analytics</span>
              </h1>
              <p className="brand-subtitle">Inteligência em Dados Químicos</p>
            </div>
          </div>
        
        {/* Navegação */}
        <div className="nav-menu">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} className="nav-icon" />
                <span className="nav-label">{item.label}</span>
              </Link>
            )
          })}
        </div>

      </div>
    </nav>
  )
}

export default Navbar