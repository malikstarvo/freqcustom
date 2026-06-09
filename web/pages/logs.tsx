import dynamic from "next/dynamic";
const Logs = dynamic(() => import("@/pages/Logs"), { ssr: false });
export default Logs;
