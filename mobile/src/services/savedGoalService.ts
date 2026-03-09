/**
 * Saved goals service — persists plans by goal type for goal-based orchestration.
 * Uses AsyncStorage for offline/session and syncs to backend when not in demo mode.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { getSavedGoalsApi, saveGoalApi } from './aiClient';
import type { GoalType } from './aiClient';

const STORAGE_KEY = 'saved_goals:v2';

export type SavedGoalPlan = {
  goalType: GoalType;
  target: number;
  currentInvested: number;
  monthlyContribution: number;
  yearsToReach: number;
  targetAge: number;
};

const IS_DEMO = process.env.EXPO_PUBLIC_DEMO_MODE === 'true';

export async function getSavedGoals(userId: string): Promise<Record<GoalType, SavedGoalPlan>> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const local: Record<string, SavedGoalPlan> = raw ? JSON.parse(raw) : {};
    if (IS_DEMO) return local as Record<GoalType, SavedGoalPlan>;
    try {
      const res = await getSavedGoalsApi(userId);
      if (res?.goals && typeof res.goals === 'object') {
        const merged = { ...local, ...res.goals };
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
        return merged as Record<GoalType, SavedGoalPlan>;
      }
    } catch {
      // Offline or API error: use local
    }
    return local as Record<GoalType, SavedGoalPlan>;
  } catch {
    return {} as Record<GoalType, SavedGoalPlan>;
  }
}

export async function saveSavedGoal(userId: string, plan: SavedGoalPlan): Promise<void> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const goals: Record<string, SavedGoalPlan> = raw ? JSON.parse(raw) : {};
    goals[plan.goalType] = plan;
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(goals));
  } catch {
    // ignore
  }
  if (!IS_DEMO) {
    try {
      await saveGoalApi(userId, plan);
    } catch {
      // Best-effort sync
    }
  }
}

export async function removeSavedGoal(userId: string, goalType: GoalType): Promise<void> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const goals: Record<string, SavedGoalPlan> = raw ? JSON.parse(raw) : {};
    delete goals[goalType];
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(goals));
  } catch {
    // ignore
  }
  // Backend could support DELETE; for now removal is local-only
}
