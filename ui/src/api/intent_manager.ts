import axios from "axios";
import { v4 as uuidv4 } from "uuid";

const apiUrl = import.meta.env.VITE_INTENT_MANAGER_URL;

export const submitQuery = async (text: string) => {
  const response = await axios.post(
    `${apiUrl}/intent`,
    {
      expression: text,
      id: uuidv4(),
    },
    {
      headers: {
        "Content-Type": "application/json",
      },
    },
  );
  if (response.status != 200) {
    throw new Error("Cannot reach intent manager");
  } else {
    return response.data;
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
