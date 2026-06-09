import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Trading from "./pages/Trading";
import TradesPage from "./pages/Trades";
import Balance from "./pages/Balance";
import Paper from "./pages/Paper";
import ModelPage from "./pages/Model";
import Backtest from "./pages/Backtest";
import Logs from "./pages/Logs";
import Config from "./pages/Config";
import System from "./pages/System";
import Overview from "./pages/Overview";
import Market from "./pages/Market";
import DataQuality from "./pages/DataQuality";
import Features from "./pages/Features";
import Collector from "./pages/Collector";
import NotFound from "./pages/NotFound";
import { ToastProvider } from "./hooks/useToast";
import { ThemeProvider } from "./hooks/useTheme";

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trading" element={<Trading />} />
        <Route path="/trades" element={<TradesPage />} />
        <Route path="/balance" element={<Balance />} />
        <Route path="/paper" element={<Paper />} />
        <Route path="/model" element={<ModelPage />} />
        <Route path="/backtest" element={<Backtest />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/config" element={<Config />} />
        <Route path="/system" element={<System />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/market" element={<Market />} />
        <Route path="/data-quality" element={<DataQuality />} />
        <Route path="/features" element={<Features />} />
        <Route path="/collector" element={<Collector />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
      </ToastProvider>
    </ThemeProvider>
  );
}
