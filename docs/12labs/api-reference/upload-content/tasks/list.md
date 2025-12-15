# List video indexing tasks

GET https://api.twelvelabs.io/v1.3/tasks

This method returns a list of the video indexing tasks in your account. The platform returns your video indexing tasks sorted by creation date, with the newest at the top of the list.

Reference: https://docs.twelvelabs.io/api-reference/upload-content/tasks/list

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List video indexing tasks
  version: endpoint_tasks.list
paths:
  /tasks:
    get:
      operationId: list
      summary: List video indexing tasks
      description: >-
        This method returns a list of the video indexing tasks in your account.
        The platform returns your video indexing tasks sorted by creation date,
        with the newest at the top of the list.
      tags:
        - - subpackage_tasks
      parameters:
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
        - name: sort_by
          in: query
          description: >
            The field to sort on. The following options are available:

            - `updated_at`: Sorts by the time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"), when the item was updated.

            - `created_at`: Sorts by the time, in the RFC 3339 format
            ("YYYY-MM-DDTHH:mm:ssZ"), when the item was created.


            **Default**: `created_at`.
          required: false
          schema:
            type: string
        - name: sort_option
          in: query
          description: |
            The sorting direction. The following options are available:
            - `asc`
            - `desc`

            **Default**: `desc`.
          required: false
          schema:
            type: string
        - name: index_id
          in: query
          description: |
            Filter by the unique identifier of an index.
          required: false
          schema:
            type: string
        - name: status
          in: query
          description: >
            Filter by one or more video indexing task statuses. The following
            options are available:

            - `ready`: The video has been successfully uploaded and indexed.

            - `uploading`: The video is being uploaded.

            - `validating`: The video is being validated against the
            prerequisites.

            - `pending`: The video is pending.

            - `queued`: The video is queued.

            - `indexing`: The video is being indexed.

            - `failed`: The video indexing task failed.


            To filter by multiple statuses, specify the `status` parameter for
            each value:

            ```

            status=ready&status=validating

            ```
          required: false
          schema:
            type: array
            items:
              $ref: '#/components/schemas/TasksGetParametersStatusSchemaItems'
        - name: filename
          in: query
          description: |
            Filter by filename.
          required: false
          schema:
            type: string
        - name: duration
          in: query
          description: |
            Filter by duration. Expressed in seconds.
          required: false
          schema:
            type: number
            format: double
        - name: width
          in: query
          description: |
            Filter by width.
          required: false
          schema:
            type: integer
        - name: height
          in: query
          description: |
            Filter by height.
          required: false
          schema:
            type: integer
        - name: created_at
          in: query
          description: >
            Filter video indexing tasks by the creation date and time, in the
            RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"). The platform returns the
            video indexing tasks that were created on the specified date at or
            after the given time.
          required: false
          schema:
            type: string
        - name: updated_at
          in: query
          description: >
            Filter video indexing tasks by the last update date and time, in the
            RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"). The platform returns the
            video indexing tasks that were updated on the specified date at or
            after the given time.
          required: false
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
          description: The video indexing tasks have successfully been retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/tasks_list_Response_200'
        '400':
          description: The request has failed.
          content: {}
components:
  schemas:
    TasksGetParametersStatusSchemaItems:
      type: string
      enum:
        - value: ready
        - value: uploading
        - value: validating
        - value: pending
        - value: queued
        - value: indexing
        - value: failed
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
    videoIndexingTask:
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
    limit_per_page_simple:
      type: integer
    page:
      type: integer
    total_page:
      type: integer
    total_results:
      type: integer
    TasksGetResponsesContentApplicationJsonSchemaPageInfo:
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
    tasks_list_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/videoIndexingTask'
        page_info:
          $ref: >-
            #/components/schemas/TasksGetResponsesContentApplicationJsonSchemaPageInfo

```

## SDK Code Examples

```python
import requests

url = "https://api.twelvelabs.io/v1.3/tasks"

headers = {"x-api-key": "<apiKey>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.twelvelabs.io/v1.3/tasks';
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

	url := "https://api.twelvelabs.io/v1.3/tasks"

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

url = URI("https://api.twelvelabs.io/v1.3/tasks")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["x-api-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.twelvelabs.io/v1.3/tasks")
  .header("x-api-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.twelvelabs.io/v1.3/tasks', [
  'headers' => [
    'x-api-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.twelvelabs.io/v1.3/tasks");
var request = new RestRequest(Method.GET);
request.AddHeader("x-api-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["x-api-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.twelvelabs.io/v1.3/tasks")! as URL,
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