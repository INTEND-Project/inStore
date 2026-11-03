import {
  Box,
  Button,
  Card,
  CloseButton,
  Dialog,
  Drawer,
  DrawerPositioner,
  Flex,
  Image,
  Portal,
  SimpleGrid,
  Progress,
  Table,
  HStack,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { getIntentActions, getIntents } from "../api/intent_manager";
import { GiFlagObjective } from "react-icons/gi";

type Intent = {
  name: string;
  objective: string;
  active_from: string | null;
  // null when the intent has no end
  active_until: string | null;
  action_count: number;
  failed_action_count: number;
};

type IntentAction = {
  type: string;
  content_id: string;
  source: string;
  destination: string;
  executed_at: string | null;
  status: string | null;
  error: string | null;
};

const until = (intent: Intent) => intent.active_until ?? "no end date";

const IntentsPage = () => {
  const [intents, setIntents] = useState<Intent[]>([]);
  useEffect(() => {
    getIntents().then(setIntents).catch(console.error);
  }, []);

  return (
    <SimpleGrid columns={[2, null, 3]} paddingLeft="200px" width="85%">
      {intents.map((intent, index) => {
        if (!intent) {
          return <div />;
        }
        return (
          <Card.Root
            key={index}
            _hover={{
              boxShadow: "8px 8px 8px #A9A9A9",
              transform: "scale(1.01)",
            }}
            padding="12px"
            transition="all 0.3s ease"
            marginTop="25px"
            marginLeft="20px"
            borderRadius="16px"
            borderColor="#0076CE"
            borderWidth="2px"
            boxShadow="4px 4px 8px #A9A9A9"
            maxWidth="800px"
          >
            <Card.Body>
              <HStack
                style={{ fontSize: "18px", fontWeight: "bold", color: "black" }}
              >
                <GiFlagObjective />
                {intent.name}
              </HStack>
              <div
                style={{
                  paddingLeft: "8px",
                  paddingBottom: "4px",
                  fontSize: "16px",
                  fontWeight: "lighter",
                }}
              >
                Objective: {intent.objective}
              </div>
              <div
                style={{
                  paddingLeft: "8px",
                  fontSize: "16px",
                  fontWeight: "lighter",
                }}
              >
                Timeline: {intent.active_from} to {until(intent)}
              </div>
              <div
                style={{
                  paddingLeft: "8px",
                  fontSize: "16px",
                  fontWeight: "lighter",
                }}
              >
                Actions: {intent.action_count}
                {intent.failed_action_count > 0 &&
                  ` (${intent.failed_action_count} failed)`}
              </div>
              {/* Mounted only when opened, so the actions are fetched on demand */}
              <Drawer.Root size="xl" lazyMount unmountOnExit>
                <Drawer.Trigger asChild>
                  <Button
                    marginTop="12px"
                    width="100px"
                    alignSelf="end"
                    backgroundColor="#0076EA"
                    borderRadius="4px"
                    _focus={{ borderColor: "white", outline: "none" }}
                    _hover={{ borderColor: "white" }}
                    _active={{
                      borderColor: "white",
                      border: "none",
                      outline: "none",
                    }}
                  >
                    View More
                  </Button>
                </Drawer.Trigger>
                <Portal>
                  <DrawerPositioner>
                    <Drawer.Content backgroundColor="rgb(250,250,250)">
                      <Drawer.Header>
                        <Drawer.Title fontSize="xl">
                          Intent: {intent.name}
                        </Drawer.Title>
                      </Drawer.Header>
                      <Drawer.Body fontSize="18px">
                        <Box>Objective: {intent.objective}</Box>
                        <Box pt="4px">
                          Target start date: {intent.active_from}
                        </Box>
                        <Box pt="4px">Target end date: {until(intent)}</Box>
                        <Box pt="12px" fontWeight="bold" fontSize="24px">
                          Actions
                        </Box>
                        <Box pt="12px"></Box>
                        <IntentActions name={intent.name} />
                      </Drawer.Body>
                      <Drawer.ActionTrigger asChild>
                        <Button
                          marginTop="12px"
                          width="100px"
                          alignSelf="end"
                          backgroundColor="#0076DA"
                          borderColor="white"
                          marginBottom="12px"
                          marginRight="12px"
                          borderRadius="4px"
                          _focus={{ borderColor: "white", outline: "none" }}
                          _hover={{ borderColor: "white" }}
                          _active={{
                            borderColor: "white",
                            border: "none",
                            outline: "none",
                          }}
                        >
                          Close
                        </Button>
                      </Drawer.ActionTrigger>
                    </Drawer.Content>
                  </DrawerPositioner>
                </Portal>
              </Drawer.Root>
            </Card.Body>
          </Card.Root>
        );
      })}
    </SimpleGrid>
  );
};

const IntentActions = (props: { name: string }) => {
  const [actions, setActions] = useState<IntentAction[] | null>(null);
  useEffect(() => {
    getIntentActions(props.name).then(setActions).catch(console.error);
  }, [props.name]);

  if (actions === null) {
    return <Box>Loading actions...</Box>;
  }
  return actions.length != 0 && actions[0].type === "ADD_SG" ? (
    <StorageConfigTable actions={actions} />
  ) : (
    <PlacementTable actions={actions} />
  );
};

const PlacementTable = (props: { actions: IntentAction[] }) => {
  return (
    <Table.Root size="sm" striped interactive>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Date</Table.ColumnHeader>
          <Table.ColumnHeader>Action</Table.ColumnHeader>
          <Table.ColumnHeader>Content ID</Table.ColumnHeader>
          <Table.ColumnHeader>From</Table.ColumnHeader>
          <Table.ColumnHeader>To</Table.ColumnHeader>
          <Table.ColumnHeader>Status</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {props.actions.map((action, index) => (
          <Table.Row key={`${action.content_id}${index}`}>
            <Table.Cell>{action.executed_at}</Table.Cell>
            <Table.Cell>{action.type}</Table.Cell>
            <Table.Cell>{action.content_id}</Table.Cell>
            <Table.Cell>
              <NodeName name={action.source} />
            </Table.Cell>
            <Table.Cell>
              <NodeName name={action.destination} />
            </Table.Cell>
            <Table.Cell
              color={action.status === "failed" ? "red" : undefined}
              title={action.error ?? undefined}
            >
              {action.status}
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  );
};

const StorageConfigTable = (props: { actions: IntentAction[] }) => {
  return (
    <Table.Root size="sm" striped interactive>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Date</Table.ColumnHeader>
          <Table.ColumnHeader>Action</Table.ColumnHeader>
          <Table.ColumnHeader>Size</Table.ColumnHeader>
          <Table.ColumnHeader>To</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {props.actions.map((action, index) => (
          <Table.Row key={`${action.content_id}${index}`}>
            <Table.Cell>{action.executed_at}</Table.Cell>
            <Table.Cell>{action.type}</Table.Cell>
            <Table.Cell>100GB</Table.Cell>
            <Table.Cell>
              <NodeName name={action.destination} />
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  );
};

const NodeName = (props: { name: String }) => {
  return (
    <Dialog.Root size="lg" placement="center" motionPreset="slide-in-bottom">
      <Dialog.Trigger asChild>
        <Box color="blue" textDecoration="underline" cursor="pointer">
          {props.name}
        </Box>
      </Dialog.Trigger>
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header justifyContent="center">
              <Dialog.Title>{props.name}</Dialog.Title>
              <Dialog.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Dialog.CloseTrigger>
            </Dialog.Header>
            <Dialog.Body>
              <Flex justifyContent="center" alignItems="start">
                <Box paddingTop="24px">
                  <Box>CPU: Intel Xeon E5-2697-v4 2.8GHz 18 core</Box>
                  <Box>Cache-System MIN (RAW): 1024GB </Box>
                  <Box>Cache-System MAX (RAW) 16TB</Box>
                  <Box>Location: EU (Cork LAB_2)</Box>
                  <HStack>
                    Status: <Box color="green">Healthy</Box>
                  </HStack>
                </Box>
                <Flex direction="column" alignItems="center">
                  <Box fontWeight="bold" fontSize="16px" paddingBottom="20px">
                    PowerMax 8000
                  </Box>
                  <Image
                    width="400px"
                    height="80px"
                    src="./src/assets/dellemc_powermax2000_ff_header.png"
                  />
                  <Progress.Root
                    width="350px"
                    paddingTop="20px"
                    colorPalette="blue"
                    defaultValue={20}
                  >
                    <HStack gap="5">
                      <Progress.Label>Storage </Progress.Label>
                      <Progress.Track flex="1">
                        <Progress.Range />
                      </Progress.Track>
                      <Progress.ValueText>15.36TB</Progress.ValueText>
                    </HStack>
                  </Progress.Root>
                  <Box>5.76TB</Box>
                </Flex>
              </Flex>
            </Dialog.Body>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
};
export default IntentsPage;
