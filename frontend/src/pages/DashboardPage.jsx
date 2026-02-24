import { useState, useCallback, useEffect, useRef } from 'react';
import { Box, Toolbar, useMediaQuery, useTheme } from '@mui/material';
import Sidebar, { SIDEBAR_WIDTH } from '../components/Sidebar';
import TopBar from '../components/TopBar';
import ChatPage from './ChatPage';
import ProfilePage from './ProfilePage';
import ResumesPage from './ResumesPage';
import { threadsAPI } from '../services/api';

const PAGE_TITLES = {
  chat: 'Chat',
  profile: 'Profile',
  resume: 'Resumes',
};

export default function DashboardPage() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activePage, setActivePage] = useState('chat');
  const [threads, setThreads] = useState([]);
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [loadedMessages, setLoadedMessages] = useState([]);
  const chatKeyRef = useRef(0);

  const toggleMobile = useCallback(() => setMobileOpen((p) => !p), []);

  // Load threads on mount
  useEffect(() => {
    threadsAPI.list()
      .then(({ data }) => {
        setThreads(data.threads || []);
      })
      .catch(() => {});
  }, []);

  const refreshThreads = useCallback(async () => {
    try {
      const { data } = await threadsAPI.list();
      setThreads(data.threads || []);
    } catch {}
  }, []);

  const navigate = useCallback((page) => setActivePage(page), []);

  const newChat = useCallback(() => {
    setActiveThreadId(null);
    setLoadedMessages([]);
    chatKeyRef.current += 1; // force remount
    setActivePage('chat');
  }, []);

  const selectThread = useCallback(async (id) => {
    if (id === activeThreadId) return;
    
    // Load messages FIRST, then mount ChatPage with them
    let msgs = [];
    try {
      const { data } = await threadsAPI.get(id);
      msgs = (data.messages || []).map((m) => ({
        role: m.role,
        content: m.content,
        attachments: m.attachments,
      }));
    } catch {}

    // Now update state all at once — ChatPage remounts with correct data
    setLoadedMessages(msgs);
    setActiveThreadId(id);
    chatKeyRef.current += 1;
    setActivePage('chat');
  }, [activeThreadId]);

  const deleteThread = useCallback(async (id) => {
    try {
      await threadsAPI.delete(id);
      setThreads((prev) => prev.filter((t) => t.id !== id));
      if (activeThreadId === id) {
        setActiveThreadId(null);
        setLoadedMessages([]);
        chatKeyRef.current += 1;
      }
    } catch {}
  }, [activeThreadId]);

  const renameThread = useCallback(async (id, newTitle) => {
    try {
      await threadsAPI.updateTitle(id, newTitle);
      setThreads((prev) => prev.map((t) => t.id === id ? { ...t, title: newTitle } : t));
    } catch {}
  }, []);

  // Called by ChatPage when a new thread is created from the first message
  // Just update the sidebar — do NOT remount ChatPage
  const handleNewThreadCreated = useCallback((threadId) => {
    setActiveThreadId(threadId);
    refreshThreads(); // adds the new thread to sidebar
  }, [refreshThreads]);

  const renderPage = () => {
    switch (activePage) {
      case 'profile': return <ProfilePage />;
      case 'resume': return <ResumesPage />;
      case 'chat':
      default:
        return (
          <ChatPage
            key={chatKeyRef.current}
            threadId={activeThreadId}
            initialMessages={loadedMessages}
            onNewThreadCreated={handleNewThreadCreated}
          />
        );
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar
        activePage={activePage}
        onNavigate={navigate}
        chatHistory={threads}
        onNewChat={newChat}
        onSelectChat={selectThread}
        onDeleteChat={deleteThread}
        onRenameChat={renameThread}
        activeChatId={activeThreadId}
        mobileOpen={mobileOpen}
        onMobileToggle={toggleMobile}
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1, display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
          width: isMobile ? '100%' : `calc(100% - ${SIDEBAR_WIDTH}px)`,
        }}
      >
        <TopBar
          title={PAGE_TITLES[activePage] || 'Chat'}
          onNavigate={navigate}
          onMobileMenuToggle={toggleMobile}
        />
        <Toolbar sx={{ minHeight: '52px !important' }} />
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          {renderPage()}
        </Box>
      </Box>
    </Box>
  );
}
