import React, { createContext, useContext, useState, useEffect } from 'react';
import { Appearance, useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Theme Types
export interface Theme {
  name: string;
  displayName: string;
  description: string;
  category: 'cultural' | 'accessibility' | 'professional' | 'creative';
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    // Accessibility colors
    highContrast: string;
    lowContrast: string;
    // Cultural colors
    culturalPrimary: string;
    culturalSecondary: string;
    culturalAccent: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: number;
      sm: number;
      md: number;
      lg: number;
      xl: number;
      xxl: number;
    };
    fontWeight: {
      light: string;
      regular: string;
      medium: string;
      bold: string;
    };
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  shadows: {
    sm: any;
    md: any;
    lg: any;
    xl: any;
  };
  accessibility: {
    highContrast: boolean;
    largeText: boolean;
    reducedMotion: boolean;
    voiceNavigation: boolean;
  };
}

// BIPOC-Inspired Cultural Themes
export const CULTURAL_THEMES: Theme[] = [
  {
    name: 'african_heritage',
    displayName: 'African Heritage',
    description: 'Rich earth tones and vibrant colors inspired by African culture',
    category: 'cultural',
    colors: {
      primary: '#D2691E', // Sienna
      secondary: '#8B4513', // Saddle Brown
      accent: '#FFD700', // Gold
      background: '#F5F5DC', // Beige
      surface: '#FFFFFF',
      text: '#2F2F2F',
      textSecondary: '#666666',
      border: '#D3D3D3',
      success: '#228B22',
      warning: '#FF8C00',
      error: '#DC143C',
      info: '#4169E1',
      highContrast: '#000000',
      lowContrast: '#808080',
      culturalPrimary: '#D2691E',
      culturalSecondary: '#8B4513',
      culturalAccent: '#FFD700',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18, xl: 20, xxl: 24 },
      fontWeight: { light: '300', regular: '400', medium: '500', bold: '700' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
    borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
      md: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4, elevation: 4 },
      lg: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.25, shadowRadius: 16, elevation: 16 },
    },
    accessibility: {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      voiceNavigation: false,
    },
  },
  {
    name: 'latinx_vibrancy',
    displayName: 'Latinx Vibrancy',
    description: 'Bold, energetic colors celebrating Latinx culture and traditions',
    category: 'cultural',
    colors: {
      primary: '#FF6B35', // Orange Red
      secondary: '#F7931E', // Orange
      accent: '#FFD700', // Gold
      background: '#FFF8DC', // Cornsilk
      surface: '#FFFFFF',
      text: '#2F2F2F',
      textSecondary: '#666666',
      border: '#D3D3D3',
      success: '#32CD32',
      warning: '#FFA500',
      error: '#FF4500',
      info: '#1E90FF',
      highContrast: '#000000',
      lowContrast: '#808080',
      culturalPrimary: '#FF6B35',
      culturalSecondary: '#F7931E',
      culturalAccent: '#FFD700',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18, xl: 20, xxl: 24 },
      fontWeight: { light: '300', regular: '400', medium: '500', bold: '700' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
    borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
      md: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4, elevation: 4 },
      lg: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.25, shadowRadius: 16, elevation: 16 },
    },
    accessibility: {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      voiceNavigation: false,
    },
  },
  {
    name: 'asian_harmony',
    displayName: 'Asian Harmony',
    description: 'Balanced, harmonious colors inspired by Asian design principles',
    category: 'cultural',
    colors: {
      primary: '#4A90E2', // Blue
      secondary: '#7B68EE', // Medium Slate Blue
      accent: '#FFD700', // Gold
      background: '#F8F8FF', // Ghost White
      surface: '#FFFFFF',
      text: '#2F2F2F',
      textSecondary: '#666666',
      border: '#D3D3D3',
      success: '#00CED1',
      warning: '#FFB347',
      error: '#FF6347',
      info: '#87CEEB',
      highContrast: '#000000',
      lowContrast: '#808080',
      culturalPrimary: '#4A90E2',
      culturalSecondary: '#7B68EE',
      culturalAccent: '#FFD700',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18, xl: 20, xxl: 24 },
      fontWeight: { light: '300', regular: '400', medium: '500', bold: '700' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
    borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
      md: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4, elevation: 4 },
      lg: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.25, shadowRadius: 16, elevation: 16 },
    },
    accessibility: {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      voiceNavigation: false,
    },
  },
  {
    name: 'indigenous_wisdom',
    displayName: 'Indigenous Wisdom',
    description: 'Natural, earthy tones reflecting Indigenous connection to nature',
    category: 'cultural',
    colors: {
      primary: '#8FBC8F', // Dark Sea Green
      secondary: '#A0522D', // Sienna
      accent: '#DAA520', // Goldenrod
      background: '#F0F8FF', // Alice Blue
      surface: '#FFFFFF',
      text: '#2F2F2F',
      textSecondary: '#666666',
      border: '#D3D3D3',
      success: '#9ACD32',
      warning: '#DAA520',
      error: '#CD5C5C',
      info: '#20B2AA',
      highContrast: '#000000',
      lowContrast: '#808080',
      culturalPrimary: '#8FBC8F',
      culturalSecondary: '#A0522D',
      culturalAccent: '#DAA520',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18, xl: 20, xxl: 24 },
      fontWeight: { light: '300', regular: '400', medium: '500', bold: '700' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
    borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
      md: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4, elevation: 4 },
      lg: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.25, shadowRadius: 16, elevation: 16 },
    },
    accessibility: {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      voiceNavigation: false,
    },
  },
];

