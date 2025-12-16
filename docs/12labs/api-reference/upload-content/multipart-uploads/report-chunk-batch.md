# Report uploaded chunks

POST https://api.twelvelabs.io/v1.3/assets/multipart-uploads/{upload_id}
Content-Type: application/json

This method reports successfully uploaded chunks to the platform. The platform finalizes the upload after you report all chunks.


For optimal performance, report chunks in batches and in any order.


Reference: https://docs.twelvelabs.io/api-reference/upload-content/multipart-uploads/report-chunk-batch

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Report uploaded chunks
  version: endpoint_multipartUpload.report_chunk_batch
paths:
  /assets/multipart-uploads/{upload_id}:
    post:
      operationId: report-chunk-batch
      summary: Report uploaded chunks
      description: >
        This method reports successfully uploaded chunks to the platform. The
        platform finalizes the upload after you report all chunks.



        For optimal performance, report chunks in batches and in any order.
      tags:
        - - subpackage_multipartUpload
      parameters:
        - name: upload_id
          in: path
          description: |
            The unique identifier of the upload session.
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
        '200':
          description: The completion of this batch has been successfully reported.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReportChunkBatchResponse'
        '400':
          description: The request has failed.
          content: {}
        '403':
          description: The request has failed.
          content: {}
        '404':
          description: Upload not found.
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReportChunkBatchRequest'
components:
  schemas:
    CompletedChunkProofType:
      type: string
      enum:
        - value: etag
    CompletedChunk:
      type: object
      properties:
        chunk_index:
          type: integer
        proof:
          type: string
        proof_type:
          $ref: '#/components/schemas/CompletedChunkProofType'
        chunk_size:
          type: integer
      required:
        - chunk_index
        - proof
        - proof_type
        - chunk_size
    ReportChunkBatchRequest:
      type: object
      properties:
        completed_chunks:
          type: array
          items:
            $ref: '#/components/schemas/CompletedChunk'
      required:
        - completed_chunks
    ReportChunkBatchResponse:
      type: object
      properties:
        url:
          type: string
          format: uri
        asset_id:
          type: string
        processed_chunks:
          type: integer
        duplicate_chunks:
          type: integer
        total_completed:
          type: integer

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011"

payload = { "completed_chunks": [
        {
            "chunk_index": 1,
            "proof": "d41d8cd98f00b204e9800998ecf8427e",
            "proof_type": "etag",
            "chunk_size": 5242880
        }
    ] }
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"completed_chunks":[{"chunk_index":1,"proof":"d41d8cd98f00b204e9800998ecf8427e","proof_type":"etag","chunk_size":5242880}]}'
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

	url := "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011"

	payload := strings.NewReader("{\n  \"completed_chunks\": [\n    {\n      \"chunk_index\": 1,\n      \"proof\": \"d41d8cd98f00b204e9800998ecf8427e\",\n      \"proof_type\": \"etag\",\n      \"chunk_size\": 5242880\n    }\n  ]\n}")

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

url = URI("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"completed_chunks\": [\n    {\n      \"chunk_index\": 1,\n      \"proof\": \"d41d8cd98f00b204e9800998ecf8427e\",\n      \"proof_type\": \"etag\",\n      \"chunk_size\": 5242880\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"completed_chunks\": [\n    {\n      \"chunk_index\": 1,\n      \"proof\": \"d41d8cd98f00b204e9800998ecf8427e\",\n      \"proof_type\": \"etag\",\n      \"chunk_size\": 5242880\n    }\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011', [
  'body' => '{
  "completed_chunks": [
    {
      "chunk_index": 1,
      "proof": "d41d8cd98f00b204e9800998ecf8427e",
      "proof_type": "etag",
      "chunk_size": 5242880
    }
  ]
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"completed_chunks\": [\n    {\n      \"chunk_index\": 1,\n      \"proof\": \"d41d8cd98f00b204e9800998ecf8427e\",\n      \"proof_type\": \"etag\",\n      \"chunk_size\": 5242880\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["completed_chunks": [
    [
      "chunk_index": 1,
      "proof": "d41d8cd98f00b204e9800998ecf8427e",
      "proof_type": "etag",
      "chunk_size": 5242880
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011")! as URL,
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