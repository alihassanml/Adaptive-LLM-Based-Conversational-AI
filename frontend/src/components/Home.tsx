import React, { useState, useRef, useEffect } from 'react';
import { Button, Offcanvas, Form, Card } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

function Home() {
  const [show, setShow] = useState(true); // Sidebar default visible
  const [input, setInput] = useState('');
  const [chat, setChat] = useState([]); // [{ type: 'user' | 'bot', message }]
  const messagesEndRef = useRef(null);

  const toggleCanvas = () => setShow(!show);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput(''); // Clear input immediately

    // Add user message first
    setChat(prev => [...prev, { type: 'user', message: userMessage }]);

    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await res.json();
      const botResponse = data.response || 'No response';

      // Add bot response
      setChat(prev => [...prev, { type: 'bot', message: botResponse }]);
    } catch (err) {
      setChat(prev => [...prev, { type: 'bot', message: 'Error sending message' }]);
    }
  };

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat]);

  return (
    <div className="d-flex">
      {/* Sidebar */}
      <Offcanvas
        show={show}
        onHide={toggleCanvas}
        backdrop={false}
        scroll={true}
        style={{ width: '300px' }}
        className="border-end"
      >
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Sidebar</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <p>Navigation or tools here.</p>
        </Offcanvas.Body>
      </Offcanvas>

      {/* Main Content */}
      <div
        className="flex-grow-1 d-flex flex-column"
        style={{
          marginLeft: show ? '300px' : '0',
          transition: 'margin-left 0.3s ease',
          height: '100vh',
        }}
      >
        {/* Chat display area */}
        <div
          className="flex-grow-1 overflow-auto p-3"
          style={{ backgroundColor: '#f8f9fa' }}
        >
          {!show && (
            <Button onClick={toggleCanvas} variant="primary" className="mb-3">
              Show Menu
            </Button>
          )}

          {chat.map((msg, idx) => (
            <div
              key={idx}
              className={`d-flex mb-3 ${msg.type === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
            >
              <Card
                bg={msg.type === 'user' ? 'primary' : 'light'}
                text={msg.type === 'user' ? 'white' : 'dark'}
                className="p-2"
                style={{ maxWidth: '75%' }}
              >
                <Card.Text className="mb-0">{msg.message}</Card.Text>
              </Card>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area (fixed at bottom) */}
        <div className="border-top p-3 bg-white">
          <Form onSubmit={handleSubmit}>
            <Form.Group className="d-flex">
              <Form.Control
                type="text"
                value={input}
                placeholder="Type a message..."
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    handleSubmit(e);
                  }
                }}
              />
              <Button type="submit" variant="success" className="ms-2"style={{transform:"rotate(-90deg)"}}>
               <span style={{fontSize:"18px",fontWeight:"bold"}}>&#10139;</span>
              </Button>
            </Form.Group>
          </Form>
        </div>
      </div>
    </div>
  );
}

export default Home;
