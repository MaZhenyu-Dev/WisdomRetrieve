import { MotionPlugin } from "@vueuse/motion";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import "./styles.css";

const app = createApp(App);

app.use(router);
app.use(ElementPlus);
app.use(MotionPlugin);

app.mount("#app");
