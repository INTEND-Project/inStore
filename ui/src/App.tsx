import { submitQuery } from './api/intent_manager.ts'
import './App.css'
import ChatbotInput from "./components/input.tsx"
import { Flex } from "@chakra-ui/react"
import { useState } from "react" 
import { ChatMessages } from './components/messages.tsx'

interface Message {
	sender: "human" | "instore"
	content: string
	tool_calls?: string[],
	commands?: string[],
}

function App() {
  
  const [messages, setMessages] = useState<Message[]>(
	  [{"sender":"instore","content":"Hello, how may I assist you to manage your data and storage ?"}]
  )
  const [loading, setLoading] = useState<boolean>(false)

  const submit = async (newMessage: string): Promise<boolean> => {
	  setLoading(true)
	  const newMessages = [...messages, {sender: "human", content: newMessage} as Message]
	  setMessages(newMessages)
	  try {
		  const res = await submitQuery(newMessage)
		  setMessages(
			  [...newMessages, 
			   {
				   sender: "instore", 
				   content: res["reply"],
				   tool_calls: res["tool_calls"],
				   commands: res["cmds"],
			   },
			  ]
		  )
		  setLoading(false)
		  return true
	  } catch(e) {
		  console.log(e)
		  setLoading(false)
		  return false
	  }
  }
  
  return (
	<Flex paddingTop="64px" height="95vh" width="95vw" direction="column" align="center" justify="space-between">
		<ChatMessages messages={messages}/>
		<ChatbotInput onSubmit={submit} loading={loading}/>
  	</Flex>
  )
}

export default App
