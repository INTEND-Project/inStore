# Intent Manager
This service is responsible for receiving natural language (intent expressions) and translating it
to machine-readable requirements for storage management. 

## Agentic Architecture
The **Intent Manager** acts as an AI Agent, taking inputs from the user and then performing the
proper **Tool Calls**. At the moment, the available tools are the data placement optimizer and 
the storage controller.

## Steps to run
To run the service from this directory, simply run
```bash
export NT_BEARER_TOKEN={bearer_token_for_octo_openwebui}
python intent_manager.py
```

To get the bearer token, login to http://10.60.26.10/ and inspect the network tab during a chat,
you should see in the request headers an authorization bearer token such as:

```
Authorization:     Bearer
                   eyJhbGciOiJIUzI1NiIsAnR5cCI6IkpXVCJ9.eyJpZCI6IjY4NmRmYYgyLWRhZjYtNDk0OS05NGUyL
                   WY3NTYyMzdjYzIyOCJ9.rpdsLqln6bKdkp_pT1ihVfd1Txvf5NZNcRVmn7i5x95
```

**[Important]: Treat this token as a secret!**
