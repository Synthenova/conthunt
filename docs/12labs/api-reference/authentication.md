# Authentication

To make HTTP requests, you must include the API key in the header of each request.

# Prerequisites

To use the platform, you need an API key:

<Steps>
  <Step>
    If you don’t have an account, [sign up](https://playground.twelvelabs.io/) for a free account.
  </Step>

  <Step>
    Go to the [API Keys](https://playground.twelvelabs.io/dashboard/api-keys) page.
  </Step>

  <Step>
    Select the **Copy** icon next to your key.
  </Step>
</Steps>

# Procedure

<Steps>
  <Step>
    Verify that the required packages are installed on your system. If necessary, install the following packages:

    <Tabs>
      <Tab title="Python">
        Install the `requests` package by entering the following command:

        ```shell
        python -m pip install requests
        ```
      </Tab>

      <Tab title=" Node.js">
        Install the `axios` and `form-data` packages by entering the following command:

        ```shell
        npm install axios form-data
        ```
      </Tab>
    </Tabs>
  </Step>

  <Step>
    Define the URL of the API and the specific endpoint for your request.
  </Step>

  <Step>
    Create the necessary headers for authentication.
  </Step>

  <Step>
    Prepare the data payload for your API request.
  </Step>

  <Step>
    Send the API request and process the response.
  </Step>
</Steps>

Below are complete code examples for Python and Node.js, integrating all the steps outlined above:

<CodeBlocks>
  <CodeBlock title="Python">
    ```Python Python
    import requests

    # Step 2: Define the API URL and the specific endpoint
    API_URL = "https://api.twelvelabs.io/v1.3"
    INDEXES_URL = f"{API_URL}/indexes"

    # Step 3: Create the necessary headers for authentication
    headers = {
        "x-api-key": "<YOUR_API_KEY>"
    }

    # Step 4: Prepare the data payload for your API request
    INDEX_NAME = "<YOUR_INDEX_NAME>"
    data = {
        "models": [
            {
                "model_name": "marengo3.0",
                "model_options": ["visual", "audio"]
            }
        ],
        "index_name": INDEX_NAME
    }

    # Step 5: Send the API request and process the response
    response = requests.post(INDEXES_URL, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    if response.status_code == 201:
        print(response.json())
    else:
        print("Error:", response.json())
    ```
  </CodeBlock>

  <CodeBlock title="Node.js">
    ```Javascript Node.js
    const axios = require('axios');

    // Step 2: Define the API URL and the specific endpoint
    const API_URL = 'https://api.twelvelabs.io/v1.3';
    const INDEXES_URL = `${API_URL}/indexes`;

    // Step 3: Create the necessary headers for authentication
    const headers = {
        'x-api-key': '<YOUR_API_KEY>'
    };

    // Step 4: Prepare the data payload for your API request
    const INDEX_NAME = '<YOUR_INDEX_NAME>';
    const data = {
        models: [
            {
                model_name: 'marengo3.0',
                model_options: ['visual', 'audio']
            }
        ],
        index_name: INDEX_NAME
    };

    // Step 5: Send the API request and process the response
    axios.post(INDEXES_URL, data, { headers })
        .then(resp => {
            console.log(`Status code: ${resp.status}`);
            console.log(resp.data);
        })
        .catch(error => {
            console.error(`Error: ${error.response.status} - ${error.response.data.message}`);
        });
    ```
  </CodeBlock>
</CodeBlocks>