// Accessibility Themes
export const ACCESSIBILITY_THEMES: Theme[] = [
  {
    name: 'high_contrast',
    displayName: 'High Contrast',
    description: 'Maximum contrast for better visibility',
    category: 'accessibility',
    colors: {
      primary: '#000000',
      secondary: '#FFFFFF',
      accent: '#FFFF00',
      background: '#FFFFFF',
      surface: '#F0F0F0',
      text: '#000000',
      textSecondary: '#333333',
      border: '#000000',
      success: '#008000',
      warning: '#FF8C00',
      error: '#FF0000',
      info: '#0000FF',
      highContrast: '#000000',
      lowContrast: '#FFFFFF',
      culturalPrimary: '#000000',
      culturalSecondary: '#FFFFFF',
      culturalAccent: '#FFFF00',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 14, sm: 16, md: 18, lg: 20, xl: 22, xxl: 26 },
      fontWeight: { light: '400', regular: '500', medium: '600', bold: '700' },
    },
    spacing: { xs: 6, sm: 12, md: 18, lg: 24, xl: 30, xxl: 36 },
    borderRadius: { sm: 6, md: 10, lg: 14, xl: 18 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, shadowRadius: 4, elevation: 4 },
      md: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.4, shadowRadius: 6, elevation: 6 },
      lg: { shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.5, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.6, shadowRadius: 12, elevation: 12 },
    },
    accessibility: {
      highContrast: true,
      largeText: true,
      reducedMotion: false,
      voiceNavigation: true,
    },
  },
  {
    name: 'large_text',
    displayName: 'Large Text',
    description: 'Enhanced text size for better readability',
    category: 'accessibility',
    colors: {
      primary: '#667eea',
      secondary: '#764ba2',
      accent: '#f093fb',
      background: '#f8f9fa',
      surface: '#ffffff',
      text: '#1a1a1a',
      textSecondary: '#666666',
      border: '#e0e0e0',
      success: '#34c759',
      warning: '#ff9500',
      error: '#ff3b30',
      info: '#007aff',
      highContrast: '#000000',
      lowContrast: '#ffffff',
      culturalPrimary: '#667eea',
      culturalSecondary: '#764ba2',
      culturalAccent: '#f093fb',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 16, sm: 18, md: 20, lg: 22, xl: 24, xxl: 28 },
      fontWeight: { light: '400', regular: '500', medium: '600', bold: '700' },
    },
    spacing: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24, xxl: 28 },
    borderRadius: { sm: 6, md: 10, lg: 14, xl: 18 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
      md: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4, elevation: 4 },
      lg: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.25, shadowRadius: 16, elevation: 16 },
    },
    accessibility: {
      highContrast: false,
      largeText: true,
      reducedMotion: false,
      voiceNavigation: true,
    },
  },
  {
    name: 'reduced_motion',
    displayName: 'Reduced Motion',
    description: 'Minimized animations for motion sensitivity',
    category: 'accessibility',
    colors: {
      primary: '#667eea',
      secondary: '#764ba2',
      accent: '#f093fb',
      background: '#f8f9fa',
      surface: '#ffffff',
      text: '#1a1a1a',
      textSecondary: '#666666',
      border: '#e0e0e0',
      success: '#34c759',
      warning: '#ff9500',
      error: '#ff3b30',
      info: '#007aff',
      highContrast: '#000000',
      lowContrast: '#ffffff',
      culturalPrimary: '#667eea',
      culturalSecondary: '#764ba2',
      culturalAccent: '#f093fb',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18, xl: 20, xxl: 24 },
      fontWeight: { light: '300', regular: '400', medium: '500', bold: '700' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
    borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 1, elevation: 1 },
      md: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.08, shadowRadius: 2, elevation: 2 },
      lg: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 3, elevation: 3 },
      xl: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.12, shadowRadius: 4, elevation: 4 },
    },
    accessibility: {
      highContrast: false,
      largeText: false,
      reducedMotion: true,
      voiceNavigation: false,
    },
  },
];

