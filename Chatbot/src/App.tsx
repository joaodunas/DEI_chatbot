import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Trash2 } from "lucide-react";
import { encode } from "gpt-tokenizer";

// Import the logos from the assets folder
import deiLogoFull from "./assets/dei_logo_full.svg";
import deiLogoAvatar from "./assets/dei_logo.svg"; // Assuming this is the avatar version

// Import the types from the new file
import { Message, ChatMessage, OllamaChatStreamResponse } from "./types/chat";
// Import the system prompt content from the new file
import { systemPrompt } from "./config/systemPrompt";

// Function to generate a simple unique ID
const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
};

// Define your system message
// Type annotation using imported ChatMessage
const SYSTEM_MESSAGE: ChatMessage = {
  role: "system",
  content: systemPrompt, // Use the imported content
};

const INFO_MESSAGE: Message = {
  id: generateId(), // Use the new function
  text: `
  Olá! Eu sou o ChatBot do DEI!\n
  Fui criado por alunos do DEI para te ajudar!\n
  Podes fazer perguntas sobre o DEI, a sua sobre a oferta pedagógica, bem como detalhes sobre os cursos, saídas profissionais, entre outros!\n
  Sou uma versão **beta**, pelo que é importante confirmar informação importante no site do DEI https://www.uc.pt/fctuc/dei/.\n\n
  `,
  sender: "assistant",
};

