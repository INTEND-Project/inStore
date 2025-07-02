import { submitQuery } from "./api/intent_manager.ts";
import "./App.css";
import ChatbotInput from "./components/input.tsx";
import { Box, Flex } from "@chakra-ui/react";
import { useState } from "react";
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

function App() {
  const [page, setPage] = useState<String>("messages");
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "instore",
      content: "Hello, how may I assist you to manage your data and storage ?",
    },
  ]);
  const [loading, setLoading] = useState<boolean>(false);

  const submit = async (newMessage: string): Promise<boolean> => {
    setLoading(true);
    const newMessages = [
      ...messages,
      { sender: "human", content: newMessage } as Message,
    ];
    setMessages(newMessages);
    try {
      const res = await submitQuery(newMessage);
      setMessages([
        ...newMessages,
        {
          sender: "instore",
          content: res["reply"],
          tool_calls: res["tool_calls"],
          commands: res["cmds"],
        },
      ]);
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
            <ChatMessages messages={messages} loading={loading} />
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
      <SideBar onNavigate={setPage} />
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
