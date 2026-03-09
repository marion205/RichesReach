/**
 * Saved goal service — persists the user's plan (target, monthly, timeline) for goal-based orchestration.
 * Uses AsyncStorage for offline/session and syncs to backend when not in demo mode.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { getSavedGoalApi, saveGoalApi } from './aiClient';

const STORAGE_KEY = 'saved_goal:v1';

export type SavedGoalPlan = {
  target: number;
  currentInvested: number;
  monthlyContribution: number;
  yearsToReach: number;
  targetAge: number;
};

const IS_DEMO = process.env.EXPO_PUBLIC_DEMO_MODE === 'true';

export async function getSavedGoal(userId: string): Promise<SavedGoalPlan | null> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const local: SavedGoalPlan | null = raw ? JSON.parse(raw) : null;
    if (IS_DEMO) return local;
    try {
      const res = await getSavedGoalApi(userId);
      if (res?.goal) return res.goal as SavedGoalPlan;
    } catch {
      // Offline or API error: use local
    }
    return local;
  } catch {
    return null;
  }
}

export async function saveSavedGoal(userId: string, plan: SavedGoalPlan): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(plan));
  if (!IS_DEMO) {
    try {
      await saveGoalApi(userId, plan);
    } catch {
      // Best-effort sync; local is already saved
    }
  }
}
