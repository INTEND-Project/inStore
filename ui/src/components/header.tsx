import { Box, Flex, Image, Text } from "@chakra-ui/react";

const Header = (props: { logoSrc: string; title: string }) => {
  return (
    <Flex
      as="header"
      position="fixed"
      top="0"
      left="0"
      right="0"
      zIndex="sticky"
      px={8}
      color="#0076CE"
      fontFamily="Roboto"
      py={2}
      height="80px"
      backgroundColor="white"
      alignItems="center"
      justifyContent="space-between"
      borderBottomColor="lightgrey"
      borderBottomWidth="1px"
    >
      <Flex>
        <Image src={props.logoSrc} width="300px" />
        <Text
          as="h1"
          paddingTop="4px"
          fontSize="xx-large"
          fontWeight="bold"
          fontFamily="Roboto"
          paddingLeft="20px"
        >
          OCTO
        </Text>
      </Flex>
      <Text as="h1" textAlign="center" fontSize="xx-large" fontWeight="light">
        {props.title}
      </Text>
      <Box width="300px" />
    </Flex>
  );
};

export default Header;
