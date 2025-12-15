# List async embedding tasks

GET https://api.twelvelabs.io/v1.3/embed-v2/tasks

This method returns a list of the async embedding tasks in your account. The platform returns your async embedding tasks sorted by creation date, with the newest at the top of the list.


Reference: https://docs.twelvelabs.io/api-reference/create-embeddings-v2/list-async-embedding-tasks

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List async embedding tasks
  version: endpoint_embed/v2/tasks.list
paths:
  /embed-v2/tasks:
    get:
      operationId: list
      summary: List async embedding tasks
      description: >
        This method returns a list of the async embedding tasks in your account.
        The platform returns your async embedding tasks sorted by creation date,
        with the newest at the top of the list.
      tags:
        - - subpackage_embed
          - subpackage_embed/v2
          - subpackage_embed/v2/tasks
      parameters:
        - name: started_at
          in: query
          description: >
            Retrieve the embedding tasks that were created after the given date
            and time, expressed in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ").
          required: false
          schema:
            type: string
        - name: ended_at
          in: query
          description: >
            Retrieve the embedding tasks that were created before the given date
            and time, expressed in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ").
          required: false
          schema:
            type: string
        - name: status
          in: query
          description: |
            Filter the embedding tasks by their current status.

            **Values**: `processing`, `ready`, or `failed`.
          required: false
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
          description: |
            A list of async embedding tasks has successfully been retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/embed_v2_tasks_list_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    created_at:
      type: string
      format: date-time
    updated_at:
      type: string
      format: date-time
    VideoEmbeddingMetadata:
      type: object
      properties:
        input_url:
          type: string
        input_filename:
          type: string
        video_clip_length:
          type: number
          format: double
        video_embedding_scope:
          type: array
          items:
            type: string
        duration:
          type: number
          format: double
    MediaEmbeddingTaskVideoEmbedding:
      type: object
      properties:
        metadata:
          $ref: '#/components/schemas/VideoEmbeddingMetadata'
    AudioEmbeddingMetadata:
      type: object
      properties:
        input_url:
          type: string
        input_filename:
          type: string
        audio_embedding_options:
          type: array
          items:
            type: string
        audio_embedding_scopes:
          type: array
          items:
            type: string
        duration:
          type: number
          format: double
        start_offset_sec:
          type: number
          format: double
        end_offset_sec:
          type: number
          format: double
    MediaEmbeddingTaskAudioEmbedding:
      type: object
      properties:
        metadata:
          $ref: '#/components/schemas/AudioEmbeddingMetadata'
    MediaEmbeddingTask:
      type: object
      properties:
        _id:
          type: string
        model_name:
          type: string
        status:
          type: string
        created_at:
          $ref: '#/components/schemas/created_at'
        updated_at:
          $ref: '#/components/schemas/updated_at'
        video_embedding:
          $ref: '#/components/schemas/MediaEmbeddingTaskVideoEmbedding'
        audio_embedding:
          $ref: '#/components/schemas/MediaEmbeddingTaskAudioEmbedding'
    limit_per_page_simple:
      type: integer
    page:
      type: integer
    total_page:
      type: integer
    total_results:
      type: integer
    EmbedV2TasksGetResponsesContentApplicationJsonSchemaPageInfo:
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
    embed_v2_tasks_list_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/MediaEmbeddingTask'
        page_info:
          $ref: >-
            #/components/schemas/EmbedV2TasksGetResponsesContentApplicationJsonSchemaPageInfo

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks';
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

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

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

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/embed-v2/tasks")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks")! as URL,
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