import dynamic from "next/dynamic";
const Balance = dynamic(() => import("@/pages/Balance"), { ssr: false });
export default Balance;
