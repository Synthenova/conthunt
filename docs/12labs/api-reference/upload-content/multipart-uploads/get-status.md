# Retrieve the status of an upload session

GET https://api.twelvelabs.io/v1.3/assets/multipart-uploads/{upload_id}

This method provides information about an upload session, including its current status, chunk-level progress, and completion state.

Use this method to:
- Verify upload completion (`status` = `completed`)
- Identify any failed chunks that require a retry
- Monitor the upload progress by comparing `uploaded_size` with `total_size`
- Determine if the session has expired
- Retrieve the status information for each chunk

You must call this method after reporting chunk completion to confirm the upload has transitioned to the `completed` status before using the asset.


Reference: https://docs.twelvelabs.io/api-reference/upload-content/multipart-uploads/get-status

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve the status of an upload session
  version: endpoint_multipartUpload.get_status
paths:
  /assets/multipart-uploads/{upload_id}:
    get:
      operationId: get-status
      summary: Retrieve the status of an upload session
      description: >
        This method provides information about an upload session, including its
        current status, chunk-level progress, and completion state.


        Use this method to:

        - Verify upload completion (`status` = `completed`)

        - Identify any failed chunks that require a retry

        - Monitor the upload progress by comparing `uploaded_size` with
        `total_size`

        - Determine if the session has expired

        - Retrieve the status information for each chunk


        You must call this method after reporting chunk completion to confirm
        the upload has transitioned to the `completed` status before using the
        asset.
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
        - name: page
          in: query
          description: |
            A number that identifies the page to retrieve.

            **Default**: `1`.
          required: false
          schema:
            type: integer
        - name: page_limit
          in: query
          description: |
            The number of items to return on each page.

            **Default**: `10`.
            **Max**: `50`.
          required: false
          schema:
            type: integer
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The status of your upload session has been successfully retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetUploadStatusResponse'
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
components:
  schemas:
    MultipartUploadStatusType:
      type: string
      enum:
        - value: active
        - value: completed
        - value: failed
        - value: expired
    ChunkInfoStatus:
      type: string
      enum:
        - value: completed
        - value: pending
        - value: failed
    updated_at:
      type: string
      format: date-time
    ChunkInfo:
      type: object
      properties:
        index:
          type: integer
        status:
          $ref: '#/components/schemas/ChunkInfoStatus'
        uploaded_at:
          type: string
          format: date-time
        updated_at:
          $ref: '#/components/schemas/updated_at'
        error:
          type: string
    limit_per_page_simple:
      type: integer
    page:
      type: integer
    total_page:
      type: integer
    total_results:
      type: integer
    page_info:
      type: object
      properties:
        limit_per_page:
          $ref: '#/components/schemas/limit_per_page_simple'
        page:
          $ref: '#/components/schemas/page'
        total_page:
          $ref: '#/components/schemas/total_page'
        total_results:
          $ref: '#/components/schemas/total_results'
    created_at:
      type: string
      format: date-time
    GetUploadStatusResponse:
      type: object
      properties:
        upload_id:
          type: string
        status:
          $ref: '#/components/schemas/MultipartUploadStatusType'
        uploaded_chunks:
          type: array
          items:
            $ref: '#/components/schemas/ChunkInfo'
        chunks_completed:
          type: integer
        chunks_failed:
          type: integer
        chunks_pending:
          type: integer
        page_info:
          $ref: '#/components/schemas/page_info'
        total_size:
          type: integer
        uploaded_size:
          type: integer
        created_at:
          $ref: '#/components/schemas/created_at'
        updated_at:
          $ref: '#/components/schemas/updated_at'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011';
const options = {method: 'GET', headers: {'x-api-key': '<apiKey>'}};

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
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")

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

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/assets/multipart-uploads/507f1f77bcf86cd799439011")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

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