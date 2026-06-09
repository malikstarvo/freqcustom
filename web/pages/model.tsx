import dynamic from "next/dynamic";
const Model = dynamic(() => import("@/pages/Model"), { ssr: false });
export default Model;
