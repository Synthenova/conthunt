# Webhooks

> Receive real-time notifications when events occur in Dodo Payments. Automate workflows and keep your systems synchronized with instant event delivery.

<Frame>
  <img src="https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=477435b1004773582aa51236b5cc58e7" alt="Webhook Cover Image" data-og-width="1200" width="1200" data-og-height="630" height="630" data-path="images/cover-images/Webhooks.webp" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?w=280&fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=4499081979872a5281c76ec5c2fca3d4 280w, https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?w=560&fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=81bdc2f85d8d2fc0b3bf6b15488aac95 560w, https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?w=840&fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=a7895a74bca4f5f08cdda49aee2fcf1c 840w, https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?w=1100&fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=1756398be4696df7d9c5b732b8ed7f84 1100w, https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?w=1650&fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=fcc1e8d80719712e8c60d9a0a395d725 1650w, https://mintcdn.com/dodopayments/mOQO5ej_lx0yH9p-/images/cover-images/Webhooks.webp?w=2500&fit=max&auto=format&n=mOQO5ej_lx0yH9p-&q=85&s=ed239cefb0cce030f7a58c2b91266f27 2500w" />
</Frame>

Webhooks provide real-time notifications when specific events occur in your Dodo Payments account. Use webhooks to automate workflows, update your database, send notifications, and keep your systems synchronized.

