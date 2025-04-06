import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'

// Components
import Navbar from './components/Navbar'
import Footer from './components/Footer'

// Pages
import Home from './pages/Home'
import Conferences from './pages/Conferences'
import Papers from './pages/Papers'
import Trends from './pages/Trends'
import Query from './pages/Query'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }

  return (
    <Router>
      <div className={`app-container ${darkMode ? 'dark-mode' : ''}`}>
        <Navbar darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/conferences" element={<Conferences />} />
            <Route path="/papers" element={<Papers />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/query" element={<Query />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  )
}

export default App
