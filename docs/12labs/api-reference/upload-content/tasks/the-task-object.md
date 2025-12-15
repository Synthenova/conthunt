# The task object

A task represents a request to upload and index a video. The `task` object is composed of the following fields:

* `_id`: A string representing the unique identifier of the task. It is assigned by the platform service when a new task is created.
* `created_at`: A string indicating the date and time, in the RFC 3339 format, that the task was created.
* `estimated_time`: A string indicating the estimated date and time, in the RFC 3339 format, that the video is ready to be searched.
* `index_id`: A string representing the index to which the video has been uploaded.
* `video_id`: A string representing the unique identifier of the video associated with this video indexing task.
* `system_metadata`: An object that contains the system-generated metadata about the video
* `status`: A string indicating the status of the video indexing task. It can take one of the following values:
  * **Validating**: Your video has finished uploading, and the API service is validating it by ensuring it meets the requirements listed on the [Create a video indexing task](/v1.3/api-reference/upload-content/tasks/create) page.
  * **Pending**: The platform is spawning a new worker server to process your video.
  * **Queued**: A worker server has been assigned, and the platform is preparing to begin indexing.
  * **Indexing**: The platform transforms the video you uploaded into embeddings. An embedding is a compressed version of the video and contains all the information that TwelveLabs' deep-learning models need to perform downstream tasks.
  * **Ready**: The platform has finished indexing your video.
  * **Failed**: If an error occurs, the status is set to `Failed`.
* `hls`: The platform returns this object only for the videos that you uploaded with the `enable_video_stream` parameter set to `true`. This object has the following fields:
  * `video_url`: A string representing the URL of the video. You can use this URL to access the stream over the <a href="https://en.wikipedia.org/wiki/HTTP_Live_Streaming" target="_blank">HLS</a> protocol.
  * `thumbnail_urls`: An array containing the URL of the thumbnail.
  * `status`: A string representing the encoding status of the video file from its original format to a streamable format.
  * `updated_at`: A string indicating the date and time, in the RFC 3339 format, that the encoding status was last updated.
* `updated_at`: A string indicating the date and time, in the RFC 3339 format, that the task object was last updated. The API service updates this field every time the video indexing task transitions to a different state.