<Info>
  Our webhook implementation follows the [Standard Webhooks](https://standardwebhooks.com/) specification, ensuring compatibility with industry best practices and existing webhook libraries.
</Info>

## Key Features

<CardGroup cols={2}>
  <Card title="Real-time Delivery" icon="bolt">
    Receive instant notifications when events occur
  </Card>

  <Card title="Secure by Default" icon="shield-check">
    HMAC SHA256 signature verification included
  </Card>

  <Card title="Automatic Retries" icon="rotate">
    Built-in retry logic with exponential backoff
  </Card>

  <Card title="Event Filtering" icon="filter">
    Subscribe only to events you need
  </Card>
</CardGroup>

## Getting Started

<Steps>
  <Step title="Access Webhook Settings">
    Navigate to the DodoPayments Dashboard and go to `Settings > Webhooks`.
  </Step>

  <Step title="Create Webhook Endpoint">
    Click on `Add Webhook` to create a new webhook endpoint.

    <Frame>
      <img src="https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=fc60e939a2bd92b6761c98f5ad58a226" alt="Add Webhook" data-og-width="2872" width="2872" data-og-height="1574" height="1574" data-path="images/webhooks/create-endpoint.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?w=280&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=42e9e9a129a525dc1ea8449d858920a7 280w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?w=560&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=eb96a65147487c60df78573195f6c693 560w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?w=840&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=716342e6ff539cfd077cac4fb262c6e7 840w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?w=1100&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=2d3b589aa66ec2e306099460987ea937 1100w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?w=1650&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=348de527b56321897f7f3addc3e70795 1650w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/create-endpoint.png?w=2500&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=b66f245b8e85cda8d2af30ca62a38440 2500w" />
    </Frame>
  </Step>

  <Step title="Add Endpoint URL">
    Enter the URL where you want to receive webhook events.
  </Step>

  <Step title="Select Events to Receive">
    Choose the specific events your webhook endpoint should listen for by selecting them from the event list.

    <Tip>
      Only selected events will trigger webhooks to your endpoint, helping you avoid unnecessary traffic and processing.
    </Tip>
  </Step>

  <Step title="Get Secret Key">
    Obtain your webhook `Secret Key` from the settings page. You'll use this to verify the authenticity of received webhooks.

    <Warning>
      Keep your webhook secret key secure and never expose it in client-side code or public repositories.
    </Warning>
  </Step>

  <Step title="Rotate Secret (Optional)">
    If needed, you can rotate your webhook secret for enhanced security. Click the **Rotate Secret** button in your webhook settings.

    <Warning>
      Rotating the secret will **expire it** and **replace it** with a new one. The old secret will only be valid for the next 24 hours. Afterward, trying to verify with the old secret will fail.
    </Warning>

    <Info>
      Use secret rotation periodically or immediately if you suspect your current secret has been compromised.
    </Info>
  </Step>
</Steps>

## Configuring Subscribed Events

You can configure which specific events they want to receive for each webhook endpoint.

### Accessing Event Configuration

<Steps>
  <Step title="Navigate to Webhook Details">
    Go to your Dodo Payments Dashboard and navigate to `Settings > Webhooks`.
  </Step>

  <Step title="Select Your Endpoint">
    Click on the webhook endpoint you want to configure.
  </Step>

  <Step title="Open Event Settings">
    In the webhook details page, you'll see a "Subscribed events" section. Click the **Edit** button to modify your event subscriptions.
  </Step>
</Steps>

### Managing Event Subscriptions

<Steps>
  <Step title="View Available Events">
    The interface displays all available webhook events organized in a hierarchical structure. Events are grouped by category (e.g., `dispute`, `payment`, `subscription`).
  </Step>

  <Step title="Search and Filter">
    Use the search bar to quickly find specific events by typing event names or keywords.
  </Step>

  <Step title="Select Events">
    Check the boxes next to the events you want to receive. You can:

    * Select individual sub-events (e.g., `dispute.accepted`, `dispute.challenged`)
    * Select parent events to receive all related sub-events
    * Mix and match specific events based on your needs
  </Step>

  <Step title="Review Event Details">
    Hover over the information icon (ⓘ) next to each event to see a description of when that event is triggered.
  </Step>

  <Step title="Save Configuration">
    Click **Save** to apply your changes, or **Cancel** to discard modifications.
  </Step>
</Steps>

<Warning>
  If you deselect all events, your webhook endpoint will not receive any notifications. Make sure to select at least the events your application needs to function properly.
</Warning>

## Webhook Delivery

### Timeouts

Webhooks have a **15-second timeout window** for both connection and read operations. Ensure your endpoint responds quickly to avoid timeouts.

<Tip>
  Process webhooks asynchronously by acknowledging receipt immediately with a `200` status code, then handling the actual processing in the background.
</Tip>

### Automatic Retries

If a webhook delivery fails, Dodo Payments automatically retries with exponential backoff to prevent overwhelming your system.

| Attempt | Delay       | Description                                                  |
| ------- | ----------- | ------------------------------------------------------------ |
| 1       | Immediately | First retry happens right away                               |
| 2       | 5 seconds   | Second attempt after short delay                             |
| 3       | 5 minutes   | Third attempt with increased backoff                         |
| 4       | 30 minutes  | Fourth attempt continuing backoff                            |
| 5       | 2 hours     | Fifth attempt with extended delay                            |
| 6       | 5 hours     | Sixth attempt with longer delay                              |
| 7       | 10 hours    | Seventh attempt with maximum delay                           |
| 8       | 10 hours    | **Final attempt** - webhook marked as failed if unsuccessful |

<Info>
  **Maximum of 8 retry attempts** per webhook event. For example, if a webhook fails three times before succeeding, the total delivery time is approximately 35 minutes and 5 seconds from the first attempt.
</Info>

<Tip>
  Use the Dodo Payments dashboard to manually retry individual messages or bulk recover all failed messages at any time.
</Tip>

### Idempotency

Each webhook event includes a unique `webhook-id` header. Use this identifier to implement idempotency and prevent duplicate processing.

```javascript  theme={null}
// Example: Storing webhook IDs to prevent duplicate processing
const processedWebhooks = new Set();

app.post('/webhook', (req, res) => {
  const webhookId = req.headers['webhook-id'];
  
  if (processedWebhooks.has(webhookId)) {
    return res.status(200).json({ received: true });
  }
  
  processedWebhooks.add(webhookId);
  // Process the webhook...
});
```

<Warning>
  Always implement idempotency checks. Due to retries, you may receive the same event multiple times.
</Warning>

### Event Ordering

Webhook events may arrive out of order due to retries or network conditions. Design your system to handle events in any sequence.

<Info>
  You will receive the **latest payload at the time of delivery**, regardless of when the webhook event was originally emitted.
</Info>

## Securing Webhooks

To ensure the security of your webhooks, always validate the payloads and use HTTPS.

### Verifying Signatures

Each webhook request includes a `webhook-signature` header, an HMAC SHA256 signature of the webhook payload and timestamp, signed with your secret key.

#### SDK verification (recommended)

All official SDKs include built‑in helpers to securely validate and parse incoming webhooks. Two methods are available:

* `unwrap()`: Verifies signatures using your webhook secret key
* `unsafe_unwrap()`: Parses payloads without verification

<Tip>
  Provide your webhook secret via `DODO_PAYMENTS_WEBHOOK_KEY` when initializing the Dodo Payments client.
</Tip>

<CodeGroup>
  ```typescript TypeScript/Node.js theme={null}
  import DodoPayments from 'dodopayments';
  import express from 'express';

  const app = express();
  app.use(express.raw({ type: 'application/json' }));

  const client = new DodoPayments({
    bearerToken: process.env.DODO_PAYMENTS_API_KEY,
    environment: process.env.DODO_PAYMENTS_ENVIRONMENT,
    webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  });

  app.post('/webhook', async (req, res) => {
    try {
      const unwrapped = client.webhooks.unwrap(req.body.toString(), {
        headers: {
          'webhook-id': req.headers['webhook-id'] as string,
          'webhook-signature': req.headers['webhook-signature'] as string,
          'webhook-timestamp': req.headers['webhook-timestamp'] as string,
        },
      });
      res.json({ received: true });
    } catch (error) {
      res.status(401).json({ error: 'Invalid signature' });
    }
  });
  ```

  ```python Python theme={null}
  from fastapi import FastAPI, Request, HTTPException
  from dodopayments import DodoPayments
  import os

  app = FastAPI()
  client = DodoPayments(
      bearer_token=os.getenv("DODO_PAYMENTS_API_KEY"),
      environment=os.getenv("DODO_PAYMENTS_ENVIRONMENT"),
      webhook_key=os.getenv("DODO_PAYMENTS_WEBHOOK_KEY"),
  )

  @app.post("/webhook")
  async def handle_webhook(request: Request):
      try:
          unwrapped = client.webhooks.unwrap(
              await request.body(),
              headers={
                  "webhook-id": request.headers.get("webhook-id", ""),
                  "webhook-signature": request.headers.get("webhook-signature", ""),
                  "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
              },
          )
          return {"received": True}
      except Exception:
          raise HTTPException(status_code=401, detail="Invalid signature")
  ```

  ```go Go theme={null}
  import (
  	"context"
  	"io"
  	"net/http"
  	"os"
  	"github.com/dodopayments/dodopayments-go"
  	"github.com/dodopayments/dodopayments-go/option"
  )

  func webhookHandler(w http.ResponseWriter, r *http.Request) {
  	client := dodopayments.NewClient(
  		option.WithBearerToken(os.Getenv("DODO_PAYMENTS_API_KEY")),
  		option.WithEnvironment(os.Getenv("DODO_PAYMENTS_ENVIRONMENT")),
  		option.WithWebhookKey(os.Getenv("DODO_PAYMENTS_WEBHOOK_KEY")),
  	)
  	rawBody, _ := io.ReadAll(r.Body)
  	if _, err := client.Webhooks.Unwrap(context.Background(), rawBody, map[string]string{
  		"webhook-id":       r.Header.Get("webhook-id"),
  		"webhook-signature": r.Header.Get("webhook-signature"),
  		"webhook-timestamp": r.Header.Get("webhook-timestamp"),
  	}); err != nil {
  		http.Error(w, "Invalid signature", http.StatusUnauthorized)
  		return
  	}
  	w.WriteHeader(http.StatusOK)
  }
  ```
</CodeGroup>

#### Manual verification (alternative)

If you are not using an SDK, you can verify signatures yourself following the Standard Webhooks spec:

1. Build the signed message by concatenating `webhook-id`, `webhook-timestamp`, and the exact raw stringified `payload`, separated by periods (`.`).
2. Compute the HMAC SHA256 of that string using your webhook secret key from the Dashboard.
3. Compare the computed signature to the `webhook-signature` header. If they match, the webhook is authentic.

<Info>
  We follow the Standard Webhooks specification. You can use their libraries to verify signatures: [https://github.com/standard-webhooks/standard-webhooks/tree/main/libraries](https://github.com/standard-webhooks/standard-webhooks/tree/main/libraries). For event payload formats, see the [Webhook Payload](/developer-resources/webhooks/intents/payment).
</Info>

### Responding to Webhooks

* Your webhook handler must return a `2xx status code` to acknowledge receipt of the event.
* Any other response will be treated as a failure, and the webhook will be retried.

### Best Practices

<AccordionGroup>
  <Accordion title="Use HTTPS endpoints only" icon="lock">
    Always use HTTPS URLs for webhook endpoints. HTTP endpoints are vulnerable to man-in-the-middle attacks and expose your webhook data.
  </Accordion>

  <Accordion title="Respond immediately" icon="bolt">
    Return a `200` status code immediately upon receiving the webhook. Process the event asynchronously to avoid timeouts.

    ```javascript  theme={null}
    app.post('/webhook', async (req, res) => {
      // Acknowledge receipt immediately
      res.status(200).json({ received: true });
      
      // Process asynchronously
      processWebhookAsync(req.body).catch(console.error);
    });
    ```
  </Accordion>

  <Accordion title="Handle duplicate events" icon="rotate">
    Implement idempotency using the `webhook-id` header to safely process the same event multiple times without side effects.
  </Accordion>

  <Accordion title="Secure your webhook secret" icon="key">
    Store your webhook secret securely using environment variables or a secrets manager. Never commit secrets to version control.
  </Accordion>
</AccordionGroup>

## Webhook Payload Structure

Understanding the webhook payload structure helps you parse and process events correctly.

### Request Format

```http  theme={null}
POST /your-webhook-url
Content-Type: application/json
```

### Headers

<ParamField header="webhook-id" type="string" required>
  Unique identifier for this webhook event. Use this for idempotency checks.
</ParamField>

<ParamField header="webhook-signature" type="string" required>
  HMAC SHA256 signature for verifying the webhook authenticity.
</ParamField>

<ParamField header="webhook-timestamp" type="string" required>
  Unix timestamp (in seconds) when the webhook was sent.
</ParamField>

### Request Body

<ResponseField name="business_id" type="string" required>
  Your Dodo Payments business identifier.
</ResponseField>

<ResponseField name="type" type="string" required>
  Event type that triggered this webhook (e.g., `payment.succeeded`, `subscription.created`).
</ResponseField>

<ResponseField name="timestamp" type="string" required>
  ISO 8601 formatted timestamp of when the event occurred.
</ResponseField>

<ResponseField name="data" type="object" required>
  Event-specific payload containing detailed information about the event.

  <Expandable title="Data object properties">
    <ResponseField name="payload_type" type="string">
      Type of resource: `Payment`, `Subscription`, `Refund`, `Dispute`, or `LicenseKey`.
    </ResponseField>

    Additional fields vary by event type. See the event-specific documentation for complete schemas.
  </Expandable>
</ResponseField>

### Example Payload

```json  theme={null}
{
  "business_id": "string",
  "type": "payment.succeeded | payment.failed |...",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "payload_type": "Payment | Subscription | Refund | Dispute | LicenseKey",
    // ... event-specific fields (see below)
  }
}
```

<CardGroup cols={2}>
  <Card title="Event Types" icon="list" href="/developer-resources/webhooks/intents/webhook-events-guide">
    Browse all available webhook event types
  </Card>

  <Card title="Event Payloads" icon="code" href="/developer-resources/webhooks/intents/payment">
    View detailed payload schemas for each event
  </Card>
</CardGroup>

## Testing Webhooks

You can test your webhook integration directly from the Dodo Payments dashboard to ensure your endpoint is working correctly before going live.

<Frame>
  <img src="https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=b0dfd4a19af0d5b7163c15728e215e89" alt="Endpoint Details" data-og-width="2880" width="2880" data-og-height="1576" height="1576" data-path="images/webhooks/endpoints.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?w=280&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=7aed11a1fbfb9a70415bd344d9482413 280w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?w=560&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=dce335811476847a18399c246549a95f 560w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?w=840&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=329b38c8f03671888b24e448be5d270f 840w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?w=1100&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=4e2425a1165edbe24b23326cd3f06d9f 1100w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?w=1650&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=9d48ad24ab915cd879bb802a98b4d2c6 1650w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/endpoints.png?w=2500&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=9592db9397b85880483109a0af195e7e 2500w" />
</Frame>

### Accessing the Testing Interface

<Steps>
  <Step title="Navigate to Webhooks">
    Go to your Dodo Payments Dashboard and navigate to `Settings > Webhooks`.
  </Step>

  <Step title="Select Your Endpoint">
    Click on your webhook endpoint to access its details page.
  </Step>

  <Step title="Open Testing Tab">
    Click on the **Testing** tab to access the webhook testing interface.
  </Step>
</Steps>

### Testing Your Webhook

The testing interface provides a comprehensive way to test your webhook endpoint:

<Steps>
  <Step title="Select Event Type">
    Use the dropdown menu to select the specific event type you want to test (e.g., `payment.succeeded`, `payment.failed`, etc.).

    <Info>
      The dropdown contains all available webhook event types that your endpoint can receive.
    </Info>
  </Step>

  <Step title="Review Schema and Example">
    The interface displays both the **Schema** (data structure) and **Example** (sample payload) for the selected event type.
  </Step>

  <Step title="Send Test Event">
    Click the **Send Example** button to send a test webhook to your endpoint.

    <Warning>
      **Important**: Failed messages sent through the testing interface will not be retried. This is for testing purposes only.
    </Warning>
  </Step>
</Steps>

### Verifying Your Test

<Steps>
  <Step title="Check Your Endpoint">
    Monitor your webhook endpoint logs to confirm the test event was received.
  </Step>

  <Step title="Verify Signature">
    Ensure your signature verification is working correctly with the test payload.
  </Step>

  <Step title="Test Response">
    Confirm your endpoint returns a `2xx` status code to acknowledge receipt.
  </Step>
</Steps>

### Implementation Example

Here's a complete Express.js implementation showing webhook verification and handling:

<CodeGroup>
  ```typescript Express.js Webhook Handler theme={null}
  import { Webhook } from "standardwebhooks";
  import express from "express";

  const app = express();
  app.use(express.json());

  const webhook = new Webhook(process.env.DODO_WEBHOOK_SECRET);

  app.post('/webhook/dodo-payments', async (req, res) => {
    try {
      // Extract webhook headers
      const webhookHeaders = {
        "webhook-id": req.headers["webhook-id"] as string,
        "webhook-signature": req.headers["webhook-signature"] as string,
        "webhook-timestamp": req.headers["webhook-timestamp"] as string,
      };

      // Verify the webhook signature
      const payload = JSON.stringify(req.body);
      await webhook.verify(payload, webhookHeaders);
      
      // Acknowledge receipt immediately
      res.status(200).json({ received: true });
      
      // Process webhook asynchronously
      processWebhookAsync(req.body).catch(console.error);
      
    } catch (error) {
      console.error('Webhook verification failed:', error);
      res.status(400).json({ error: 'Invalid signature' });
    }
  });

  async function processWebhookAsync(data: any) {
    // Handle the webhook event based on type
    switch (data.type) {
      case 'payment.succeeded':
        await handlePaymentSucceeded(data);
        break;
      case 'subscription.created':
        await handleSubscriptionCreated(data);
        break;
      // Add more event handlers...
    }
  }
  ```

  ```javascript Testing Webhooks Locally theme={null}
  const { Webhook } = require("standardwebhooks");
  const axios = require("axios");
  const crypto = require("crypto");

  // Generate test webhook
  const timestamp = new Date();
  const webhookId = crypto.randomUUID();
  const payload = {
    business_id: "biz_test123",
    type: "payment.succeeded",
    timestamp: timestamp.toISOString(),
    data: {
      payload_type: "Payment",
      payment_id: "pay_test456",
      amount: 2999
    }
  };

  // Sign the payload
  const webhookSecret = process.env.DODO_WEBHOOK_SECRET;
  const webhookInstance = new Webhook(webhookSecret);
  const payloadString = JSON.stringify(payload);
  const signature = webhookInstance.sign(webhookId, timestamp, payloadString);

  // Send test webhook
  const response = await axios.post('http://localhost:3000/webhook/dodo-payments', payload, {
    headers: {
      "webhook-id": webhookId,
      "webhook-timestamp": Math.floor(timestamp.getTime() / 1000),
      "webhook-signature": signature,
      "Content-Type": "application/json"
    }
  });

  console.log("Test webhook sent successfully:", response.data);
  ```
</CodeGroup>

<Tip>
  Test your webhook handler thoroughly using the dashboard testing interface before processing production events. This helps identify and fix issues early.
</Tip>

## Advanced Settings

The Advanced Settings tab provides additional configuration options for fine-tuning your webhook endpoint behavior.

### Rate Limiting (Throttling)

Control the rate at which webhook events are delivered to your endpoint to prevent overwhelming your system.

<Steps>
  <Step title="Access Rate Limit Settings">
    In the **Advanced** tab, locate the "Rate Limit (throttling)" section.
  </Step>

  <Step title="Configure Rate Limit">
    Click the **Edit** button to modify the rate limit settings.

    <Info>
      By default, webhooks have "No rate limit" applied, meaning events are delivered as soon as they occur.
    </Info>
  </Step>

  <Step title="Set Limits">
    Configure your desired rate limit to control webhook delivery frequency and prevent system overload.
  </Step>
</Steps>

<Tip>
  Use rate limiting when your webhook handler needs time to process events or when you want to batch multiple events together.
</Tip>

### Custom Headers

Add custom HTTP headers to all webhook requests sent to your endpoint. This is useful for authentication, routing, or adding metadata to your webhook requests.

<Steps>
  <Step title="Add Custom Header">
    In the "Custom Headers" section, enter a **Key** and **Value** for your custom header.
  </Step>

  <Step title="Add Multiple Headers">
    Click the **+** button to add additional custom headers as needed.
  </Step>

  <Step title="Save Configuration">
    Your custom headers will be included in all webhook requests to this endpoint.
  </Step>
</Steps>

### Transformations

Transformations allow you to modify a webhook's payload and redirect it to a different URL. This powerful feature enables you to:

* Modify the payload structure before processing
* Route webhooks to different endpoints based on content
* Add or remove fields from the payload
* Transform data formats

<Steps>
  <Step title="Enable Transformations">
    Toggle the **Enabled** switch to activate the transformation feature.
  </Step>

  <Step title="Configure Transformation">
    Click **Edit transformation** to define your transformation rules.

    <Info>
      You can use JavaScript to transform the webhook payload and specify a different target URL.
    </Info>
  </Step>

  <Step title="Test Transformation">
    Use the testing interface to verify your transformation works correctly before going live.
  </Step>
</Steps>

<Warning>
  Transformations can significantly impact webhook delivery performance. Test thoroughly and keep transformation logic simple and efficient.
</Warning>

<Tip>
  Transformations are particularly useful for:

  * Converting between different data formats
  * Filtering events based on specific criteria
  * Adding computed fields to the payload
  * Routing events to different microservices
</Tip>

## Monitoring Webhook Logs

The Logs tab provides comprehensive visibility into your webhook delivery status, allowing you to monitor, debug, and manage webhook events effectively.

<Frame>
  <img src="https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=97555b00a8ed1ca89ae1246a987f853f" alt="Logs" data-og-width="2880" width="2880" data-og-height="1576" height="1576" data-path="images/webhooks/logs.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?w=280&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=09ead56bfe74ebb19dd8d2c5ce1e162e 280w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?w=560&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=9ce2f0fdc740b8a190d4841d6cbe94c7 560w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?w=840&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=1e3a2027a6540fc0b797698251eae1fd 840w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?w=1100&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=a924fa13f129698934e910a6fcccbe7c 1100w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?w=1650&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=ef12fd2a486b09ca3a3d4f3d5676dadb 1650w, https://mintcdn.com/dodopayments/BHDbjXQkGsSXJEiK/images/webhooks/logs.png?w=2500&fit=max&auto=format&n=BHDbjXQkGsSXJEiK&q=85&s=85805e3d15023ce66914a5e449158dac 2500w" />
</Frame>

## Activity Monitoring

The Activity tab provides real-time insights into your webhook delivery performance with visual analytics.

<Frame>
  <img src="https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=7958b2bdfa5d516cca3bb263ae6a1ef5" alt="Activity" data-og-width="2876" width="2876" data-og-height="1570" height="1570" data-path="images/webhooks/activity.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?w=280&fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=af6ec67849508a8d38b5e67308802ee4 280w, https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?w=560&fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=9e716f2609b1e0cc749cefb01e690ec5 560w, https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?w=840&fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=6a84a454e6e856138665828bf56b8b1e 840w, https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?w=1100&fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=d731f882c298b6d6e5b7707ee116c76b 1100w, https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?w=1650&fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=663069962158eceb1bb4f3de9519354d 1650w, https://mintcdn.com/dodopayments/kDL9h03D3wN164Ru/images/webhooks/activity.png?w=2500&fit=max&auto=format&n=kDL9h03D3wN164Ru&q=85&s=41a4079e8698e0903b262f85eca5e543 2500w" />
</Frame>

## Email Alerts

Stay informed about your webhook health with automatic email notifications. When webhook deliveries start failing or your endpoint stops responding, you'll receive email alerts so you can quickly address issues and keep your integrations running smoothly.

<Frame>
  <img src="https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=25382b6e34a81c78695d550cb1cedc79" alt="Webhook Alerting Settings showing email notifications configuration" data-og-width="1684" width="1684" data-og-height="1054" height="1054" data-path="images/webhooks/alerting.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?w=280&fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=8d9faeb8c18b0b171277723162f4c85f 280w, https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?w=560&fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=afddb13a7282d24d709bb55b0a081ae5 560w, https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?w=840&fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=99af3e84e13b80fc3671ecc596e596f0 840w, https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?w=1100&fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=447ac605f867e01f8e3abc0557a05523 1100w, https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?w=1650&fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=a04110debdf0f1e65655c3424838bb21 1650w, https://mintcdn.com/dodopayments/uUqnqbXnxLP9Xiux/images/webhooks/alerting.png?w=2500&fit=max&auto=format&n=uUqnqbXnxLP9Xiux&q=85&s=45fa53c1b37e4f5f631ee1e6ec1f053d 2500w" />
</Frame>

### Enable Email Alerts

<Steps>
  <Step title="Navigate to Alerting Settings">
    Go to your Dodo Payments Dashboard and navigate to **Dashboard → Webhooks → Alerting**.
  </Step>

  <Step title="Enable Email Notifications">
    Toggle on **Email notifications** to start receiving alerts about webhook delivery issues.
  </Step>

  <Step title="Configure Email Address">
    Enter the email address where you want to receive webhook alerts. We'll send notifications to this address when certain events occur with your webhooks setup, such as delivery issues that might affect your integrations.
  </Step>
</Steps>

<Tip>
  Enable email alerts to catch webhook delivery problems early and maintain reliable integrations. You'll be notified when deliveries fail or your endpoint becomes unresponsive.
</Tip>

## Deploy to Cloud Platforms

Ready to deploy your webhook handler to production? We provide platform-specific guides to help you deploy webhooks to popular cloud providers with best practices for each platform.

<CardGroup cols={2}>
  <Card title="Vercel" icon="triangle" href="/developer-resources/webhooks/examples/vercel-example">
    Deploy webhooks to Vercel with serverless functions
  </Card>

  <Card title="Cloudflare Workers" icon="cloud" href="/developer-resources/webhooks/examples/cloudflare-example">
    Run webhooks on Cloudflare's edge network
  </Card>

  <Card title="Supabase Edge Functions" icon="database" href="/developer-resources/webhooks/examples/supabase-example">
    Integrate webhooks with Supabase
  </Card>

  <Card title="Netlify Functions" icon="circle-nodes" href="/developer-resources/webhooks/examples/netlify-example">
    Deploy webhooks as Netlify serverless functions
  </Card>
</CardGroup>

<Info>
  Each platform guide includes environment setup, signature verification, and deployment steps specific to that provider.
</Info>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.dodopayments.com/llms.txt