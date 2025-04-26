// Define the base structure for UI messages
export interface Message {
  id: string;
  text: string;
  sender: "user" | "assistant" | "system";
}

// Define the structure for messages sent to the /api/chat endpoint
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

// Define the structure of the streamed JSON response from Ollama /api/chat
export interface OllamaChatStreamResponse {
  model: string;
  created_at: string;
  message: ChatMessage; // The actual message chunk
  done: boolean;
}
