import dynamic from "next/dynamic";
const System = dynamic(() => import("@/pages/System"), { ssr: false });
export default System;
