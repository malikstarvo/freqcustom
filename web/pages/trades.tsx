import dynamic from "next/dynamic";
const Trades = dynamic(() => import("@/pages/Trades"), { ssr: false });
export default Trades;
