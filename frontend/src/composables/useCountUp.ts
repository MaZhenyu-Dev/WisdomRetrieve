import { ref, watch, type Ref } from "vue";

export interface CountUpOptions {
  /** 起始值 */
  start?: number;
  /** 目标值 */
  end: number;
  /** 动画时长（ms） */
  duration?: number;
  /** 小数位 */
  decimals?: number;
  /** 是否使用 easeOutExpo 曲线 */
  ease?: boolean;
  /** 触发器：设为 true 时开始计数 */
  trigger?: Ref<boolean>;
}

function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

/**
 * 数字滚动 composable。
 * 当 trigger 变为 true 时，从 start 缓动到 end。
 */
export function useCountUp(opts: CountUpOptions): Ref<number> {
  const {
    start = 0,
    end,
    duration = 1400,
    decimals = 0,
    ease = true,
    trigger
  } = opts;
  const value = ref(start);

  const run = () => {
    const startTime = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - startTime) / duration);
      const eased = ease ? easeOutExpo(t) : t;
      const current = start + (end - start) * eased;
      value.value = decimals > 0 ? Number(current.toFixed(decimals)) : Math.round(current);
      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        value.value = end;
      }
    };
    requestAnimationFrame(tick);
  };

  if (trigger) {
    watch(
      trigger,
      (v) => {
        if (v) run();
      },
      { immediate: true }
    );
  } else {
    run();
  }

  return value;
}
