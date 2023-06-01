# Voting System

## Overview:

The goal of this project is to create a simple voting system for product features. Users will be able to vote for their favorite product features, and the system will display the vote count for each feature, as well as the total number of votes in the last 10 minutes. The system will consist of two RESTful backend service endpoints: one for voting and one for displaying the result.

## Design:

The system will be implemented using Python and the Sanic web framework. We will use a PostgreSQL database to store the product features and their vote counts, as well as a table to store the votes. To make it easy to deploy and manage the system, we will use Docker Compose to define and run the backend services. The system will consist of two services: a web service running the Sanic app and a PostgreSQL service running the database.

## Implementation:

1. Setting up the environment

   - Install Docker and Docker Compose
   - Create a `Dockerfile` for the Sanic app
   - Create a `docker-compose.yml file` to define and run the backend services
   - Build and run the Docker containers
   - Run 'start.sh' to create the database and tables and populate the database with some sample data
   - The Sanic app should be running on port 8000 and the PostgreSQL database should be running on port 5432

2. Implementing the voting endpoint

   - Create a Sanic app
   - Define a route for the voting endpoint (/vote)
   - Parse the incoming JSON request to extract the feature ID
   - Validate the feature ID and return a 400 Bad Request response if it is invalid
   - Update the vote count for the feature in the database
   - Insert a new record into the votes table to log the vote
   - Return a JSON response indicating whether the vote was successful or not

3. Implementing the result endpoint
   - Create a route for the result endpoint (/result)
   - Query the database to get the vote count for each feature
   - Calculate the total number of votes in the last 10 minutes
   - Return a JSON response with the vote count for each feature and the total number of votes in the last 10 minutes

## Voting to Individual Product Feature

This endpoint allows users to vote for a specific product feature.

### Example Request

- URL: `POST /vote`
- Headers:
  - `Content-Type`: `application/json`
- Body:
  - `feature_id`: ID of the product feature to vote for (integer)

To vote for product feature with ID 1:

```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"feature_id": 1}' \
  http://localhost:8000/vote
```

Example request body:

```json
{
  "feature_id": 1
}
```

### Example Response

- Status code: `200 OK` or `400 Bad Request`
- Body:
  - `success`: `true` if the vote was successful, `false` otherwise (boolean)
  - `message`: A message indicating the result of the vote (string)

Example response body for a successful vote:

```json
{
  "success": true,
  "message": "Voted successfully"
}
```

Example response body for a failed vote due to an invalid feature ID:

```json
{
  "success": false,
  "message": "Invalid feature ID"
}
```

Example response body for a failed vote due to missing feature ID in request body:

```json
{
  "success": false,
  "message": "Missing feature ID in request body"
}
```

## Displaying the Result

This endpoint allows users to view the vote count for all product features and the total number of votes in the last 10 minutes.

### Request

- URL: `GET /result`
- Headers:
  - `Content-Type`: `application/json`

### Response

- Status code: `200 OK`
- Body:

  - `features`: A list of product features and their vote counts
    - `name`: Name of the product feature (string)
    - `cumulative_vote_count`: Number of votes for the product feature (integer)
  - `total_votes_last_10_min`: Total number of votes in the last 10 minutes (integer)

To get the result of the vote:

```
curl -X GET \
  -H "Content-Type: application/json" \
  http://localhost:8000/result
```

Example response body:

```json
{
  "features": [
    {
      "name": "P1_chatbot",
      "cumulative_vote_count": 10
    },
    {
      "name": "P2_user_generated_content",
      "cumulative_vote_count": 5
    },
    {
      "name": "P3_personalized_push",
      "cumulative_vote_count": 2
    }
  ],
  "total_votes_last_10_min": 20
}
```

In conclusion, I have designed and implemented a simple voting system for product features using Python, Sanic, and PostgreSQL, and deployed it using Docker Compose. The system consists of two RESTful backend service endpoints: one for voting and one for displaying the result. The system can be easily deployed and managed thanks to the use of Docker and Docker Compose. The system is also scalable and fault-tolerant thanks to the use of PostgreSQL as the database and the use of Docker Compose to define and run the backend services. The system can be easily extended to support more features and more users by adding more backend services and scaling up the database. The system can also be easily extended to support more types of votes by adding more tables to the database and adding more routes to the Sanic app.
