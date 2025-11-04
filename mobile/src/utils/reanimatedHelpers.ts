/**
 * Safe Reanimated helpers to prevent reentrancy crashes
 * 
 * These helpers prevent calling runOnUI from within a worklet,
 * which causes SIGABRT crashes in Hermes + Reanimated 3.
 */

import { runOnUI, runOnJS } from 'react-native-reanimated';

/**
 * Check if we're currently on the UI thread (worklet context)
 */
export function isWorklet() {
  'worklet';
  return typeof _WORKLET !== 'undefined' && _WORKLET === true;
}

/**
 * DEPRECATED: Do not use. Always use runOnJS from within worklets.
 * 
 * This function was intended to be safe but can still cause reentrancy.
 * The correct pattern is:
 * - If you're in a worklet and need to do JS side-effects: use runOnJS
 * - If you're in JS and need UI work: use runOnUI (but not from within a worklet)
 */
export function safeRunOnUI<T extends (...args: any[]) => void>(
  fn: T,
): T {
  'worklet';
  
  // CRITICAL FIX: If we're already on UI thread, we MUST bounce to JS first
  // Never call runOnUI from within a worklet - it causes reentrancy crashes
  if (isWorklet()) {
    // We're in a worklet, so we need to use runOnJS to get to JS thread first
    // Then from JS we can safely use runOnUI if needed
    return ((...args: Parameters<T>) => {
      runOnJS((fnPtr, ...fnArgs) => {
        // Now we're on JS thread, safe to call the function
        // But actually, if the function needs UI thread work, it should handle that itself
        (fnPtr as any)(...fnArgs);
      })(fn, ...args);
    }) as T;
  }
  
  // We're on JS thread, safe to use runOnUI
  return ((...args: Parameters<T>) => {
    runOnUI(fn)(...args);
  }) as T;
}

/**
 * Safely execute an animation, ensuring we're not re-entering the UI thread
 */
export function safeAnimate(
  value: { value: number },
  animation: (target: number) => any,
  target: number,
) {
  'worklet';
  
  // If already on UI thread, we need to bounce back to JS first
  if (isWorklet()) {
    runOnJS((val, anim, tgt) => {
      val.value = anim(tgt);
    })(value, animation, target);
    return;
  }
  
  // Otherwise, safe to animate directly
  value.value = animation(target);
}

