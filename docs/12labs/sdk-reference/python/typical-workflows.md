# Typical workflows

This page provides an overview of common workflows for using the TwelveLabs Python SDK. Each workflow consists of a series of steps, with links to detailed documentation for each step.

All workflows involving uploading video content to the platform require asynchronous processing. You must wait for the video processing to complete before proceeding with the subsequent steps.

# Prerequisites

Ensure that the following prerequisites are met before using the Python SDK:

* [Python](https://www.python.org) 3.7 or newer must be installed on your machine.
* To use the platform, you need an API key:
  <Steps>
    <Step>
      If you don’t have an account, [sign up](https://playground.twelvelabs.io/) for a free account.
    </Step>

    <Step>
      Go to the [API Keys](https://playground.twelvelabs.io/dashboard/api-keys) page.
    </Step>

    <Step>
      Select the **Copy** icon next to your key.
    </Step>
  </Steps>

# Install the SDK

Install the TwelveLabs SDK by enntering the following command:

```shell Shell
pip install twelvelabs
```

# Initialize the SDK

1. Import the required packages:

```python Python
from twelvelabs import TwelveLabs
```

2. Instantiate the SDK client with your API key.:

```python Python
client = TwelveLabs(api_key="<YOUR_API_KEY>")
```

# Search

Follow the steps in this section to search your video content for specific moments, scenes, or information.

**Steps**:

1. [Create an index](/v1.3/sdk-reference/python/manage-indexes#create-an-index), enabling the Marengo video understanding model.
2. [Upload videos](/v1.3/sdk-reference/python/upload-content/video-indexing-tasks#create-a-video-indexing-task) and monitor the processing.
3. [Perform a search request](/v1.3/sdk-reference/python/search#make-a-search-request),  using text or images as queries.

<Note title="Notes">
  * The search scope is an individual index.
  * Results support pagination, filtering, sorting, and grouping.
</Note>

## Set up entity search

1. [Create an entity collection](/v1.3/sdk-reference/python/manage-entities#create-an-entity-collection) to group related people.
2. [Create assets](/v1.3/sdk-reference/python/manage-entities#create-an-asset) (reference images) for each person.
3. [Create entities](/v1.3/sdk-reference/python/manage-entities#create-an-entity) and link them to their assets.
4. [Use entity IDs in search queries](/v1.3/sdk-reference/python/search#make-a-search-request) with the format `<@entity_id>`.

# Create text, image, and audio embeddings

This workflow guides you through creating embeddings for text.

**Steps**:

1. [Create text, image, and audio embeddings](/v1.3/sdk-reference/python/create-embeddings-v-1/create-text-image-and-audio-embeddings#create-text-image-and-audio-embeddings)

<Note title="Note">
  Creating text, image, and audio embeddings is a synchronous process.
</Note>

# Create video embeddings

This workflow guides you through creating embeddings for videos.

**Steps**:

1. [Upload a video](/v1.3/sdk-reference/python/create-embeddings-v-1/create-video-embeddings#create-a-video-embedding-task) and monitor the processing.
2. [Retrieve the embeddings](/v1.3/sdk-reference/python/create-embeddings-v-1/create-video-embeddings#retrieve-video-embeddings).

<Note title="Note">
  Creating video  embeddings is an asynchronous process.
</Note>

# Analyze videos

Follow the steps in this section to analyze your videos and generate text based on their content.

**Steps**:

1. [Create an index](/v1.3/sdk-reference/python/manage-indexes#create-an-index), enabling the Pegasus video understanding model.
2. [Upload videos](/v1.3/sdk-reference/python/upload-content/video-indexing-tasks#create-a-video-indexing-task) and monitor the processing.
3. Depending on your use case:

* [Generate titles, topics and hastags](/v1.3/sdk-reference/python/analyze-videos#titles-topics-and-hashtags)
* [Generate Summaries, chapters, and highlights](/v1.3/sdk-reference/python/analyze-videos#summaries-chapters-and-highlights)
* [Perform open-ended analysis](/v1.3/sdk-reference/python/analyze-videos#open-ended-analysis).