function App() {
  // Type annotation using imported Message
  const [messages, setMessages] = useState<Message[]>([INFO_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null); // Ref to scroll to the bottom

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    setIsLoading(true);

    // Type annotation using imported Message
    const userMessage: Message = {
      id: generateId(), // Use the new function
      text: trimmedInput,
      sender: "user",
    };

    const assistantMessageId = generateId(); // Use the new function
    // Type annotation using imported Message
    const initialAssistantMessage: Message = {
      id: assistantMessageId,
      text: "",
      sender: "assistant",
    };

    // Add user message and initial empty assistant message to the UI state
    const updatedMessages = [...messages, userMessage, initialAssistantMessage];
    setMessages(updatedMessages);
    setInput("");

    /* JRC 20250506 comment to avoid sending history
    // Prepare messages for the API call
    // Type annotation using imported ChatMessage
    const apiMessages: ChatMessage[] = [
      SYSTEM_MESSAGE,
      ...updatedMessages
        .filter((msg) => msg.id !== assistantMessageId) // Exclude the placeholder
        .map(
          (msg) =>
            ({
              role: msg.sender,
              content: msg.text,
            } as ChatMessage) // Type assertion using imported ChatMessage
        ),
    ];
    */

    // JRC 20250506 include just the current message
    /*
    const apiMessages: ChatMessage[] = [
      SYSTEM_MESSAGE,
      {
        role: "user",
        content: trimmedInput,
      },
    ];
    */

    const MAX_CONTEXT_MESSAGES = 1; // total messages to include (user+assistant pairs)

    const relevantMessages = messages
      .filter((msg) => msg.sender === "user" || msg.sender === "assistant")
      .slice(-MAX_CONTEXT_MESSAGES)
      .map((msg) => ({
        role: msg.sender,
        content: msg.text,
      }));

    const apiMessages: ChatMessage[] = [
      SYSTEM_MESSAGE,
      ...relevantMessages,
      {
        role: "user",
        content: trimmedInput,
      },
    ];

    try {
      const apiEndpoint = import.meta.env.VITE_OLLAMA_API_ENDPOINT;
      const ragApiEndpoint = import.meta.env.VITE_RAG_API_ENDPOINT;
      const modelName = import.meta.env.VITE_OLLAMA_MODEL_NAME;

      //console.log(apiMessages); removed, only for debugging

      const contextResponse = await fetch(ragApiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: trimmedInput,
          context: apiMessages,
          top_k: 3, // number of results you want
        }),
      });

      if (!contextResponse.ok) {
        throw new Error("Failed to fetch context");
      }

      const contextData = await contextResponse.json();

      const contextString = contextData.results
        .map((item: { text: string }) => item.text)
        .join("\n");

      //add this contextString to the last user message of the apiMessages
      apiMessages[apiMessages.length - 1].content =
        "<context>" +
        contextString +
        "</context>" +
        "<user_query>" +
        trimmedInput +
        "</user_query>";

      // const messageContent = apiMessages[apiMessages.length - 1].content;

      let totalTokens = 0;
      apiMessages.forEach((message) => {
        totalTokens += encode(message.content).length;
      });

      //console.log(
      //  "Total token count for all messages (using gpt-tokenizer, specific model might be diff):",
      //  totalTokens
      //); removed, only for debugging

      // Create message with context and user prompt
      const response = await fetch(apiEndpoint, {
        method: "POST",
        body: JSON.stringify({
          model: modelName,
          messages: apiMessages,
          stream: true,
          options: {
            temperature: 0.5, // 0.2; 0.5 works well for gemma3;
          },
        }),
      });

      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter((line) => line.trim() !== "");

        for (const line of lines) {
          try {
            // Parse the chat stream response structure
            // Type annotation using imported OllamaChatStreamResponse
            const parsed: OllamaChatStreamResponse = JSON.parse(line);
            // Append content from the 'message' object
            if (parsed.message?.content) {
              streamedText += parsed.message.content;
              setMessages((prevMessages) =>
                prevMessages.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, text: streamedText }
                    : msg
                )
              );
            }
            if (parsed.done) {
              break;
            }
          } catch (parseError) {
            console.error("Failed to parse stream chunk:", line, parseError);
          }
        }
        if (
          lines.some((line) => {
            try {
              // Check the 'done' field in the parsed response
              return JSON.parse(line).done;
            } catch {
              return false;
            }
          })
        ) {
          break;
        }
      }
    } catch (error) {
      console.error("Error fetching Ollama chat response:", error);
      setMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, text: "Sorry, I encountered an error." }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Prevent sending if loading or shift key is pressed
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSend();
    }
  };

  // Function to reset the chat
  const handleReset = () => {
    setMessages([INFO_MESSAGE]);
  };

  // Effect to scroll down when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]); // Dependency: run when messages change

  return (
    <div className="flex flex-col h-screen bg-background">
      <header className="p-4 shrink-0 border-b flex items-center justify-between gap-3">
        {/*img src={deiLogoFull} alt="DEI Logo" className="h-10 w-auto" />*/}
        <div className="w-10" />{" "}
        {/* Spacer to balance the button on the right */}
        <h1 className="text-xl font-semibold">DEI ChatBot</h1>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleReset}
          aria-label="Reset Chat"
        >
          <Trash2 className="h-10" />
        </Button>
      </header>
      <div className="flex-1 flex flex-col max-w-3xl w-full mx-auto my-8 overflow-hidden rounded-lg border bg-card shadow-lg">
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4">
            <div className="space-y-4">
              {messages
                .filter((msg) => msg.sender !== "system")
                .map((message) => (
                  <div
                    key={message.id}
                    className={`flex items-end gap-2 ${
                      message.sender === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    {message.sender === "assistant" && (
                      <Avatar className="h-10 w-10 border">
                        <AvatarImage
                          src={deiLogoAvatar}
                          alt="Assistant"
                          className="scale-80"
                        />
                        <AvatarFallback>DEI</AvatarFallback>
                      </Avatar>
                    )}
                    <Card
                      className={`max-w-xs md:max-w-md lg:max-w-lg ${
                        message.sender === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <CardContent className="px-5 break-words">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.text ||
                            (message.sender === "assistant" && isLoading
                              ? "..."
                              : "")}
                        </ReactMarkdown>
                      </CardContent>
                    </Card>
                    {message.sender === "user" && (
                      <Avatar className="h-10 w-10 border">
                        <AvatarFallback>U</AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                ))}
              {/* Empty div at the end of messages to target for scrolling */}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>
        {/* Existing chat input footer, now inside the box */}
        <footer className="p-4 border-t shrink-0">
          {/* Removed max-w-3xl and mx-auto from this div */}
          <div className="flex gap-2 items-center">
            <Textarea
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={
                isLoading
                  ? "Generating response..."
                  : "Type your message... (Shift + Enter for new line)"
              }
              className="flex-1 resize-none"
              maxLength={300}
              disabled={isLoading}
            />
            <Button onClick={handleSend} disabled={isLoading}>
              {isLoading ? "..." : "Send"}
            </Button>
          </div>
        </footer>
      </div>{" "}
      {/* End of new box wrapper */}
      <footer className="text-center p-4 text-xs text-muted-foreground border-t shrink-0">
        <p>
          © 2025 DEI ChatBot. For demonstration purposes only. Verify critical
          information.
        </p>
        <p>
          Created by João Donato, Rodrigo Nogueira, João Braz Simões and João R
          Campos.
        </p>
      </footer>
    </div>
  );
}

export default App;
