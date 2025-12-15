# The index object

The `index` object is composed of the following fields:

* `_id`: A string representing the unique identifier of the index. It is assigned by the platform when an index is created.
* `index_name`: A string representing the name of the index.
* `models`: An array that specifies the [video understanding models](/v1.3/docs/concepts/models) and the [model options](/v1.3/docs/concepts/modalities#model-options) that are enabled for this index. Models determine what tasks you can perform with your videos. Model options determine which modalities the platform analyzes.
* `created_at`: A string representing the date and time, in the RFC 3339 format, that the index was created.
* `updated_at`: A string representing the date and time, in the RFC 3339 format, that the index was updated.
* `expires_at`: A string representing the date and time, in the RFC 3339 format, when your index will expire.
* `video_count`: An integer representing the number of videos in the index.
* `total_duration`: An integer representing the total duration of the videos in the index.
* `addons`: The list of add-ons that are enabled for this index.
