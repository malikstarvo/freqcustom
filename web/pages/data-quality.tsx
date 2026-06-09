import dynamic from "next/dynamic";
const DataQuality = dynamic(() => import("@/pages/DataQuality"), { ssr: false });
export default DataQuality;
