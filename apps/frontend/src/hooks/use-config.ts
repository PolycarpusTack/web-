import { useState } from 'react';

export interface Config {
  style: string;
  theme: string;
  radius: number;
}

const defaultConfig: Config = {
  style: 'default',
  theme: 'zinc',
  radius: 0.5,
};

export function useConfig() {
  const [config, setConfig] = useState<Config>(() => {
    const stored = localStorage.getItem('config');
    return stored ? JSON.parse(stored) : defaultConfig;
  });

  const updateConfig = (updates: Partial<Config>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    localStorage.setItem('config', JSON.stringify(newConfig));
  };

  return {
    config,
    setConfig: updateConfig,
  };
}