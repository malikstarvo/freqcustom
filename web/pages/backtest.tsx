import dynamic from "next/dynamic";
const Backtest = dynamic(() => import("@/pages/Backtest"), { ssr: false });
export default Backtest;
