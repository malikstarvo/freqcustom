import dynamic from "next/dynamic";
const Config = dynamic(() => import("@/pages/Config"), { ssr: false });
export default Config;
