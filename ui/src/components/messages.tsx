import {
  Avatar,
  Box,
  Card,
  Flex,
  HStack,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useEffect, useRef, useState } from "react";
import {
  TbChartBubbleFilled,
  TbCheck,
  TbChevronDown,
  TbChevronUp,
  TbListSearch,
} from "react-icons/tb";
import { motion, AnimatePresence } from "framer-motion";
import Markdown from "react-markdown";

type Message = {
  sender: "human" | "instore";
  content: string;
  failed?: boolean;
};
interface ChatMessagesProps {
  messages: Message[];
  notifications: string[];
  loading: boolean;
}

export function ChatMessages(props: ChatMessagesProps) {
  const bottomRef = useRef<null | HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(true);

  // Auto-expand when loading starts to show live progress
  useEffect(() => {
    if (props.loading) {
      setIsExpanded(true);
    }
  }, [props.loading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [props.messages, props.notifications, props.loading, isExpanded]);

  return (
    <div style={{ fontFamily: "Roboto", paddingBottom: "40px" }}>
      {props.messages.map((m, i) => (
        <div key={i}>
          {m.sender === "human" ? (
            <HumanMessage message={m} />
          ) : (
            <AgentMessage message={m.content} />
          )}
        </div>
      ))}

      {(props.notifications.length > 0 || props.loading) && (
        <Flex direction="row" gap="5" mt="6" align="flex-start">
          <Stack align="center" gap="0">
            <Avatar.Root
              size="2xl"
              backgroundColor={props.loading ? "#0077DE" : "gray.100"}
            >
              {props.loading ? (
                <TbChartBubbleFilled color="white" size={28} />
              ) : (
                <TbListSearch color="gray.500" size={24} />
              )}
            </Avatar.Root>
            <Box width="2px" flex="1" bg="gray.100" my="2" minHeight="20px" />
          </Stack>

          <Stack flex="1" gap="2">
            <HStack justify="space-between" width="full" pr="4">
              <Text
                fontSize="xs"
                fontWeight="bold"
                color="gray.400"
                letterSpacing="widest"
                textTransform="uppercase"
              >
                {props.loading ? "InStorage Processing..." : "Execution Log"}
              </Text>

              {/* Toggle Button */}
              <HStack
                as="button"
                onClick={() => setIsExpanded(!isExpanded)}
                color="blue.500"
                _hover={{ color: "blue.700" }}
                cursor="pointer"
                gap="1"
              >
                <Text fontSize="xs" fontWeight="bold">
                  {isExpanded ? "HIDE" : `SHOW (${props.notifications.length})`}
                </Text>
                {isExpanded ? (
                  <TbChevronUp size={14} />
                ) : (
                  <TbChevronDown size={14} />
                )}
              </HStack>
            </HStack>

            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  style={{ overflow: "hidden" }}
                >
                  <Box
                    bg="gray.50"
                    p="4"
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor="gray.100"
                  >
                    <AnimatePresence>
                      {props.notifications.map((note, index) => {
                        const isLast = index === props.notifications.length - 1;
                        const isCurrentAction = isLast && props.loading;
                        return (
                          <motion.div
                            layout
                            key={note + index}
                            initial={{ opacity: 0, x: -5 }}
                            animate={{
                              opacity: isCurrentAction ? 1 : 0.6,
                              x: 0,
                              color: isCurrentAction ? "#0077DE" : "#4A5568",
                            }}
                            transition={{ duration: 0.2 }}
                          >
                            <HStack gap="3" py="1">
                              {isCurrentAction ? (
                                <Spinner size="xs" color="#0077DE" />
                              ) : (
                                <TbCheck size={14} color="green" />
                              )}
                              <Text fontSize="sm" fontFamily="monospace">
                                {note}
                              </Text>
                            </HStack>
                          </motion.div>
                        );
                      })}
                    </AnimatePresence>
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </Stack>
        </Flex>
      )}

      <div ref={bottomRef} />
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
          <Markdown>{intent.message}</Markdown>
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
            </Card.Body>
          </Card.Root>
        </div>
      );
    } else {
      return <Markdown>{msg}</Markdown>;
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
