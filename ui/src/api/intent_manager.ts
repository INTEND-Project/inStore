import axios from "axios"

const apiUrl = import.meta.env.VITE_INTENT_MANAGER_URL

export const submitQuery = async (text: string) => {
	const response = await axios.post(`${apiUrl}/intent`, {
		expression: text
	}, {
		headers: {
			"Content-Type": "application/json"
		}
	})
	console.log(response)
	if (response.status != 200) {
		throw new Error("Cannot reach intent manager")
	} else {
		return response.data
	}
}

