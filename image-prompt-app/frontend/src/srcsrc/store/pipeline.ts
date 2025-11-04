import create from 'zustand';
import { persist } from 'zustand/middleware';
import { ResearchOutput, SynthesisOutput } from '../types/pipeline';

export type PipelineState = {
  research: ResearchOutput | null;
  synthesis: SynthesisOutput | null;
  images: string[][]; // Array of image URLs/b64 strings, one array per prompt
  setResearch: (r: ResearchOutput | null) => void;
  setSynthesis: (s: SynthesisOutput | null) => void;
  setImages: (imgs: string[][]) => void;
  clearState: () => void;
};

const usePipelineStore = create<PipelineState>()(
  persist(
    (set) => ({
      research: null,
      synthesis: null,
      images: [],
      setResearch: (research) => set({ research }),
      setSynthesis: (synthesis) => set({ synthesis }),
      setImages: (images) => set({ images }),
      clearState: () => set({ research: null, synthesis: null, images: [] }),
    }),
    {
      name: 'imdai-pipeline-storage', // name of the item in the storage (must be unique)
      getStorage: () => localStorage, // (optional) by default, 'localStorage' is used
    }
  )
);

export default usePipelineStore;
