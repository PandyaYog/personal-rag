export type SearchMethod = 
  | 'dense'
  | 'sparse'
  | 'multi_vector'
  | 'hybrid_dense_sparse'
  | 'dense_rerank_multi'
  | 'sparse_rerank_multi'
  | 'rrf'
  | 'full_rrf';

export interface LLMConfig {
  provider: string;
  model: string;
  temperature: number;
  top_p: number;
  system_prompt: string;
  search_type: SearchMethod;
}

export interface EmbeddingModelConfig {
  dense: string;
  sparse: string;
  multi_vector: string;
}

export interface LinkedKnowledgeBase {
  id: string;
  name: string;
}

export interface AssistantBase {
  name: string;
}

export interface AssistantCreate extends AssistantBase {
  knowledge_base_ids: string[];
  llm_config?: LLMConfig;
  embedding_config?: EmbeddingModelConfig;
}

export interface AssistantUpdate extends AssistantBase {
  name?: string;
  knowledge_base_ids?: string[];
  llm_config?: LLMConfig;
  embedding_config?: EmbeddingModelConfig;
}

export interface Assistant extends AssistantBase {
  id: string;
  created_at: string;
  updated_at: string | null;
  num_chats: number;
  knowledge_bases: LinkedKnowledgeBase[];
  llm_config: LLMConfig;
  embedding_config: EmbeddingModelConfig;
}
