# NovaBuild Frontend Studio

The official browser-based single-page application for **NovaBuild**.

## Features

- **Prompt & Blueprint Studio**: Natural language idea input with real-time SSE progress streaming and interactive blueprint visualization (Project DNA, Entities, Fields, Pages, Navigation, RBAC).
- **Code Explorer**: Syntax-highlighted code tree inspector for generated Next.js 14 App Router projects, Supabase SQL schemas, and one-click ZIP download.
- **Projects Dashboard**: Manage, view, and inspect all created projects.
- **Iteration Studio**: Conversational modifications with visual diff and version bump tracking.
- **User Authentication**: Sign In, Sign Up, and User Session management.

## How to Run

1. **Start the NovaBuild Backend** (from the `backend/` directory):
   ```bash
   cd ../backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Open the Frontend**:
   You can open `index.html` directly in your browser, or serve it using any local static file server:

   ```bash
   # Using Python:
   python -m http.server 3000

   # Or using Node.js npx:
   npx serve .
   ```

3. Open [http://localhost:3000](http://localhost:3000) (or your local file URL) in your browser.
