# Typical workflows

This page provides an overview of common workflows for interacting with the TwelveLabs Video Understanding Platform using an HTTP client. Each workflow consists of a series of steps, with links to detailed documentation for each step.

All workflows involving uploading video content to the platform require asynchronous processing. You must wait for the video processing to complete before proceeding with the subsequent steps.

# Authentication

The API uses keys for authentication. For details, see the [Authentication](/v1.3/api-reference/authentication) page.

# Search

Follow the steps in this section to search through your video content and find specific moments, scenes, or information.

**Steps**:

1. [Create an index](/v1.3/api-reference/indexes/create), enabling the Marengo video understanding model.
2. [Upload videos](/v1.3/api-reference/upload-content/tasks/create) and [monitor the processing](/v1.3/api-reference/upload-content/tasks/retrieve).
3. [Perform a search request](/v1.3/api-reference/any-to-video-search/make-search-request), using text or images as queries.

<Note title="Notes">
  * The search scope is an individual index.
  * Results support pagination, filtering, sorting, and grouping.
</Note>

For an interactive implementation using the [Python SDK](https://github.com/twelvelabs-io/twelvelabs-python), see the [Quickstart Search](https://colab.research.google.com/github/twelvelabs-io/twelvelabs-developer-experience/blob/main/quickstarts/TwelveLabs_Quickstart_Search.ipynb) quickstart notebook.

## Set up entity search

1. [Create an entity collection](/v1.3/api-reference/entities/entity-collections/create) to group related people.
2. [Create assets](/v1.3/api-reference/entities/assets/create) (reference images) for each person.
3. [Create entities](/v1.3/api-reference/entities/entity-collections/entities/create) and link them to their assets.
4. [Use entity IDs in search queries](/v1.3/api-reference/any-to-video-search/make-search-request) with the format `<@entity_id>`.

# Analyze videos

Follow the steps in this section to analyze videos and generate text based their content.

**Steps**:

1. [Create an index](/v1.3/api-reference/indexes/create), enabling the Pegasus video understanding model.
2. [Upload videos](/v1.3/api-reference/upload-content/tasks/create) and [monitor the processing](/v1.3/api-reference/upload-content/tasks/retrieve).
3. Depending on your use case, analyze videos and generate one of the following types of text:
   * [Titles, topics, and hashtags](/v1.3/api-reference/analyze-videos/gist)
   * [Summaries, chapters, and highlights](/v1.3/api-reference/analyze-videos/summarize)
   * [Open-ended analysis](/api-reference/analyze-videos/analyze).

For an interactive implementation using the [Python SDK](https://github.com/twelvelabs-io/twelvelabs-python), see the [Analyze](https://colab.research.google.com/github/twelvelabs-io/twelvelabs-developer-experience/blob/main/quickstarts/TwelveLabs_Quickstart_Analyze.ipynb) quickstart notebook.

# Create text, image, and audio embeddings

This workflow guides you through creating embeddings for text.

**Steps**:

1. [Create text, image, and audio embeddings](/v1.3/api-reference/create-embeddings-v1/text-image-audio-embeddings/create-text-image-audio-embeddings).

<Note title="Note">
  Creating text, image, and audio embeddings is a synchronous process.
</Note>

# Create video embeddings

This workflow guides you through creating embeddings for videos.

**Steps**:

1. [Upload a video](/v1.3/api-reference/create-embeddings-v1/video-embeddings/create-video-embedding-task) and [monitor the processing](/v1.3/api-reference/create-embeddings-v1/video-embeddings/retrieve-video-embedding-task-statuss).
2. [Retrieve the embeddings](/v1.3/api-reference/create-embeddings-v1/video-embeddings/retrieve-video-embeddings).

<Note title="Note">
  Creating video embeddings is a synchronous process.
</Note>

For an interactive implementation using the [Python SDK](https://github.com/twelvelabs-io/twelvelabs-python), see the [Quickstart Embed](https://colab.research.google.com/github/twelvelabs-io/twelvelabs-developer-experience/blob/main/quickstarts/TwelveLabs_Quickstart_Embeddings.ipynb) quickstart notebook.
