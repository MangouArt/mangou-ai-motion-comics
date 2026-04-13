import fs from 'node:fs';
import path from 'node:path';

export interface AppConfig {
  bltai?: {
    apiKey: string;
    baseUrl: string;
  };
  workspaceDir: string;
  lastProjectId?: string;
}

const DEFAULT_CONFIG: AppConfig = {
  workspaceDir: 'projects',
};

function resolveConfigPath() {
  const envRoot = process.env.MANGOU_HOME || process.cwd();
  return path.resolve(envRoot, 'config.json');
}

class ConfigStore {
  private config: AppConfig;

  constructor() {
    this.config = this.loadConfig();
  }

  private loadConfig(): AppConfig {
    try {
      const configPath = resolveConfigPath();
      if (!fs.existsSync(configPath)) {
        return { ...DEFAULT_CONFIG };
      }
      const data = fs.readFileSync(configPath, 'utf-8');
      return { ...DEFAULT_CONFIG, ...JSON.parse(data) };
    } catch {
      return { ...DEFAULT_CONFIG };
    }
  }

  get<K extends keyof AppConfig>(key: K): AppConfig[K] {
    return this.config[key];
  }

  set<K extends keyof AppConfig>(key: K, value: AppConfig[K]): void {
    this.config[key] = value;
    this.saveConfig();
  }

  update(patch: Partial<AppConfig>): void {
    this.config = { ...this.config, ...patch };
    this.saveConfig();
  }

  private saveConfig() {
    try {
      const configPath = resolveConfigPath();
      fs.writeFileSync(configPath, JSON.stringify(this.config, null, 2), 'utf-8');
    } catch {
      // ignore
    }
  }

  getAll(): AppConfig {
    return { ...this.config };
  }
}

export const configStore = new ConfigStore();
