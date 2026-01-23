export const MENTION_RE = /(?:^|\s)@([^\s@]*)$/;
export const MEDIA_DRAG_TYPE = 'application/x-conthunt-media';
export const CHIP_TITLE_LIMIT = 10;

export const MODEL_OPTIONS = [

    { label: 'Gemini 3 Flash', value: 'google/gemini-3-flash-preview' },
    { label: 'Grok 4.1 Fast (xAI)', value: 'openrouter/x-ai/grok-4.1-fast' },
    // { label: 'Gemini 3 Flash', value: 'google/gemini-3-flash-preview' },
    { label: 'MiMo-V2-Flash (Xiaomi, free)', value: 'openrouter/xiaomi/mimo-v2-flash:free' },
    { label: 'GPT-5.2 (OpenAI)', value: 'openrouter/openai/gpt-5.2' },
    { label: 'GPT-5.1 (OpenAI)', value: 'openrouter/openai/gpt-5.1' },
    { label: 'DeepSeek V3.2 (DeepSeek)', value: 'openrouter/deepseek/deepseek-v3.2' },
    { label: 'Mistral Small Creative (Mistral)', value: 'openrouter/mistralai/mistral-small-creative' },
];
