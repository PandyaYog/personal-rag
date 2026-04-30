export interface MessageVersion {
  text: string;
  reference_docs?: string[];
}

export interface MessageContent {
  versions: MessageVersion[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: MessageContent;
  is_good: boolean | null;
  created_at: string;
  
  // Computed fields from backend
  text: string;
  reference_docs?: string[];
}

export interface ChatBase {
  name: string;
}

export interface ChatCreate {
  name?: string;
}

export interface ChatUpdate extends ChatBase {}

export interface Chat extends ChatBase {
  id: string;
  assistant_id: string;
  created_at: string;
  updated_at: string | null;
}

export interface ChatWithHistory extends Chat {
  messages: Message[];
}

export interface UserQuery {
  query: string;
}

export interface Feedback {
  is_good: boolean;
}
