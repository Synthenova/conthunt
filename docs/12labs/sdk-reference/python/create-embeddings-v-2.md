# Create embeddings v2

Use the Embed API v2 to create embeddings for text, images, audio, and video content. Embeddings are vector representations that enable semantic search and content understanding.

<Note title="Note">
  This API only supports Marengo version 3.0 or newer.
</Note>

# Choose a method

* For text, images, or audio/video under 10 minutes use the [`embed.v_2.create`](/v1.3/sdk-reference/python/create-embeddings-v-2/create-sync-embeddings#create-sync-embeddings) method. This method returns embeddings immediately in the response.
* For audio and video up to 4 hours, use the [`embed.v_2.tasks.create`](/v1.3/sdk-reference/python/create-embeddings-v-2/create-async-embeddings#create-an-async-embedding-task) method. This method creates embeddings asynchronously
