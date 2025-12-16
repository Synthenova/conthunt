# Manage entities

<Info>
   The Entity Search feature is currently in beta.
</Info>

The SDK offers methods for managing entities related to video search. It operates with three types of resources:

* **Assets**: Reference images of the persons you wish to identify.
* **Entity collections**: Logical groupings of related entities, such as players on a team.
* **Entities**: Specific persons you want to locate in videos, associated with their reference images.

<Note title="Note">
  - To use the Entity Search feature, the Marengo 3.0 video understanding model must be enabled in your index.
  - The platform automatically creates a sample entity collection when you create your account. Users on the Free plan can have a total of one entity collection with up to fifteen entities. The default collection is included in this limit. To create more entity collections, upgrade to the Developer plan. For instructions, see the [Upgrade your plan](/v1.3/docs/get-started/manage-your-plan#upgrade-your-plan) section.
</Note>

# Assets

Assets are reference images that help identify people in videos. Upload multiple images per person to improve identification accuracy.

For a complete reference on how to create assets, see the [Direct uploads](/v1.3/sdk-reference/python/upload-content/direct-uploads) section.

# Entity collections

Entity collections organize related entities into logical groups.

## List entity collections

**Description**: This method returns a list of the entity collections in your account.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def list(
      self,
      *,
      page: typing.Optional[int] = None,
      page_limit: typing.Optional[int] = None,
      name: typing.Optional[str] = None,
      sort_by: typing.Optional[EntityCollectionsListRequestSortBy] = None,
      sort_option: typing.Optional[str] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> SyncPager[EntityCollection]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client = TwelveLabs(
      api_key="<YOUR_API_KEY",
  )

  response = client.entity_collections.list(
      # page=1,
      # page_limit=10,
      # name="<YOUR_ENTITY_COLLECTION_NAME>",
      # sort_option="desc",
  )

  for page in response.iter_pages():
      for collection in page:
          print(f"\nEntity collection ID: {collection.id}")
          print(f"Name: {collection.name}")
          print(f"Description: {collection.description}")
          print(f"Created at: {collection.created_at}")
          print(f"Updated at: {collection.updated_at}")
          print("-" * 50)
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                                                  | Required | Description                                                                                                                                                                                                                                                                                                                                                    |                                    |
| :---------------- | :---------------------------------------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `page`            | `typing.Optional[int]`                                | No       | A number that identifies the page to retrieve. Default: 1.                                                                                                                                                                                                                                                                                                     |                                    |
| `page_limit`      | `typing.Optional[int]`                                | No       | The number of items to return on each page. Default: 10. Max: 50                                                                                                                                                                                                                                                                                               |                                    |
| `name`            | `typing.Optional[str]`                                | No       |                                                                                                                                                                                                                                                                                                                                                                | Filter entity collections by name. |
| `sort_by`         | `typing.Optional[EntityCollectionsListRequestSortBy]` | No       | The field to sort on. The following options are available:<br />- `created_at`: Sorts by the time, in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when the entity collection was updated.<br />- `updated_at`: Sorts by the time, in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when the entity collection was created.<br />- `name`: Sorts by the name. |                                    |
| `sort_option`     | `typing.Optional[str]`                                | No       | The sorting direction. The following options are available: `asc` and `desc`. Default: `desc`.                                                                                                                                                                                                                                                                 |                                    |
| `request_options` | `typing.Optional[RequestOptions]`                     | No       | Request-specific configuration                                                                                                                                                                                                                                                                                                                                 |                                    |

**Return value**: Returns a `SyncPager[EntityCollection]` object containing a paginated list of `EntityCollection` objects, representing the entity collections that match the specified criteria.

The `SyncPager[T]` class contains the following properties and methods:

| Name           | Type                                             | Description                                                            |
| -------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| `items`        | `Optional[List[T]]`                              | A list containing the current page of items. Can be `None`.            |
| `has_next`     | `bool`                                           | Indicates whether there is a next page to load.                        |
| `get_next`     | `Optional[Callable[[], Optional[SyncPager[T]]]]` | A callable function that retrieves the next page. Can be `None`.       |
| `response`     | `Optional[BaseHttpResponse]`                     | The HTTP response object. Can be `None`.                               |
| `next_page()`  | `Optional[SyncPager[T]]`                         | Calls `get_next()` if available and returns the next page object.      |
| `__iter__()`   | `Iterator[T]`                                    | Allows iteration through all items across all pages using `for` loops. |
| `iter_pages()` | `Iterator[SyncPager[T]]`                         | Allows iteration through page objects themselves.                      |

The `EntityCollection` class contains the following properties:

| Name          | Type                                                                            | Description                                                                                                  |
| ------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `id`          | `typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier for the entity collection.                                                             |
| `name`        | `typing.Optional[str]`                                                          | The name of the entity collection.                                                                           |
| `description` | `typing.Optional[str]`                                                          | The description of the entity collection.                                                                    |
| `created_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was created.      |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was last updated. |

**API Reference**: [List entity collections](/v1.3/api-reference/entities/entity-collections/list)

## Create an entity collection

**Description**: This method creates an entity collection.

<Note>
  Free plan users can create one entity collection with up to 15 entities. If your needs exceed the Free plan, consider [upgrading to the Developer plan](/v1.3/docs/get-started/manage-your-plan#upgrade-your-plan).
</Note>

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      *,
      name: str,
      description: typing.Optional[str] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> EntityCollection
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.entity_collections.create(name="<YOUR_ENTITY_COLLECTION_NAME>", description="<YOUR_ENTITY_COLLECTION_DESCRIPTION>")

  print(f"Entity collection ID: {response.id}")
  print(f"Name: {response.name}")
  print(f"Description: {response.description}")
  print(f"Created at: {response.created_at}")
  print(f"Updated at: {response.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name              | Type                              | Required | Description                                                                           |
| :---------------- | :-------------------------------- | :------- | :------------------------------------------------------------------------------------ |
| `name`            | `str`                             | Yes      | The name of the entity collection. Make sure you use a succinct and descriptive name. |
| `description`     | `typing.Optional[str]`            | No       | A description of the entity collection.                                               |
| `request_options` | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                                                        |

**Return value**: Returns an object of type `EntityCollection` representing the newly created entity collection. The `EntityCollection` class contains the following properties:

| Name          | Type                                                                            | Description                                                                                                  |
| ------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `id`          | `typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier for the entity collection.                                                             |
| `name`        | `typing.Optional[str]`                                                          | The name of the entity collection.                                                                           |
| `description` | `typing.Optional[str]`                                                          | The description of the entity collection.                                                                    |
| `created_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was created.      |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was last updated. |

**API Reference**: [Create an entity collection](/v1.3/api-reference/entities/entity-collections/create)

## Retrieve an entity collection

**Description**: This method retrieves details about the specified entity collection.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def retrieve(
      self, entity_collection_id: str, *, request_options: typing.Optional[RequestOptions] = None
  ) -> EntityCollection
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = await client.entity_collections.retrieve("<YOUR_ENTITY_COLLECTION_ID>");

  print(f"Entity collection ID: {response.id}")
  print(f"Name: {response.name}")
  print(f"Description: {response.description}")
  print(f"Created at: {response.created_at}")
  print(f"Updated at: {response.updated_at}")

  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                                 |
| :--------------------- | :-------------------------------- | :------- | :---------------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection to retrieve. |
| `request_options`      | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                              |

**Return value**: Returns an object of type `EntityCollection` representing the specified entity collection. The `EntityCollection` class contains the following properties:

| Name          | Type                                                                            | Description                                                                                                  |
| ------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `id`          | `typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier for the entity collection.                                                             |
| `name`        | `typing.Optional[str]`                                                          | The name of the entity collection.                                                                           |
| `description` | `typing.Optional[str]`                                                          | The description of the entity collection.                                                                    |
| `created_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was created.      |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was last updated. |

**API Reference**: [Retrieve an entity collection](/v1.3/api-reference/entities/entity-collections/retrieve)

## Update an entity collection

**Description**: This method updates the specified entity collection.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def update(
      self,
      entity_collection_id: str,
      *,
      name: typing.Optional[str] = OMIT,
      description: typing.Optional[str] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> EntityCollection
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.entity_collections.update(entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>", name="<UPDATED_NAME>", description="<UPDATED_DESCRIPTION>")

  print(f"Entity collection ID: {response.id}")
  print(f"Name: {response.name}")
  print(f"Description: {response.description}")
  print(f"Created at: {response.created_at}")
  print(f"Updated at: {response.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                               |                                                   |
| :--------------------- | :-------------------------------- | :------- | :-------------------------------------------------------- | ------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection to update. |                                                   |
| `name`                 | `typing.Optional[str]`            | No       | The updated name of the entity collection.                |                                                   |
| `description`          | `typing.Optional[str]`            |          | No                                                        | The updated description of the entity collection. |
| `request_options`      | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                            |                                                   |

**Return value**: Returns an object of type `EntityCollection` representing the updated entity collection. The `EntityCollection` class contains the following properties:

| Name          | Type                                                                            | Description                                                                                                  |
| ------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `id`          | `typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier for the entity collection.                                                             |
| `name`        | `typing.Optional[str]`                                                          | The name of the entity collection.                                                                           |
| `description` | `typing.Optional[str]`                                                          | The description of the entity collection.                                                                    |
| `created_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was created.      |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                  | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity collection was last updated. |

**API Reference**: [Update an entity collection](/v1.3/api-reference/entities/entity-collections/update)

## Delete an entity collection

**Description**: This method deletes the specified entity collection. This action cannot be undone.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def delete(self, entity_collection_id: str, *, request_options: typing.Optional[RequestOptions] = None) -> None
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client.entity_collections.delete(entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                               |                                |
| :--------------------- | :-------------------------------- | :------- | :-------------------------------------------------------- | ------------------------------ |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection to delete. |                                |
| `request_options`      | `typing.Optional[RequestOptions]` |          | No                                                        | Request-specific configuration |

**Return value**: `None`. This method doesn't return any data upon successful completion.

**API Reference**: [Delete an entity collection](/v1.3/api-reference/entities/entity-collections/delete)

# Entities

Entities represent logical groupings of related entities.

## List entities in an entity collection

**Description**: This method returns a list of the entities in the specified entity collection.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def list(
      self,
      entity_collection_id: str,
      *,
      page: typing.Optional[int] = None,
      page_limit: typing.Optional[int] = None,
      name: typing.Optional[str] = None,
      status: typing.Optional[EntitiesListRequestStatus] = None,
      sort_by: typing.Optional[EntitiesListRequestSortBy] = None,
      sort_option: typing.Optional[str] = None,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> SyncPager[Entity]
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  response = client.entity_collections.entities.list(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      # page=1,
      # page_limit=10,
      # name="<YOUR_ENTITY_NAME>",
      # sort_option="desc",
  )
  for page in response.iter_pages():
      for entity in page:
          print(f"\nEntity ID: {entity.id}")
          print(f"Name: {entity.name}")
          print(f"Description: {entity.description}")
          print(f"Metadata: {entity.metadata}")
          print(f"Asset IDs: {entity.asset_ids}")
          print(f"Status: {entity.status}")
          print(f"Created at: {entity.created_at}")
          print(f"Updated at: {entity.updated_at}")
          print("-" * 50)
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                                         | Required | Description                                                                                                                                                                                                                                                                                                                              |                          |
| :--------------------- | :------------------------------------------- | :------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `entity_collection_id` | `str`                                        | Yes      | The unique identifier of the entity collection for which the platform will retrieve the entities.                                                                                                                                                                                                                                        |                          |
| `page`                 | `typing.Optional[int]`                       | No       | A number that identifies the page to retrieve. Default: 1.                                                                                                                                                                                                                                                                               |                          |
| `page_limit`           | `typing.Optional[int]`                       | No       | The number of items to return on each page. Default: 10. Max: 50.                                                                                                                                                                                                                                                                        |                          |
| `name`                 | `typing.Optional[str]`                       | No       |                                                                                                                                                                                                                                                                                                                                          | Filter entities by name. |
| `status`               | `typing.Optional[EntitiesListRequestStatus]` | No       | Filter entities by status. Values: `processing`, `ready`.                                                                                                                                                                                                                                                                                |                          |
| `sort_by`              | `typing.Optional[EntitiesListRequestSortBy]` | No       | The field to sort on. The following options are available:<br />- `created_at`: Sorts by the time, in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when the entity was created.<br />- `updated_at`: Sorts by the time, in the RFC 3339 format ("YYYY-MM-DDTHH:mm:ssZ"), when the entity was updated.<br />- `name`: Sorts by the name. |                          |
| `sort_option`          | `typing.Optional[str]`                       | No       | The sorting direction. The following options are available: `asc` and `desc`. Default: `desc`.                                                                                                                                                                                                                                           |                          |
| `request_options`      | `typing.Optional[RequestOptions]`            | No       | Request-specific configuration                                                                                                                                                                                                                                                                                                           |                          |

**Return value**: Returns a `SyncPager[Entity]` object containing a paginated list of `Entity` objects, representing the entities that match the specified criteria.

The `SyncPager[T]` class contains the following properties and methods:

| Name           | Type                                             | Description                                                            |
| -------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| `items`        | `Optional[List[T]]`                              | A list containing the current page of items. Can be `None`.            |
| `has_next`     | `bool`                                           | Indicates whether there is a next page to load.                        |
| `get_next`     | `Optional[Callable[[], Optional[SyncPager[T]]]]` | A callable function that retrieves the next page. Can be `None`.       |
| `response`     | `Optional[BaseHttpResponse]`                     | The HTTP response object. Can be `None`.                               |
| `next_page()`  | `Optional[SyncPager[T]]`                         | Calls `get_next()` if available and returns the next page object.      |
| `__iter__()`   | `Iterator[T]`                                    | Allows iteration through all items across all pages using `for` loops. |
| `iter_pages()` | `Iterator[SyncPager[T]]`                         | Allows iteration through page objects themselves.                      |

The `Entity` class contains the following properties:

| Name          | Type                                                                             | Description                                                                                       |                                                                                                                                                                                                                                                        |
| ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`          | ` typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                              |                                                                                                                                                                                                                                                        |
| `name`        | `typing.Optional[str]`                                                           | The name of the entity.                                                                           |                                                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                                           | A description of the entity.                                                                      |                                                                                                                                                                                                                                                        |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]`                 | Custom metadata for the entity.                                                                   |                                                                                                                                                                                                                                                        |
| `asset_ids`   | `typing.Optional[typing.List[str]]`                                              | An array of asset IDs associated with the entity.                                                 |                                                                                                                                                                                                                                                        |
| `status`      | `typing.Optional[EntityStatus]`                                                  | The status of the entity. Values: `processing`, `ready`.                                          | The current status of the entity creation process. Possible values are: <br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |
| `created_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was created.      |                                                                                                                                                                                                                                                        |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was last updated. |                                                                                                                                                                                                                                                        |

**API Reference**: [List entities in an entity collection](0/v1.3/api-reference/entities/entity-collections/entities/list)

## Create an entity

**Description**: This method creates an entity within a specified entity collection. Each entity must be associated with at least one asset.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create(
      self,
      entity_collection_id: str,
      *,
      name: str,
      asset_ids: typing.Sequence[str],
      description: typing.Optional[str] = OMIT,
      metadata: typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> Entity
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  entity = client.entity_collections.entities.create(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      name="<YOUR_ENTITY_NAME>",
      asset_ids=["<YOUR_ASSET_ID_1>", "<YOUR_ASSET_ID_2>"],
  )

  print(f"\nEntity ID: {entity.id}")
  print(f"Name: {entity.name}")
  print(f"Description: {entity.description}")
  print(f"Metadata: {entity.metadata}")
  print(f"Asset IDs: {entity.asset_ids}")
  print(f"Status: {entity.status}")
  print(f"Created at: {entity.created_at}")
  print(f"Updated at: {entity.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required                                                         | Description                                                                              |                                                                                                                                                                                                                                                                                                   |
| :--------------------- | :-------------------------------- | :--------------------------------------------------------------- | :--------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes                                                              | The unique identifier of the entity collection in which to create the entity.            |                                                                                                                                                                                                                                                                                                   |
| `name`                 | `str`                             | Yes                                                              | The name of the entity. Make sure you use a succinct and descriptive name.               |                                                                                                                                                                                                                                                                                                   |
| `asset_ids`            | `typing.Sequence[str]`            | Yes                                                              | An array of asset IDs to associate with the entity. You must provide at least one value. |                                                                                                                                                                                                                                                                                                   |
| `description`          | `typing.Optional[str]`            | No                                                               | A description of the entity.                                                             |                                                                                                                                                                                                                                                                                                   |
| `metadata`             |                                   | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` | No                                                                                       | Optional metadata for the entity, provided as key-value pairs to store additional context or attributes. Use metadata to categorize or describe the entity for easier management and search. Keys must be of type `string`, and values can be of type `string`, `integer`, `float`, or `boolean`. |
| `request_options`      | `typing.Optional[RequestOptions]` | No                                                               | Request-specific configuration                                                           |                                                                                                                                                                                                                                                                                                   |

**Return value**: Returns an object of type `Entity` representing the newly created entity. The `Entity` class contains the following properties:

| Name          | Type                                                                             | Description                                                                                       |                                                                                                                                                                                                                                                        |
| ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`          | ` typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                              |                                                                                                                                                                                                                                                        |
| `name`        | `typing.Optional[str]`                                                           | The name of the entity.                                                                           |                                                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                                           | A description of the entity.                                                                      |                                                                                                                                                                                                                                                        |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]`                 | Custom metadata for the entity.                                                                   |                                                                                                                                                                                                                                                        |
| `asset_ids`   | `typing.Optional[typing.List[str]]`                                              | An array of asset IDs associated with the entity.                                                 |                                                                                                                                                                                                                                                        |
| `status`      | `typing.Optional[EntityStatus]`                                                  | The status of the entity. Values: `processing`, `ready`.                                          | The current status of the entity creation process. Possible values are: <br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |
| `created_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was created.      |                                                                                                                                                                                                                                                        |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was last updated. |                                                                                                                                                                                                                                                        |

**API Reference**: [Create an entity](/v1.3/api-reference/entities/entity-collections/entities/create)

## Create multiple entities in bulk

**Description**: This method creates multiple entities within a specified entity collection in a single request. Each entity must be associated with at least one asset. This method is useful for efficiently adding multiple entities, such as a roster of players or a group of characters.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create_bulk(
      self,
      entity_collection_id: str,
      *,
      entities: typing.Sequence[EntitiesCreateBulkRequestEntitiesItem],
      request_options: typing.Optional[RequestOptions] = None,
  ) -> BulkCreateEntityResponse
  ```

  ```python Python example
  from twelvelabs import TwelveLabs
  from twelvelabs.entity_collections.entities import (
      EntitiesCreateBulkRequestEntitiesItem,
  )

  response = client.entity_collections.entities.create_bulk(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      entities=[
          EntitiesCreateBulkRequestEntitiesItem(
              name="<YOUR_ENTITY_NAME_1>",
              asset_ids=["<YOUR_ASSET_ID_1>", "<YOUR_ASSET_ID_2>"],
          )
      ],
  )

  print(f"Success Count: {response.success_count}")
  print(f"Failed Count: {response.failed_count}")

  if response.entities:
      for entity in response.entities:
          print(f"\nEntity ID: {entity.id}")
          print(f"Name: {entity.name}")
          print(f"Status: {entity.status}")
          print("-" * 50)

  if response.errors:
      for error in response.errors:
          print(f"\nError entity index: {error.entity_index}")
          print(f"Error entity name: {error.entity_name}")
          print(f"Error reason: {error.error_reason}")
          print("-" * 50)
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                                                     | Required | Description                                                                                                                                                                                                                                      |
| :--------------------- | :------------------------------------------------------- | :------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                                                    | Yes      | The unique identifier of the entity collection in which to create the entities.                                                                                                                                                                  |
| `entities`             | `typing.Sequence[EntitiesCreateBulkRequestEntitiesItem]` | Yes      | An array of objects, each representing an entity to be created. Each object must include the `name` and `asset_ids` properties, and can optionally include `description` and `metadata`. Each entity must be associated with at least one asset. |
| `request_options`      | `typing.Optional[RequestOptions]`                        | No       | Request-specific configuration                                                                                                                                                                                                                   |

The `EntitiesCreateBulkRequestEntitiesItem` class contains the following properties:

| Name          | Type                                                             | Description                                                                                                                                                                                                                                                                                       |
| ------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | `str`                                                            | The name of the entity. Make sure you use a succinct and descriptive name.                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                           | A description of the entity.                                                                                                                                                                                                                                                                      |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` | Optional metadata for the entity, provided as key-value pairs to store additional context or attributes. Use metadata to categorize or describe the entity for easier management and search. Keys must be of type `string`, and values can be of type `string`, `integer`, `float`, or `boolean`. |
| `asset_ids`   | `typing.List[str]`                                               | An array of asset IDs to associate with the entity. You must provide at least one value.                                                                                                                                                                                                          |

**Return value**: Returns an object of type `BulkCreateEntityResponse` representing the result of the bulk entity creation operation. The `BulkCreateEntityResponse` class contains the following properties:

| Name            | Type                                                                 | Description                                                                             |
| --------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `success_count` | `typing.Optional[int]`                                               | The number of entities that were successfully created.                                  |
| `failed_count`  | `typing.Optional[int]`                                               | The number of entities that failed to be created due to errors, such as missing assets. |
| `entities`      | `typing.Optional[typing.List[BulkCreateEntityResponseEntitiesItem]]` | An array of objects representing the entities that were successfully created.           |
| `errors`        | `typing.Optional[typing.List[BulkCreateEntityResponseErrorsItem]]`   | An array of error objects for entities that failed to be created.                       |

The `BulkCreateEntityResponseEntitiesItem` class contains the following properties:

| Name     | Type                                                                            | Description                                                                                                                                                                                                     |
| -------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`     | `typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                                                                                                                                            |
| `name`   | `typing.Optional[str]`                                                          | The name of the entity.                                                                                                                                                                                         |
| `status` | `typing.Optional[EntityStatus]`                                                 | The status of the entity. Values:<br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |

The `BulkCreateEntityResponseErrorsItem` class contains the following properties:

| Name           | Type                   | Description                                                                                                                       |
| -------------- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `entity_index` | `typing.Optional[int]` | The zero-based index of the entity in the original request array. This helps identify which specific entity failed to be created. |
| `entity_name`  | `typing.Optional[str]` | The name of the entity that failed to be created, as provided in the request.                                                     |
| `error_reason` | `typing.Optional[str]` | A message explaining why the entity failed to be created.                                                                         |

**API Reference**: [Create multiple entities in bulk](/v1.3/api-reference/entities/entity-collections/entities/create-bulk)

## Retrieve an entity

**Description**: This method retrieves details about the specified entity.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def retrieve(
          self, entity_collection_id: str, entity_id: str, *, request_options: typing.Optional[RequestOptions] = None
      ) -> Entity
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  entity = client.entity_collections.entities.retrieve(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      entity_id="<YOUR_ENTITY_ID>",
  )

  print(f"\nEntity ID: {entity.id}")
  print(f"Name: {entity.name}")
  print(f"Description: {entity.description}")
  print(f"Metadata: {entity.metadata}")
  print(f"Asset IDs: {entity.asset_ids}")
  print(f"Status: {entity.status}")
  print(f"Created at: {entity.created_at}")
  print(f"Updated at: {entity.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                                                          |
| :--------------------- | :-------------------------------- | :------- | :----------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection that contains the entity to retrieve. |
| `entity_id`            | `str`                             | Yes      | The unique identifier of the entity to retrieve.                                     |
| `request_options`      | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                                                       |

**Return value**: Returns an object of type `Entity` representing the specified entity. The `Entity` class contains the following properties:

| Name          | Type                                                                             | Description                                                                                       |                                                                                                                                                                                                                                                        |
| ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`          | ` typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                              |                                                                                                                                                                                                                                                        |
| `name`        | `typing.Optional[str]`                                                           | The name of the entity.                                                                           |                                                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                                           | A description of the entity.                                                                      |                                                                                                                                                                                                                                                        |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]`                 | Custom metadata for the entity.                                                                   |                                                                                                                                                                                                                                                        |
| `asset_ids`   | `typing.Optional[typing.List[str]]`                                              | An array of asset IDs associated with the entity.                                                 |                                                                                                                                                                                                                                                        |
| `status`      | `typing.Optional[EntityStatus]`                                                  | The status of the entity. Values: `processing`, `ready`.                                          | The current status of the entity creation process. Possible values are: <br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |
| `created_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was created.      |                                                                                                                                                                                                                                                        |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was last updated. |                                                                                                                                                                                                                                                        |

**API Reference**: [Retrieve an entity](/v1.3/api-reference/entities/entity-collections/entities/retrieve)

## Update an entity

**Description**:  This method updates the specified entity within an entity collection. This operation allows modification of the entity's name, description, or metadata. Note that this method does not affect the assets associated with the entity.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def update(
      self,
      entity_collection_id: str,
      entity_id: str,
      *,
      name: typing.Optional[str] = OMIT,
      description: typing.Optional[str] = OMIT,
      metadata: typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]] = OMIT,
      request_options: typing.Optional[RequestOptions] = None,
  ) -> Entity
  ```

  ```python Python example

  from twelvelabs import TwelveLabs

  entity = client.entity_collections.entities.update(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      entity_id="<YOUR_ENTITY_ID>",
      name="<UPDATED_NAME>",
      description="<UPDATED_DESCRIPTION>",
      metadata={"<KEY>": "<VALUE>"},
  )

  print(f"\nEntity ID: {entity.id}")
  print(f"Name: {entity.name}")
  print(f"Description: {entity.description}")
  print(f"Metadata: {entity.metadata}")
  print(f"Asset IDs: {entity.asset_ids}")
  print(f"Status: {entity.status}")
  print(f"Created at: {entity.created_at}")
  print(f"Updated at: {entity.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                                                             | Required | Description                                                                                   |
| :--------------------- | :--------------------------------------------------------------- | :------- | :-------------------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                                                            | Yes      | The unique identifier of the entity collection containing the entity to be updated.           |
| `entity_id`            | `str`                                                            | Yes      | The unique identifier of the entity to be updated.                                            |
| `name`                 | `typing.Optional[str]`                                           | No       | The updated name of the entity.                                                               |
| `description`          | `typing.Optional[str]`                                           | No       | The updated description of the entity.                                                        |
| `metadata`             | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` | No       | Updated metadata for the entity. If provided, this completely replaces the existing metadata. |
| `request_options`      | `typing.Optional[RequestOptions]`                                | No       | Request-specific configuration                                                                |

**Return value**: Returns an object of type `Entity` representing the updated entity. The `Entity` class contains the following properties:

| Name          | Type                                                                             | Description                                                                                       |                                                                                                                                                                                                                                                        |
| ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`          | ` typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                              |                                                                                                                                                                                                                                                        |
| `name`        | `typing.Optional[str]`                                                           | The name of the entity.                                                                           |                                                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                                           | A description of the entity.                                                                      |                                                                                                                                                                                                                                                        |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]`                 | Custom metadata for the entity.                                                                   |                                                                                                                                                                                                                                                        |
| `asset_ids`   | `typing.Optional[typing.List[str]]`                                              | An array of asset IDs associated with the entity.                                                 |                                                                                                                                                                                                                                                        |
| `status`      | `typing.Optional[EntityStatus]`                                                  | The status of the entity. Values: `processing`, `ready`.                                          | The current status of the entity creation process. Possible values are: <br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |
| `created_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was created.      |                                                                                                                                                                                                                                                        |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was last updated. |                                                                                                                                                                                                                                                        |

**API Reference**: [Update an entity](/v1.3/api-reference/entities/entity-collections/entities/update)

## Delete an entity

**Description**: This method deletes a specific entity from an entity collection. It permanently removes the entity and its associated data, but does not affect the assets associated with this entity.

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def delete(
          self, entity_collection_id: str, entity_id: str, *, request_options: typing.Optional[RequestOptions] = None
      ) -> None
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  client.entity_collections.entities.delete(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      entity_id="<YOUR_ENTITY_ID>",
  )
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                                                         |
| :--------------------- | :-------------------------------- | :------- | :---------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection containing the entity to be deleted. |
| `entity_id`            | `str`                             | Yes      | The unique identifier of the entity to be deleted.                                  |
| `request_options`      | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                                                      |

**Return value**: `None`. This method doesn't return any data upon successful completion.

**API Reference**: [Delete an entity](/v1.3/api-reference/entities/entity-collections/entities/delete)

## Add assets to an entity

**Description**: This method adds assets to the specified entity within an entity collection. Assets are used to identify the entity in media content, and adding multiple assets can improve the accuracy of entity recognition in searches. When assets are added, the entity may temporarily enter the "processing" state while the platform updates the necessary data. Once processing is complete, the entity status will return to "ready."

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def create_assets(
      self,
      entity_collection_id: str,
      entity_id: str,
      *,
      asset_ids: typing.Sequence[str],
      request_options: typing.Optional[RequestOptions] = None,
  ) -> Entity
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  entity = client.entity_collections.entities.create_assets(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      entity_id="<YOUR_ENTITY_ID>",
      asset_ids=["<YOUR_ASSET_ID_1>", "<YOUR_ASSET_ID_2>"],
  )

  print(f"\nEntity ID: {entity.id}")
  print(f"Name: {entity.name}")
  print(f"Description: {entity.description}")
  print(f"Metadata: {entity.metadata}")
  print(f"Asset IDs: {entity.asset_ids}")
  print(f"Status: {entity.status}")
  print(f"Created at: {entity.created_at}")
  print(f"Updated at: {entity.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                                                                            |
| :--------------------- | :-------------------------------- | :------- | :----------------------------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection that contains the entity to which assets will be added. |
| `entity_id`            | `str`                             | Yes      | The unique identifier of the entity to which assets will be added.                                     |
| `asset_ids`            | `typing.Sequence[str]`            | Yes      | An array of asset IDs to add to the entity.                                                            |
| `request_options`      | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                                                                         |

**Return value**: Returns an object of type `Entity` representing the updated entity with the newly added assets. The `Entity` class contains the following properties:

| Name          | Type                                                                             | Description                                                                                       |                                                                                                                                                                                                                                                        |
| ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`          | ` typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                              |                                                                                                                                                                                                                                                        |
| `name`        | `typing.Optional[str]`                                                           | The name of the entity.                                                                           |                                                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                                           | A description of the entity.                                                                      |                                                                                                                                                                                                                                                        |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]`                 | Custom metadata for the entity.                                                                   |                                                                                                                                                                                                                                                        |
| `asset_ids`   | `typing.Optional[typing.List[str]]`                                              | An array of asset IDs associated with the entity.                                                 |                                                                                                                                                                                                                                                        |
| `status`      | `typing.Optional[EntityStatus]`                                                  | The status of the entity. Values: `processing`, `ready`.                                          | The current status of the entity creation process. Possible values are: <br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |
| `created_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was created.      |                                                                                                                                                                                                                                                        |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was last updated. |                                                                                                                                                                                                                                                        |

**API Reference**: [Add assets to an entity](/v1.3/api-reference/entities/entity-collections/entities/add-assets)

## Remove assets from an entity

**Description**: This method removes from the specified entity. Assets are used to identify the entity in media content, and removing assets may impact the accuracy of entity recognition in searches if too few assets remain.

When assets are removed, the entity may temporarily enter a "processing" state while the system updates the necessary data. Once processing is complete, the entity status will return to "ready."

<Note title="Notes">
  * This operation only removes the association between the entity and the specified assets; it does not delete the assets themselves.
  * An entity must always have at least one asset associated with it. You can't remove the last asset from an entity.
</Note>

**Function signature and example**:

<CodeGroup>
  ```python Function signature
  def delete_assets(
      self,
      entity_collection_id: str,
      entity_id: str,
      *,
      asset_ids: typing.Sequence[str],
      request_options: typing.Optional[RequestOptions] = None,
  ) -> Entity
  ```

  ```python Python example
  from twelvelabs import TwelveLabs

  entity = client.entity_collections.entities.delete_assets(
      entity_collection_id="<YOUR_ENTITY_COLLECTION_ID>",
      entity_id="<YOUR_ENTITY_ID>",
      asset_ids=["<YOUR_ASSET_ID_1>", "<YOUR_ASSET_ID_2>"],
  )

  print(f"\nEntity ID: {entity.id}")
  print(f"Name: {entity.name}")
  print(f"Description: {entity.description}")
  print(f"Metadata: {entity.metadata}")
  print(f"Asset IDs: {entity.asset_ids}")
  print(f"Status: {entity.status}")
  print(f"Created at: {entity.created_at}")
  print(f"Updated at: {entity.updated_at}")
  ```
</CodeGroup>

**Parameters**:

| Name                   | Type                              | Required | Description                                                                                                |
| :--------------------- | :-------------------------------- | :------- | :--------------------------------------------------------------------------------------------------------- |
| `entity_collection_id` | `str`                             | Yes      | The unique identifier of the entity collection that contains the entity from which assets will be removed. |
| `entity_id`            | `str`                             | Yes      | The unique identifier of the entity from which assets will be removed.                                     |
| `asset_ids`            | `typing.Sequence[str]`            | Yes      | An array of asset IDs to remove from the entity.                                                           |
| `request_options`      | `typing.Optional[RequestOptions]` | No       | Request-specific configuration                                                                             |

**Return value**: Returns an object of type `Entity` representing the updated entity after the specified assets have been removed. The `Entity` class contains the following properties:

| Name          | Type                                                                             | Description                                                                                       |                                                                                                                                                                                                                                                        |
| ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`          | ` typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="_id")]` | The unique identifier of the entity.                                                              |                                                                                                                                                                                                                                                        |
| `name`        | `typing.Optional[str]`                                                           | The name of the entity.                                                                           |                                                                                                                                                                                                                                                        |
| `description` | `typing.Optional[str]`                                                           | A description of the entity.                                                                      |                                                                                                                                                                                                                                                        |
| `metadata`    | `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]`                 | Custom metadata for the entity.                                                                   |                                                                                                                                                                                                                                                        |
| `asset_ids`   | `typing.Optional[typing.List[str]]`                                              | An array of asset IDs associated with the entity.                                                 |                                                                                                                                                                                                                                                        |
| `status`      | `typing.Optional[EntityStatus]`                                                  | The status of the entity. Values: `processing`, `ready`.                                          | The current status of the entity creation process. Possible values are: <br />- `processing`: The entity is being processed and is not yet ready for use in searches.<br />- `ready`: The entity is fully processed and can be used in search queries. |
| `created_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was created.      |                                                                                                                                                                                                                                                        |
| `updated_at`  | `typing.Optional[dt.datetime]`                                                   | The date and time, in RFC 3339 format (“YYYY-MM-DDTHH:mm:ssZ”), when the entity was last updated. |                                                                                                                                                                                                                                                        |

**API Reference**: [Remove assets from an entity](/v1.3/api-reference/entities/entity-collections/entities/remove-assets)
