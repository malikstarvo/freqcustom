import dynamic from "next/dynamic";
const Market = dynamic(() => import("@/pages/Market"), { ssr: false });
export default Market;
