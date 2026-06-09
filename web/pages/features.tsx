import dynamic from "next/dynamic";
const Features = dynamic(() => import("@/pages/Features"), { ssr: false });
export default Features;
