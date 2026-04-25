import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getAIGCProvider } from '../../src/logic/aigc-provider-registry';

describe('AnyInt Provider', () => {
  const provider = getAIGCProvider('anyint');

  beforeEach(() => {
    if (typeof vi.stubGlobal === 'function') {
      vi.stubGlobal('fetch', vi.fn());
    } else {
      (globalThis as any).fetch = vi.fn();
    }
  });

  it('buildPayload validates doubao video request with defaults', () => {
    const payload = provider.buildPayload('videos', {
      model: 'doubao-seedance-2-0-260128',
      content: [{ type: 'text', text: '一个小猫对着镜头打哈欠' }],
    });

    expect(payload).toEqual({
      model: 'doubao-seedance-2-0-260128',
      content: [{ type: 'text', text: '一个小猫对着镜头打哈欠' }],
      duration: 5,
      ratio: 'adaptive',
      resolution: '720p',
      watermark: false,
      generate_audio: true,
    });
  });

  it('submit uploads data url image references before calling doubao video generations', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: {
            url: 'https://storage.googleapis.com/bucket/uuid_reference.jpg',
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM',
          task_id: 'task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM',
          status: 'queued',
        }),
      });

    const taskId = await provider.submit({
      baseUrl: 'https://gateway.api.anyint.ai',
      apiKey: 'test-key',
      scope: 'videos',
      payload: {
        model: 'doubao-seedance-2-0-260128',
        content: [
          { type: 'text', text: '小猫做出可爱的动作' },
          {
            type: 'image_url',
            role: 'first_frame',
            image_url: { url: 'data:image/png;base64,aaaa' },
          },
        ],
        duration: 5,
        ratio: '16:9',
        resolution: '720p',
        watermark: false,
        generate_audio: true,
      },
      fetchImpl,
    });

    expect(taskId).toBe('task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM');
    expect(fetchImpl).toHaveBeenNthCalledWith(
      1,
      'https://gateway.api.anyint.ai/files/upload',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      }),
    );
    expect(fetchImpl).toHaveBeenNthCalledWith(
      2,
      'https://gateway.api.anyint.ai/doubao/video/generations',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-key',
        },
        body: JSON.stringify({
          model: 'doubao-seedance-2-0-260128',
          content: [
            { type: 'text', text: '小猫做出可爱的动作' },
            {
              type: 'image_url',
              role: 'first_frame',
              image_url: { url: 'https://storage.googleapis.com/bucket/uuid_reference.jpg' },
            },
          ],
          duration: 5,
          ratio: '16:9',
          resolution: '720p',
          watermark: false,
          generate_audio: true,
        }),
      }),
    );
  });

  it('poll reads task status from doubao videos endpoint and extractOutputs returns metadata.url', async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: 'task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM',
        task_id: 'task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM',
        status: 'completed',
        progress: 100,
        metadata: {
          url: 'https://ark-acg-cn-beijing.tos-cn-beijing.volces.com/doubao-seedance-2-0/xxx.mp4',
        },
      }),
    });

    const result = await provider.poll({
      baseUrl: 'https://gateway.api.anyint.ai',
      apiKey: 'test-key',
      scope: 'videos',
      taskId: 'task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM',
      fetchImpl,
    });

    expect(fetchImpl).toHaveBeenCalledWith(
      'https://gateway.api.anyint.ai/doubao/videos/task_GDeNXUt2rnTe9iUrkDch3R5y6YIfk9gM',
      expect.objectContaining({
        headers: { Authorization: 'Bearer test-key' },
      }),
    );
    expect(provider.extractOutputs('videos', result)).toEqual([
      'https://ark-acg-cn-beijing.tos-cn-beijing.volces.com/doubao-seedance-2-0/xxx.mp4',
    ]);
  });
});
