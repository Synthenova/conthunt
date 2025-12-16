# Request presigned URLs for the remaining chunks

POST https://api.twelvelabs.io/v1.3/assets/multipart-uploads/{upload_id}/presigned-urls
Content-Type: application/json

This method generates new presigned URLs for specific chunks that require uploading. Use this endpoint in the following situations:
- Your initial URLs have expired (URLs expire after one hour).
- The initial set of presigned URLs does not include URLs for all chunks.
- You need to retry failed chunk uploads with new URLs.
To specify which chunks need URLs, use the `start` and `count` parameters. For example, to generate URLs for chunks 21 to 30, use `start=21` and `count=10`.
The response will provide new URLs, each with a fresh expiration time of one hour.


Reference: https://docs.twelvelabs.io/api-reference/upload-content/multipart-uploads/get-additional-presigned-urls

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Request presigned URLs for the remaining chunks
  version: endpoint_multipartUpload.get_additional_presigned_urls
paths:
  /assets/multipart-uploads/{upload_id}/presigned-urls:
    post:
      operationId: get-additional-presigned-urls
      summary: Request presigned URLs for the remaining chunks
      description: >
        This method generates new presigned URLs for specific chunks that
        require uploading. Use this endpoint in the following situations:

        - Your initial URLs have expired (URLs expire after one hour).

        - The initial set of presigned URLs does not include URLs for all
        chunks.

        - You need to retry failed chunk uploads with new URLs.

        To specify which chunks need URLs, use the `start` and `count`
        parameters. For example, to generate URLs for chunks 21 to 30, use
        `start=21` and `count=10`.

        The response will provide new URLs, each with a fresh expiration time of
        one hour.
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
          description: Additional presigned URLs have been successfully generated.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RequestAdditionalPresignedURLsResponse'
        '400':
          description: The request has failed.
          content: {}
        '403':
          description: The request has failed.
          content: {}
        '404':
          description: Upload not found.
          content: {}
        '500':
          description: The request has failed.
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RequestAdditionalPresignedURLsRequest'
components:
  schemas:
    RequestAdditionalPresignedURLsRequest:
      type: object
      properties:
        start:
          type: integer
        count:
          type: integer
      required:
        - start
        - count
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
    RequestAdditionalPresignedURLsResponse:
      type: object
      properties:
        upload_id:
          type: string
        start_index:
          type: integer
        count:
          type: integer
        upload_urls:
          type: array
          items:
            $ref: '#/components/schemas/PresignedURLChunk'
        generated_at:
          type: string
          format: date-time
        expires_at:
          $ref: '#/components/schemas/expires_at'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls"

payload = {
    "start": 1,
    "count": 10
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"start":1,"count":10}'
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

	url := "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls"

	payload := strings.NewReader("{\n  \"start\": 1,\n  \"count\": 10\n}")

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

url = URI("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"start\": 1,\n  \"count\": 10\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"start\": 1,\n  \"count\": 10\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls', [
  'body' => '{
  "start": 1,
  "count": 10
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"start\": 1,\n  \"count\": 10\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "start": 1,
  "count": 10
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011/presigned-urls")! as URL,
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