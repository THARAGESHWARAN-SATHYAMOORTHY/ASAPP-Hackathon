import React, { useState, useEffect, useRef } from 'react';
import { customerAPI } from '../services/api';
import './CustomerSupport.css';

const CustomerSupport = () => {
  const [messages, setMessages] = useState([
    {
      sender: 'system',
      text: 'Hello! I\'m your AI customer support assistant. How can I help you today?',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [needsInput, setNeedsInput] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      sender: 'user',
      text: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      let response;
      
      if (sessionId && needsInput) {
        // Send as additional input for existing session
        response = await customerAPI.sendInput(sessionId, inputValue);
      } else {
        // Send as new query
        response = await customerAPI.sendQuery(inputValue, sessionId);
      }

      // Update session ID if new
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      // Add system response
      const systemMessage = {
        sender: 'system',
        text: response.response,
        timestamp: new Date(),
        needsInput: response.needs_input,
        inputType: response.input_type,
      };

      setMessages(prev => [...prev, systemMessage]);
      setNeedsInput(response.needs_input || false);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        sender: 'system',
        text: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = async (query) => {
    setInputValue(query);
    // Trigger form submission
    setTimeout(() => {
      document.getElementById('message-form').requestSubmit();
    }, 100);
  };

  const quickActions = [
    { label: 'Cancel my flight', query: 'I want to cancel my flight' },
    { label: 'Check flight status', query: 'What is my flight status?' },
    { label: 'Seat availability', query: 'Show me available seats' },
    { label: 'Pet policy', query: 'Can I bring my pet on the flight?' },
    { label: 'Cancellation policy', query: 'What is your cancellation policy?' },
  ];

  return (
    <div className="customer-support">
      <div className="support-container">
        <div className="chat-container">
          <div className="chat-header">
            <h2>Customer Support Chat</h2>
            {sessionId && (
              <span className="session-id">Session: {sessionId.substring(0, 8)}...</span>
            )}
          </div>

          <div className="messages-container">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message ${message.sender === 'user' ? 'user-message' : 'system-message'} ${
                  message.isError ? 'error-message' : ''
                }`}
              >
                <div className="message-content">
                  <div className="message-text">{message.text}</div>
                  <div className="message-time">
                    {message.timestamp.toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message system-message">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form id="message-form" className="input-container" onSubmit={handleSendMessage}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              className="message-input"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="send-button"
              disabled={!inputValue.trim() || isLoading}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>

        <div className="quick-actions">
          <h3>Quick Actions</h3>
          <div className="actions-grid">
            {quickActions.map((action, index) => (
              <button
                key={index}
                className="action-button"
                onClick={() => handleQuickAction(action.query)}
                disabled={isLoading}
              >
                {action.label}
              </button>
            ))}
          </div>

          <div className="info-section">
            <h3>Sample PNR Numbers</h3>
            <p className="info-text">For testing, you can use:</p>
            <ul className="pnr-list">
              <li><code>ABC123</code> - JFK to LAX</li>
              <li><code>DEF456</code> - BOS to SFO</li>
              <li><code>GHI789</code> - ORD to MIA</li>
              <li><code>JKL012</code> - SEA to JFK</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerSupport;

