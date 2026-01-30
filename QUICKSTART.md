# 🌱 Cresco - Brontend Integration Quick Start

## ✅ Integration Complete!

The Brontend (React frontend) is now fully connected to the Cresco backend (FastAPI + LangChain + Azure OpenAI).

---

## 🚀 How to Run

### Option 1: Use Startup Scripts (Easiest)

1. **Start Backend**: Double-click `start-backend.bat`
2. **Start Frontend**: Double-click `start-frontend.bat`
3. **Open Browser**: Go to http://localhost:5173

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd src
python -m cresco.main
```

**Terminal 2 - Frontend:**
```bash
cd brontend
npm install  # First time only
npm run dev
```

---

## 📋 What Changed

### ✨ New Files Created:
1. **`.env`** - Azure OpenAI configuration (API keys, endpoints)
2. **`brontend/src/services/api.js`** - API client for backend communication
3. **`start-backend.bat`** - Backend launcher script
4. **`start-frontend.bat`** - Frontend launcher script
5. **`INTEGRATION_GUIDE.md`** - Full technical documentation
6. **`INTEGRATION_COMPLETE.md`** - Detailed integration summary

### 🔧 Modified Files:
- **`brontend/src/App.jsx`** - Added conversation ID state and real API calls

---

## 🧪 Test It Out

1. **Open the app**: http://localhost:5173
2. **Try these queries**:
   - "How do I manage wheat diseases?"
   - "What nutrients does barley need?"
   - "Tell me about crop rotation"

3. **You should see**:
   - ✅ Real AI responses (no more "[offline stub]"!)
   - ✅ Source citations from knowledge base documents
   - ✅ Conversation memory across messages

---

## 🔗 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/chat` | POST | Send messages to chatbot |
| `/api/v1/health` | GET | Check backend status |
| `/api/v1/index` | POST | Index knowledge base docs |

**Base URL**: `http://localhost:8000/api/v1`

---

## 🏗️ Architecture

```
Frontend (React)  ──HTTP──>  Backend (FastAPI)
    ↓                              ↓
Port 5173                    Port 8000
                                   ↓
                          LangChain Agent
                                   ↓
                    ┌──────────────┴──────────────┐
                    ↓                             ↓
              ChromaDB                    Azure OpenAI
           (Vector Store)               (gpt-5.1-chat)
```

---

## 🛠️ Troubleshooting

### Backend won't start?
- Run: `pip install -e .` or `uv sync`
- Check: `.env` file exists and has valid API key

### Still seeing "[offline stub]"?
- Verify Azure OpenAI credentials in `.env`
- Check the API key is valid and hasn't expired

### "Error communicating with the server"?
- Make sure backend is running on port 8000
- Check browser console for errors

### No source citations?
- Index the knowledge base first:
  ```bash
  curl -X POST http://localhost:8000/api/v1/index
  ```

---

## 📚 Documentation

- **Full Guide**: See `INTEGRATION_GUIDE.md`
- **Summary**: See `INTEGRATION_COMPLETE.md`
- **This File**: Quick start reference

---

## 🎯 Current Status

✅ **Frontend-Backend Connection** - Working  
✅ **Azure OpenAI Integration** - Configured  
✅ **RAG Pipeline** - Operational  
✅ **Conversation Memory** - Active  
✅ **Source Citations** - Displaying  
❌ **Task Suggestions** - Not implemented yet  
❌ **File Upload Processing** - UI only  
❌ **Streaming Responses** - Not implemented  

---

## 📝 Environment Variables

Your `.env` file is configured with:
- **Model**: `gpt-5.1-chat` (Azure OpenAI)
- **Embeddings**: `text-embedding-3-small`
- **Endpoint**: Cresco AI Azure instance
- **Knowledge Base**: `./data/knowledge_base` (27+ documents)

---

## 🎓 How It Works

1. User types a message in the chat
2. Frontend calls `sendMessage()` from `api.js`
3. Backend receives request at `/api/v1/chat`
4. LangChain agent:
   - Searches ChromaDB for relevant docs
   - Sends query + context to Azure OpenAI
   - Generates response with citations
5. Frontend displays answer + sources

---

**Ready to chat with Cresco!** 🌾🤖

For detailed technical info, see `INTEGRATION_GUIDE.md`
