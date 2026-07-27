# Fulda Fall 2025 Team2 Frontend

React frontend application for the Fulda Fall 2025 Team2 project.

## Setup

### Prerequisites

- Node.js (v18 or higher recommended)
- npm (comes with Node.js)

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the `frontend` directory based on your backend configuration. 
   Example `.env`:
   ```env
   VITE_BASE_HTTP_URL=http://localhost:8000/api/
   VITE_BASE_WS_URL=ws://localhost:8000/ws/
   ```

## Running the Application

### Local Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173` (or the port shown in your terminal).

### Production Build

To build the application for production:

```bash
npm run build
```

To preview the production build locally:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── public/               # Static assets
├── src/
│   ├── assets/           # Images, fonts, etc.
│   ├── components/       # Reusable UI components (PascalCase)
│   │   ├── ui/           # Shadcn UI components
│   │   └── ...           # Feature-specific components
│   ├── lib/              # Utility libraries (e.g., utils.js)
│   ├── pages/            # Page components (PascalCase)
│   ├── store/            # Redux store and slices
│   │   └── slices/       # Redux slices (camelCase)
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # Entry point
│   └── routes.js         # API route definitions
├── index.html            # HTML entry point
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
└── README.md             # This file
```

## Naming Conventions

- **Components**: Use `PascalCase` (e.g., `Login.jsx`, `Header.jsx`).
- **Hooks**: Use `camelCase` starting with `use` (e.g., `useAuth.js`).
- **Utilities/Functions**: Use `camelCase` (e.g., `formatDate.js`).
- **Redux Slices**: Use `camelCase` (e.g., `authSlice.js`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`).

## Technology Stack

- **Framework**: [React](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Library**: [shadcn/ui](https://ui.shadcn.com/)
- **State Management**: [Redux Toolkit](https://redux-toolkit.js.org/)
- **Routing**: [React Router](https://reactrouter.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **HTTP Client**: [Axios](https://axios-http.com/)

## Linting

Run the linter to check for code quality issues:

```bash
npm run lint
```
