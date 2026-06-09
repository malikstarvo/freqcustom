import dynamic from "next/dynamic";
const Paper = dynamic(() => import("@/pages/Paper"), { ssr: false });
export default Paper;
