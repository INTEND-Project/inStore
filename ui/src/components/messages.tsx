import { Avatar, Card, Flex, HStack, Skeleton, Stack } from "@chakra-ui/react";
import { useEffect, useRef } from "react";
import { TbChartBubbleFilled } from "react-icons/tb";
import Markdown from "react-markdown";

type Message = {
  sender: "human" | "instore";
  content: string;
  tool_calls?: string[];
  commands?: string[];
  failed?: boolean;
};
interface ChatMessagesProps {
  messages: Message[];
  loading: boolean;
}

export function ChatMessages(props: ChatMessagesProps) {
  const bottomRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  });
  //TODO: Change key prop from content to id
  return (
    <div style={{ fontFamily: "Roboto" }}>
      {props.messages.map((m, i) => {
        let messageComponent;
        if (m.sender === "human") {
          messageComponent = <HumanMessage message={m} />;
        } else {
          messageComponent = <AgentMessage message={m.content} />;
        }
        if (i + 1 === props.messages.length) {
          return <div ref={bottomRef}>{messageComponent}</div>;
        } else {
          return messageComponent;
        }
      })}
      {props.loading ? (
        <HStack gap="5">
          <Avatar.Root size="2xl" backgroundColor="#0077DE">
            <TbChartBubbleFilled color="white" size={28} />
          </Avatar.Root>
          <Stack flex="1">
            <Skeleton height="8" width="1000px" />
            <Skeleton height="8" width="500px" />
          </Stack>
        </HStack>
      ) : (
        <div />
      )}
    </div>
  );
}

const HumanMessage = (props: { message: Message }) => {
  return (
    <div>
      <Flex
        key={props.message.content}
        direction="row"
        minHeight="80px"
        width="85vw"
        justify="right"
        alignItems="center"
      >
        <div
          style={{
            marginRight: "12px",
            fontSize: "20px",
            backgroundColor: "rgb(250,250,250)",
            padding: "12px",
            borderRadius: "12px",
          }}
        >
          <div
            style={{
              alignItems: "right",
              color: props.message.failed ? "grey" : "black",
            }}
          >
            {props.message.content}
          </div>
          {props.message.failed ? (
            <div
              style={{
                color: "red",
                fontSize: "12pt",
                alignItems: "left",
              }}
            >
              Failed to send
            </div>
          ) : null}
        </div>
        <Avatar.Root size="2xl" colorPalette="cyan">
          <Avatar.Fallback name="John Doe" />
        </Avatar.Root>
      </Flex>
    </div>
  );
};

const AgentMessage = (props: { message: string }) => {
  const renderMessage = (message: string) => {
    const msg = message.trim();
    let intent;
    if (msg.substring(0, 7) === "```json") {
      intent = JSON.parse(msg.substring(7).split("```")[0]);
    } else if (msg[0] == "{") {
      const possible_intent = JSON.parse(msg);
      if (possible_intent["message"]) {
        intent = possible_intent;
      }
    }
    if (intent) {
      return (
        <div>
          {intent.message}
          {":"}
          <Card.Root
            style={{
              padding: "12px",
              marginTop: "25px",
              marginLeft: "20px",
              borderRadius: "16px",
              borderColor: "#0076CE",
              borderWidth: "2px",
              boxShadow: "4px 4px 8px #A9A9A9",
              maxWidth: "800px",
            }}
          >
            <Card.Body>
              <div
                style={{ fontSize: "18px", fontWeight: "bold", color: "black" }}
              >
                {intent["intent_name"]}
              </div>
              <div
                style={{
                  paddingLeft: "8px",
                  paddingBottom: "4px",
                  fontSize: "16px",
                  fontWeight: "lighter",
                }}
              >
                Actions: {intent["actions"]}
              </div>
              <div
                style={{
                  paddingLeft: "8px",
                  fontSize: "16px",
                  fontWeight: "lighter",
                }}
              >
                Results: {intent["results"]}
              </div>
            </Card.Body>
          </Card.Root>
        </div>
      );
    } else {
      return msg;
    }
  };

  return (
    <Flex
      key={props.message}
      direction="row"
      minHeight="80px"
      width="80vw"
      justify="left"
      align="center"
      color="black"
    >
      <Avatar.Root size="2xl" backgroundColor="#0077DF">
        <TbChartBubbleFilled color="white" size={28} />
      </Avatar.Root>
      <div
        style={{
          marginLeft: "12px",
          fontSize: "20px",
          backgroundColor: "rgb(250,250,250)",
          padding: "12px",
          borderRadius: "12px",
        }}
      >
        <div>{renderMessage(props.message)}</div>
      </div>
    </Flex>
  );
};
