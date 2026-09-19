import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowDown } from 'lucide-react';
import {
  ChatViewport,
  ChatInput,
  type Message,
  type ChatModes,
} from '@/components/chat';
import { Sidebar } from '@/components/sidebar';
import { WorkspaceViews } from '@/components/workspace/workspace-views';
import { useChat } from '@/hooks/useChat';
import { useDocuments } from '@/hooks/useDocuments';
import { useTheme } from '@/hooks/useTheme';

function App() {
  const { messages: rawMessages, isStreaming, sendMessage, clearMessages } = useChat();
  const { documents, uploading, setDocuments, setUploading, setError } = useDocuments();
  const { theme, toggleTheme } = useTheme();

  // Sidebar ALWAYS starts in collapsed mode when website loads (Item 8)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [activeModule, setActiveModule] = useState<string>('assistant');

  const mainScrollRef = useRef<HTMLDivElement>(null);
  const topAnchorRef = useRef<HTMLDivElement>(null);
  const footerAnchorRef = useRef<HTMLDivElement>(null);

  const [modes, setModes] = useState<ChatModes>({
    rag: false,
    reasoning: false,
    webSearch: false,
  });

  const messages: Message[] = useMemo(
    () =>
      rawMessages.map((msg) => ({
        id: String(msg.id),
        role: msg.sender === 'user' ? ('user' as const) : ('assistant' as const),
        content: msg.text,
        isStreaming: msg.isStreaming,
      })),
    [rawMessages],
  );

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content, modes.rag);
    },
    [sendMessage, modes.rag],
  );

  const handleNewChat = useCallback(() => {
    clearMessages();
    setActiveModule('assistant');
  }, [clearMessages]);

  const handleToggleSidebar = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev);
  }, []);

  
  // Functional Scroll Down to Footer/Team (Item 7)
  const handleScrollToFooter = useCallback(() => {
    const footerEl = document.getElementById("meet-the-team-footer");
    if (footerEl) {
      footerEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    if (mainScrollRef.current) {
      mainScrollRef.current.scrollTo({
        top: mainScrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
    try {
      window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: "smooth",
      });
    } catch {
      // ignore
    }
  }, []);

  const handleSwitchToAssistant = useCallback(
    (prompt?: string) => {
      setActiveModule('assistant');
      if (prompt) {
        setTimeout(() => {
          handleSend(prompt);
        }, 100);
      }
    },
    [handleSend],
  );

  // Keyboard shortcut listeners (Alt+N: New Chat, Ctrl+B / Alt+B: Toggle Sidebar)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.altKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        handleNewChat();
      }
      if ((e.ctrlKey || e.metaKey || e.altKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        handleToggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleNewChat, handleToggleSidebar]);

  const handleUploadStart = useCallback(
    (filename: string) => {
      setError(null);
      setUploading({ filename, progress: 0 });
    },
    [setError, setUploading],
  );

  const handleUploadProgress = useCallback(
    (filename: string, progress: number) => {
      setUploading({ filename, progress });
    },
    [setUploading],
  );

  const handleUploadEnd = useCallback(() => {
    setUploading(null);
  }, [setUploading]);

  const handleError = useCallback(
    (message: string) => {
      setError(message);
    },
    [setError],
  );

  const chatInputNode = (
    <div className="relative w-full">
      <ChatInput
        onSend={handleSend}
        isLoading={isStreaming}
        modes={modes}
        onModesChange={setModes}
        documents={documents}
        uploading={uploading}
        onDocumentsChange={setDocuments}
        onUploadStart={handleUploadStart}
        onUploadProgress={handleUploadProgress}
        onUploadEnd={handleUploadEnd}
        onError={handleError}
      />

      {/* Scroll-down option near search area at bottom/right (Item 7) */}
      <div className="flex justify-end max-w-4xl mx-auto px-4 -mt-2 mb-2">
        <motion.button
          onClick={handleScrollToFooter}
          whileHover={{ y: 2, scale: 1.04 }}
          whileTap={{ scale: 0.95 }}
          type="button"
          className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-card/90 border border-border/80 shadow-2xs hover:border-primary/50 hover:bg-primary/5 hover:text-primary text-[11px] font-medium text-muted-foreground transition-all cursor-pointer group"
          title="Scroll down to Meet the Team & Footer"
        >
          <span>Meet the Team</span>
          <ArrowDown className="w-3 h-3 text-primary group-hover:translate-y-0.5 transition-transform" />
        </motion.button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground transition-colors duration-200">
      {/* Left Sidebar (Starts Collapsed by Default, No Recents, Left-aligned bottom) */}
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={handleToggleSidebar}
        activeModule={activeModule}
        onSelectModule={setActiveModule}
        onNewChat={handleNewChat}
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenSettings={() => {}}
        onOpenProfile={() => {}}
      />

      {/* Main Workspace Area (NO TOP HEADER - starts naturally from top) */}
      <div
        ref={mainScrollRef}
        className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto overflow-x-hidden relative"
      >
        {/* Top anchor for reliable smooth Back to Top */}
        <div id="top-anchor" ref={topAnchorRef} className="h-0 w-0 pointer-events-none" />

        {activeModule === 'assistant' ? (
          <>
            {/* Viewport for messages or empty hero state */}
            <div className="flex-1 flex flex-col min-h-full">
              <ChatViewport
                messages={messages}
                onSelectSuggestion={handleSend}
              >
                {/* In empty state, the chat input sits comfortably below suggestions */}
                {messages.length === 0 ? chatInputNode : null}
              </ChatViewport>

              {/* In active chat, chat input stays docked at the bottom of the screen */}
              {messages.length > 0 && (
                <div className="sticky bottom-0 z-20 border-t border-border/40 bg-background/85 backdrop-blur-md">
                  {chatInputNode}
                </div>
              )}
            </div>

            {/* Footer anchor for reliable scroll-down */}
            <div ref={footerAnchorRef} className="h-0 w-0 pointer-events-none" />
          </>
        ) : (
          <motion.div
            key={activeModule}
            className="flex-1 min-h-0 flex flex-col overflow-hidden"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <WorkspaceViews
              activeModule={activeModule}
              onSwitchToAssistant={handleSwitchToAssistant}
              documents={documents}
              uploading={uploading}
              onDocumentsChange={setDocuments}
              onUploadStart={handleUploadStart}
              onUploadProgress={handleUploadProgress}
              onUploadEnd={handleUploadEnd}
              onError={handleError}
            />
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default App;