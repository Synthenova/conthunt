# Error codes

This page lists the most common error messages you may encounter while using the platform.

# General

* `parameter_invalid`
  * The `{parameter}` parameter is invalid.
  * The following parameters are invalid: `{parameters}`.
  * The request contains some invalid parameters.
* `parameter_not_provided`
  * The `{parameter}` parameter is required but was not provided.
  * The following required parameters were not provided: `{parameters}`.
  * Some required parameters are not provided.
* `parameter_unknown`
  * The `{parameter}` parameter is unknown.
  * The following parameters are unknown: `{parameters}`.
  * The request contains some unknown parameters.
* `resource_not_exist`
  * Resource with id `{resource_id}` does not exist in `{collection_name}`.
* `api_key_invalid`
  * API Key is either invalid or expired. Please check your API key or generate a new one from the dashboard and try again.
* `tags_not_allowed`
  * Tag `{tag}` is not allowed to use. Please remove it from the request.
  * The following tags are not allowed to be used: `{tags}`. Please remove these from the request.
* `api_upgrade_required`
  * This endpoint is supported starting with version `{version}`. Your version is `{current_version}`.

# The `/indexes` endpoint

* `index_option_cannot_be_changed`
  * Index option cannot be changed. Please remove index\_options parameter and try again. If you want to change index option, please create new index.
* `index_engine_cannot_be_changed`
  * Index engine cannot be changed. Please remove engine\_id parameter and try again. If you want to change engine, please create new index.
* `index_name_already_exists`
  * Index name `{index_name}` already exists. Please use another unique name and try again.

# The `/tasks` endpoint

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

# The `/search` endpoint

* `search_option_not_supported`
  * Search option `{search_option}` is not supported for index `{index_id}`. Please use one of the following search options: `{supported_search_option}`.
* `search_option_combination_not_supported`
  * Search option `{search_option}` is not supported with `{other_combination}`.
* `search_filter_invalid`
  * Filter used in search is invalid. Please use the valid filter syntax by following filtering documentation.
* `search_page_token_expired`
  * The token that identifies the page to be retrieved is expired or invalid. You must make a new search request. Token: `{next_page_token}`.
* `index_not_supported_for_search`:
  * You can only perform search requests on indexes with an engine from the Marengo family enabled.

# The `/analyze` endpoint

* `token_limit_exceeded`
  * Your request could not be processed due to exceeding maximum token limit. Please try with another request or another video with shorter duration.
* `index_not_supported_for_generate`
  * You can only summarize videos uploaded to an index with an engine from the Pegasus family enabled.

# The `/summarize` endpoint

* `token_limit_exceeded`
  * Your request could not be processed due to exceeding maximum token limit. Please try with another request or another video with shorter duration.

# The `/embed` endpoint

* `parameter_invalid`
  * The `text` parameter is invalid. The text token length should be less than or equal to 77.
  * The `text_truncate` parameter is invalid. You should use one of the following values: `none`, `start`, `end`.

# The `/embed/tasks` endpoint

* `parameter_invalid`
  * The `video_clip_length` parameter is invalid. `video_clip_length` should be within 2-10 seconds long
  * The `video_end_offset_sec` parameter is invalid. `video_end_offset_sec` should be greater than `video_start_offset_sec`

# The `/embed/tasks/{task-id}/status` endpoint

* `parameter_invalid`
  * The `task_id` parameter is invalid. `task_id` value is invalid
