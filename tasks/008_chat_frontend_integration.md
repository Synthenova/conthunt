# Chat Frontend Integration

## Objective
Implement a robust, responsive, and authenticated chat interface for the application, integrated as a global sidebar.

## Key Features Implemented

### 1. **Responsive Chat Sidebar**
   - **Desktop**: Persistent fixed sidebar (width: 500px) that slides in from the right.
     - **Layout Shift**: Implemented `ChatLayoutWrapper` to adjust the main content's right margin (`mr-[500px]`) when the sidebar is open, preventing overlay/dimming on desktop.
     - **Trigger**: Global floating action button (FAB) that toggles the sidebar.
   - **Mobile**: Uses Shadcn's `Sheet` component for a standard modal drawer experience with an overlay.
   - **Logic**: Used a custom `useMediaQuery` hook to switch implementations based on screen width (`md: 768px` breakpoint).
   - **Exclusion**: Sidebar is conditionally hidden on the `/billing` route.

### 2. **Chat Interface UI**
   - **Components**: Built using `prompt-kit` components (`Message`, `PromptInput`) and standard UI components (`ScrollArea`, `Popover`).
   - **Layout**: 
     - Fixed `ScrollArea` height issues by applying `min-h-0` and `flex-1` to the scroll container, ensuring the input area remains visible and "sticky" at the bottom.
     - Implemented "Recent Conversations" history using a `Popover` within the chat header.
   - **Theme**: Ensured consistent Dark Mode styling across the application.

### 3. **State Management**
   - **Store**: Created `useChatUI` (Zustand store) to manage the global `isOpen` state of the chat sidebar, allowing it to be controlled from anywhere (e.g., layout wrapper, sidebar component).

### 4. **API Integration & Refactoring**
   - **Service Layer**: Extracted all API calls into `src/lib/api/chats.ts` for better modularity.
     - `getChats`, `getMessages`, `createChat`, `deleteChat`, `sendMessage`.
     - **Authentication**: Automatically injects Firebase ID Token into `Authorization: Bearer <token>` headers for all requests.
   - **Hook Refactor**: Cleaned up `use-chat.ts` to focus solely on state management (Optimistic updates, `react-query` integration) and SSE connection logic.
   - **Streaming**: Switched from standard `EventSource` to `@microsoft/fetch-event-source` to support custom headers (Authorization) for Server-Sent Events.
   - **Data Handling**: Fixed response parsing for message arrays (unwrapping `{ messages: [] }` response from backend).

### 5. **Backend Synchronization**
   - **Delete Chat**: Implemented the missing `DELETE /v1/chats/{chat_id}` endpoint and corresponding `delete_chat` DB query (soft delete) to resolve frontend errors.
   - **Response Formats**: Verified and aligned backend JSON structures with frontend TypeScript interfaces.

## Files Created/Modified
- `src/app/layout.tsx`: Integrated `ChatLayoutWrapper` and restored `dark` theme class.
- `src/components/layout/chat-layout-wrapper.tsx`: New component for handling main content layout shifts.
- `src/components/chat/chat-sidebar.tsx`: Updated with responsive logic (Fixed Div vs Sheet).
- `src/components/chat/chat-interface.tsx`: UI implementation and layout fixes.
- `src/hooks/use-chat-ui.ts`: Zustand store for UI state.
- `src/hooks/use-chat.ts`: Refactored logic.
- `src/lib/api/chats.ts`: New API service layer.
- `tasks/008_chat_frontend_integration.md`: This documentation.

## Next Steps
- Implement tool usage visualization in the chat stream (if applicable).
- Add "Stop Generating" functionality for streaming responses.
- comprehensive end-to-end testing of the chat flow.
