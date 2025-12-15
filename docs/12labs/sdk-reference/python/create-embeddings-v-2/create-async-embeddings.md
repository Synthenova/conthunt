# Create async embeddings

The `EmbedClient.V2Client.TasksClient` class provides methods to create embeddings asynchronously for audio and video content. Use this class for processing files longer than 10 minutes.

<Note title="Note">
  This class only supports Marengo version 3.0 or newer.
</Note>

**When to use this class**:

* Process audio or video files longer than 10 minutes
* Process files up to 4 hours in duration

<Accordion title="Input requirements">
  **Video**:

  * Minimum duration: 4 seconds
  * Maximum duration: 4 hours
  * Maximum file size: 4 GB
  * Formats: [FFmpeg supported formats](https://ffmpeg.org/ffmpeg-formats.html)
  * Resolution: 360x360 to 5184x2160 pixels
  * Aspect ratio: Between 1:1 and 1:2.4, or between 2.4:1 and 1:1

  **Audio**:

  * Minimum duration: 4 seconds
  * Maximum duration: 4 hours
  * Maximum file size: 2 GB
  * Formats: WAV (uncompressed), MP3 (lossy), FLAC (lossless)
</Accordion>

Creating embeddings asynchronously requires three steps:

1. Create a task using the `create` method. The platform returns a task ID.
2. Poll for the status of the task using the `retrieve` method. Wait until the status is `ready`.
3. Retrieve the embeddings from the response when the status is `ready` using the `retrieve` method.

# Methods

## List embedding tasks

**Description**: This method returns a list of the async embedding tasks in your account. The platform returns your async embedding tasks sorted by creation date, with the newest at the top of the list.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def list(
      self,
      *,
      started_at: typing.Optional[str] = None,
      ended_at: typing.Optional[str] = None,
      status: typing.Optional[str] = None,
      page: typing.Optional[int] = None,
      page_limit: typing.Optional[int] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> SyncPager[MediaEmbeddingTask]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.embed.v_2.tasks.list(
      page=1,
      page_limit=10,
  )

  print("Embedding tasks:")
  for task in response:
      print(f"  Task ID: {task.id}")
      print(f"  Model: {task.model_name}")
      print(f"  Status: {task.status}")
      print(f"  Created: {task.created_at}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                                                                                                                   |
| ----------------- | ---------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `started_at`      | `str`            | No       | Retrieve the embedding tasks that were created after the specified date and time, expressed in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ").  |
| `ended_at`        | `str`            | No       | Retrieve the embedding tasks that were created before the specified date and time, expressed in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"). |
| `status`          | `str`            | No       | Filter the embedding tasks by their current status. Values: `processing`, `ready`, or `failed`.                                               |
| `page`            | `int`            | No       | A number that identifies the page to retrieve. Default: `1`.                                                                                  |
| `page_limit`      | `int`            | No       | The number of items to return on each page. Default: `10`. Max: `50`.                                                                         |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.                                                                                                               |

**Return value**: Returns a `SyncPager[MediaEmbeddingTask]` object that allows you to iterate through the paginated task results.

The `SyncPager[T]` class contains the following properties and methods:

| Name           | Type                                             | Description                                                            |
| -------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| `items`        | `Optional[List[T]]`                              | A list containing the current page of items. Can be `None`.            |
| `has_next`     | `bool`                                           | Indicates whether there is a next page to load.                        |
| `get_next`     | `Optional[Callable[[], Optional[SyncPager[T]]]]` | A callable function that retrieves the next page. Can be `None`.       |
| `response`     | `Optional[BaseHttpResponse]`                     | The HTTP response object. Can be `None`.                               |
| `next_page()`  | `Optional[SyncPager[T]]`                         | Calls `get_next()` if available and returns the next page object.      |
| `__iter__()`   | `Iterator[T]`                                    | Allows iteration through all items across all pages using `for` loops. |
| `iter_pages()` | `Iterator[SyncPager[T]]`                         | Allows iteration through page objects themselves.                      |

The `MediaEmbeddingTask` class contains the following properties:

| Name              | Type                                         | Description                                                                                       |
| ----------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `id`              | `Optional[str]`                              | The unique identifier of the embedding task.                                                      |
| `model_name`      | `Optional[str]`                              | The name of the video understanding model the platform used to create the embedding.              |
| `status`          | `Optional[str]`                              | A string indicating the status of the embedding task. Values: `processing`, `ready`, or `failed`. |
| `created_at`      | `Optional[datetime]`                         | The date and time when the task was created.                                                      |
| `updated_at`      | `Optional[datetime]`                         | The date and time when the task was last updated.                                                 |
| `video_embedding` | `Optional[MediaEmbeddingTaskVideoEmbedding]` | An object containing the metadata associated with the video embedding.                            |
| `audio_embedding` | `Optional[MediaEmbeddingTaskAudioEmbedding]` | An object containing the metadata associated with the audio embedding.                            |

**API Reference**: [List async embedding tasks](/v1.3/api-reference/create-embeddings-v2/list-async-embedding-tasks)

## Create an async embedding task

**Description**: This method creates embeddings for audio and video content asynchronously.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      *,
      input_type: CreateAsyncEmbeddingRequestInputType,
      model_name: str,
      audio: typing.Optional[AudioInputRequest] = OMIT,
      video: typing.Optional[VideoInputRequest] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TasksCreateResponse
  ```

  ```python Python example
  from twelvelabs import (
      TwelveLabs,
      VideoInputRequest,
      VideoSegmentation_Fixed,
      VideoSegmentationFixedFixed,
      MediaSource,
  )

  task = client.embed.v_2.tasks.create(
      input_type="video",
      model_name="marengo3.0",
      video=VideoInputRequest(
          media_source=MediaSource(
              url="<YOUR_VIDEO_URL>",
          ),
          start_sec=0.0,
          end_sec=50.0,
          segmentation=VideoSegmentation_Fixed(
              fixed=VideoSegmentationFixedFixed(
                  duration_sec=10,
              ),
          ),
          embedding_option=["visual", "audio", "transcription"],
          embedding_scope=["clip", "asset"],
      ),
  )

  print(f"Task ID: {task.id}")
  print(f"Status: {task.status}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                                   | Required | Description                                                                                                                |
| ----------------- | -------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `input_type`      | `CreateAsyncEmbeddingRequestInputType` | Yes      | The type of content for the embedding Values: `audio`, `video`.                                                            |
| `model_name`      | `str`                                  | Yes      | The model you wish to use. Example: `marengo3.0`.                                                                          |
| `audio`           | `AudioInputRequest`                    | No       | Audio input configuration. Required when `input_type` is `audio`. See [AudioInputRequest](#audioinputrequest) for details. |
| `video`           | `VideoInputRequest`                    | No       | Video input configuration. Required when `input_type` is `video`. See [VideoInputRequest](#videoinputrequest) for details. |
| `request_options` | `RequestOptions`                       | No       | Request-specific configuration.                                                                                            |

### AudioInputRequest

The `AudioInputRequest` class specifies configuration for processing audio content. Required when `input_type` is `audio`.

| Name               | Type                | Required | Description                                                                                                                                                                                                                                                                                                                   |
| ------------------ | ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `media_source`     | `MediaSource`       | Yes      | Specifies the source of the audio file. See [MediaSource](#mediasource) for details.                                                                                                                                                                                                                                          |
| `start_sec`        | `float`             | No       | The start time in seconds for processing the audio file. Use this parameter to process a portion of the audio file starting from a specific time. Default: `0` (start from the beginning).                                                                                                                                    |
| `end_sec`          | `float`             | No       | The end time in seconds for processing the audio file. Use this parameter to process a portion of the audio file ending at a specific time. The end time must be greater than the start time. Default: End of the audio file.                                                                                                 |
| `segmentation`     | `AudioSegmentation` | No       | Specifies how the platform divides the audio into segments. See [AudioSegmentation](#audiosegmentation) for details.                                                                                                                                                                                                          |
| `embedding_option` | `List[str]`         | No       | The types of embeddings you wish to generate. Values:<br />- `audio`: Generates embeddings based on audio content (sounds, music, effects)<br />- `transcription`: Generates embeddings based on transcribed speech<br /><br />You can specify multiple options to generate different types of embeddings for the same audio. |
| `embedding_scope`  | `List[str]`         | No       | The scope for which you wish to generate embeddings. Values:<br />- `clip`: Generates one embedding for each segment<br />- `asset`: Generates one embedding for the entire audio file<br /><br />You can specify multiple scopes to generate embeddings at different levels.                                                 |

### VideoInputRequest

The `VideoInputRequest` class specifies configuration for processing video content. Required when `input_type` is `video`.

| Name               | Type                | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------ | ------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `media_source`     | `MediaSource`       | Yes      | Specifies the source of the video file. See [MediaSource](#mediasource) for details.                                                                                                                                                                                                                                                                                                                                                                                         |
| `start_sec`        | `float`             | No       | The start time in seconds for processing the video file. Use this parameter to process a portion of the video file starting from a specific time. Default: `0` (start from the beginning).                                                                                                                                                                                                                                                                                   |
| `end_sec`          | `float`             | No       | The end time in seconds for processing the video file. Use this parameter to process a portion of the video file ending at a specific time. The end time must be greater than the start time. Default: End of the video file.                                                                                                                                                                                                                                                |
| `segmentation`     | `VideoSegmentation` | No       | Specifies how the platform divides the video into segments. See [VideoSegmentation](#videosegmentation) for details.                                                                                                                                                                                                                                                                                                                                                         |
| `embedding_option` | `List[str]`         | No       | The types of embeddings to generate for the video. Values:<br />- `visual`: Generates embeddings based on visual content (scenes, objects, actions)<br />- `audio`: Generates embeddings based on audio content (sounds, music, effects)<br />- `transcription`: Generates embeddings based on transcribed speech<br /><br />You can specify multiple options to generate different types of embeddings for the same video. Default: `["visual", "audio", "transcription"]`. |
| `embedding_scope`  | `List[str]`         | No       | The scope for which you wish to generate embeddings. Values:<br />- `clip`: Generates one embedding for each segment<br />- `asset`: Generates one embedding for the entire video file. Use this scope for videos up to 10-30 seconds to maintain optimal performance.<br /><br />You can specify multiple scopes to generate embeddings at different levels. Default: `["clip", "asset"]`.                                                                                  |

### MediaSource

The `MediaSource` class specifies the source of the media file. Provide exactly one of the following:

| Name            | Type  | Required | Description                                                                                                                                                                                     |
| --------------- | ----- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `base64_string` | `str` | No       | The base64-encoded media data.                                                                                                                                                                  |
| `url`           | `str` | No       | The publicly accessible URL of the media file. Use direct links to raw media files. Video hosting platforms and cloud storage sharing links are not supported.                                  |
| `asset_id`      | `str` | No       | The unique identifier of an asset from a [direct](/v1.3/sdk-reference/python/upload-content/direct-uploads) or [multipart](/v1.3/sdk-reference/python/upload-content/multipart-uploads) upload. |

### AudioSegmentation

The `AudioSegmentation` class specifies how the platform divides the audio into segments using fixed-length intervals.

| Name       | Type                     | Required | Description                                                                                              |
| ---------- | ------------------------ | -------- | -------------------------------------------------------------------------------------------------------- |
| `strategy` | `Literal["fixed"]`       | Yes      | The segmentation strategy. Value: `fixed`.                                                               |
| `fixed`    | `AudioSegmentationFixed` | Yes      | Configuration for fixed segmentation. See [AudioSegmentationFixed](#audiosegmentationfixed) for details. |

### AudioSegmentationFixed

The `AudioSegmentationFixed` class configures fixed-length segmentation for audio.

| Name           | Type  | Required | Description                                                                                                                                                                                                                                                                                                          |
| -------------- | ----- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `duration_sec` | `int` | Yes      | The duration in seconds for each segment. The platform divides the audio into segments of this exact length. The final segment may be shorter if the audio duration is not evenly divisible.<br /><br />**Example**: With `duration_sec: 5`, a 12-second audio file produces segments: \[0-5s], \[5-10s], \[10-12s]. |

### VideoSegmentation

The `VideoSegmentation` type specifies how the platform divides the video into segments. Use one of the following:

**Fixed segmentation**: Divides the video into equal-length segments:

| Name       | Type                          | Required | Description                                                                                                        |
| ---------- | ----------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------ |
| `strategy` | `Literal["fixed"]`            | Yes      | The segmentation strategy. Value: `fixed`.                                                                         |
| `fixed`    | `VideoSegmentationFixedFixed` | Yes      | Configuration for fixed segmentation. See [VideoSegmentationFixedFixed](#videosegmentationfixedfixed) for details. |

**Dynamic segmentation**: Divides the video into adaptive segments based on scene changes:

| Name       | Type                              | Required | Description                                                                                                                  |
| ---------- | --------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `strategy` | `Literal["dynamic"]`              | Yes      | The segmentation strategy. Value: `dynamic`.                                                                                 |
| `dynamic`  | `VideoSegmentationDynamicDynamic` | Yes      | Configuration for dynamic segmentation. See [VideoSegmentationDynamicDynamic](#videosegmentationdynamicdynamic) for details. |

### VideoSegmentationFixedFixed

The `VideoSegmentationFixedFixed` class configures fixed-length segmentation for video.

| Name           | Type  | Required | Description                                                                                                                                                                                                                                                                                                     |
| -------------- | ----- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `duration_sec` | `int` | Yes      | The duration in seconds for each segment. The platform divides the video into segments of this exact length. The final segment may be shorter if the video duration is not evenly divisible.<br /><br />**Example**: With `duration_sec: 5`, a 12-second video produces segments: \[0-5s], \[5-10s], \[10-12s]. |

### VideoSegmentationDynamicDynamic

The `VideoSegmentationDynamicDynamic` class configures dynamic segmentation for video based on scene changes.

| Name               | Type  | Required | Description                                                                                                                                                                                                                                                                                                                         |
| ------------------ | ----- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `min_duration_sec` | `int` | Yes      | The minimum duration in seconds for each segment. The platform divides the video into segments that are at least this long. Segments adapt to scene changes and content boundaries and may be longer than the minimum.<br /><br />**Example**: With `min_duration_sec: 3`, segments might be: \[0-3.2s], \[3.2-7.8s], \[7.8-12.1s]. |

**Return value**: Returns a `TasksCreateResponse` object containing the task details.

The `TasksCreateResponse` class contains the following properties:

| Name     | Type                            | Description                                                    |
| -------- | ------------------------------- | -------------------------------------------------------------- |
| `id`     | `str`                           | The unique identifier of the embedding task.                   |
| `status` | `Literal["processing"]`         | The initial status of the embedding task. Value: `processing`. |
| `data`   | `Optional[List[EmbeddingData]]` | Array of embedding results (only when status is ready).        |

**API Reference**: [Create an async embedding task](/v1.3/api-reference/create-embeddings-v2/create-async-embedding-task)

## Retrieve task status and results

**Description**: This method retrieves the status and the results of an async embedding task.

**Task statuses**:

* `processing`: The platform is creating the embeddings.
* `ready`: Processing is complete. Embeddings are available in the response.
* `failed`: The task failed. Embeddings were not created.

Invoke this method repeatedly until the `status` field is `ready`. When `status` is `ready`, use the embeddings from the response.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def retrieve(
      self,
      task_id: str,
      *,
      request_options: typing.Optional[RequestOptions] = None
  ) -> EmbeddingTaskResponse
  ```

  ```python Poll for task completion
  from twelvelabs import TwelveLabs
  import time

  while True:
      task = client.embed.v_2.tasks.retrieve(task_id="<YOUR_TASK_ID>")

      print(f"Task Status: {task.status}")

      if task.status == "ready":
          print(f"Task completed!")
          break
      elif task.status == "failed":
          print("Task failed")
          break
      else:
          print("Task still processing, waiting...")
          time.sleep(5)
  ```

  ```python Retrieve embeddings
  from twelvelabs import TwelveLabs

  task = client.embed.v_2.tasks.retrieve(
      task_id="<YOUR_TASK_ID>",
  )

  print(f"Task ID: {task.id}")
  print(f"Status: {task.status}")
  print(f"Created: {task.created_at}")
  print(f"Updated: {task.updated_at}")

  if task.status == "ready" and task.data:
      print(f"\nNumber of embeddings: {len(task.data)}")
      for embedding_data in task.data:
          print(f"Embedding dimensions: {len(embedding_data.embedding)}")
          print(f"First 10 values: {embedding_data.embedding[:10]}")
          print(f"Option: {embedding_data.embedding_option}")
          print(f"Scope: {embedding_data.embedding_scope}")
          if embedding_data.start_sec is not None:
              print(f"Time range: {embedding_data.start_sec}s - {embedding_data.end_sec}s")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type             | Required | Description                                  |
| ----------------- | ---------------- | -------- | -------------------------------------------- |
| `task_id`         | `str`            | Yes      | The unique identifier of the embedding task. |
| `request_options` | `RequestOptions` | No       | Request-specific configuration.              |

**Return value**: Returns an `EmbeddingTaskResponse` object containing the task status and results.

The `EmbeddingTaskResponse` class contains the following properties:

| Name         | Type                                   | Description                                                                                                                                                                                                                                            |
| ------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`         | `str`                                  | The unique identifier of the embedding task.                                                                                                                                                                                                           |
| `status`     | `EmbeddingTaskResponseStatus`          | The current status of the task. Values:<br />- `processing`: The platform is creating the embeddings<br />- `ready`: Processing is complete. Embeddings are available in the `data` field<br />- `failed`: The task failed. The `data` field is `null` |
| `created_at` | `Optional[datetime]`                   | The date and time when the task was created.                                                                                                                                                                                                           |
| `updated_at` | `Optional[datetime]`                   | The date and time when the task was last updated.                                                                                                                                                                                                      |
| `data`       | `Optional[List[EmbeddingData]]`        | An array of embedding results. The platform returns this field when `status` is `ready`.                                                                                                                                                               |
| `metadata`   | `Optional[EmbeddingTaskMediaMetadata]` | Metadata about the embedding task.                                                                                                                                                                                                                     |

For details about the `EmbeddingData` class, see the [Create an async embedding task](/v1.3/sdk-reference/python/create-embeddings-v-2/create-async-embeddings#create-an-async-embedding-task) section.

**API Reference**: [Retrieve task status and results](/v1.3/api-reference/create-embeddings-v2/retrieve-embeddings)
