import { submitQuery } from "./api/intent_manager.ts";
import "./App.css";
import ChatbotInput from "./components/input.tsx";
import { Box, Flex } from "@chakra-ui/react";
import { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { ChatMessages } from "./components/messages.tsx";
import Header from "./components/header.tsx";
import SideBar from "./components/sidebar.tsx";
import IntentsPage from "./components/intents.tsx";

interface Message {
  sender: "human" | "instore";
  content: string;
  tool_calls?: string[];
  commands?: string[];
  failed?: boolean;
}

const GREETING: Message = {
  sender: "instore",
  content: "Hello, how may I assist you to manage your data and storage ?",
};

function App() {
  const [page, setPage] = useState<String>("messages");
  const [notifications, setNotifications] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [loading, setLoading] = useState<boolean>(false);
  // Identifies the conversation on the intent manager, so the agent remembers earlier messages of the same chat
  const [conversationId, setConversationId] = useState<string>(() => uuidv4());

  const newChat = () => {
    setConversationId(uuidv4());
    setMessages([GREETING]);
    setNotifications([]);
    setPage("messages");
  };

  const submit = async (newMessage: string): Promise<boolean> => {
    setLoading(true);
    const newMessages = [
      ...messages,
      { sender: "human", content: newMessage } as Message,
    ];
    setMessages(newMessages);
    try {
      await submitQuery(
        newMessage,
        conversationId,
        (msg) => {
          setNotifications((n) => [...n, msg]);
        },
        (msg) => {
          setMessages([
            ...newMessages,
            {
              sender: "instore",
              content: msg,
            },
          ]);
        },
      );
      setLoading(false);
      return true;
    } catch (e) {
      const lastMessage = newMessages.pop();
      if (lastMessage) {
        lastMessage.failed = true;
        setMessages([...messages, lastMessage]);
      }
      console.log(e);
      setLoading(false);
      return false;
    }
  };

  const renderPage = () => {
    if (page === "messages") {
      return (
        <>
          <Box paddingBottom="200px" marginLeft="300px">
            <ChatMessages
              messages={messages}
              notifications={notifications}
              loading={loading}
            />
          </Box>
          <ChatbotInput onSubmit={submit} loading={loading} />
        </>
      );
    } else if (page === "intents") {
      return <IntentsPage />;
    }
  };

  return (
    <div>
      <Header
        logoSrc="./src/assets/delltech-logo-prm-blue-rgb-proof.svg"
        title="Intent-driven Agentic Data Placement"
      />
      <SideBar onNavigate={setPage} onNewChat={newChat} />
      <Flex
        paddingTop="100px"
        height="95vh"
        width="95vw"
        direction="column"
        align="center"
        justify="space-between"
      >
        {renderPage()}
      </Flex>
    </div>
  );
}

export default App;
