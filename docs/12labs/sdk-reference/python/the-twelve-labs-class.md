# The TwelveLabs class

The `TwelveLabs`  class is the main entry point for the SDK. It initializes the client and provides access to resources for uploading videos, managing indexes, performing searches, creating embeddings, and analyzing videos.

{/* # Properties

| Name       | Type                                                                                                                  | Description                                   |
| ---------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `indexes`    | `IndexesClient`      | Use this object to manage your indexes.       |
| `tasks`     | `TaskClientWrapper`         | Use this object to upload videos.             |
| `search`   | `SearchClientWrapper`     | Use this object to perform search requests.   |
| `embed`    | `EmbedClientWrapper`       | Use this object to create embeddings.         | */}

# Methods

## The initializer

**Description**: The constructor creates a new instance of the `TwelveLabs` class.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def __init__(
      self,
      *,
      api_key: typing.Optional[str] = None,
      **kwargs,
  )
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client = TwelveLabs(api_key="<YOUR_API_KEY>", timeout=180)
  ```
</CodeGroup>

**Parameters**:

| Name       | Type                   | Required | Description                                                                                                                                                                                                                 |
| :--------- | :--------------------- | :------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api_key`  | `typing.Optional[str]` | Yes      | Your TwelveLabs API key. If not provided, the `TWELVE_LABS_API_KEY` environment variable will be used.                                                                                                                      |
| `**kwargs` | `dict`                 | No       | Additional parameters to pass to the base client. You can pass a variable named `timeout` of type `float` to set the request timeout in seconds. The default timeout is 60 seconds, unless you use a custom `httpx` client. |

**Return value**:  None. This method initializes the instance.
