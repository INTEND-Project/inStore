# InStorage

InStorage is part of the INTEND project toolset. It is a combination of AI agents and tools to achieve intent-driven management of storage environments. Additionally, InStorage utilizes insights on data and access patterns to optimize the placement of data according to objectives specified by intents.

## Architecture

![image](https://github.com/user-attachments/assets/2c6a74bf-d832-4c5e-bab3-58b831e5426f)

### Intent Agent

A multi-role LLM-powered AI agent that takes in intents, translates them into objectives and parameters, then identifies the required tools to call. Additionally, the agent is also responsible for identifying conflicting or similar intents. This agent takes the role of the intent manager and intent handler.

### Recommendation Engine

The AI/ML inventory that takes the current environment, objectives, and the system’s state to generate a set of actions that will achieve an intent’s objectives using the best suited algorithms and models.

### Storage Controller

A job-scheduling component which takes a set of client-agnostic commands and translates them to implementation-specific commands (e.g., S3 storage), then executes them remotely on the storage environment using multiple implemented storage clients.

![storage](https://github.com/user-attachments/assets/a8db7663-e379-42bf-80ba-623f255430d8)

The storage controller can be replaced by use case specific tools, such as tools to call API endpoints that do the storage control logic.

### Knowledge Graph

The graph-based knowledge store that contains the intent inventory, the storage environment’s topology (i.e., devices, allocation, geolocations, regions, etc.), and the timeline of actions to be taken to achieve the goals for each intent.
![kg-schema](https://github.com/user-attachments/assets/3a1b3aed-f31b-4572-9c19-6bbf6f9883f7)
![neo4j](https://github.com/user-attachments/assets/9b5f15b2-d02e-4ab7-9927-e06656a2c45a)

## Workflows

![workflow](https://github.com/user-attachments/assets/f894a804-ee08-4ce2-97e1-000dc4e799f9)

## How to run

The easiest way to get a version running is to run the docker-compose.yaml file in `./instore/docker-compose.yaml`.

First, create a `.env` file which includes LLM API keys, Neo4j auth username and passwords, and API endpoints.

```bash
cp ./instore/.env-example ./instore/.env
vi ./instore/.env
```

Next, choose the LLM backend by pointing `INSTORE_CONFIG` in `.env` to one of the config files in `./instore/intents/`, for example:

```bash
INSTORE_CONFIG=./intents/config-gemini-docker.json  # Gemini 3 Flash, requires GEMINI_API_KEY
INSTORE_CONFIG=./intents/config-octo.json           # OCTO EU LLM served by vLLM
```

Each config file contains the LLM provider, endpoint, and model name. To use your own OpenAI-compatible server (e.g., vLLM), copy one of the `vllm` config files and change its `endpoint` and `model_name`. When `INSTORE_CONFIG` is not set, Docker uses `./intents/config-docker.json`.

The optional `use_case` section of the config file selects the recommendation engine, which decides the storage actions that achieve an intent, and the executor, which carries them out. When the section is missing, the MOG CDN use case is used:

```json
"use_case": {
  "engine": { "provider": "mog_cdn" },
  "executor": { "provider": "mog" }
}
```

The MOG engine and executor call the MOG API at `MOG_API_URL`. If the MOG API is not reachable, set `MOG_DRY_RUN=true` in `.env`. The engine then plans against mock video data, and the actions are logged instead of being executed.

Then run the docker compose up command. This command will run both Neo4j and the Python application for inStore

```bash
cd instore
docker compose up
```

> [!TIP]
> It is possible to configure your own LLM instance. vLLM may be integrated with inStore directly, but custom models/servings will require some implementation effort. We have created an interface for LLM backends in inStore, to add your own you can create an implementation in `./instore/pkg/llms/` and add configuration for it by following the same schema as `./instore/intents/config.json`. Additionally, you should extend the LLM backend factory to look for your new configuration before instantiating your new LLM backend `./instore/pkg/llms/factory.py`.

At this point, you will have inStore and the intend database (Neo4j) running. To start the UI webapp, ensure you have `node >= v20.18.0` and `npm >= 10.8.2` and run:

```bash
cd ./ui
cp .env-example .env # points the UI to the intent manager at http://localhost:5001

npm install && npm run dev
```

The UI is then available at `http://localhost:5173`.

### API key

To require an API key, set `INSTORE_API_KEY` in `./instore/.env`. Every route except `/api/v1/health` then requires the key in the `X-API-Key` header, and the UI needs the same key in `VITE_INTENT_MANAGER_API_KEY` in `./ui/.env`. The UI runs in the browser, so anyone using it can see the key: it protects the API from other clients, not the UI itself.

### Running on a remote machine

The UI runs in your browser, so it calls the intent manager from the machine you browse from, not from the remote machine. When running inStore on a remote machine (e.g., `remote-host`), point the UI to the remote intent manager in `./ui/.env`:

```bash
VITE_INTENT_MANAGER_URL=http://remote-host:5001
```

Vite only listens on `localhost` by default, so start the UI with `--host` to make it reachable from other machines:

```bash
npm run dev -- --host
```

The UI is then available at `http://remote-host:5173`. Ports `5173` (UI) and `5001` (intent manager) must be reachable on the remote machine. Vite reads `./ui/.env` only at startup, so restart `npm run dev` after changing it.

## Running the tests

The API tests use an in-memory intent database and the dry run executor, so they need neither Neo4j nor an LLM:

```bash
cd instore
pip install -r requirements-dev.txt
pytest
```

## Contributions

To get started with contributions and how to setup your git and IDE, see [CONTRIBUTIONS.md](./CONTRIBUTION.md).
