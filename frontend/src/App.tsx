import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/common/Navbar';
import { Footer } from './components/common/Footer';
import { LoadingSpinner } from './components/common/LoadingSpinner';

const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const DiagnosticWizardPage = lazy(() => import('./pages/DiagnosticWizardPage').then(m => ({ default: m.DiagnosticWizardPage })));
const ResultPage = lazy(() => import('./pages/ResultPage').then(m => ({ default: m.ResultPage })));
const ExplanationCenterPage = lazy(() => import('./pages/ExplanationCenterPage').then(m => ({ default: m.ExplanationCenterPage })));
const HistoryPage = lazy(() => import('./pages/HistoryPage').then(m => ({ default: m.HistoryPage })));
const KnowledgeExplorerPage = lazy(() => import('./pages/KnowledgeExplorerPage').then(m => ({ default: m.KnowledgeExplorerPage })));

export const App: React.FC = () => {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-[#F2EEE4] text-[#2B2822]">
        <Navbar />
        <main className="flex-1">
          <Suspense
            fallback={
              <div className="flex items-center justify-center min-h-[60vh]">
                <LoadingSpinner message="Loading NetSage view..." />
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/diagnose" element={<DiagnosticWizardPage />} />
              <Route path="/results/:id" element={<ResultPage />} />
              <Route path="/explain/:id" element={<ExplanationCenterPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/knowledge" element={<KnowledgeExplorerPage />} />
            </Routes>
          </Suspense>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App;

