#!/bin/bash
TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6IjM4MTFiMDdmMjhiODQxZjRiNDllNDgyNTg1ZmQ2NmQ1NWUzOGRiNWQiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiTmlybWFsIFYiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSTdLYVBLWmtFMGFTUks3ZUlURzYxd2RrVFRXa05fdE1yYk5LVS15OXV6OWNfZzFNeGs9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vY29udGh1bnQtZGV2IiwiYXVkIjoiY29udGh1bnQtZGV2IiwiYXV0aF90aW1lIjoxNzY1NjU2ODQxLCJ1c2VyX2lkIjoiUXdnNUV3VDNRUU9NRUFZVGV6amJxQmFPVG5LMiIsInN1YiI6IlF3ZzVFd1QzUVFPTUVBWVRlempicUJhT1RuSzIiLCJpYXQiOjE3NjU3MDE0MDMsImV4cCI6MTc2NTcwNTAwMywiZW1haWwiOiJuaXJtYWx2ZWx1MjAwMEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjExNDk1MTM2NzAwNDQ0NDY2ODM2MiJdLCJlbWFpbCI6WyJuaXJtYWx2ZWx1MjAwMEBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.NgB5NuDk5iOkVHxj2q63RTwtLzal75OFzbZYf4kJ3luux26YmGeki9rBV3tM7eOpne7rWadIF4LrSuKwju8aeN6G8O61s7VKzIhkbqVU_El38CN-L1HgkC6aqpOf0grbujOdLgJLZP0HKsOFYQ5sI2cKjowM0ygKiC_K3MXsdHYdQ_YU2BF5Pj7fZTpptxn59vM52jAr71fKuQ1bAmklJem-Df4tbJPfw418FZ5ilqRnKZ7LlNUPJ2gU3lQLF7M5V1HYtxcB4cNX_2RUWIiZ0qkfvAyiTYeECzbHT0Tz4S7W0vSc5s_uc05GnY5BsDMIxVnDPwPVi5sKdF8DDnM8VQ"
BASE_URL="http://localhost:8000/v1"

echo "--- 1. Creating Board ---"
BOARD_RESP=$(curl -s -X POST "$BASE_URL/boards/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Board 1"}')
echo $BOARD_RESP | jq .
BOARD_ID=$(echo $BOARD_RESP | jq -r .id)
echo "Board ID: $BOARD_ID"

echo -e "\n--- 2. Listing Boards ---"
curl -s -X GET "$BASE_URL/boards/" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n--- 3. Searching/Getting Content Item ---"
# We'll search to ensure we have content. 
SEARCH_RESP=$(curl -s -X POST "$BASE_URL/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "boards_test", "inputs": {"tiktok_keyword": {"sort_by": "relevance"}}}')

# Try to get first item
ITEM_ID=$(echo $SEARCH_RESP | jq -r '.results[0].content_item.id')
echo "Content Item ID: $ITEM_ID"

if [ "$ITEM_ID" != "null" ] && [ "$ITEM_ID" != "" ]; then
    echo -e "\n--- 4. Adding item to board ---"
    curl -s -X POST "$BASE_URL/boards/$BOARD_ID/items" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"content_item_id\": \"$ITEM_ID\"}" | jq .
      
    echo -e "\n--- 5. Listing items in board ---"
    curl -s -X GET "$BASE_URL/boards/$BOARD_ID/items" \
      -H "Authorization: Bearer $TOKEN" | jq .
      
    echo -e "\n--- 6. Global Board Search ---"
    curl -s -X GET "$BASE_URL/boards/search?q=test" \
      -H "Authorization: Bearer $TOKEN" | jq .

    echo -e "\n--- 7. Search IN board ---"
    curl -s -X GET "$BASE_URL/boards/$BOARD_ID/search?q=boards" \
      -H "Authorization: Bearer $TOKEN" | jq .

    echo -e "\n--- 8. Removing item ---"
    curl -s -X DELETE "$BASE_URL/boards/$BOARD_ID/items/$ITEM_ID" \
      -H "Authorization: Bearer $TOKEN" -v
fi

echo -e "\n--- 9. Deleting board ---"
curl -s -X DELETE "$BASE_URL/boards/$BOARD_ID" \
  -H "Authorization: Bearer $TOKEN" -v

echo "Done."
