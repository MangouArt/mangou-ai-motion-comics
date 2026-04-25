#!/usr/bin/env bun
import { AIGC_PROVIDER_TEMPLATE } from '@logic/aigc-provider-template';

type AnyIntContentItem =
  | { type: 'text'; text: string }
  | { type: 'image_url'; role: string; image_url: { url: string } }
  | { type: 'video_url'; role: string; video_url: { url: string } }
  | { type: 'audio_url'; role: string; audio_url: { url: string } };

const SUPPORTED_MODELS = new Set([
  'doubao-seedance-2-0-260128',
  'doubao-seedance-2-0-fast-260128',
]);

const ALLOWED_RATIOS = new Set([
  '21:9',
  '16:9',
  '4:3',
  '1:1',
  '3:4',
  '9:16',
  'adaptive',
]);

const ALLOWED_RESOLUTIONS = new Set([
  '480p',
  '720p',
]);

const ROLE_BY_TYPE: Record<string, Set<string>> = {
  image_url: new Set(['first_frame', 'last_frame', 'reference_image']),
  video_url: new Set(['reference_video']),
  audio_url: new Set(['reference_audio']),
};

function joinUrl(base: any, ...parts: any[]) {
  const normalizedBase = String(base || '').replace(/\/+$/, '');
  const normalizedPath = parts
    .map((part) => String(part || '').replace(/^\/+/, '').replace(/\/+$/, ''))
    .filter(Boolean)
    .join('/');
  return normalizedPath ? `${normalizedBase}/${normalizedPath}` : normalizedBase;
}

function normalizeBaseUrl(baseUrl: any) {
  return String(baseUrl || '').trim().replace(/\/+$/, '') || 'https://gateway.api.anyint.ai';
}

async function fetchWithRetry(url: any, options: any, maxRetries = 3) {
  let lastError: unknown;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetch(url, options);
    } catch (err: unknown) {
      lastError = err;
      if (i < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000 * (i + 1)));
      }
    }
  }
  throw lastError;
}

async function parseJsonResponse(response: Response, context: string) {
  if (typeof (response as any).text !== 'function') {
    if (typeof (response as any).json === 'function') {
      return await (response as any).json();
    }
    throw new Error(`[anyint] Failed to parse JSON from ${context}: response has neither text() nor json()`);
  }

  const raw = await response.text();
  try {
    return JSON.parse(raw);
  } catch {
    const preview = raw.slice(0, 400);
    throw new Error(`[anyint] Failed to parse JSON from ${context}: ${response.status} ${preview}`);
  }
}

function validateDuration(duration: any) {
  const value = duration === undefined || duration === null || duration === '' ? 5 : Number(duration);
  if (!Number.isFinite(value) || value < 4 || value > 15) {
    throw new Error('[anyint] duration 必须在 4 到 15 秒之间');
  }
  return value;
}

function validateRatio(ratio: any) {
  const value = ratio === undefined || ratio === null || ratio === '' ? 'adaptive' : String(ratio);
  if (!ALLOWED_RATIOS.has(value)) {
    throw new Error("[anyint] ratio 只接受 '21:9'、'16:9'、'4:3'、'1:1'、'3:4'、'9:16' 或 'adaptive'");
  }
  return value;
}

function validateResolution(resolution: any) {
  const value = resolution === undefined || resolution === null || resolution === '' ? '720p' : String(resolution);
  if (!ALLOWED_RESOLUTIONS.has(value)) {
    throw new Error("[anyint] resolution 只接受 '480p' 或 '720p'");
  }
  return value;
}

function validateContent(content: any): AnyIntContentItem[] {
  if (!Array.isArray(content) || content.length === 0) {
    throw new Error('[anyint] content 必须是非空数组');
  }

  return content.map((item, index) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      throw new Error(`[anyint] content[${index}] 必须是对象`);
    }

    if (item.type === 'text') {
      const text = String(item.text || '').trim();
      if (!text) {
        throw new Error(`[anyint] content[${index}].text 不能为空`);
      }
      return { type: 'text', text };
    }

    if (item.type === 'image_url' || item.type === 'video_url' || item.type === 'audio_url') {
      const allowedRoles = ROLE_BY_TYPE[item.type];
      const role = String(item.role || '').trim();
      if (!allowedRoles?.has(role)) {
        throw new Error(`[anyint] content[${index}].role 对于 ${item.type} 不合法`);
      }
      const field = item.type;
      const url = item?.[field]?.url;
      if (typeof url !== 'string' || !url.trim()) {
        throw new Error(`[anyint] content[${index}].${field}.url 必须是非空字符串`);
      }
      return {
        type: item.type,
        role,
        [field]: { url: url.trim() },
      } as AnyIntContentItem;
    }

    throw new Error(`[anyint] 不支持的 content[${index}].type: ${item.type}`);
  });
}

function dataUrlToBlob(dataUrl: string) {
  const matches = dataUrl.match(/^data:([A-Za-z0-9.+-\/]+);base64,(.+)$/);
  if (!matches) {
    throw new Error('[anyint] Invalid Data URL: expected data:<mime>;base64,<data>');
  }
  const mimeType = matches[1];
  const base64Data = matches[2];
  const extension = mimeType.split('/')[1] || 'bin';
  const buffer = Buffer.from(base64Data, 'base64');
  return {
    mimeType,
    extension,
    blob: new Blob([buffer], { type: mimeType }),
  };
}

