import dynamic from "next/dynamic";
const Trading = dynamic(() => import("@/pages/Trading"), { ssr: false });
export default Trading;
