export interface PromptDTO {
  positive: string;
  negative: string;
  params: Record<string, unknown>;
}

export interface ImageWithPrompt {
  image_path: string;
  prompt: PromptDTO | null;
}