async function uploadToAnyInt(baseUrl: string, dataUrl: string, fetchImpl = fetchWithRetry) {
  const endpoint = joinUrl(normalizeBaseUrl(baseUrl), 'files', 'upload');
  const { mimeType, extension, blob } = dataUrlToBlob(dataUrl);
  const formData = new FormData();
  formData.append('file', blob, `upload.${extension}`);
  formData.append('fileType', mimeType.startsWith('image/') ? 'image' : mimeType.startsWith('video/') ? 'video' : mimeType.startsWith('audio/') ? 'audio' : 'other');
  formData.append('public', 'true');
  formData.append('folder', 'seedance-references');

  const response = await fetchImpl(endpoint, {
    method: 'POST',
    body: formData,
  });

  const data = await parseJsonResponse(response as any, 'anyint file upload');
  const url = data?.data?.url || data?.url;
  if (!response.ok || !url || typeof url !== 'string') {
    throw new Error(`[anyint] File upload failed: ${response.status} ${JSON.stringify(data)}`);
  }
  return url;
}

async function materializeContentMedia(baseUrl: string, content: AnyIntContentItem[], fetchImpl = fetchWithRetry) {
  const next = JSON.parse(JSON.stringify(content));
  for (const item of next) {
    if (item.type === 'image_url' && typeof item.image_url?.url === 'string' && item.image_url.url.startsWith('data:')) {
      item.image_url.url = await uploadToAnyInt(baseUrl, item.image_url.url, fetchImpl);
    }
    if (item.type === 'video_url' && typeof item.video_url?.url === 'string' && item.video_url.url.startsWith('data:')) {
      item.video_url.url = await uploadToAnyInt(baseUrl, item.video_url.url, fetchImpl);
    }
    if (item.type === 'audio_url' && typeof item.audio_url?.url === 'string' && item.audio_url.url.startsWith('data:')) {
      item.audio_url.url = await uploadToAnyInt(baseUrl, item.audio_url.url, fetchImpl);
    }
  }
  return next;
}

export const ANYINT_PROVIDER = {
  ...AIGC_PROVIDER_TEMPLATE,
  id: 'anyint',
  label: 'AnyInt',
  env: {
    apiKey: 'ANYINT_API_KEY',
    baseUrl: 'ANYINT_BASE_URL',
    defaultBaseUrl: 'https://gateway.api.anyint.ai',
  },
  scopes: {
    image: 'images',
    video: 'videos',
  },
  buildPayload(scope: any, params: any) {
    if (scope !== 'videos') {
      throw new Error('[anyint] 当前只支持视频生成');
    }
    const model = String(params.model || '').trim();
    if (!SUPPORTED_MODELS.has(model)) {
      throw new Error(`[anyint] 不支持的 model: ${model || '(empty)'}`);
    }
    return {
      model,
      content: validateContent(params.content),
      duration: validateDuration(params.duration),
      ratio: validateRatio(params.ratio),
      resolution: validateResolution(params.resolution),
      watermark: params.watermark === undefined ? false : Boolean(params.watermark),
      generate_audio: params.generate_audio === undefined ? true : Boolean(params.generate_audio),
    };
  },
  async submit({ baseUrl, apiKey, scope, payload, fetchImpl = fetchWithRetry }: any) {
    if (scope !== 'videos') {
      throw new Error('[anyint] 当前只支持视频生成');
    }
    const normalizedBase = normalizeBaseUrl(baseUrl);
    const finalPayload = JSON.parse(JSON.stringify(payload));
    finalPayload.content = await materializeContentMedia(normalizedBase, finalPayload.content || [], fetchImpl);

    const response = await fetchImpl(joinUrl(normalizedBase, 'doubao', 'video', 'generations'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(finalPayload),
    });

    const data = await parseJsonResponse(response as any, 'anyint video submit');
    if (!response.ok) {
      throw new Error(`[anyint] Submit failed: ${response.status} ${JSON.stringify(data)}`);
    }
    const taskId = data?.task_id || data?.id;
    if (!taskId) {
      throw new Error(`[anyint] Missing task id: ${JSON.stringify(data)}`);
    }
    return taskId;
  },
  async poll({ baseUrl, apiKey, scope, taskId, timeoutMs = 30 * 60 * 1000, fetchImpl = fetchWithRetry }: any) {
    if (scope !== 'videos') {
      throw new Error('[anyint] 当前只支持视频生成');
    }
    const normalizedBase = normalizeBaseUrl(baseUrl);
    const startedAt = Date.now();
    let delayMs = 2000;

    for (;;) {
      const response = await fetchImpl(joinUrl(normalizedBase, 'doubao', 'videos', taskId), {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });
      const data = await parseJsonResponse(response as any, 'anyint video poll');
      if (!response.ok) {
        throw new Error(`[anyint] Poll failed: ${response.status} ${JSON.stringify(data)}`);
      }
      const status = String(data?.status || '').toLowerCase();
      if (status === 'completed') {
        return data;
      }
      if (['failed', 'expired', 'cancelled'].includes(status)) {
        throw new Error(`[anyint] Provider task failed: ${JSON.stringify(data)}`);
      }
      if (Date.now() - startedAt > timeoutMs) {
        throw new Error('[anyint] Provider polling timeout');
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      delayMs = Math.min(delayMs * 2, 8000);
    }
  },
  extractOutputs(scope: any, result: any) {
    if (scope !== 'videos') {
      return [];
    }
    const candidates = [
      result?.metadata?.url,
      result?.data?.url,
      result?.url,
    ].filter(Boolean);
    return candidates;
  },
};
