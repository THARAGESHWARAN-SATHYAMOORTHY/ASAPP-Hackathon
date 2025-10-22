import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CustomerSupport from './pages/CustomerSupport';
import AdminPanel from './pages/AdminPanel';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <h1 className="logo">✈️ Airline Support</h1>
            <div className="nav-links">
              <Link to="/" className="nav-link">Customer Support</Link>
              <Link to="/admin" className="nav-link">Admin Panel</Link>
            </div>
          </div>
        </nav>
        
        <Routes>
          <Route path="/" element={<CustomerSupport />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

