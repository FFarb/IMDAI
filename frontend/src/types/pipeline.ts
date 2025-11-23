// Simplified shared type definitions for the string-based pipeline flow.

export interface ResearchOutput {
  analysis: string;
  highlights: string[];
  segments: string[];
}

export interface SynthesisPrompt {
  positive: string;
  negative: string[];
  notes?: string | null;
}

export interface SynthesisOutput {
  prompts: SynthesisPrompt[];
  raw_text: string;
}

export interface ImageResult {
  url?: string | null;
  b64_json?: string | null;
  error?: string;
}

export interface GenerateRequest {
  topic: string;
  audience: string;
  age?: string | null;
  variants?: number;
  images_per_prompt?: number;
  mode?: 'full' | 'prompts-only';

  // Multi-agent parameters
  use_agents?: boolean;
  visual_references?: string[];
  max_iterations?: number;
  trend_count?: number;
  history_count?: number;
  skip_research?: boolean;
  provided_strategy?: any;
  use_smart_recall?: boolean;

  // Research parameters
  research_model?: string;
  research_mode?: string;
  reasoning_effort?: string;

  // Synthesis parameters
  synthesis_mode?: string;

  // Image parameters
  image_model?: string;
  image_quality?: string;
  image_size?: string;
}

export type BriefValues = GenerateRequest;

export interface GenerateResponse {
  research: ResearchOutput;
  synthesis: SynthesisOutput;
  images: ImageResult[][];
}

// Multi-agent system types
export interface AgentSystemOutput {
  vision_analysis: string;
  style_context: Array<{
    name: string;
    style: string;
    mood: string;
    lighting: string;
    similarity_score: number;
  }>;
  master_strategy: string | any;
  market_trends?: string;
  critique_score: number;
  iteration_count: number;
}

export interface AgentGenerateResponse {
  agent_system: AgentSystemOutput;
  prompts: Array<{
    positive: string;
    negative: string[];
    notes?: string | null;
  }>;
  images: ImageResult[][];
  generation_ids?: number[];  // IDs for approving/saving to library
}

// SSE event types
export interface AgentStepEvent {
  type: 'agent_step';
  agent: 'vision' | 'historian' | 'analyst' | 'promptsmith' | 'critic' | 'increment';
  agent_name: string;
  status: 'started' | 'completed';
  data?: {
    message: string;
    [key: string]: any;
  };
}

export interface StreamStartEvent {
  type: 'start';
  message: string;
}

export interface StreamCompleteEvent {
  type: 'complete';
  message: string;
}

export interface StreamErrorEvent {
  type: 'error';
  message: string;
}

export type StreamEvent = AgentStepEvent | StreamStartEvent | StreamCompleteEvent | StreamErrorEvent;

