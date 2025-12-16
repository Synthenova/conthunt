# Retrieve a video indexing task

GET https://api.twelvelabs.io/v1.3/tasks/{task_id}

This method retrieves a video indexing task.

Reference: https://docs.twelvelabs.io/api-reference/upload-content/tasks/retrieve

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve a video indexing task
  version: endpoint_tasks.retrieve
paths:
  /tasks/{task_id}:
    get:
      operationId: retrieve
      summary: Retrieve a video indexing task
      description: This method retrieves a video indexing task.
      tags:
        - - subpackage_tasks
      parameters:
        - name: task_id
          in: path
          description: |
            The unique identifier of the video indexing task to retrieve.
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
          description: The specified video indexing task has successfully been retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/tasks_retrieve_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    VideoIndexingTaskSystemMetadata:
      type: object
      properties:
        duration:
          type: number
          format: double
        filename:
          type: string
        height:
          type: integer
        width:
          type: integer
    HlsObjectStatus:
      type: string
      enum:
        - value: PROCESSING
        - value: COMPLETE
        - value: CANCELED
        - value: ERROR
    HLSObject:
      type: object
      properties:
        video_url:
          type: string
        thumbnail_urls:
          type: array
          items:
            type: string
        status:
          $ref: '#/components/schemas/HlsObjectStatus'
        updated_at:
          type: string
    tasks_retrieve_Response_200:
      type: object
      properties:
        _id:
          type: string
        video_id:
          type: string
        created_at:
          type: string
        updated_at:
          type: string
        status:
          type: string
        index_id:
          type: string
        system_metadata:
          $ref: '#/components/schemas/VideoIndexingTaskSystemMetadata'
        hls:
          $ref: '#/components/schemas/HLSObject'

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c';
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

	url := "https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c"

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

url = URI("https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/tasks/6298d673f1090f1100476d4c")! as URL,
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