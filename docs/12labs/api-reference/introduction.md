# Introduction

Use the TwelveLabs Video Understanding API to extract information from your videos and make it available to your applications. The API is organized around REST and returns responses in JSON format. It is compatible with most programming languages, and you can use one of the [available SDKs](/v1.3/docs/resources/twelve-labs-sd-ks), Postman, or other REST clients to interact with the API.

# Call an endpoint

To call an endpoint, you must construct a URL similar to the following one:

`{Method} {BaseURL}/{version}/{resource}/{path_parameters}?{query_parameters}`

The list below describes each component of a request:

* **Method**: The API supports the following methods:
  * `GET`: Reads data.
  * `POST`: Creates a new object or performs an action.
  * `PUT`: Updates an object.
  * `DELETE`: Deletes an object.\
    Note that the `POST` and `PUT` methods require you to pass a request body containing additional parameters.
* **Base URL**: The base URL of the API is `https://api.twelvelabs.io`.
* **Version**: To use this version of the API, it must be set to `v1.3`.
* **Resource**: The name of the resource you want to interact with.
* **Path Parameters**: Allow you to indicate a specific object. For example, you can retrieve details about an engine or index.
* **Query Parameters**: Any parameters that an endpoint accepts. For example, you can filter] or sort a response using query parameters.

Note that the API requires you to pass a header parameter containing your API key to authenticate each request. For details, see the [Authentication](/api-reference/authentication) page.

# Responses

TwelveLabs Video Understanding API follows the <a href="https://www.rfc-editor.org/rfc/rfc9110.html" target="_blank">RFC 9110</a> standard to indicate the success or failure of a request. Each response contains a field named `X-Api-Version` that indicates the version of the API against which the operation was performed.

## HTTP status codes

The following list is a summary of the HTTP status codes returned by the platform:

* `200`: The request was successful.
* `201`: The request was successful and a new resource was created.
* `400`: The API service cannot process the request. See the `code` and `message` fields in the response for more details about the error.
* `401`: The API key you provided is not valid. Note that, for security reasons, your API key automatically expires every two months. When your key has expired, you must generate a new one to continue using the API.
* `404`: The requested resource was not found.
* `429`: Indicates that a rate limit has been reached.

## Errors

HTTP status codes in the `4xx` range indicate an error caused by the parameters you provided in the request. For each error, the API service returns the following fields in the body of the response:

* `code`: A string representing the error code.
* `message`: A human-readable string describing the error, intended to be suitable for display in a user interface.
* *(Optional)* `docs_url`: The URL of the relevant documentation page.

For more details, see the [Error codes](/v1.3/api-reference/error-codes) page.
