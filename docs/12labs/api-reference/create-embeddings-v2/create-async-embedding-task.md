# Create an async embedding task

POST https://api.twelvelabs.io/v1.3/embed-v2/tasks
Content-Type: application/json

This endpoint creates embeddings for audio and video content asynchronously.

<Note title="Note">
  This method only supports Marengo version 3.0 or newer.
</Note>

**When to use this endpoint**:
- Process audio or video files longer than 10 minutes
- Process files up to 4 hours in duration

<Accordion title="Input requirements">
  **Video**:
  - Minimum duration: 4 seconds
  - Maximum duration: 4 hours
  - Maximum file size: 4 GB
  - Formats: [FFmpeg supported formats](https://ffmpeg.org/ffmpeg-formats.html)
  - Resolution: 360x360 to 5184x2160 pixels
  - Aspect ratio: Between 1:1 and 1:2.4, or between 2.4:1 and 1:1

  **Audio**:
  - Minimum duration: 4 seconds
  - Maximum duration: 4 hours
  - Maximum file size: 2 GB
  - Formats: WAV (uncompressed), MP3 (lossy), FLAC (lossless)
</Accordion>

  Creating embeddings asynchronously requires three steps:
  
  1. Create a task using this endpoint. The platform returns a task ID.
  2. Poll for the status of the task using the [`GET`](/v1.3/api-reference/create-embeddings-v2/retrieve-embeddings) method of the `/embed-v2/tasks/{task_id}` endpoint. Wait until the status is `ready`.
  3. Retrieve the embeddings from the response when the status is `ready` using the [`GET`](/v1.3/api-reference/create-embeddings-v2/retrieve-embeddings) method of the `/embed-v2/tasks/{task_id}` endpoint.


Reference: https://docs.twelvelabs.io/api-reference/create-embeddings-v2/create-async-embedding-task

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create an async embedding task
  version: endpoint_embed/v2/tasks.create
paths:
  /embed-v2/tasks:
    post:
      operationId: create
      summary: Create an async embedding task
      description: >
        This endpoint creates embeddings for audio and video content
        asynchronously.


        <Note title="Note">
          This method only supports Marengo version 3.0 or newer.
        </Note>


        **When to use this endpoint**:

        - Process audio or video files longer than 10 minutes

        - Process files up to 4 hours in duration


        <Accordion title="Input requirements">
          **Video**:
          - Minimum duration: 4 seconds
          - Maximum duration: 4 hours
          - Maximum file size: 4 GB
          - Formats: [FFmpeg supported formats](https://ffmpeg.org/ffmpeg-formats.html)
          - Resolution: 360x360 to 5184x2160 pixels
          - Aspect ratio: Between 1:1 and 1:2.4, or between 2.4:1 and 1:1

          **Audio**:
          - Minimum duration: 4 seconds
          - Maximum duration: 4 hours
          - Maximum file size: 2 GB
          - Formats: WAV (uncompressed), MP3 (lossy), FLAC (lossless)
        </Accordion>

          Creating embeddings asynchronously requires three steps:
          
          1. Create a task using this endpoint. The platform returns a task ID.
          2. Poll for the status of the task using the [`GET`](/v1.3/api-reference/create-embeddings-v2/retrieve-embeddings) method of the `/embed-v2/tasks/{task_id}` endpoint. Wait until the status is `ready`.
          3. Retrieve the embeddings from the response when the status is `ready` using the [`GET`](/v1.3/api-reference/create-embeddings-v2/retrieve-embeddings) method of the `/embed-v2/tasks/{task_id}` endpoint.
      tags:
        - - subpackage_embed
          - subpackage_embed/v2
          - subpackage_embed/v2/tasks
      parameters:
        - name: x-api-key
          in: header
          description: Header authentication of the form `undefined <token>`
          required: true
          schema:
            type: string
      responses:
        '202':
          description: An embedding task has successfully been created.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/embed_v2_tasks_create_Response_202'
        '400':
          description: Validation failure or inaccessible artifact
          content: {}
        '500':
          description: Internal server error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAsyncEmbeddingRequest'
components:
  schemas:
    CreateAsyncEmbeddingRequestInputType:
      type: string
      enum:
        - value: audio
        - value: video
    CreateAsyncEmbeddingRequestModelName:
      type: string
      enum:
        - value: marengo3.0
    MediaSource:
      type: object
      properties:
        base64_string:
          type: string
        url:
          type: string
          format: uri
        asset_id:
          type: string
    AudioSegmentationFixed:
      type: object
      properties:
        duration_sec:
          type: integer
      required:
        - duration_sec
    AudioSegmentation:
      type: object
      properties:
        strategy:
          type: string
          enum:
            - type: stringLiteral
              value: fixed
        fixed:
          $ref: '#/components/schemas/AudioSegmentationFixed'
      required:
        - strategy
        - fixed
    AudioInputRequestEmbeddingOptionItems:
      type: string
      enum:
        - value: audio
        - value: transcription
    AudioInputRequestEmbeddingScopeItems:
      type: string
      enum:
        - value: clip
        - value: asset
    AudioInputRequest:
      type: object
      properties:
        media_source:
          $ref: '#/components/schemas/MediaSource'
        start_sec:
          type: number
          format: double
        end_sec:
          type: number
          format: double
        segmentation:
          $ref: '#/components/schemas/AudioSegmentation'
        embedding_option:
          type: array
          items:
            $ref: '#/components/schemas/AudioInputRequestEmbeddingOptionItems'
        embedding_scope:
          type: array
          items:
            $ref: '#/components/schemas/AudioInputRequestEmbeddingScopeItems'
      required:
        - media_source
    VideoSegmentationOneOf0Dynamic:
      type: object
      properties:
        min_duration_sec:
          type: integer
      required:
        - min_duration_sec
    VideoSegmentation0:
      type: object
      properties:
        strategy:
          type: string
          enum:
            - type: stringLiteral
              value: dynamic
        dynamic:
          $ref: '#/components/schemas/VideoSegmentationOneOf0Dynamic'
      required:
        - strategy
        - dynamic
    VideoSegmentationOneOf1Fixed:
      type: object
      properties:
        duration_sec:
          type: integer
      required:
        - duration_sec
    VideoSegmentation1:
      type: object
      properties:
        strategy:
          type: string
          enum:
            - type: stringLiteral
              value: fixed
        fixed:
          $ref: '#/components/schemas/VideoSegmentationOneOf1Fixed'
      required:
        - strategy
        - fixed
    VideoSegmentation:
      oneOf:
        - $ref: '#/components/schemas/VideoSegmentation0'
        - $ref: '#/components/schemas/VideoSegmentation1'
    VideoInputRequestEmbeddingOptionItems:
      type: string
      enum:
        - value: visual
        - value: audio
        - value: transcription
    VideoInputRequestEmbeddingScopeItems:
      type: string
      enum:
        - value: clip
        - value: asset
    VideoInputRequest:
      type: object
      properties:
        media_source:
          $ref: '#/components/schemas/MediaSource'
        start_sec:
          type: number
          format: double
        end_sec:
          type: number
          format: double
        segmentation:
          $ref: '#/components/schemas/VideoSegmentation'
        embedding_option:
          type: array
          items:
            $ref: '#/components/schemas/VideoInputRequestEmbeddingOptionItems'
        embedding_scope:
          type: array
          items:
            $ref: '#/components/schemas/VideoInputRequestEmbeddingScopeItems'
      required:
        - media_source
    CreateAsyncEmbeddingRequest:
      type: object
      properties:
        input_type:
          $ref: '#/components/schemas/CreateAsyncEmbeddingRequestInputType'
        model_name:
          $ref: '#/components/schemas/CreateAsyncEmbeddingRequestModelName'
        audio:
          $ref: '#/components/schemas/AudioInputRequest'
        video:
          $ref: '#/components/schemas/VideoInputRequest'
      required:
        - input_type
        - model_name
    EmbedV2TasksPostResponsesContentApplicationJsonSchemaStatus:
      type: string
      enum:
        - value: processing
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
    embed_v2_tasks_create_Response_202:
      type: object
      properties:
        _id:
          type: string
        status:
          $ref: >-
            #/components/schemas/EmbedV2TasksPostResponsesContentApplicationJsonSchemaStatus
        data:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/EmbeddingData'
      required:
        - _id
        - status

```

## SDK Code Examples

```python embed_v2_tasks_create_example
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

print(response.json())
```

```javascript embed_v2_tasks_create_example
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: undefined
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go embed_v2_tasks_create_example
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("x-api-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby embed_v2_tasks_create_example
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'

response = http.request(request)
puts response.read_body
```

```java embed_v2_tasks_create_example
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2/tasks")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .asString();
```

```php embed_v2_tasks_create_example
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks', [
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp embed_v2_tasks_create_example
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
IRestResponse response = client.Execute(request);
```

```swift embed_v2_tasks_create_example
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
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

```python Audio with fixed segmentation
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

payload = {
    "input_type": "audio",
    "model_name": "marengo3.0",
    "audio": {
        "media_source": { "url": "https://user-bucket.com/audio/long-audio.wav" },
        "start_sec": 0,
        "end_sec": 3600,
        "segmentation": {
            "strategy": "fixed",
            "fixed": { "duration_sec": 6 }
        },
        "embedding_option": ["audio", "transcription"],
        "embedding_scope": ["clip", "asset"]
    }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Audio with fixed segmentation
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"audio","model_name":"marengo3.0","audio":{"media_source":{"url":"https://user-bucket.com/audio/long-audio.wav"},"start_sec":0,"end_sec":3600,"segmentation":{"strategy":"fixed","fixed":{"duration_sec":6}},"embedding_option":["audio","transcription"],"embedding_scope":["clip","asset"]}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Audio with fixed segmentation
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

	payload := strings.NewReader("{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/long-audio.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 3600,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")

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

```ruby Audio with fixed segmentation
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/long-audio.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 3600,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Audio with fixed segmentation
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2/tasks")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/long-audio.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 3600,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")
  .asString();
```

```php Audio with fixed segmentation
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks', [
  'body' => '{
  "input_type": "audio",
  "model_name": "marengo3.0",
  "audio": {
    "media_source": {
      "url": "https://user-bucket.com/audio/long-audio.wav"
    },
    "start_sec": 0,
    "end_sec": 3600,
    "segmentation": {
      "strategy": "fixed",
      "fixed": {
        "duration_sec": 6
      }
    },
    "embedding_option": [
      "audio",
      "transcription"
    ],
    "embedding_scope": [
      "clip",
      "asset"
    ]
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Audio with fixed segmentation
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"audio\",\n  \"model_name\": \"marengo3.0\",\n  \"audio\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/audio/long-audio.wav\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 3600,\n    \"segmentation\": {\n      \"strategy\": \"fixed\",\n      \"fixed\": {\n        \"duration_sec\": 6\n      }\n    },\n    \"embedding_option\": [\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Audio with fixed segmentation
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "audio",
  "model_name": "marengo3.0",
  "audio": [
    "media_source": ["url": "https://user-bucket.com/audio/long-audio.wav"],
    "start_sec": 0,
    "end_sec": 3600,
    "segmentation": [
      "strategy": "fixed",
      "fixed": ["duration_sec": 6]
    ],
    "embedding_option": ["audio", "transcription"],
    "embedding_scope": ["clip", "asset"]
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks")! as URL,
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

```python Video with dynamic segmentation
import requests

url = "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

payload = {
    "input_type": "video",
    "model_name": "marengo3.0",
    "video": {
        "media_source": { "url": "https://user-bucket.com/video/long-video.mp4" },
        "start_sec": 0,
        "end_sec": 7200,
        "segmentation": {
            "strategy": "dynamic",
            "dynamic": { "min_duration_sec": 4 }
        },
        "embedding_option": ["visual", "audio", "transcription"],
        "embedding_scope": ["clip", "asset"]
    }
}
headers = {
    "x-api-key": "<apiKey>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Video with dynamic segmentation
const url = 'https://api.twelvelabs.io/v1.3/embed-v2/tasks';
const options = {
  method: 'POST',
  headers: {'x-api-key': '<apiKey>', 'Content-Type': 'application/json'},
  body: '{"input_type":"video","model_name":"marengo3.0","video":{"media_source":{"url":"https://user-bucket.com/video/long-video.mp4"},"start_sec":0,"end_sec":7200,"segmentation":{"strategy":"dynamic","dynamic":{"min_duration_sec":4}},"embedding_option":["visual","audio","transcription"],"embedding_scope":["clip","asset"]}}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Video with dynamic segmentation
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.twelvelabs.io/v1.3/embed-v2/tasks"

	payload := strings.NewReader("{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/long-video.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 7200,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")

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

```ruby Video with dynamic segmentation
require 'uri'
require 'net/http'

url = URI("https://api.twelvelabs.io/v1.3/embed-v2/tasks")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["x-api-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/long-video.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 7200,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java Video with dynamic segmentation
HttpResponse<String> response = Unirest.post("https://api.twelvelabs.io/v1.3/embed-v2/tasks")
  .header("x-api-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/long-video.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 7200,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}")
  .asString();
```

```php Video with dynamic segmentation
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.twelvelabs.io/v1.3/embed-v2/tasks', [
  'body' => '{
  "input_type": "video",
  "model_name": "marengo3.0",
  "video": {
    "media_source": {
      "url": "https://user-bucket.com/video/long-video.mp4"
    },
    "start_sec": 0,
    "end_sec": 7200,
    "segmentation": {
      "strategy": "dynamic",
      "dynamic": {
        "min_duration_sec": 4
      }
    },
    "embedding_option": [
      "visual",
      "audio",
      "transcription"
    ],
    "embedding_scope": [
      "clip",
      "asset"
    ]
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp Video with dynamic segmentation
var client = new RestClient("https://api.twelvelabs.io/v1.3/embed-v2/tasks");
var request = new RestRequest(Method.POST);
request.AddHeader("x-api-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input_type\": \"video\",\n  \"model_name\": \"marengo3.0\",\n  \"video\": {\n    \"media_source\": {\n      \"url\": \"https://user-bucket.com/video/long-video.mp4\"\n    },\n    \"start_sec\": 0,\n    \"end_sec\": 7200,\n    \"segmentation\": {\n      \"strategy\": \"dynamic\",\n      \"dynamic\": {\n        \"min_duration_sec\": 4\n      }\n    },\n    \"embedding_option\": [\n      \"visual\",\n      \"audio\",\n      \"transcription\"\n    ],\n    \"embedding_scope\": [\n      \"clip\",\n      \"asset\"\n    ]\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Video with dynamic segmentation
import Foundation

let headers = [
  "x-api-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "input_type": "video",
  "model_name": "marengo3.0",
  "video": [
    "media_source": ["url": "https://user-bucket.com/video/long-video.mp4"],
    "start_sec": 0,
    "end_sec": 7200,
    "segmentation": [
      "strategy": "dynamic",
      "dynamic": ["min_duration_sec": 4]
    ],
    "embedding_option": ["visual", "audio", "transcription"],
    "embedding_scope": ["clip", "asset"]
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/embed-v2/tasks")! as URL,
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