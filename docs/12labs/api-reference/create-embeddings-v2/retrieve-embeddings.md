# Retrieve task status and results

GET https://api.twelvelabs.io/v1.3/embed-v2/tasks/{task_id}

This method retrieves the status and the results of an async embedding task.

**Task statuses**:
- `processing`: The platform is creating the embeddings.
- `ready`: Processing is complete. Embeddings are available in the response.
- `failed`: The task failed. Embeddings were not created.

Invoke this method repeatedly until the `status` field is `ready`. When `status` is `ready`, use the embeddings from the response.


Reference: https://docs.twelvelabs.io/api-reference/create-embeddings-v2/retrieve-embeddings

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieve task status and results
  version: endpoint_embed/v2/tasks.retrieve
paths:
  /embed-v2/tasks/{task_id}:
    get:
      operationId: retrieve
      summary: Retrieve task status and results
      description: >
        This method retrieves the status and the results of an async embedding
        task.


        **Task statuses**:

        - `processing`: The platform is creating the embeddings.

        - `ready`: Processing is complete. Embeddings are available in the
        response.

        - `failed`: The task failed. Embeddings were not created.


        Invoke this method repeatedly until the `status` field is `ready`. When
        `status` is `ready`, use the embeddings from the response.
      tags:
        - - subpackage_embed
          - subpackage_embed/v2
          - subpackage_embed/v2/tasks
      parameters:
        - name: task_id
          in: path
          description: The unique identifier of the embedding task.
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
          description: Task status and results retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EmbeddingTaskResponse'
        '404':
          description: Task not found
          content: {}
components:
  schemas:
    EmbeddingTaskResponseStatus:
      type: string
      enum:
        - value: processing
        - value: ready
        - value: failed
    created_at:
      type: string
      format: date-time
    updated_at:
      type: string
      format: date-time
    EmbeddingDataEmbeddingOption:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
    EmbeddingDataEmbeddingScope:
      type: string
      enum:
        - value: clip
        - value: asset
    EmbeddingData:
      type: object
      properties:
        embedding:
          type: array
          items:
            type: number
            format: double
        embedding_option:
          oneOf:
            - $ref: '#/components/schemas/EmbeddingDataEmbeddingOption'
            - type: 'null'
        embedding_scope:
          oneOf:
            - $ref: '#/components/schemas/EmbeddingDataEmbeddingScope'
            - type: 'null'
        start_sec:
          type:
            - number
            - 'null'
          format: double
        end_sec:
          type:
            - number
            - 'null'
          format: double
      required:
        - embedding
    EmbeddingAudioMetadataInputType:
      type: string
      enum:
        - value: audio
    EmbeddingAudioMetadataEmbeddingScopesItems:
      type: string
      enum:
        - value: clip
        - value: asset
    EmbeddingAudioMetadata:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/EmbeddingAudioMetadataInputType'
        input_url:
          type: string
        input_filename:
          type: string
        embedding_options:
          type: array
          items:
            type: string
        embedding_scopes:
          type: array
          items:
            $ref: '#/components/schemas/EmbeddingAudioMetadataEmbeddingScopesItems'
        duration:
          type: number
          format: double
        start_offset_sec:
          type: number
          format: double
        end_offset_sec:
          type: number
          format: double
      required:
        - input_type
        - embedding_options
        - embedding_scopes
        - duration
    EmbeddingVideoMetadataInputType:
      type: string
      enum:
        - value: video
    EmbeddingVideoMetadataEmbeddingScopesItems:
      type: string
      enum:
        - value: clip
        - value: asset
    EmbeddingVideoMetadata:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/EmbeddingVideoMetadataInputType'
        input_url:
          type: string
        input_filename:
          type: string
        clip_length:
          type: integer
        embedding_scopes:
          type: array
          items:
            $ref: '#/components/schemas/EmbeddingVideoMetadataEmbeddingScopesItems'
        embedding_options:
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
      required:
        - input_type
        - embedding_scopes
        - embedding_options
        - duration
    EmbeddingTaskMediaMetadata:
      oneOf:
        - $ref: '#/components/schemas/EmbeddingAudioMetadata'
        - $ref: '#/components/schemas/EmbeddingVideoMetadata'
    EmbeddingTaskResponse:
      type: object
      properties:
        _id:
          type: string
        status:
          $ref: '#/components/schemas/EmbeddingTaskResponseStatus'
        created_at:
          $ref: '#/components/schemas/created_at'
        updated_at:
          $ref: '#/components/schemas/updated_at'
        data:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/EmbeddingData'
        metadata:
          $ref: '#/components/schemas/EmbeddingTaskMediaMetadata'
      required:
        - _id
        - status
        - data

```

## SDK Code Examples

```python Task still processing
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript Task still processing
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12';
const options = {method: 'GET', headers: {'x-api-key': '<apiKey>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Task still processing
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Task still processing
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java Task still processing
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php Task still processing
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Task still processing
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift Task still processing
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")! as URL,
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

```python Task completed with results
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript Task completed with results
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12';
const options = {method: 'GET', headers: {'x-api-key': '<apiKey>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Task completed with results
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Task completed with results
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java Task completed with results
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php Task completed with results
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Task completed with results
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift Task completed with results
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")! as URL,
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

```python Task failed
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript Task failed
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12';
const options = {method: 'GET', headers: {'x-api-key': '<apiKey>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Task failed
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Task failed
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java Task failed
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php Task failed
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Task failed
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift Task failed
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks/64f8d2c7e4a1b37f8a9c5d12")! as URL,
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