import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout/Layout';

// Pages
import Home from './pages/Home';
import Login from './pages/Auth/Login';
import Signup from './pages/Auth/Signup';
import ConfirmEmail from './pages/Auth/ConfirmEmail';
import ForgotPassword from './pages/Auth/ForgotPassword';
import ResetPassword from './pages/Auth/ResetPassword';
import KBList from './pages/KnowledgeBase/KBList';
import KBCreate from './pages/KnowledgeBase/KBCreate';
import KBDetails from './pages/KnowledgeBase/KBDetails';
import DocumentDetails from './pages/KnowledgeBase/DocumentDetails';
import AssistantsLayout from './pages/Assistants/AssistantsLayout';
import AssistantCreate from './pages/Assistants/AssistantCreate';
import ChatPage from './pages/Assistants/ChatPage';
import Profile from './pages/Profile/Profile';

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/confirm-email" element={<ConfirmEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Navigate to="/knowledge-bases" replace />} />

            {/* Knowledge Base Routes */}
            <Route path="/knowledge-bases" element={<KBList />} />
            <Route path="/knowledge-bases/create" element={<KBCreate />} />
            <Route path="/knowledge-bases/:id" element={<KBDetails />} />
            <Route path="/knowledge-bases/:kbId/documents/:docId" element={<DocumentDetails />} />

            {/* Assistant Routes (Unified Master-Detail Layout) */}
            <Route path="/assistants" element={<AssistantsLayout />}>
              <Route path="create" element={<AssistantCreate />} />
              <Route path=":id/edit" element={<AssistantCreate />} />
              <Route path=":assistantId/chat/:chatId" element={<ChatPage />} />
            </Route>

            {/* Profile Route */}
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Route>


        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
