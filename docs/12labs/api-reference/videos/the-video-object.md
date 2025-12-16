# The video object

The `video` object has the following fields:

* `_id`: A string representing the unique identifier of a video. The platform creates a new video object and assigns it a unique identifier when the video has been indexed. Note that video IDs are different from task IDs.
* `created_at`: A string indicating the date and time, in the RFC 3339 format, that the video indexing task was created.
* `indexed_at`: A string indicating the date and time, in the RFC 3339 format, that the video has finished indexing.
* `system_metadata`: An object that contains system-generated metadata about the video. It contains the following fields:
  * `duration`
  * `filename`
  * `fps`
  * `height`
  * `model_names`
  * `size`
  * `video_title`
  * `width`
* `user_metadata`: Any custom metadata you've specified by calling the [`PUT`](/v1.3/api-reference/videos/update)  method of the `/indexes/:index-id/videos/:video-id` endpoint.
* `hls`: The platform returns this object only for the videos that you uploaded with the `enable_video_stream` parameter set to `true`. This object has the following fields:
  * `video_url`: A string representing the URL of the video. You can use this URL to access the stream over the <a href="https://en.wikipedia.org/wiki/HTTP_Live_Streaming" target="_blank">HLS</a> protocol.
  * `thumbnail_urls`: An array containing the URL of the thumbnail.
  * `status`: A string representing the encoding status of the video file from its original format to a streamable format.
  * `updated_at`: A string indicating the date and time, in the RFC 3339 format, that the encoding status was last updated.
* `updated_at`: A string indicating the date and time, in the RFC 3339 format, that the video indexing task object was last updated. The platform updates this field every time the video indexing task transitions to a different state.
