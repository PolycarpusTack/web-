import { useState, useCallback } from 'react';

export interface ModelSettings {
  temperature: number;
  maxTokens: number;
  topP: number;
  topK?: number;
  streamResponse: boolean;
  stopSequences?: string[];
  frequencyPenalty?: number;
  presencePenalty?: number;
}

const DEFAULT_SETTINGS: ModelSettings = {
  temperature: 0.7,
  maxTokens: 2000,
  topP: 0.95,
  streamResponse: true
};

interface UseModelSettingsReturn {
  settings: ModelSettings;
  updateSetting: <K extends keyof ModelSettings>(key: K, value: ModelSettings[K]) => void;
  updateSettings: (updates: Partial<ModelSettings>) => void;
  resetSettings: () => void;
  isDefaultSettings: boolean;
}

export const useModelSettings = (
  initialSettings?: Partial<ModelSettings>
): UseModelSettingsReturn => {
  const [settings, setSettings] = useState<ModelSettings>({
    ...DEFAULT_SETTINGS,
    ...initialSettings
  });

  const updateSetting = useCallback(
    <K extends keyof ModelSettings>(key: K, value: ModelSettings[K]) => {
      setSettings(prev => ({ ...prev, [key]: value }));
    },
    []
  );

  const updateSettings = useCallback((updates: Partial<ModelSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  const isDefaultSettings = 
    settings.temperature === DEFAULT_SETTINGS.temperature &&
    settings.maxTokens === DEFAULT_SETTINGS.maxTokens &&
    settings.topP === DEFAULT_SETTINGS.topP &&
    settings.streamResponse === DEFAULT_SETTINGS.streamResponse;

  return {
    settings,
    updateSetting,
    updateSettings,
    resetSettings,
    isDefaultSettings
  };
};