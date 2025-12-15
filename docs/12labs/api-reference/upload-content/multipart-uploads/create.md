# Create a multipart upload session

POST https://api.twelvelabs.io/v1.3/assets/multipart-uploads
Content-Type: application/json

This method creates a multipart upload session.

**Supported content**: Video and audio

**File size**: 4GB maximum.

**Additional requirements** depend on your workflow:
- **Search**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)
- **Video analysis**: [Pegasus requirements](/v1.3/docs/concepts/models/pegasus#input-requirements)
- **Create embeddings**: [Marengo requirements](/v1.3/docs/concepts/models/marengo#input-requirements)


Reference: https://docs.twelvelabs.io/api-reference/upload-content/multipart-uploads/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create a multipart upload session
  version: endpoint_multipartUpload.create
paths:
  /assets/multipart-uploads:
    post:
      operationId: create
      summary: Create a multipart upload session
      description: >
        This method creates a multipart upload session.


        **Supported content**: Video and audio


        **File size**: 4GB maximum.


        **Additional requirements** depend on your workflow:

        - **Search**: [Marengo
        requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements)

        - **Video analysis**: [Pegasus
        requirements](/v1.3/docs/concepts/models/pegasus#input-requirements)

        - **Create embeddings**: [Marengo
        requirements](/v1.3/docs/concepts/models/marengo#input-requirements)
      tags:
        - - subpackage_multipartUpload
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: The multipart upload session has been successfully created.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateAssetUploadResponse'
        '400':
          description: The request has failed.
          content: {}
        '403':
          description: The request has failed.
          content: {}
        '500':
          description: The request has failed.
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAssetUploadRequest'
components:
  schemas:
    CreateAssetUploadRequestType:
      type: string
      enum:
        - value: video
    CreateAssetUploadRequest:
      type: object
      properties:
        filename:
          type: string
        type:
          $ref: '#/components/schemas/CreateAssetUploadRequestType'
        total_size:
          type: integer
      required:
        - filename
        - type
        - total_size
    expires_at:
      type: string
      format: date-time
    PresignedURLChunk:
      type: object
      properties:
        chunk_index:
          type: integer
        url:
          type: string
          format: uri
        expires_at:
          $ref: '#/components/schemas/expires_at'
    CreateAssetUploadResponse:
      type: object
      properties:
        upload_id:
          type: string
        asset_id:
          type: string
        upload_urls:
          type: array
          items:
            $ref: '#/components/schemas/PresignedURLChunk'
        upload_headers:
          type: object
          additionalProperties:
            type: string
        chunk_size:
          type: integer
        total_chunks:
          type: integer
        expires_at:
          type: string
          format: date-time

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/assets/multipart-uploads"

payload = {
    "filename": "my-video.mp4",
    "type": "video",
    "total_size": 104857600
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"filename":"my-video.mp4","type":"video","total_size":104857600}'
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

	url := "https://api.twelvelabs.io/v1.3/assets/multipart-uploads"

	payload := strings.NewReader("{\n  \"filename\": \"my-video.mp4\",\n  \"type\": \"video\",\n  \"total_size\": 104857600\n}")

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

url = URI("https://api.twelvelabs.io/v1.3/assets/multipart-uploads")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"filename\": \"my-video.mp4\",\n  \"type\": \"video\",\n  \"total_size\": 104857600\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/assets/multipart-uploads")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"filename\": \"my-video.mp4\",\n  \"type\": \"video\",\n  \"total_size\": 104857600\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads', [
  'body' => '{
  "filename": "my-video.mp4",
  "type": "video",
  "total_size": 104857600
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets/multipart-uploads");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"filename\": \"my-video.mp4\",\n  \"type\": \"video\",\n  \"total_size\": 104857600\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "filename": "my-video.mp4",
  "type": "video",
  "total_size": 104857600
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets/multipart-uploads")! as URL,
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