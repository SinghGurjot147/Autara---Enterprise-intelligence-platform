import React, { useEffect, useRef } from "react"
import { ChatMessage, type Message } from "./chat-message"
import { Bot, Sparkles, Brain, FileText, Globe } from "lucide-react"
import { motion } from "framer-motion"


interface ChatViewportProps {
  messages: Message[]
  onSelectSuggestion?: (text: string) => void
  children?: React.ReactNode
  
}

export function ChatViewport({
  messages,
  onSelectSuggestion,
  children,
  
}: ChatViewportProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (messages.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  if (messages.length === 0) {
    return (
      <EmptyState
        onSelectSuggestion={onSelectSuggestion}
      >
        {children}
      </EmptyState>
    )
  }

  return (
    <div className="w-full flex-1 flex flex-col justify-between">
      <div className="max-w-4xl mx-auto w-full py-8 px-4 sm:px-6 space-y-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>

    </div>
  )
}

/* =========================================================
   EMPTY STATE (HERO + CARDS + SUGGESTIONS + INPUT + FOOTER)
   ========================================================= */

function EmptyState({
  onSelectSuggestion,
  children,
}: {
  onSelectSuggestion?: (text: string) => void
  children?: React.ReactNode
}) {
  return (
    <div className="relative w-full flex-1 flex flex-col items-center justify-start overflow-x-hidden pt-16 sm:pt-24">
      {/* Background ambient accents (subtle in light mode, richer in dark) */}
      <motion.div
        className="absolute w-72 h-72 rounded-full bg-purple-500/10 blur-3xl pointer-events-none"
        style={{ top: "5%", left: "10%" }}
        animate={{
          x: [0, 25, 0],
          y: [0, 15, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 9,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <motion.div
        className="absolute w-72 h-72 rounded-full bg-cyan-400/10 blur-3xl pointer-events-none"
        style={{ top: "15%", right: "10%" }}
        animate={{
          x: [0, -25, 0],
          y: [0, -15, 0],
          scale: [1, 1.08, 1],
        }}
        transition={{
          duration: 11,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Main Hero Container (Centered hero and chat box, with footer appearing right below on scroll) */}
      <div className="relative z-10 w-full max-w-4xl px-4 sm:px-6 text-center space-y-7 min-h-[88vh] flex flex-col justify-center py-10">
        {/* =================================================
            3D AI ORB
            ================================================= */}
        <div className="relative w-24 h-24 sm:w-28 sm:h-28 mx-auto mb-8 sm:mb-10">
          {/* Glow */}
          <motion.div
            className="absolute inset-[-25px] rounded-full bg-purple-500/20 blur-2xl dark:bg-purple-500/25"
            animate={{
              scale: [1, 1.18, 1],
              opacity: [0.35, 0.7, 0.35],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          {/* Outer Ring */}
          <motion.div
            className="absolute inset-[-12px] rounded-full border border-purple-400/30"
            animate={{ rotate: 360 }}
            transition={{
              duration: 14,
              repeat: Infinity,
              ease: "linear",
            }}
          />

          {/* Second Ring */}
          <motion.div
            className="absolute inset-[-6px] rounded-full border border-cyan-400/30"
            animate={{ rotate: -360 }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "linear",
            }}
          />

          {/* Orbit Dot */}
          <motion.div
            className="absolute inset-[-12px]"
            animate={{ rotate: 360 }}
            transition={{
              duration: 7,
              repeat: Infinity,
              ease: "linear",
            }}
          >
            <div className="absolute top-1/2 -left-1.5 w-2.5 h-2.5 rounded-full bg-purple-500 shadow-[0_0_12px_rgba(168,85,247,0.9)]" />
          </motion.div>

          {/* Main Orb Center */}
          <motion.div
            className="
              absolute
              inset-0
              rounded-full
              border
              border-border/80
              bg-card/90
              dark:border-white/10
              dark:bg-gradient-to-br
              dark:from-purple-500/30
              dark:via-background
              dark:to-cyan-400/20
              backdrop-blur-xl
              flex
              items-center
              justify-center
              shadow-md
            "
            animate={{
              boxShadow: [
                "0 0 20px rgba(168,85,247,0.2)",
                "0 0 45px rgba(168,85,247,0.4)",
                "0 0 20px rgba(168,85,247,0.2)",
              ],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            whileHover={{ scale: 1.06 }}
          >
            <Bot className="relative z-10 w-10 h-10 sm:w-11 sm:h-11 text-primary dark:text-purple-300 drop-shadow-[0_0_12px_rgba(168,85,247,0.6)]" />
          </motion.div>
        </div>

        {/* =================================================
            WELCOME TITLE & SUBTITLE
            ================================================= */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.45 }}
          className="mt-10"
        >
          <div className="inline-flex items-center justify-center gap-2.5 mb-4 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 shadow-2xs">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span className="text-[11px] uppercase tracking-[0.2em] font-bold text-primary">
              Intelligent Workspace
            </span>
            <Sparkles className="w-3.5 h-3.5 text-primary" />
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-foreground">
            Welcome to{" "}
            <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 dark:from-purple-300 dark:via-pink-300 dark:to-cyan-300 bg-clip-text text-transparent">
              Autara
            </span>
          </h1>

          <p className="mt-3 text-muted-foreground text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
            Your intelligent assistant for conversations, document Q&A, and research.
          </p>
        </motion.div>

        {/* =================================================
            CAPABILITY CARDS
            ================================================= */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          {capabilities.map((capability, index) => (
            <CapabilityCard
              key={capability.title}
              capability={capability}
              index={index}
            />
          ))}
        </div>

        {/* =================================================
            TRY ASKING SUGGESTIONS
            ================================================= */}
        <motion.div
          className="space-y-2.5"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.4 }}
        >
          <p className="text-[11px] uppercase tracking-widest text-muted-foreground font-semibold">
            Try asking
          </p>

          <div className="flex flex-wrap justify-center gap-2">
            {suggestions.map((suggestion) => (
              <motion.button
                key={suggestion}
                type="button"
                onClick={() => onSelectSuggestion?.(suggestion)}
                className="
                  px-3.5
                  py-1.5
                  rounded-full
                  border
                  border-border/80
                  bg-card
                  text-xs sm:text-sm
                  text-foreground/85
                  hover:border-primary/50
                  hover:bg-primary/5
                  hover:text-primary
                  shadow-2xs
                  cursor-pointer
                  transition-colors
                "
                whileHover={{
                  y: -2,
                  scale: 1.03,
                }}
                whileTap={{ scale: 0.97 }}
              >
                {suggestion}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* =================================================
            CHAT INPUT CONTAINER (Center of the workspace)
            ================================================= */}
        {children && (
          <div className="w-full pt-2">
            {children}
          </div>
        )}
      </div>

     
    </div>
  )
}

/* =========================================================
   CAPABILITY CARD
   ========================================================= */

function CapabilityCard({
  capability,
  index,
}: {
  capability: (typeof capabilities)[number]
  index: number
}) {
  const Icon =
    index === 0
      ? FileText
      : index === 1
        ? Brain
        : Globe

  return (
    <motion.div
      className="
        relative
        p-4.5
        rounded-2xl
        text-left
        border
        border-border/80
        bg-card
        dark:border-white/10
        dark:bg-white/[0.035]
        shadow-xs
        hover:shadow-xl
        hover:shadow-primary/10
        hover:border-primary/40
        overflow-hidden
        transition-all
      "
      style={{ transformStyle: "preserve-3d", perspective: 800 }}
      whileHover={{
        y: -6,
        rotateX: 4,
        rotateY: -3,
        scale: 1.025,
        transition: { duration: 0.25, ease: "easeOut" },
      }}
    >
      <div className="relative z-10">
        <div className="
          w-9
          h-9
          rounded-xl
          flex
          items-center
          justify-center
          mb-3
          bg-primary/10
          border
          border-primary/20
          text-primary
        ">
          <Icon className="w-4.5 h-4.5 text-primary" />
        </div>

        <h3 className="text-xs sm:text-sm font-semibold text-foreground mb-1">
          {capability.title}
        </h3>

        <p className="text-[11.5px] text-muted-foreground leading-relaxed">
          {capability.description}
        </p>
      </div>
    </motion.div>
  )
}

/* =========================================================
   DATA
   ========================================================= */

const capabilities = [
  {
    title: "Document Q&A",
    description:
      "Upload Markdown files for intelligent document-based Q&A.",
  },
  {
    title: "(WIP) Deep Reasoning",
    description:
      "(WIP) Enable step-by-step reasoning for complex problem solving.",
  },
  {
    title: "(WIP) Web Research",
    description:
      "(WIP) Search the web in real-time to find current information.",
  },
]

const suggestions = [
  "Explain quantum computing",
 
  "Summarize a document",
  "Help me brainstorm",
]