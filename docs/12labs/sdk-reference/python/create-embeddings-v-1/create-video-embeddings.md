# Create video embeddings

The `EmbedClient.TasksClient` class provides methods to create embeddings for your videos.

To create video embeddings:

1. Create a video embedding task that uploads and processes a video.
2. Monitor the status of your task.
3. Retrieve the embeddings once the task is completed.

[**Related quickstart notebook**](https://colab.research.google.com/github/twelvelabs-io/twelvelabs-developer-experience/blob/main/quickstarts/TwelveLabs_Quickstart_Embeddings.ipynb)

# Methods

## Create a video embedding task

**Description**: This method creates a new video embedding task that uploads a video to the platform.

Your video files must meet the [format requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements).

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      *,
      model_name: str,
      video_file: typing.Optional[core.File] = OMIT,
      video_url: typing.Optional[str] = OMIT,
      video_start_offset_sec: typing.Optional[float] = OMIT,
      video_end_offset_sec: typing.Optional[float] = OMIT,
      video_clip_length: typing.Optional[float] = OMIT,
      video_embedding_scope: typing.Optional[typing.List[TasksCreateRequestVideoEmbeddingScopeItem]] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TasksCreateResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  task = client.embed.tasks.create(
      model_name="marengo3.0",
      # video_file="<YOUR_VIDEO_FILE>",
      video_url="<YOUR_VIDEO_URL>",
      video_start_offset_sec=0,
      video_end_offset_sec=10,
      video_clip_length=5,
      video_embedding_scope=["clip", "video"]
  )

  print(f"Task ID: {task.id}")
  ```
</CodeGroup>

**Parameters**:

| Name                     | Type                                                                                              | Required | Description                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model_name`             | `str`                                                                                             | Yes      | The name of the model you want to use. The following models are available:<br />- `marengo3.0`: Enhanced model with sports intelligence and extended content support. For a list of the new features, see the [New in Marengo 3.0](/v1.3/docs/concepts/models/marengo#new-in-marengo-30) section.<br />- `marengo2.7`: Video embedding model for multimodal search. |
| `video_file`             | `typing.Optional[core.File]`                                                                      | No       | The video file to upload.                                                                                                                                                                                                                                                                                                                                           |
| `video_url`              | `typing.Optional[str]`                                                                            | No       | Specify this parameter to upload a video from a publicly accessible URL.                                                                                                                                                                                                                                                                                            |
| `video_start_offset_sec` | `typing.Optional[float]`                                                                          | No       | The start offset in seconds from the beginning of the video where processing should begin. Specifying 0 means starting from the beginning of the video. **Default**: 0, **Min**: 0, **Max**: Duration of the video minus `video_clip_length`.                                                                                                                       |
| `video_end_offset_sec`   | `typing.Optional[float]`                                                                          | No       | The end offset in seconds from the beginning of the video where processing should stop. You must set both start and end offsets when using this parameter. **Min**: video\_start\_offset + video\_clip\_length, **Max**: Duration of the video file.                                                                                                                |
| `video_clip_length`      | `typing.Optional[float]`                                                                          | No       | The desired duration in seconds for each clip for which the platform generates an embedding. Ensure that the clip length does not exceed the interval between the start and end offsets. **Default**: 6, **Min**: 2, **Max**: 10.                                                                                                                                   |
| `video_embedding_scope`  | `typing.`<br />`Optional`<br />`[typing.List`<br />`[TasksCreateRequestVideoEmbeddingScopeItem]]` | No       | Defines the scope of video embedding generation. Valid values are: `["clip"]` and `["clip", "video"]`. Use the `video` scope for videos up to 10-30 seconds to maintain optimal performance. **Default**: `clip`.                                                                                                                                                   |
| `request_options`        | `typing.Optional[RequestOptions]`                                                                 | No       | Request-specific configuration.                                                                                                                                                                                                                                                                                                                                     |

**Return value**: **Return value**: Returns a `TasksCreateResponse` object representing the new video embedding task.

The `TasksCreateResponse` class contains the following properties:

| Name | Type            | Description                                                                                                                                  |
| ---- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `id` | `Optional[str]` | The unique identifier of the video embedding task. You can use the identifier to retrieve the status of your task or retrieve the embedding. |

**API Reference**: [Create a video embedding task](/v1.3/api-reference/create-embeddings-v1/video-embeddings/create-video-embedding-task).

**Related guide**: [Create video embeddings](/v1.3/docs/guides/create-embeddings/video).

## Retrieve the status of a video embedding task

**Description**: This method retrieves the status of a video embedding task.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def status(self, task_id: str, *, request_options: typing.Optional[RequestOptions] = None) -> TasksStatusResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  from twelvelabs.embed import TasksStatusResponse

  from twelvelabs import TwelveLabs

  response = client.embed.tasks.status(task_id="<YOUR_TASK_ID>")

  print(f"Task ID: {response.id}")
  print(f"Model Name: {response.model_name}")
  print(f"Status: {response.status}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                              | Required | Description                                        |
| :---------------- | :-------------------------------- | :------- | :------------------------------------------------- |
| `task_id`         | `string`                          | Yes      | The unique identifier of the video embedding task. |
| `request_options` | `typing.Optional[RequestOptions]` | No       | Request-specific configuration.                    |

**Return value**: Returns a `TasksStatusResponse` object containing the current status of the embedding task.

The `TasksStatusResponse` class contains the following properties:

| Name              | Type                                          | Description                                                                                                        |
| ----------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `id`              | `Optional[str]`                               | The unique identifier of the video embedding task.                                                                 |
| `status`          | `Optional[str]`                               | The status of the video indexing task. It can take one of the following values: `processing`, `ready` or `failed`. |
| `model_name`      | `Optional[str]`                               | The name of the video understanding model the platform used to create the embedding.                               |
| `video_embedding` | `Optional[TasksStatusResponseVideoEmbedding]` | An object containing the metadata associated with the embedding.                                                   |

The `TasksStatusResponseVideoEmbedding` class contains the following properties:

| Name       | Type                               | Description                             |
| ---------- | ---------------------------------- | --------------------------------------- |
| `metadata` | `Optional[VideoEmbeddingMetadata]` | Metadata associated with the embedding. |

The `VideoEmbeddingMetadata` class extends `BaseEmbeddingMetadata` and contains the following properties:

| Name                    | Type                  | Description                                                                                                                                                                     |
| ----------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `video_clip_length`     | `Optional[float]`     | The duration for each clip in seconds, as specified by the `video_clip_length` parameter. Note that the platform automatically truncates video segments shorter than 2 seconds. |
| `video_embedding_scope` | `Optional[List[str]]` | The scope you've specified in the request. It can take one of the following values: `['clip']` or `['clip', 'video']`.                                                          |
| `duration`              | `Optional[float]`     | The total duration of the video in seconds.                                                                                                                                     |
| `input_url`             | `Optional[str]`       | The URL of the media file used to generate the embedding. Present if a URL was provided in the request.                                                                         |
| `input_filename`        | `Optional[str]`       | The name of the media file used to generate the embedding. Present if a file was provided in the request.                                                                       |

**API Reference**: [Retrieve the status of a video embedding task](/v1.3/api-reference/upload-content/tasks/retrieve).

**Related guide**: [Create video embeddings](/v1.3/docs/guides/create-embeddings/video).

## Wait for a video embedding task to complete

**Description**: This method waits until a video embedding task is completed by periodically checking its status. If you provide a callback function, it calls the function after each status update with the current task object, allowing you to monitor progress.

<CodeGroup>
  ```python Function signature
  def wait_for_done(
      self,
      task_id: str,
      *,
      sleep_interval: float = 5.0,
      callback: typing.Optional[typing.Callable[[TasksStatusResponse], None]] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TasksStatusResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  from twelvelabs.embed import TasksStatusResponse

  def on_task_update(task: TasksStatusResponse):
      print(f"  Status={task.status}")

  status = client.embed.tasks.wait_for_done("<YOUR_TASK_ID>", callback=on_task_update)
  ```
</CodeGroup>

**Parameters**

| Name              | Type                                              | Required | Description                                                                                                                                   |
| :---------------- | :------------------------------------------------ | :------- | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| `task_id`         | `str`                                             | Yes      | The unique identifier of the task to wait for.                                                                                                |
| `sleep_interval`  | `float`                                           | No       | Sets the time in seconds to wait between status checks. Must be greater than 0. Default: 5.0.                                                 |
| `callback`        | `Optional[Callable[[TasksStatusResponse], None]]` | No       | Provides an optional function to call after each status check. The function receives the current task response. Use this to monitor progress. |
| `request_options` | `Optional[RequestOptions]`                        | No       | Request-specific configuration.                                                                                                               |

**Return value**: Returns a `TasksStatusResponse` object containing the status of your completed task. See the [Retrieve the status of a video embedding task](#retrieve-the-status-of-a-video-embedding-task) section above for complete property details.

## Retrieve video embeddings

**Description**: This method retrieves embeddings for a specific video embedding task. Ensure the task status is `ready` before retrieving your embeddings.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def retrieve(
      self,
      task_id: str,
      *,
      embedding_option: typing.Optional[
          typing.Union[
              TasksRetrieveRequestEmbeddingOptionItem, typing.Sequence[TasksRetrieveRequestEmbeddingOptionItem]
          ]
      ] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TasksRetrieveResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  from twelvelabs.types import VideoSegment

  task = client.embed.tasks.retrieve(
      task_id="<YOUR_TASK_ID>",
      embedding_option=["visual", "audio", "transcription"]
  )

  def print_segments(segments: List[VideoSegment], max_elements: int = 5):
      for segment in segments:
          print(f"  embedding_scope={segment.embedding_scope} embedding_option={segment.embedding_option} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}")
          first_few = segment.float_[:max_elements]
          print(
              f"  embeddings: [{', '.join(str(x) for x in first_few)}...] (total: {len(segment.float_)} values)"
          )
  if task.video_embedding is not None and task.video_embedding.segments is not None:
      print_segments(task.video_embedding.segments)

  ```
</CodeGroup>

**Parameters**:

| Name               | Type                                                                                                                                                                       | Required | Description                                                                                                                                                                                                                                                                                     |
| :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `task_id`          | `str`                                                                                                                                                                      | Yes      | The unique identifier of your video embedding task.                                                                                                                                                                                                                                             |
| `embedding_option` | `typing.`<br />`Optional`<br />`[typing.Union`<br />`[TasksRetrieveRequestEmbeddingOptionItem, typing.`<br />`Sequence`<br />`[TasksRetrieveRequestEmbeddingOptionItem]]]` | No       | Specifies which types of embeddings to retrieve. Values vary depending on the version of the model. For details, see the [Embedding options](/v1.3/docs/concepts/modalities#embedding-options) section.<br />The platform returns all available embeddings if you don't provide this parameter. |
| `request_options`  | `typing.Optional[RequestOptions]`                                                                                                                                          | No       | Request-specific configuration.                                                                                                                                                                                                                                                                 |

**Return value**: Returns a `TasksRetrieveResponse` object containing your embeddings.

The `TasksRetrieveResponse` class contains the following properties:

| Name              | Type                                            | Description                                                                                                        |
| ----------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `id`              | `Optional[str]`                                 | The unique identifier of the video embedding task.                                                                 |
| `model_name`      | `Optional[str]`                                 | The name of the video understanding model the platform used to create the embedding.                               |
| `status`          | `Optional[str]`                                 | The status of the video indexing task. It can take one of the following values: `processing`, `ready` or `failed`. |
| `created_at`      | `Optional[datetime]`                            | The date and time, in the RFC 3339 format, that the video embedding task was created.                              |
| `video_embedding` | `Optional[TasksRetrieveResponseVideoEmbedding]` | An object containing the embeddings and metadata.                                                                  |

The `TasksRetrieveResponseVideoEmbedding` class contains the following properties:

| Name       | Type                               | Description                                                                                          |
| ---------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `metadata` | `Optional[VideoEmbeddingMetadata]` | Metadata associated with the embedding.                                                              |
| `segments` | `Optional[List[VideoSegment]]`     | An array of objects containing the embeddings for each video segment and the associated information. |

The `VideoEmbeddingMetadata` class extends `BaseEmbeddingMetadata` and contains the following properties:

| Name                    | Type                  | Description                                                                                                                  |
| ----------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `video_clip_length`     | `Optional[float]`     | The duration for each clip in seconds. Note that the platform automatically truncates video segments shorter than 2 seconds. |
| `video_embedding_scope` | `Optional[List[str]]` | The scope you've specified in the request. It can take one of the following values: `['clip']` or `['clip', 'video']`.       |
| `duration`              | `Optional[float]`     | The total duration of the video in seconds.                                                                                  |
| `input_url`             | `Optional[str]`       | The URL of the media file used to generate the embedding. Present if a URL was provided in the request.                      |
| `input_filename`        | `Optional[str]`       | The name of the media file used to generate the embedding. Present if a file was provided in the request.                    |

The `VideoSegment` class extends `AudioSegment` and contains the following properties:

| Name               | Type                    | Description                                                                                                                                |
| ------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `start_offset_sec` | `Optional[float]`       | The start time, in seconds, from which the platform generated the embedding.                                                               |
| `end_offset_sec`   | `Optional[float]`       | The end time, in seconds, of the video segment for this embedding.                                                                         |
| `embedding_option` | `Optional[str]`         | The type of the embedding.                                                                                                                 |
| `embedding_scope`  | `Optional[str]`         | The scope of the video embedding.                                                                                                          |
| `float_`           | `Optional[List[float]]` | An array of floating point numbers representing the embedding. You can use this array with cosine similarity for various downstream tasks. |

**API Reference**: [Retrieve video embeddings](/v1.3/api-reference/create-embeddings-v1/video-embeddings/retrieve-video-embeddings).

**Related guide**: [Create video embeddings](/v1.3/docs/guides/create-embeddings/video).

# Error codes

This section lists the most common error messages you may encounter while creating video embeddings.

* `parameter_invalid`
  * The `video_clip_length` parameter is invalid. `video_clip_length` should be within 2-10 seconds long
  * The `video_end_offset_sec` parameter is invalid. `video_end_offset_sec` should be greater than `video_start_offset_sec`
