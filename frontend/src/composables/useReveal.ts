import { useIntersectionObserver } from "@vueuse/core";
import { ref, type Ref } from "vue";

/**
 * 滚动到视口时触发一次的 composable。
 * 给元素加 v-reveal，配合 .reveal/.in-view CSS 即可做"滚动入场"。
 */
export function useReveal<T extends HTMLElement = HTMLElement>(
  options: IntersectionObserverInit = { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
): { target: Ref<T | null>; isInView: Ref<boolean> } {
  const target = ref<T | null>(null) as Ref<T | null>;
  const isInView = ref(false);

  useIntersectionObserver(
    target as unknown as Ref<HTMLElement>,
    ([entry]) => {
      if (entry?.isIntersecting) {
        isInView.value = true;
      }
    },
    options as Parameters<typeof useIntersectionObserver>[2]
  );

  return { target, isInView };
}
