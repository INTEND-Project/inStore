import { useState } from "react";
import { Field, HStack, Textarea, Button, ButtonGroup } from "@chakra-ui/react";
import { RiArrowRightLine } from "react-icons/ri";

interface ChatInputProps {
  loading: boolean;
  onSubmit(text: string): Promise<boolean>;
}

function ChatInput(props: ChatInputProps) {
  const [text, setText] = useState<string>("");

  const onSubmit = () => {
    props.onSubmit(text).then((success) => (success ? setText("") : null));
  };

  return (
    <HStack
      gap="10"
      width="90%"
      pos="fixed"
      backgroundColor="white"
      paddingLeft="100px"
      bottom="0px"
      paddingBottom="10px"
      marginLeft="200px"
      zIndex={0}
    >
      <Field.Root>
        <Field.Label textStyle="lg">Ask anything storage</Field.Label>
        <Textarea
          value={text}
          onChange={(v) => setText(v.target.value)}
          maxHeight="526px"
          variant="subtle"
          borderColor="#007DDA"
          size="xl"
          textStyle="xl"
          resize="vertical"
          disabled={props.loading}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              onSubmit();
            }
          }}
        />
        <Field.HelperText>Max 500 characters.</Field.HelperText>
      </Field.Root>
      <ButtonGroup color="#007DB8">
        <Button
          loading={props.loading}
          borderWidth="1pt"
          backgroundColor="#007DDA"
          borderRadius="6px"
          height="50px"
          loadingText="Sending..."
          spinnerPlacement="start"
          size="2xl"
          color="white"
          variant="plain"
          onClick={onSubmit}
        >
          {/* will clear text if successful */}
          Send <RiArrowRightLine />
        </Button>
      </ButtonGroup>
    </HStack>
  );
}

export default ChatInput;
