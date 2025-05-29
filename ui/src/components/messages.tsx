import { Avatar, Flex } from "@chakra-ui/react"
import { renderToString } from "react-dom/server";
import ReactMarkdown from 'react-markdown';


interface ChatMessagesProps {
	messages: {
		sender: "human" | "instore", 
		content: string,
		tool_calls: string[],
		commands: string[],
	}[]
}

export function ChatMessages(props: ChatMessagesProps) {
  const renderMessage = (message: string) => {
    const msg = message.trim()
    if (msg.substring(0,7) === "```json") {
      const intent = JSON.parse(msg.substring(7).split("```")[0])	
      return <div style={{padding:"24px", backgroundColor: "#141416", borderRadius: "16px", borderColor: "teal", borderWidth: "2px"}}>
      	<div style={{fontSize: "18px", fontWeight: "bold"}}>{intent["message"]}</div>
      	<div style={{paddingLeft: "8px", fontSize: "18px"}}>{intent["intent_name"]}</div>
      	<div style={{paddingLeft: "8px", paddingBottom: "4px", fontSize: "16px", fontWeight: "lighter"}}>Actions: {intent["actions"]}</div>
      	<div style={{paddingLeft: "8px", fontSize: "16px", fontWeight: "lighter"}}>Results: {intent["results"]}</div>
      </div>
    } else {
      return msg
    }
  }
	
  //TODO: Change key prop from content to id
  return (
    <div>
      {props.messages.map((m) => {
        if (m.sender === "human") {
	  return (
	    <Flex key={m.content} direction="row" minHeight="80px" width="90vw" justify="right" align="center">
	      <div style={{paddingRight: "24px", fontSize: "20px"}}>{m.content}</div>
		<Avatar.Root size="2xl" colorPalette="cyan">
		  <Avatar.Fallback name="John Doe"/>
		</Avatar.Root>
	    </Flex>
	  )
        } else {
	  return (
	    <Flex key={m.content} direction="row" minHeight="80px" width="80vw" justify="left" align="center">
	      <Avatar.Root size="2xl" backgroundColor="white">
	        <Avatar.Image src="src/assets/INTEND_standard.svg" objectFit="contain" padding="2px"/>
	      </Avatar.Root>
	      <div style={{paddingLeft: "24px", fontSize: "20px"}}>
	        <div style={{paddingBottom: "24px"}}>
		   {renderMessage(m.content)}
		</div>
	      </div>
	    </Flex>
	  )
	}
      })}
    </div>
  )
}
