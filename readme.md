# WebSocket Integration

This repository contains a WebSocket client that integrates with a GraphQL endpoint and forwards events to a webhook.

## Quick Deploy to Azure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fjumbrage%2FdeviceActivity2Webhook%2Fmain%2Fazuredeploy.json)

## Prerequisites

Before deploying, you'll need:

1. X-Token-ID and X-Token-Value for authentication
2. GraphQL WebSocket URL
3. Webhook URL to forward events

## Deployment Parameters

| Parameter          | Description                                                   |
| ------------------ | ------------------------------------------------------------- |
| containerGroupName | Name for the container group (default: websocket-integration) |
| xTokenId           | Your X-Token-ID for authentication                            |
| xTokenValue        | Your X-Token-Value for authentication                         |
| graphqlWsUrl       | WebSocket URL for GraphQL endpoint                            |
| webhookUrl         | Webhook URL to forward detection events                       |

## Local Development

To build and run locally:

```bash
# Build the container
docker build -t websocket-client ./src

# Run locally
docker run -e X_TOKEN_ID="your-token-id" \
           -e X_TOKEN_VALUE="your-token-value" \
           -e GRAPHQL_WS_URL="your-ws-url" \
           -e WEBHOOK_URL="your-webhook-url" \
           websocket-client
```

## Container Image

The container image is automatically built and published to the GitHub Container Registry with every push to the main branch. You can find the latest image at:

```
ghcr.io/jumbrage/websocket-client-da:latest
```
