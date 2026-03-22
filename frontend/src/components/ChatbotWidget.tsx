import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { MessageCircle, X, Send, Sparkles } from 'lucide-react';
import { chatService } from '../services/chatService';
import { RootState } from '../store/store';

const suggestions = [
  'Explain my score',
  'How to improve?',
  'What documents do I need?',
  'Talk to a human',
];

interface Message {
  sender: 'user' | 'assistant';
  text: string;
}

const ChatbotWidget: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated } = useSelector((s: RootState) => s.auth);
  const submissionResult = useSelector((s: RootState) => s.application.submissionResult);
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'assistant', text: 'Hello! I\'m your Barclays loan assistant. I can help you understand your credit application, loan terms, and score. How can I help you today?' },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const applicationIdFromRoute = useMemo(() => {
    const match = location.pathname.match(/^\/result\/([^/]+)$/);
    if (!match || !match[1]) {
      return null;
    }
    return match[1];
  }, [location.pathname]);

  const activeApplicationId = applicationIdFromRoute || submissionResult?.application_id || null;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { sender: 'user', text }]);
    setInput('');
    setIsTyping(true);

    if (!isAuthenticated) {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Please sign in to use the assistant with your real application data.',
        },
      ]);
      return;
    }

    try {
      const res = await chatService.sendMessage(activeApplicationId, text);
      const serverResponse = res.data.response || 'I could not generate a response right now. Please try again.';
      setMessages((prev) => [...prev, { sender: 'assistant', text: serverResponse }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'I am having trouble connecting to the assistant service right now. Please try again in a moment.',
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-br from-barclays-navy to-barclays-teal text-white shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex items-center justify-center z-50"
          aria-label="Open chat assistant"
        >
          <MessageCircle size={24} />
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[380px] h-[560px] max-h-[80vh] bg-white rounded-2xl shadow-2xl border border-user-border flex flex-col z-50 overflow-hidden md:w-[380px] md:h-[560px] max-md:inset-0 max-md:w-full max-md:h-full max-md:rounded-none max-md:bottom-0 max-md:right-0">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-barclays-navy text-white">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <Sparkles size={16} />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold font-body">Barclays Assistant</h3>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-risk-low animate-pulse-dot" />
                <span className="text-xs opacity-80">Online</span>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/10 rounded-lg transition-colors">
              <X size={18} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`
                    max-w-[80%] px-4 py-2.5 rounded-2xl text-sm font-body whitespace-pre-line
                    ${msg.sender === 'user'
                      ? 'bg-barclays-navy text-white rounded-br-md'
                      : 'bg-gray-100 text-user-text rounded-bl-md shadow-sm'
                    }
                  `}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse-dot" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse-dot" style={{ animationDelay: '300ms' }} />
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse-dot" style={{ animationDelay: '600ms' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestion chips */}
          <div className="px-4 py-2 flex gap-2 overflow-x-auto border-t border-user-border">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => sendMessage(s)}
                className="shrink-0 px-3 py-1.5 text-xs font-medium text-barclays-navy bg-barclays-lightblue rounded-pill hover:bg-barclays-blue hover:text-white transition-colors duration-200"
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-user-border flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
              placeholder="Ask about your application..."
              className="flex-1 px-4 py-2.5 rounded-pill border border-user-border text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim()}
              className="w-10 h-10 rounded-full bg-barclays-teal text-white flex items-center justify-center hover:bg-barclays-navy transition-colors disabled:opacity-40"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatbotWidget;
