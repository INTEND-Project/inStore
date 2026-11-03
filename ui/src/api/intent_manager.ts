import axios from "axios";

const apiUrl = import.meta.env.VITE_INTENT_MANAGER_URL;

export const submitQuery = async (
  text: string,
  conversationId: string,
  setUpdate: (msg: string) => void,
  setFinalMessage: (msg: string) => void,
) => {
  try {
    const response = await fetch(`${apiUrl}/intent`, {
      method: "POST",
      body: JSON.stringify({ expression: text, id: conversationId }),
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
    });

    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const handleEvent = (event: string) => {
        if (!event.startsWith("data: ")) return;
        try {
          const data = JSON.parse(event.slice("data: ".length));

          if (data.type === "tool_call") {
            setUpdate(data.message);
          } else if (data.type === "response") {
            setFinalMessage(data.reply);
          } else if (data.type === "error") {
            setFinalMessage(`Error: ${data.message}`);
          }
        } catch (e) {
          console.error("Error parsing event", e);
        }
      };

      // A network read can end in the middle of an event (long replies over a real network),
      // so keep the incomplete part until the rest arrives. Events are separated by a blank line.
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        events.forEach(handleEvent);
      }
      handleEvent(buffer.trim());
    }
  } catch (e) {
    console.error(e);
  }
};

export const getIntents = async () => {
  const response = await axios.get(`${apiUrl}/intent`);
  if (response.status != 200) {
    throw new Error("Cannot reach intent manager");
  } else {
    console.log(response.data);
    return response.data;
  }
};

export const getIntent = async (name: String) => {
  const response = await axios.get(`${apiUrl}/intent/${name}`);
  if (response.status != 200) {
    throw new Error("Cannot reach intent manager");
  } else {
    return response.data;
  }
};
