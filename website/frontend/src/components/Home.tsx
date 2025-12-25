import { useState, useRef, useEffect } from 'react';
import { Button, Offcanvas, Form, Card } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import Accordion from 'react-bootstrap/Accordion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from 'recharts';
function Home() {
  const [show, setShow] = useState(true);
  const [input, setInput] = useState('');
  const [chat, setChat] = useState([]); // [{ type: 'user' | 'bot', message, time }]
  const messagesEndRef = useRef(null);
  const toggleCanvas = () => setShow(!show);
  const [uploadStatus, setUploadStatus] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const TypingIndicator = () => (
    <div className="typing-indicator">
      <span className="dot"></span>
      <span className="dot"></span>
      <span className="dot"></span>
    </div>
  );




  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = input;
    setInput('');
    setChat(prev => [...prev, { type: 'user', message: userMessage, time: now }]);

    // 👉 Show "typing..."
    setIsTyping(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: {
          accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await res.json();
      const botTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      // ✅ Hide "typing..."
      setIsTyping(false);

      setChat(prev => [...prev, {
        type: 'bot',
        message: data.response || 'No response',
        time: botTime,
        persona: data.persona_detected,  // Add this
        ragUsed: data.rag_used,  // Add this
        ragSources: data.rag_sources
      }]);
    } catch (err) {
      const errTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setIsTyping(false);
      setChat(prev => [...prev, { type: 'bot', message: 'Error sending message', time: errTime }]);
    }
  };



  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat]);
  const [history, setHistory] = useState([]);


  useEffect(() => {
    fetch("http://127.0.0.1:8000/chat/history?user_id=user123&limit=5")
      .then((res) => res.json())
      .then((data) => setHistory(data.history || []));
  }, []);
  const [personaData, setPersonaData] = useState([]);


  // Fetch uploaded files on page load
  useEffect(() => {
    fetch("http://127.0.0.1:8000/uploaded-files")
      .then((res) => res.json())
      .then((data) => {
        if (data.files && data.files.length > 0) {
          setUploadedFiles(data.files);
        }
      })
      .catch((err) => console.error("Failed to fetch uploaded files:", err));
  }, []);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/persona-counts")
      .then((res) => res.json())
      .then((data) => {
        const formatted = Object.entries(data).map(([name, value]) => ({
          name,
          count: value,
        }));
        setPersonaData(formatted);
      });
  }, []);
  const modelStats = [
    { feature: 'Context Memory', value: 7 },
    { feature: 'Adaptivity', value: 9 },
    { feature: 'Speed', value: 8 },
    { feature: 'Model Size', value: 4.1 },
    { feature: 'Locality', value: 10 },
  ];
  const [activeKey, setActiveKey] = useState("0");
  const handleToggle = (key) => {
    if (activeKey === key) {
      // If the same item is clicked (to close), switch to the other
      setActiveKey(key === "0" ? "1" : "0");
    } else {
      setActiveKey(key); // Open new item
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploadStatus('Uploading...');

    try {
      const res = await fetch('http://127.0.0.1:8000/upload-document', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.status === 'success') {
        setUploadStatus('✅ ' + data.message);
        // Add file to the list
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          uploadedAt: new Date().toLocaleTimeString()
        }]);
      } else {
        setUploadStatus('❌ ' + data.message);
      }

      setTimeout(() => setUploadStatus(''), 5000);
    } catch (err) {
      setUploadStatus('❌ Upload failed');
      setTimeout(() => setUploadStatus(''), 5000);
    }
  };


  const handleDeleteFile = async (fileName) => {
    if (!window.confirm(`Delete ${fileName}?`)) return;

    try {
      const res = await fetch(`http://127.0.0.1:8000/delete-file/${fileName}`, {
        method: 'DELETE',
      });
      const data = await res.json();

      if (data.status === 'success') {
        setUploadedFiles(prev => prev.filter(f => f.name !== fileName));
        setUploadStatus('✅ File deleted');
      } else {
        setUploadStatus('❌ Delete failed');
      }
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (err) {
      setUploadStatus('❌ Delete failed');
      setTimeout(() => setUploadStatus(''), 3000);
    }
  };


  return (
    <div className="d-flex">
      {/* Sidebar */}
      <Offcanvas
        show={show}
        onHide={toggleCanvas}
        backdrop={false}
        scroll={true}
        style={{ width: '330px' }}
        className="border-end canvas-main"
      >
        <Offcanvas.Header >
          <Offcanvas.Title className="d-flex">
            <img
              src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTOuxrvcNMfGLh73uKP1QqYpKoCB0JLXiBMvA&s"
              style={{ height: '40px', width: '40px', borderRadius: '50%' }}
              alt=""
            />
            <h5 style={{ paddingLeft: '10px', paddingTop: '9px' }}>Anonymous</h5>
            <p style={{ paddingLeft: "130px", paddingTop: "5px", cursor: "pointer" }} onClick={toggleCanvas}><i className="fa-solid fa-bars-staggered" style={{ cursor: "pointer" }}></i></p>
          </Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Accordion defaultActiveKey="0" flush className="custom-accordion">
            <Accordion.Item eventKey="0">
              <Accordion.Header>Model Capabilities</Accordion.Header>
              <Accordion.Body>
                <ResponsiveContainer width="100%" height={200}>
                  <RadarChart cx="50%" cy="50%" outerRadius="65%" data={modelStats}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="feature" />
                    <PolarRadiusAxis angle={30} domain={[0, 10]} />
                    <Radar name="mistral:7b" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </Accordion.Body>
            </Accordion.Item>

            <Accordion.Item eventKey="2">
              <Accordion.Header>
                📄 Uploaded Documents {uploadedFiles.length > 0 && `(${uploadedFiles.length})`}
              </Accordion.Header>
              <Accordion.Body>
                {uploadedFiles.length === 0 ? (
                  <p style={{ fontSize: '0.9rem', color: '#666' }}>No files uploaded yet</p>
                ) : (
                  <div>
                    {uploadedFiles.map((file, index) => (
                      <div key={index} style={{
                        padding: '8px',
                        backgroundColor: '#f8f9fa',
                        borderRadius: '5px',
                        marginBottom: '8px',
                        fontSize: '0.85rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: '600', color: '#7678ee' }}>
                            📎 {file.name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#888', marginTop: '4px' }}>
                            {file.uploadedAt}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteFile(file.name)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#dc3545',
                            cursor: 'pointer',
                            fontSize: '16px',
                            padding: '4px'
                          }}
                          title="Delete file"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}

                  </div>
                )}
              </Accordion.Body>
            </Accordion.Item>
          </Accordion>
          <Accordion activeKey={activeKey} flush className="custom-accordion">
            <Accordion.Item eventKey="0" style={{ position: "fixed", bottom: "60px", width: "300px" }}>
              <Accordion.Header onClick={() => handleToggle("0")}>Persona Distribution</Accordion.Header>
              <Accordion.Body>
                {personaData.length === 0 ? (
                  <p>No data yet.</p>
                ) : (
                  <ResponsiveContainer style={{ marginLeft: "-50px" }} width="120%" height={200}>
                    <BarChart data={personaData}>
                      <XAxis dataKey="name" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8884d8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Accordion.Body>
            </Accordion.Item>
            <Accordion.Item eventKey="1" style={{ position: "fixed", bottom: "0px", width: "300px" }}>
              <Accordion.Header onClick={() => handleToggle("1")}>🧠 Conversation Insights</Accordion.Header>
              <Accordion.Body style={{ minHeight: "300px" }}>
                {history.length === 0 ? (
                  <p>No history yet.</p>
                ) : (
                  history.map((entry, index) => (
                    <div key={index} className="mb-3">
                      <div><strong>You:</strong> {entry.message}</div>
                      <div><strong>Bot:</strong> {entry.response}</div>
                      <hr />
                    </div>
                  ))
                )}
              </Accordion.Body>
            </Accordion.Item>
          </Accordion>
        </Offcanvas.Body>
      </Offcanvas>
      {/* Main Content */}
      <div
        className="flex-grow-1 d-flex flex-column"
        style={{
          marginLeft: show ? '330px' : '0',
          transition: 'margin-left 0.3s ease',
          height: '100vh',
        }}
      >
        <div className="flex-grow-1 overflow-auto" style={{ backgroundColor: 'white' }}>
          {/* Header */}
          <div className="main-2 d-flex">
            <img
              src="./logo1.png"
              style={{ height: '40px', width: '40px', borderRadius: '50%' }}
              className="mt-3 ms-4"
              alt=""
            />
            <h3 className="main-heading pt-3">
              <b style={{ fontSize: '20px' }}>Adaptive LLM</b>
              <br />
              <p style={{ paddingTop: '5px' }}>Conversational AI</p>
            </h3>
            <div style={{ position: 'fixed', right: '60px', top: '15px' }}>
              <label htmlFor="file-upload" style={{
                cursor: 'pointer',
                backgroundColor: '#7678ee',
                color: 'white',
                padding: '8px 12px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                display: 'inline-block'
              }}>
                📎 Upload File
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".pdf,.txt,.doc,.docx"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
              />
            </div>
            {uploadStatus && (
              <div style={{
                position: 'fixed',
                top: '60px',
                right: '20px',
                padding: '10px',
                backgroundColor: '#f0f0f0',
                borderRadius: '5px',
                fontSize: '12px'
              }}>
                {uploadStatus}
              </div>
            )}
            <i className="fa-solid fa-ellipsis-vertical" style={{ position: 'fixed', right: '20px', top: '20px' }}></i>
          </div>
          {!show && (
            <Button
              onClick={toggleCanvas}
              variant="primary"
              className="mb-3"
              style={{ position: 'fixed', top: '20px', left: '10px' }}
            >
              <i className="fa-solid fa-bars-staggered"></i>
            </Button>
          )}
          {/* Messages */}
          {chat.map((msg, idx) => (
            <div
              key={idx}
              className={`d-flex mt-2 ms-2 me-2 mb-3 ${msg.type === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
            >
              <div className={`d-flex align-items-start ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className="main-4">
                  <img
                    src={
                      msg.type === 'user'
                        ? 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTOuxrvcNMfGLh73uKP1QqYpKoCB0JLXiBMvA&s'
                        : './logo1.png'
                    }
                    className="main-4"
                    alt=""
                  />
                </div>
                <Card
                  bg={msg.type === 'user' ? '' : 'light'}
                  text={msg.type === 'user' ? 'white' : 'dark'}
                  className={`p-2 me-2 main-5 ${msg.type === 'user' ? 'from-user' : 'from-bot'}`}
                  style={{
                    borderRadius: "10px",
                    maxWidth: '75%',
                    minWidth: "60px",
                    backgroundColor: msg.type === 'user' ? '#7678ee' : '#f0f0f0',
                    border: 'none',
                  }}
                >
                  {/* 👇 Persona badge INSIDE Card, BEFORE message */}
                  {msg.type === 'bot' && msg.persona && (
                    <div style={{ marginBottom: '6px' }}>
                      <span style={{
                        fontSize: '0.65rem',
                        color: '#7678ee',
                        fontWeight: '600',
                        display: 'inline-block',
                        backgroundColor: '#e8e9ff',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        marginRight: '5px'
                      }}>
                        {msg.persona}
                      </span>
                      {msg.ragUsed && (
                        <span style={{
                          fontSize: '0.65rem',
                          color: '#28a745',
                          fontWeight: '600',
                          display: 'inline-block',
                          backgroundColor: '#d4edda',
                          padding: '2px 8px',
                          borderRadius: '10px'
                        }}>
                          {msg.ragSources} doc{msg.ragSources > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  )}
                  <Card.Text className="mb-0">{msg.message}</Card.Text>
                  <div className="text-end" style={{ fontSize: '0.75rem', opacity: 0.6, marginTop: '0px' }}>
                    {msg.time}
                  </div>
                </Card>
              </div>
            </div>
          ))}
          {/* 👇 Typing indicator */}
          {isTyping && (
            <div className="d-flex ms-2 mb-3 justify-content-start">
              <div className="d-flex align-items-start">
                <div className="main-4">
                  <img
                    src="./logo1.png"
                    className="main-4"
                    alt=""
                  />
                </div>
                <Card
                  bg="light"
                  text="dark"
                  className="p-2 me-2 main-5 from-bot"
                  style={{
                    borderRadius: "10px",
                    maxWidth: '75%',
                    backgroundColor: '#f0f0f0',
                    border: 'none',
                  }}
                >
                  <Card.Text className="mb-0">
                    <TypingIndicator />
                  </Card.Text>


                </Card>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
        {/* Input Area */}
        <div className="mb-3 pe-4 ps-4" style={{ backgroundColor: 'transparent' }}>
          <Form onSubmit={handleSubmit}>
            {uploadedFiles.length > 0 && (
              <div style={{
                fontSize: '0.75rem',
                color: '#7678ee',
                marginBottom: '8px',
                fontWeight: '500'
              }}>
                💡 {uploadedFiles.length} document{uploadedFiles.length > 1 ? 's' : ''} available for context
              </div>
            )}
            <Form.Group className="d-flex" style={{ backgroundColor: '#eeeffa', borderRadius: '8px' }}>
              <input
                type="text"
                style={{
                  outline: 'none',
                  width: '100%',
                  backgroundColor: '#eeeffa',
                  border: 'none',
                  borderRadius: '8px',
                  height: '45px',
                  paddingLeft: '10px',
                  fontSize: '15px',
                }}
                value={input}
                placeholder="Type a message..."
                className="form-input"
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    handleSubmit(e);
                  }
                }}
              />
              <Button
                type="submit"
                className="ms-2"
                style={{ transform: 'rotate(0deg)', backgroundColor: '#eeeffa', color: 'black', border: 'none' }}
              >
                <span style={{ fontSize: '25px', fontWeight: 'bold' }}>
                  <i className="fa-brands fa-telegram" style={{ color: '#7678ee' }}></i>
                </span>
              </Button>
            </Form.Group>
          </Form>
        </div>
      </div>
    </div>
  );
}
export default Home;
