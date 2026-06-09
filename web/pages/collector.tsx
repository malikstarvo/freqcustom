import dynamic from "next/dynamic";
const Collector = dynamic(() => import("@/pages/Collector"), { ssr: false });
export default Collector;
