import { useState } from "react"
import { Field, HStack, Textarea, Button, ButtonGroup } from "@chakra-ui/react"
import { RiArrowRightLine } from "react-icons/ri"

interface ChatInputProps {
	loading: boolean;
	onSubmit(text: string): Promise<boolean>
}

function ChatInput(props: ChatInputProps) {
  const [text, setText] = useState<string>("")

  return (
	<HStack gap="10" width="90%">
		<Field.Root>
			<Field.Label textStyle="lg">Ask anything storage</Field.Label>
			<Textarea 
			  value={text}
			  onChange={(v) => setText(v.target.value)}
			  maxHeight="526px" 
			  variant="subtle" 
			  colorPalette="cyan" 
			  size="xl" 
			  textStyle="xl"
			  resize="vertical"/>
			<Field.HelperText>Max 500 characters.</Field.HelperText>
		</Field.Root>
		<ButtonGroup colorPalette="cyan">
			<Button 
			  loading={props.loading}
		          loadingText="Sending..."
			  spinnerPlacement="start"
			  size="2xl" 
			  colorPalette="cyan" 
			  variant="plain"
			  onClick={() => props.onSubmit(text).then((success) => success ? setText("") : null)}> {/* will clear text if successful */}
				Send <RiArrowRightLine/> 
			</Button>
		</ButtonGroup>
	</HStack>
  )
}

export default ChatInput
