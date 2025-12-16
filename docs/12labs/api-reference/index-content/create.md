# Index an asset

POST https://api.twelvelabs.io/v1.3/indexes/{index-id}/indexed-assets
Content-Type: application/json

This method indexes an uploaded asset to make it searchable and analyzable. Indexing processes your content and extracts information that enables the platform to search and analyze your videos.

This operation is asynchronous. The platform returns an indexed asset ID immediately and processes your content in the background. Monitor the indexing status to know when your content is ready to use.

Your asset must meet the requirements based on your workflow:
- **Search**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)
- **Video analysis**: [Pegasus requirements](/v1.3/docs/concepts/models/pegasus#input-requirements).

If you want to both search and analyze your videos, the most restrictive requirements apply.


Reference: https://docs.twelvelabs.io/api-reference/index-content/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create an indexed asset
  version: endpoint_indexes/indexedAssets.create
paths:
  /indexes/{index-id}/indexed-assets:
    post:
      operationId: create
      summary: Create an indexed asset
      description: >
        This method indexes an uploaded asset to make it searchable and
        analyzable. Indexing processes your content and extracts information
        that enables the platform to search and analyze your videos.


        This operation is asynchronous. The platform returns an indexed asset ID
        immediately and processes your content in the background. Monitor the
        indexing status to know when your content is ready to use.


        Your asset must meet the requirements based on your workflow:

        - **Search**: [Marengo
        requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)

        - **Video analysis**: [Pegasus
        requirements](/v1.3/docs/concepts/models/pegasus#input-requirements).


        If you want to both search and analyze your videos, the most restrictive
        requirements apply.
      tags:
        - - subpackage_indexes
          - subpackage_indexes/indexedAssets
      parameters:
        - name: index-id
          in: path
          description: >
            The unique identifier of the index to which the asset will be
            indexed.
          required: true
          schema:
            type: string
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '202':
          description: |
            The indexing request has been accepted and is processing.
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/indexes_indexed_assets_create_Response_202
        '400':
          description: The request has failed.
          content: {}
        '404':
          description: The specified resource does not exist.
          content: {}
        '500':
          description: The request has failed.
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                asset_id:
                  type: string
                enable_video_stream:
                  type: boolean
              required:
                - asset_id
components:
  schemas:
    indexes_indexed_assets_create_Response_202:
      type: object
      properties:
        _id:
          type: string

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets"

payload = { "asset_id": "6298d673f1090f1100476d4c" }
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"asset_id":"6298d673f1090f1100476d4c"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets"

	payload := strings.NewReader("{\n  \"asset_id\": \"6298d673f1090f1100476d4c\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"asset_id\": \"6298d673f1090f1100476d4c\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"asset_id\": \"6298d673f1090f1100476d4c\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets', [
  'body' => '{
  "asset_id": "6298d673f1090f1100476d4c"
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"asset_id\": \"6298d673f1090f1100476d4c\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["asset_id": "6298d673f1090f1100476d4c"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/indexes/6298d673f1090f1100476d4c/indexed-assets")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```