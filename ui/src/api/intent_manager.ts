import axios from "axios";
import { v4 as uuidv4 } from "uuid";

const apiUrl = import.meta.env.VITE_INTENT_MANAGER_URL;

export const submitQuery = async (
  text: string,
  setUpdate: (msg: string) => void,
  setFinalMessage: (msg: string) => void,
) => {
  try {
    const response = await fetch(`${apiUrl}/intent`, {
      method: "POST",
      body: JSON.stringify({ expression: text, id: uuidv4() }),
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
    });

    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        const lines = chunk.split("\n");
        lines.forEach((line) => {
          if (line.startsWith("data: ")) {
            const jsonStr = line.replace("data: ", "");
            try {
              const data = JSON.parse(jsonStr);

              if (data.type === "tool_call") {
                setUpdate(data.message);
              } else if (data.type === "response") {
                setFinalMessage(data.reply);
              }
            } catch (e) {
              console.error("Error parsing JSON chunk", e);
            }
          }
        });
      }
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
