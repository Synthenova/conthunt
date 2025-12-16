# Video indexing tasks

<Info>
  This method of uploading videos will be deprecated in a future version. New implementations should use direct uploads or multipart uploads followed by separate indexing.
</Info>

A video indexing task represents a request to upload and index a video. The `TaskClientWrapper` class provides methods to manage your video indexing tasks.

# Methods

## Create a video indexing task

**Description**: This method creates a new video indexing task that uploads and indexes a video.

Your video files must meet requirements based on the models enabled for your index:

* [Marengo requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements).
* [Pegasus requirements](/v1.3/docs/concepts/models/pegasus#video-file-requirements).
* If both models are enabled, the most restrictive limits apply.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      *,
      index_id: str,
      video_file: typing.Optional[core.File] = OMIT,
      video_url: typing.Optional[str] = OMIT,
      enable_video_stream: typing.Optional[bool] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TasksCreateResponse:
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  task = client.tasks.create(
      index_id=index.id, video_url="<YOUR_VIDEO_URL>")
  print(f"Created task: id={task.id}")

  ```
</CodeGroup>

**Parameters**:

| Name                  | Type                                              | Required | Description                                                                                                                                                                                                                                                                |
| --------------------- | ------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `index_id`            | `str`                                             | Yes      | The unique identifier of the index to which the video will be uploaded.                                                                                                                                                                                                    |
| `video_file`          | `typing.`<br />`Optional`<br />`[core.File]`      | No       | The video file to upload.                                                                                                                                                                                                                                                  |
| `video_url`           | `typing.`<br />`Optional[str]`                    | No       | The publicly accessible URL of the video you want to upload.                                                                                                                                                                                                               |
| `enable_video_stream` | `typing.`<br />`Optional[bool]`                   | No       | Indicates if the platform stores the video for streaming. When set to `true`, the platform stores the video, and you can retrieve its URL by. For details, see the [Retrieve video information](/v1.3/sdk-reference/python/manage-videos#retrieve-video-information) page. |
| `user_metadata:`      | `typing.Optional[str]`                            | No       | Metadata that helps you categorize your videos. You can specify a stringified list of keys and values.                                                                                                                                                                     |
| `request_options`     | `typing.`<br />`Optional`<br />`[RequestOptions]` | No       | Request-specific configuration.                                                                                                                                                                                                                                            |

**Return value**: Returns a `TasksCreateResponse` instance.

The `TasksCreateResponse` interface contains the following properties:

| Name       | Type     | Description                                                                  |
| ---------- | -------- | ---------------------------------------------------------------------------- |
| `id`       | `string` | The unique identifier of your video indexing task.                           |
| `video_id` | `string` | The unique identifier of the video associated with your video indexing task. |

**API Reference**: [Create a video indexing task](/v1.3/api-reference/upload-content/tasks/create).

## Retrieve a video indexing task

**Description**: This method retrieves the details of a specific video indexing task.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def retrieve(
      self, task_id: str, *, request_options: typing.Optional[RequestOptions] = None
  ) -> TasksRetrieveResponse
  ```

  ```javascript Python example
  from twelvelabs import TwelveLabs
  from twelvelabs.tasks import TasksRetrieveResponse

  retrieved_task = client.tasks.retrieve(task_id="YOUR_VIDEO_INDEXING_TASK_ID" )

  print(f"Task ID: {retrieved_task.id}")
  print(f"Index ID: {retrieved_task.index_id}")
  print(f"Video ID: {retrieved_task.video_id}")
  print(f"Status: {retrieved_task.status}")
  print("System metadata:")
  print(retrieved_task.system_metadata)
  if retrieved_task.hls:
      print("HLS:")
      print(f"  Video URL: {retrieved_task.hls.video_url}")
      print("  Thumbnail URLs:")
      for url in retrieved_task.hls.thumbnail_urls or []:
          print(f"    {url}")
      print(f"  Status: {retrieved_task.hls.status}")
      print(f"  Updated at: {retrieved_task.hls.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                              | Required | Description                                                   |
| ----------------- | --------------------------------- | -------- | ------------------------------------------------------------- |
| `task_id`         | `str`                             | Yes      | The unique identifier of the video indexing task to retrieve. |
| `request_options` | `typing.Optional[RequestOptions]` | No       | Request-specific configuration.                               |

**Return value**: Returns a `TasksRetrieveResponse` object representing the retrieved video indexing task.

The `TasksRetrieveResponse` class extends `VideoIndexingTask` and contains the following properties:

| Name              | Type                                        | Description                                                                           |
| ----------------- | ------------------------------------------- | ------------------------------------------------------------------------------------- |
| `id`              | `Optional[str]`                             | The unique identifier of the task.                                                    |
| `video_id`        | `Optional[str]`                             | The unique identifier of the video associated with the specified video indexing task. |
| `created_at`      | `Optional[str]`                             | The date and time, in the RFC 3339 format, that the task was created.                 |
| `updated_at`      | `Optional[str]`                             | The date and time, in the RFC 3339 format, that the task object was last updated.     |
| `status`          | `Optional[str]`                             | The status of the video indexing task.                                                |
| `index_id`        | `Optional[str]`                             | The unique identifier of the index to which the video must be uploaded.               |
| `system_metadata` | `Optional[VideoIndexingTaskSystemMetadata]` | System-generated metadata about the video.                                            |
| `hls`             | `Optional[HlsObject]`                       | HLS streaming information for the video.                                              |

The `VideoIndexingTaskSystemMetadata` class contains the following properties:

| Name       | Type              | Description                |
| ---------- | ----------------- | -------------------------- |
| `duration` | `Optional[float]` | The duration of the video. |
| `filename` | `Optional[str]`   | The filename of the video. |
| `height`   | `Optional[int]`   | The height of the video.   |
| `width`    | `Optional[int]`   | The width of the video.    |

The `HlsObject` class contains the following properties:

| Name             | Type                        | Description                                                                                                                                            |
| ---------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `video_url`      | `Optional[str]`             | The URL of the video for HLS streaming.                                                                                                                |
| `thumbnail_urls` | `Optional[List[str]]`       | An array containing the URL of the thumbnail.                                                                                                          |
| `status`         | `Optional[HlsObjectStatus]` | The encoding status of the video file from its original format to a streamable format. Possible values: `PROCESSING`, `COMPLETE`, `CANCELED`, `ERROR`. |
| `updated_at`     | `Optional[str]`             | The date and time, in the RFC 3339 format, that the encoding status was last updated.                                                                  |

**API Reference**: [Retrieve a video indexing task](/v1.3/api-reference/upload-content/tasks/retrievee).

## Wait for a video indexing task to complete

**Description**: This method waits until a video indexing task is completed. It checks the task status at regular intervals by retrieving its details. If you provide a callback function, the method calls it after each status check with the current task object. This allows you to monitor the progress of the task.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def wait_for_done(
      self,
      task_id: str,
      *,
      sleep_interval: float = 5.0,
      callback: typing.Optional[
          typing.Callable[[TasksRetrieveResponse], None]
      ] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TasksRetrieveResponse
  ```

  ```Python Python example
  from twelvelabs import TwelveLabs
  from twelvelabs.tasks import TasksRetrieveResponse

  def on_task_update(task: TasksRetrieveResponse):
    print(f"  Status={task.status}")
  task = client.tasks.wait_for_done(task_id="<YOUR_TASK_ID>", callback=on_task_update)
  if task.status != "ready":
      raise RuntimeError(f"Indexing failed with status {task.status}")
  print(
      f"Upload complete. The unique identifier of your video is {task.video_id}.")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                                                                | Required | Description                                                                                                            |
| ----------------- | ------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| `task_id`         | `str`                                                               | Yes      | The unique identifier of the task to wait for.                                                                         |
| `sleep_interval`  | `float`                                                             | No       | The time in seconds to wait between status checks. Must be greater than 0. Default: `5.0`.                             |
| `callback`        | `Optional`<br />`[Callable`<br />`[[TasksRetrieveResponse], None]]` | No       | An optional function to call after each status check, receiving the current task object. Use this to monitor progress. |
| `request_options` | `Optional[RequestOptions]`                                          | No       | Request-specific configuration.                                                                                        |

**Return value**: Returns a `TasksRetrieveResponse` object representing the completed task. See the [Retrieve a video indexing task](#retrieve-a-video-indexing-task) section above for complete property details.

## List video indexing tasks

**Description**: This method returns a paginated list of the video indexing tasks in your account. By default, the platform returns your video indexing tasks sorted by creation date, with the newest at the top of the list.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def list(
      self,
      *,
      page: typing.Optional[int] = None,
      page_limit: typing.Optional[int] = None,
      sort_by: typing.Optional[str] = None,
      sort_option: typing.Optional[str] = None,
      index_id: typing.Optional[str] = None,
      status: typing.Optional[
          typing.Union[TasksListRequestStatusItem, typing.Sequence[TasksListRequestStatusItem]]
      ] = None,
      filename: typing.Optional[str] = None,
      duration: typing.Optional[float] = None,
      width: typing.Optional[int] = None,
      height: typing.Optional[int] = None,
      created_at: typing.Optional[str] = None,
      updated_at: typing.Optional[str] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> SyncPager[VideoIndexingTask]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  tasks = client.tasks.list(
      page=1,
      page_limit=5,
      sort_by="created_at",
      sort_option="desc",
      index_id="<YOUR_INDEX_ID>",
      status=["ready", "indexing"],
      filename="video.mp4",
      duration=20,
      width=640,
      height=360,
      created_at="2024-03-01T00:00:00Z",
      updated_at="2024-03-01T00:00:00Z",
  )

  if len(tasks.items) == 0:
      print("No tasks in the index, exiting")
      exit()
  for task in tasks:
      print(f"Task ID: {task.id}")
      print(f"Index ID: {task.index_id}")
      print(f"Video ID: {task.video_id}")
      print(f"Status: {task.status}")
      print("System metadata:")
      for key, value in (task.system_metadata):
          print(f"  {key}: {value}")
      print(f"Created at: {task.created_at}")
      if task.updated_at:
          print(f"Updated at: {task.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                                                                                                                                     | Required | Description                                                                                                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `page`            | `typing.Optional[int]`                                                                                                                   | No       | The page number to retrieve. Default: 1.                                                                                                                                                                |
| `page_limit`      | `typing.Optional[int]`                                                                                                                   | No       | The number of items per page. Default: 10. Max: 50.                                                                                                                                                     |
| `sort_by`         | `typing.Optional[str]`                                                                                                                   | No       | The field to sort by: `"created_at"` or `"updated_at"`. Default: `"created_at"`.                                                                                                                        |
| `sort_option`     | `typing.Optional[str]`                                                                                                                   | No       | The sort order: `"asc"` or `"desc"`. Default: `"desc"`.                                                                                                                                                 |
| `index_id`        | `typing.Optional[str]`                                                                                                                   | No       | Filter by the unique identifier of an index.                                                                                                                                                            |
| `status`          | `typing.`<br />`Optional`<br />`[typing.Union`<br />`[TasksListRequestStatusItem, typing.Sequence`<br />`[TasksListRequestStatusItem]]]` | No       | Filter by task status. Options: `"ready"`, `"uploading"`, `"validating"`, `"pending"`, `"queued"`, `"indexing"`, or `"failed"`. You can specify multiple statuses.                                      |
| `filename`        | `typing.Optional[str]`                                                                                                                   | No       | Filter by filename.                                                                                                                                                                                     |
| `duration`        | `typing.Optional[float]`                                                                                                                 | No       | Filter by duration in seconds.                                                                                                                                                                          |
| `width`           | `typing.Optional[int]`                                                                                                                   | No       | Filter by video width.                                                                                                                                                                                  |
| `height`          | `typing.Optional[int]`                                                                                                                   | No       | Filter by video height.                                                                                                                                                                                 |
| `created_at`      | `typing.Optional[str]`                                                                                                                   | No       | Filter video indexing tasks by the creation date and time, in the RFC 3339 format. The platform returns the video indexing tasks that were created on the specified date at or after the given time.    |
| `updated_at`      | `typing.Optional[str]`                                                                                                                   | No       | Filter video indexing tasks by the last update date and time, in the RFC 3339 format. The platform returns the video indexing tasks that were updated on the specified date at or after the given time. |
| `request_options` | `typing.Optional[RequestOptions]`                                                                                                        | No       | Request-specific configuration.                                                                                                                                                                         |

**Return value**: Returns a `SyncPager[VideoIndexingTask]` object that allows you to iterate through the paginated list of video indexing tasks.

The `VideoIndexingTask` class contains the following properties:

| Name              | Type                                        | Description                                                                           |
| ----------------- | ------------------------------------------- | ------------------------------------------------------------------------------------- |
| `id`              | `Optional[str]`                             | The unique identifier of the task.                                                    |
| `video_id`        | `Optional[str]`                             | The unique identifier of the video associated with the specified video indexing task. |
| `created_at`      | `Optional[str]`                             | The date and time, in the RFC 3339 format, that the task was created.                 |
| `updated_at`      | `Optional[str]`                             | The date and time, in the RFC 3339 format, that the task object was last updated.     |
| `status`          | `Optional[str]`                             | The status of the video indexing task.                                                |
| `index_id`        | `Optional[str]`                             | The unique identifier of the index to which the video must be uploaded.               |
| `system_metadata` | `Optional[VideoIndexingTaskSystemMetadata]` | System-generated metadata about the video.                                            |

The `VideoIndexingTaskSystemMetadata` class contains the following properties:

| Name       | Type              | Description                |
| ---------- | ----------------- | -------------------------- |
| `duration` | `Optional[float]` | The duration of the video. |
| `filename` | `Optional[str]`   | The filename of the video. |
| `height`   | `Optional[int]`   | The height of the video.   |
| `width`    | `Optional[int]`   | The width of the video.    |

**API Reference**: [List video indexing tasks](/v1.3/api-reference/upload-content/tasks/list).

## Delete a video indexing task

**Description**: This method deletes an existing video indexing task. This action cannot be undone. You can only delete video indexing tasks for which the status is `ready` or `failed`. If the status of your video indexing task is ready, you must first delete the video vector associated with your video indexing task.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def delete(self, task_id: str, *, request_options: typing.Optional[RequestOptions] = None) -> None
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client.tasks.delete(task_id="<YOUR_TASK_ID>")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                              | Required | Description                                                 |
| ----------------- | --------------------------------- | -------- | ----------------------------------------------------------- |
| `task_id`         | `str`                             | Yes      | The unique identifier of the video indexing task to delete. |
| `request_options` | `typing.Optional[RequestOptions]` | No       | Request-specific configuration.                             |

**Return value**: `None`. This method doesn't return any data upon successful completion.

**API Reference**: [Delete a video indexing task](/v1.3/api-reference/upload-content/tasks/delete).

## (Deprecated) Import videos

<Note title="Note">
  The cloud-to-cloud integrations feature will be deprecated on October 31, 2025. You can use the [`POST`](/v1.3/api-reference/upload-content/tasks/createe) method of the `/tasks` endpoint to upload files instead. Refer to the [Release notes](/v1.3/docs/get-started/release-notes#the-cloud-to-cloud-integrations-feature-will-be-deprecated) page for the necessary migration steps.
</Note>

**Description**:  An import represents the process of uploading and indexing all videos from the specified integration. This method initiates an asynchronous import and returns two lists: videos that will be imported, and videos that will not be imported, typically due to unmet prerequisites. The actual uploading and indexing of videos occur asynchronously after you invoke this method.

Your video files must meet requirements based on the models enabled for your index:

* [Marengo requirements](/v1.3/docs/concepts/models/marengo#video-file-requirements).
* [Pegasus requirements](/v1.3/docs/concepts/models/pegasus#video-file-requirements).
* If both models are enabled, the most restrictive limits apply.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      integration_id: str,
      *,
      index_id: str,
      incremental_import: typing.Optional[bool] = OMIT,
      retry_failed: typing.Optional[bool] = OMIT,
      user_metadata: typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> TransfersCreateResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  res = client.tasks.transfers.create(
      integration_id="<YOUR_INTEGRATION_ID>",
      index_id="<YOUR_INDEX_ID>",
      incremental_import=True,
      retry_failed=False,
      user_metadata={"category": "recentlyAdded", "batchNumber": 5},
  )
  if res.videos:
      for video in res.videos:
          print(f"Video: {video.video_id} {video.filename}")
  if res.failed_files:
      for failed_file in res.failed_files:
          print(f"Failed file: {failed_file.filename} {failed_file.error_message}")
  ```
</CodeGroup>

**Parameters**:

| Name                 | Type                                                             | Required | Description                                                                                                                                                                                                                                                                             |
| -------------------- | ---------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `integration_id`     | `str`                                                            | Yes      | The unique identifier of the integration for which you want to import videos.                                                                                                                                                                                                           |
| `index_id`           | `str`                                                            | Yes      | The unique identifier of the index to which the videos are being uploaded.                                                                                                                                                                                                              |
| `incremental_import` | `typing.Optional[bool]`                                          | No       | Specifies whether incremental sync is enabled. If `false`, all files in the bucket are synchronized. Default: `true`.                                                                                                                                                                   |
| `retry_failed`       | `typing.Optional[bool]`                                          | No       | Determines whether to retry failed uploads. If `true`, the platform attempts to re-upload failed files. Default: `false`.                                                                                                                                                               |
| `user_metadata`      | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` | No       | Metadata that helps you categorize your videos. You can specify a list of keys and values. Keys must be of type `string`, and values can be of the following types: `string`, `integer`, `float` or `boolean`. The metadata you specify applies to all videos imported in this request. |
| `request_options`    | `typing.Optional[RequestOptions]`                                | No       | Request-specific configuration.                                                                                                                                                                                                                                                         |

**Return value**: Returns a `TransfersCreateResponse` object containing two lists: videos that will be imported, and videos that will not be imported.

The `TransfersCreateResponse` class contains the following properties:

| Name           | Type                                                     | Description                                                                                                                                                                                      |
| -------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `failed_files` | `Optional[List[TransfersCreateResponseFailedFilesItem]]` | A list of the video files that failed to import. Typically, these files did not meet the [upload requirements](/v1.3/api-reference/tasks/cloud-to-cloud-integrations/create#video-requirements). |
| `videos`       | `Optional[List[TransfersCreateResponseVideosItem]]`      | A list of the videos that will be uploaded and indexed.                                                                                                                                          |

The `TransfersCreateResponseFailedFilesItem` class contains the following properties:

| Name            | Type            | Description                                           |
| --------------- | --------------- | ----------------------------------------------------- |
| `filename`      | `Optional[str]` | The filename of the video that failed to be imported. |
| `error_message` | `Optional[str]` | The error message if the import failed.               |

The `TransfersCreateResponseVideosItem` class contains the following properties:

| Name       | Type            | Description                                                                                                                |
| ---------- | --------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `video_id` | `Optional[str]` | The unique identifier of a video. This identifier identifies both the video itself and the associated video indexing task. |
| `filename` | `Optional[str]` | The filename of the video.                                                                                                 |

**API Reference**: [Import videos](/v1.3/api-reference/tasks/cloud-to-cloud-integrations/create).

**Related guide**: [Cloud-to-cloud integrations](/v1.3/docs/advanced/cloud-to-cloud-integrations).

## (Deprecated) Retrieve import status

<Note title="Note">
  The cloud-to-cloud integrations feature will be deprecated on October 31, 2025. You can use the [`POST`](/v1.3/api-reference/upload-content/tasks/createe) method of the `/tasks` endpoint to upload files instead. Refer to the [Release notes](/v1.3/docs/get-started/release-notes#the-cloud-to-cloud-integrations-feature-will-be-deprecated) page for the necessary migration steps.
</Note>

**Description**: This method retrieves the current status for each video from a specified integration and index, returning lists of videos grouped by their import status. Use this method to track import progress and troubleshoot potential issues across multiple operations.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def get_status(
      self,
      integration_id: str,
      *,
      index_id: str,
      request_options: typing.Optional[RequestOptions] = None
  ) -> TransfersGetStatusResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  status = client.tasks.transfers.get_status(
      integration_id="<YOUR_INTEGRATION_ID>",
      index_id="<YOUR_INDEX_ID>",
  )
  if status.not_imported:
      for filename in status.not_imported:
          print(f"Not imported: {filename}")
  if status.validating:
      for video in status.validating:
          print(f"Validating: {video.video_id} {video.filename} {video.created_at}")
  if status.pending:
      for video in status.pending:
          print(f"Pending: {video.video_id} {video.filename} {video.created_at}")
  if status.queued:
      for video in status.queued:
          print(f"Queued: {video.video_id} {video.filename} {video.created_at}")
  if status.indexing:
      for video in status.indexing:
          print(f"Indexing: {video.video_id} {video.filename} {video.created_at}")
  if status.ready:
      for video in status.ready:
          print(f"Ready: {video.video_id} {video.filename} {video.created_at}")
  if status.failed:
      for video in status.failed:
          print(f"Failed: {video.filename} {video.error_message}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                              | Required | Description                                                                                   |
| ----------------- | --------------------------------- | -------- | --------------------------------------------------------------------------------------------- |
| `integration_id`  | `str`                             | Yes      | The unique identifier of the integration for which to retrieve the status of imported videos. |
| `index_id`        | `str`                             | Yes      | The unique identifier of the index for which to retrieve the status of imported videos.       |
| `request_options` | `typing.Optional[RequestOptions]` | No       | Request-specific configuration.                                                               |
|                   |                                   |          |                                                                                               |

**Return value**: Returns a `TransfersGetStatusResponse` object containing lists of videos grouped by status.

The `TransfersGetStatusResponse` class contains the following properties:

| Name           | Type                              | Description                                              |
| -------------- | --------------------------------- | -------------------------------------------------------- |
| `not_imported` | `Optional[List[str]]`             | An array of filenames that haven't yet been imported.    |
| `validating`   | `Optional[List[VideoItem]]`       | An array of videos that are being validated.             |
| `pending`      | `Optional[List[VideoItem]]`       | An array of videos that are pending.                     |
| `queued`       | `Optional[List[VideoItem]]`       | An array of videos that are queued for import.           |
| `indexing`     | `Optional[List[VideoItem]]`       | An array of videos that are being indexed.               |
| `ready`        | `Optional[List[VideoItem]]`       | An array of videos that have successfully been imported. |
| `failed`       | `Optional[List[VideoItemFailed]]` | An array of videos that failed to import.                |

The `VideoItem` class contains the following properties:

| Name         | Type       | Description                                                                                |
| ------------ | ---------- | ------------------------------------------------------------------------------------------ |
| `video_id`   | `str`      | The unique identifier of the video.                                                        |
| `filename`   | `str`      | The name of the video file.                                                                |
| `created_at` | `datetime` | The date and time, in the RFC 3339 format, when the video was added to the import process. |

The `VideoItemFailed` class contains the following properties:

| Name            | Type       | Description                                                                                |
| --------------- | ---------- | ------------------------------------------------------------------------------------------ |
| `filename`      | `str`      | The name of the video file.                                                                |
| `created_at`    | `datetime` | The date and time, in the RFC 3339 format, when the video was added to the import process. |
| `error_message` | `str`      | The error message explaining why the video failed to import.                               |

**API Reference**: [Retrieve import status](/v1.3/api-reference/tasks/cloud-to-cloud-integrations/get-logs).

**Related guide**: [Cloud-to-cloud integrations](/v1.3/docs/advanced/cloud-to-cloud-integrations).

## (Deprecated) Retrieve import logs

<Note title="Note">
  The cloud-to-cloud integrations feature will be deprecated on October 31, 2025. You can use the [`POST`](/v1.3/api-reference/upload-content/tasks/create) method of the `/tasks` endpoint to upload files instead. Refer to the [Release notes](/v1.3/docs/get-started/release-notes#the-cloud-to-cloud-integrations-feature-will-be-deprecated) page for the necessary migration steps.
</Note>

**Description**: This method returns a chronological list of import operations for the specified integration, sorted by creation date with the oldest imports first. Each log entry includes the number of videos in each status and detailed error information for failed uploads.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def get_logs(
      self,
      integration_id: str,
      *,
      request_options: typing.Optional[RequestOptions] = None
  ) -> TransfersGetLogsResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  logs = client.tasks.transfers.get_logs(integration_id="<YOUR_INTEGRATION_ID>")
  if logs.data:
      for log in logs.data:
          print(
              f"index_id={log.index_id} index_name={log.index_name} created_at={log.created_at} ended_at={log.ended_at} video_status={log.video_status}"
          )
          if log.failed_files:
              for failed_file in log.failed_files:
                  print(
                      f"failed_file: {failed_file.filename} {failed_file.error_message}"
                  )
  else:
      print("No import logs found.")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                              | Required | Description                                                                     |
| ----------------- | --------------------------------- | -------- | ------------------------------------------------------------------------------- |
| `integration_id`  | `str`                             | Yes      | The unique identifier of the integration for which to retrieve the import logs. |
| `request_options` | `typing.Optional[RequestOptions]` | No       | Request-specific configuration.                                                 |

**Return value**: Returns a `TransfersGetLogsResponse` object containing a chronological list of import operations for the specified integration.

The `TransfersGetLogsResponse` class contains the following properties:

| Name   | Type                        | Description                             |
| ------ | --------------------------- | --------------------------------------- |
| `data` | `Optional[List[ImportLog]]` | An array that contains the import logs. |

The `ImportLog` class contains the following properties:

| Name           | Type                                       | Description                                                                                                                                                      |
| -------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `index_id`     | `Optional[str]`                            | The unique identifier of the index associated with this import.                                                                                                  |
| `index_name`   | `Optional[str]`                            | The name of the index associated with this import.                                                                                                               |
| `created_at`   | `Optional[datetime]`                       | The date and time, in the RFC 3339 format, when the import process was initiated.                                                                                |
| `ended_at`     | `Optional[datetime]`                       | The date and time, in the RFC 3339 format, when the platform completed importing your videos. A `null` value indicates that the import process is still ongoing. |
| `video_status` | `Optional[ImportLogVideoStatus]`           | Counts of files in different statuses.                                                                                                                           |
| `failed_files` | `Optional[List[ImportLogFailedFilesItem]]` | An array containing the video files that failed to import, along with details about the error.                                                                   |

The `ImportLogVideoStatus` class contains the following properties:

| Name         | Type  | Description                                           |
| ------------ | ----- | ----------------------------------------------------- |
| `ready`      | `int` | Count of videos that have successfully been imported. |
| `validating` | `int` | Count of videos that are being validated.             |
| `queued`     | `int` | Count of videos that are queued for import.           |
| `pending`    | `int` | Count of videos that are pending.                     |
| `indexing`   | `int` | Count of videos that are being indexed.               |
| `failed`     | `int` | Count of videos that failed to import.                |

The `ImportLogFailedFilesItem` class contains the following properties:

| Name            | Type            | Description                                       |
| --------------- | --------------- | ------------------------------------------------- |
| `filename`      | `Optional[str]` | The name of the video file that failed to import. |
| `error_message` | `Optional[str]` | A human-readable error message.                   |

**API Reference**: [Retrieve import logs](/v1.3/api-reference/tasks/cloud-to-cloud-integrations/get-logs).

**Related guide**: [Cloud-to-cloud integrations](/v1.3/docs/advanced/cloud-to-cloud-integrations).

# Error codes

This section lists the most common error messages you may encounter while uploading videos.

* `video_resolution_too_low`
  * The resolution of the video is too low. Please upload a video with resolution between 360x360 and 5184x2160. Current resolution is `{current_resolution}`.
* `video_resolution_too_high`
  * The resolution of the video is too high. Please upload a video with resolution between 360x360 and 5184x2160. Current resolution is `{current_resolution}`.
* `video_resolution_invalid_aspect_ratio`
  * The aspect ratio of the video is invalid. Please upload a video with aspect ratio between 1:1 and 2.4:1. Current resolution is `{current_resolution}`.
* `video_duration_too_short`
  * Video is too short. Please use video with duration between 10 seconds and 2 hours(7200 seconds). Current duration is `{current_duration}` seconds.
* `video_duration_too_long`
  * Video is too long. Please use video with duration between 10 seconds and 2 hours(7200 seconds). Current duration is `{current_duration}` seconds.
* `video_file_broken`
  * Cannot read video file. Please check the video file is valid and try again.
* `task_cannot_be_deleted`
  * (Returns raw error message)
* `usage_limit_exceeded`
  * Not enough free credit. Please register a payment method or contact [sales@twelvelabs.io](mailto:sales@twelvelabs.io).
* `video_filesize_too_large`
  * The video is too large. Please use a video with a size less than `{maximum_size}`. The current size is `{current_file_size}`.
