import fs from "node:fs/promises";
import { stringifyYAML } from "@core/yaml";

export async function writeStoryboardYaml(options: { absolutePath: string; yamlPathForValidation: string; data: Record<string, any> }) {
  if (!options.data?.meta?.id || !options.data?.content) {
    throw new Error(`Invalid storyboard yaml payload for ${options.yamlPathForValidation}`);
  }
  await fs.writeFile(options.absolutePath, stringifyYAML(options.data), "utf-8");
}