// Professional Themes
export const PROFESSIONAL_THEMES: Theme[] = [
  {
    name: 'corporate_blue',
    displayName: 'Corporate Blue',
    description: 'Professional blue theme for business use',
    category: 'professional',
    colors: {
      primary: '#1e3a8a',
      secondary: '#3b82f6',
      accent: '#60a5fa',
      background: '#f8fafc',
      surface: '#ffffff',
      text: '#1e293b',
      textSecondary: '#64748b',
      border: '#e2e8f0',
      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      info: '#0284c7',
      highContrast: '#000000',
      lowContrast: '#ffffff',
      culturalPrimary: '#1e3a8a',
      culturalSecondary: '#3b82f6',
      culturalAccent: '#60a5fa',
    },
    typography: {
      fontFamily: 'System',
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18, xl: 20, xxl: 24 },
      fontWeight: { light: '300', regular: '400', medium: '500', bold: '700' },
    },
    spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
    borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 },
    shadows: {
      sm: { shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
      md: { shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4, elevation: 4 },
      lg: { shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 8 },
      xl: { shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.25, shadowRadius: 16, elevation: 16 },
    },
    accessibility: {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      voiceNavigation: false,
    },
  },
];

// Theme Context
interface ThemeContextType {
  currentTheme: Theme;
  setTheme: (theme: Theme) => void;
  availableThemes: Theme[];
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  accessibilitySettings: Theme['accessibility'];
  updateAccessibilitySettings: (settings: Partial<Theme['accessibility']>) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Theme Provider
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemColorScheme = useColorScheme();
  const [currentTheme, setCurrentTheme] = useState<Theme>(CULTURAL_THEMES[0]);
  const [isDarkMode, setIsDarkMode] = useState(systemColorScheme === 'dark');
  const [accessibilitySettings, setAccessibilitySettings] = useState<Theme['accessibility']>({
    highContrast: false,
    largeText: false,
    reducedMotion: false,
    voiceNavigation: false,
  });

  // Load saved theme on app start
  useEffect(() => {
    loadSavedTheme();
  }, []);

  // Apply accessibility settings to current theme
  useEffect(() => {
    applyAccessibilitySettings();
  }, [accessibilitySettings]);

  const loadSavedTheme = async () => {
    try {
      const savedThemeName = await AsyncStorage.getItem('selectedTheme');
      const savedAccessibility = await AsyncStorage.getItem('accessibilitySettings');
      const savedDarkMode = await AsyncStorage.getItem('isDarkMode');
      
      if (savedThemeName) {
        const allThemes = [...CULTURAL_THEMES, ...ACCESSIBILITY_THEMES, ...PROFESSIONAL_THEMES];
        const theme = allThemes.find(t => t.name === savedThemeName);
        if (theme) {
          setCurrentTheme(theme);
        }
      }
      
      if (savedAccessibility) {
        setAccessibilitySettings(JSON.parse(savedAccessibility));
      }
      
      if (savedDarkMode) {
        const isDark = JSON.parse(savedDarkMode);
        setIsDarkMode(isDark);
        
        // Apply dark mode to current theme if needed
        if (isDark) {
          const updatedTheme = { ...currentTheme };
          updatedTheme.colors.background = '#1a1a1a';
          updatedTheme.colors.surface = '#2a2a2a';
          updatedTheme.colors.text = '#ffffff';
          updatedTheme.colors.textSecondary = '#cccccc';
          updatedTheme.colors.border = '#404040';
          setCurrentTheme(updatedTheme);
        }
      }
    } catch (error) {
      console.error('Error loading saved theme:', error);
    }
  };

