# InStorage
InStorage is part of the INTEND project toolset. It is a combination of AI agents and tools to achieve intent-driven management of storage environments. Additionally, InStorage utilizes insights on data and access patterns to optimize the placement of data according to objectives specified by intents. 

![image](https://github.com/user-attachments/assets/2c6a74bf-d832-4c5e-bab3-58b831e5426f)

## Components
### Intent Agent
A multi-role LLM-powered AI agent that takes in intents, translates them into objectives and parameters, then identifies the required tools to call. Additionally, the agent is also responsible for identifying conflicting or similar intents. This agent takes the role of the intent manager and intent handler.
### Recommendation Engine
The AI/ML inventory that takes the current environment, objectives, and the system’s state to generate a set of actions that will achieve an intent’s objectives using the best suited algorithms and models.
### Storage Controller
A job-scheduling component which takes a set of client-agnostic commands and translates them to implementation-specific commands (e.g., S3 storage), then executes them remotely on the storage environment using multiple implemented storage clients.

![storage](https://github.com/user-attachments/assets/a8db7663-e379-42bf-80ba-623f255430d8)

### Knowledge Graph
The graph-based knowledge store that contains the intent inventory, the storage environment’s topology (i.e., devices, allocation, geolocations, regions, etc.), and the timeline of actions to be taken to achieve the goals for each intent.
![kg-schema](https://github.com/user-attachments/assets/3a1b3aed-f31b-4572-9c19-6bbf6f9883f7)
![neo4j](https://github.com/user-attachments/assets/9b5f15b2-d02e-4ab7-9927-e06656a2c45a)

## Workflows
![workflow](https://github.com/user-attachments/assets/f894a804-ee08-4ce2-97e1-000dc4e799f9)


## Getting Started
To get started with contributions and how to setup your git and IDE, see [CONTRIBUTIONS.md](./CONTRIBUTION.md).
