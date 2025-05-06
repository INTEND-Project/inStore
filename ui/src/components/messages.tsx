import { Avatar, Flex } from "@chakra-ui/react"

interface ChatMessagesProps {
	messages: {sender: "human" | "instore", content: string}[]
}

export function ChatMessages(props: ChatMessagesProps) {
  //TODO: Change key prop from content to id
  return (
    <div>
      {props.messages.map((m) => {
        if (m.sender === "human") {
	  return (
	    <Flex key={m.content} direction="row" minHeight="80px" width="90vw" justify="right" align="center">
	      <div style={{paddingRight: "24px", fontSize: "20px"}}>{m.content}</div>
		<Avatar.Root size="2xl" colorPalette="cyan">
		  <Avatar.Fallback name="Ali Amin"/>
		</Avatar.Root>
	    </Flex>
	  )
        } else {
	  return (
	    <Flex key={m.content} direction="row" minHeight="80px" width="80vw" justify="left" align="center">
	      <Avatar.Root size="2xl" backgroundColor="white">
	        <Avatar.Image src="src/assets/INTEND_standard.svg" objectFit="contain" padding="2px"/>
	      </Avatar.Root>
	      <div style={{paddingLeft: "24px", fontSize: "20px"}}>{m.content}</div>
	    </Flex>
	  )
	}
      })}
    </div>
  )
}