  const applyAccessibilitySettings = () => {
    const updatedTheme = { ...currentTheme };
    
    if (accessibilitySettings.highContrast) {
      updatedTheme.colors.text = '#000000';
      updatedTheme.colors.background = '#FFFFFF';
      updatedTheme.colors.border = '#000000';
    }
    
    if (accessibilitySettings.largeText) {
      Object.keys(updatedTheme.typography.fontSize).forEach(key => {
        updatedTheme.typography.fontSize[key as keyof typeof updatedTheme.typography.fontSize] += 2;
      });
    }
    
    setCurrentTheme(updatedTheme);
  };

  const setTheme = async (theme: Theme) => {
    setCurrentTheme(theme);
    try {
      await AsyncStorage.setItem('selectedTheme', theme.name);
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  };

  const toggleDarkMode = async () => {
    const newDarkMode = !isDarkMode;
    setIsDarkMode(newDarkMode);
    
    try {
      await AsyncStorage.setItem('isDarkMode', JSON.stringify(newDarkMode));
      
      // Apply dark mode to current theme
      const updatedTheme = { ...currentTheme };
      if (newDarkMode) {
        // Apply dark mode colors
        updatedTheme.colors.background = '#1a1a1a';
        updatedTheme.colors.surface = '#2a2a2a';
        updatedTheme.colors.text = '#ffffff';
        updatedTheme.colors.textSecondary = '#cccccc';
        updatedTheme.colors.border = '#404040';
      } else {
        // Apply light mode colors
        updatedTheme.colors.background = '#f8f9fa';
        updatedTheme.colors.surface = '#ffffff';
        updatedTheme.colors.text = '#1a1a1a';
        updatedTheme.colors.textSecondary = '#666666';
        updatedTheme.colors.border = '#e0e0e0';
      }
      
      setCurrentTheme(updatedTheme);
    } catch (error) {
      console.error('Error saving dark mode preference:', error);
    }
  };

  const updateAccessibilitySettings = async (settings: Partial<Theme['accessibility']>) => {
    const newSettings = { ...accessibilitySettings, ...settings };
    setAccessibilitySettings(newSettings);
    
    try {
      await AsyncStorage.setItem('accessibilitySettings', JSON.stringify(newSettings));
    } catch (error) {
      console.error('Error saving accessibility settings:', error);
    }
  };

  const availableThemes = [
    ...CULTURAL_THEMES,
    ...ACCESSIBILITY_THEMES,
    ...PROFESSIONAL_THEMES,
  ];

  return (
    <ThemeContext.Provider
      value={{
        currentTheme,
        setTheme,
        availableThemes,
        isDarkMode,
        toggleDarkMode,
        accessibilitySettings,
        updateAccessibilitySettings,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

// Theme Hook
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Theme Utilities
export const getThemeStyles = (theme: Theme) => ({
  container: {
    backgroundColor: theme.colors.background,
    flex: 1,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.md,
    ...theme.shadows.md,
  },
  text: {
    color: theme.colors.text,
    fontSize: theme.typography.fontSize.md,
    fontFamily: theme.typography.fontFamily,
    fontWeight: theme.typography.fontWeight.regular,
  },
  textSecondary: {
    color: theme.colors.textSecondary,
    fontSize: theme.typography.fontSize.sm,
    fontFamily: theme.typography.fontFamily,
    fontWeight: theme.typography.fontWeight.regular,
  },
  button: {
    backgroundColor: theme.colors.primary,
    borderRadius: theme.borderRadius.md,
    padding: theme.spacing.md,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
  },
  buttonText: {
    color: theme.colors.surface,
    fontSize: theme.typography.fontSize.md,
    fontFamily: theme.typography.fontFamily,
    fontWeight: theme.typography.fontWeight.medium,
  },
  input: {
    borderColor: theme.colors.border,
    borderWidth: 1,
    borderRadius: theme.borderRadius.md,
    padding: theme.spacing.md,
    fontSize: theme.typography.fontSize.md,
    fontFamily: theme.typography.fontFamily,
    color: theme.colors.text,
    backgroundColor: theme.colors.surface,
  },
});

// Accessibility Utilities
export const getAccessibilityProps = (theme: Theme) => ({
  accessible: true,
  accessibilityRole: 'button' as const,
  accessibilityLabel: 'Button',
  accessibilityHint: 'Double tap to activate',
  ...(theme.accessibility.voiceNavigation && {
    accessibilityActions: [
      { name: 'activate', label: 'Activate' },
    ],
  }),
});

// Animation Utilities
export const getAnimationConfig = (theme: Theme) => ({
  duration: theme.accessibility.reducedMotion ? 0 : 300,
  useNativeDriver: true,
});
