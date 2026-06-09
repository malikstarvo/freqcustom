import dynamic from "next/dynamic";
const Overview = dynamic(() => import("@/pages/Overview"), { ssr: false });
export default Overview;
