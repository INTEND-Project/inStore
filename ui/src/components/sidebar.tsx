import { Collapsible, Flex } from "@chakra-ui/react";
import { IoIosChatbubbles, IoMdAdd } from "react-icons/io";
import { TbChartBubbleFilled } from "react-icons/tb";

interface SideBarProps {
  onNavigate(page: String): void;
  onNewChat(): void;
}
const SideBar = (props: SideBarProps) => {
  return (
    <Flex
      direction="column"
      position="fixed"
      left="0px"
      width="220px"
      color="black"
      paddingTop="88px"
      fontSize="18px"
      fontWeight="light"
      boxShadow="2px 2px 2px #EFEFEF"
      backgroundColor="rgb(253,253,253)"
      height="100%"
      zIndex={10}
      overflow="hidden"
      textOverflow="ellipsis"
    >
      <Collapsible.Root onClick={() => props.onNavigate("intents")}>
        <Collapsible.Trigger
          paddingY="0"
          paddingX="0"
          width="100%"
          _hover={{ cursor: "pointer" }}
        >
          <Flex
            direction="row"
            gap="20px"
            paddingLeft="24px"
            paddingTop="12px"
            paddingBottom="12px"
            _hover={{ borderColor: "#0076CE", cursor: "pointer" }}
          >
            <TbChartBubbleFilled size={28} />
            <div>Intent Inventory</div>
          </Flex>
        </Collapsible.Trigger>
      </Collapsible.Root>

      <Collapsible.Root onClick={() => props.onNavigate("messages")}>
        <Collapsible.Trigger
          paddingY="0"
          paddingX="0"
          width="100%"
          _hover={{ cursor: "pointer" }}
        >
          <Flex
            direction="row"
            gap="20px"
            paddingLeft="24px"
            paddingTop="12px"
            paddingBottom="12px"
            _hover={{ borderColor: "#0076CE", cursor: "pointer" }}
          >
            <IoIosChatbubbles size={28} />
            <div>Current Chat</div>
          </Flex>
        </Collapsible.Trigger>
      </Collapsible.Root>

      <Collapsible.Root onClick={() => props.onNewChat()}>
        <Collapsible.Trigger
          paddingY="0"
          paddingX="0"
          width="100%"
          _hover={{ cursor: "pointer" }}
        >
          <Flex
            direction="row"
            gap="20px"
            paddingLeft="24px"
            paddingTop="12px"
            paddingBottom="12px"
            _hover={{ borderColor: "#0076CE", cursor: "pointer" }}
          >
            <IoMdAdd size={28} />
            <div>New Chat</div>
          </Flex>
        </Collapsible.Trigger>
      </Collapsible.Root>

      <Flex
        width="200px"
        paddingLeft="20px"
        bottom="52px"
        position="fixed"
        direction="column"
        alignItems="center"
      >
        <img src="./../src/assets/INTEND_standard.svg" />
      </Flex>
    </Flex>
  );
};

export default SideBar;
